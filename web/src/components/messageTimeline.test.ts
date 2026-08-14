import { describe, it, expect } from 'vitest';
import { buildDisplayItems, type DisplayItem } from './messageTimeline';
import type { WsServerMessage } from '../hooks/useWebSocket';

type UserTask = { text: string; files?: Array<{ name: string; size: number }> };

/** Flatten agent-groups into document order (user / session items stay top-level). */
function flatten(items: DisplayItem[]): DisplayItem[] {
  const out: DisplayItem[] = [];
  for (const it of items) {
    if (it.kind === 'agent-group' && it.children) out.push(...it.children);
    else out.push(it);
  }
  return out;
}

function posOf(items: DisplayItem[], pred: (d: DisplayItem) => boolean): number {
  const i = items.findIndex(pred);
  if (i === -1) throw new Error('expected item not found in display order');
  return i;
}

const user = (content: string) => (d: DisplayItem) =>
  d.kind === 'user' && (d.data as { content: string }).content === content;
const llm = (needle: string) => (d: DisplayItem) =>
  d.kind === 'llm' && (d.data as { content: string }).content.includes(needle);
const tool = () => (d: DisplayItem) => d.kind === 'tool';

/**
 * WS event stream of a two-turn conversation where turn 1 uses a tool:
 * idle→planning, tool-use decision, planning→executing, read_file,
 * executing→observing, observing→planning (MID-TURN — the loop returns to
 * planning to generate the final answer), final llm.response, session.complete.
 * Turn 2 then starts with completed→planning.
 */
function twoTurnMessages(): WsServerMessage[] {
  return [
    // ---- turn 1 ----
    { type: 'state.change', from: 'idle', to: 'planning' },
    { type: 'llm.response', content: '' },
    { type: 'state.change', from: 'planning', to: 'executing' },
    { type: 'tool.invoke', tool: 'read_file', args: { path: 'README.md' } },
    { type: 'tool.result', tool_name: 'read_file', exit_code: 0, stdout: 'hi' },
    { type: 'state.change', from: 'executing', to: 'observing' },
    { type: 'state.change', from: 'observing', to: 'planning' }, // mid-turn planning
    { type: 'llm.response', content: 'Turn 1 final answer.' },
    { type: 'session.complete' },
    // ---- turn 2 ----
    { type: 'state.change', from: 'completed', to: 'planning' },
    { type: 'llm.response', content: 'Turn 2 answer.' },
    { type: 'session.complete' },
  ];
}

describe('buildDisplayItems — multi-turn ordering', () => {
  it('keeps each turn as one block: turn 2 user message comes after turn 1 final answer', () => {
    // Regression: both user messages are already in userTasks when the walk
    // runs (user sends task 2 after turn 1 finished). The mid-turn
    // observing→planning transition of turn 1 must NOT emit the second user
    // message — it belongs to turn 2, which starts at completed→planning.
    const tasks: UserTask[] = [{ text: 'Task one' }, { text: 'Task two' }];
    const flat = flatten(buildDisplayItems(twoTurnMessages(), 'Task two', 'idle', undefined, tasks));

    expect(posOf(flat, user('Task one'))).toBeLessThan(posOf(flat, tool()));
    expect(posOf(flat, tool())).toBeLessThan(posOf(flat, llm('Turn 1 final answer')));
    // The heart of the bug: user 2 used to be emitted at observing→planning,
    // landing between the tool card and turn 1's final answer.
    expect(posOf(flat, llm('Turn 1 final answer'))).toBeLessThan(posOf(flat, user('Task two')));
    expect(posOf(flat, user('Task two'))).toBeLessThan(posOf(flat, llm('Turn 2 answer')));
  });

  it('does not emit the next user message at a correcting→planning retry', () => {
    const messages: WsServerMessage[] = [
      { type: 'state.change', from: 'idle', to: 'planning' },
      { type: 'llm.response', content: '' },
      { type: 'state.change', from: 'planning', to: 'executing' },
      { type: 'tool.invoke', tool: 'execute_shell', args: { command: 'pytest' } },
      { type: 'tool.result', tool_name: 'execute_shell', exit_code: 1, stdout: '', stderr: 'boom' },
      { type: 'state.change', from: 'executing', to: 'observing' },
      { type: 'state.change', from: 'observing', to: 'correcting' },
      { type: 'feedback.analysis', verdict: 'fail', retry_count: 1 },
      { type: 'state.change', from: 'correcting', to: 'planning' }, // mid-turn retry
      { type: 'llm.response', content: 'Turn 1 retried answer.' },
      { type: 'session.complete' },
      { type: 'state.change', from: 'completed', to: 'planning' },
      { type: 'llm.response', content: 'Turn 2 answer.' },
      { type: 'session.complete' },
    ];
    const tasks: UserTask[] = [{ text: 'Task one' }, { text: 'Task two' }];
    const flat = flatten(buildDisplayItems(messages, 'Task two', 'idle', undefined, tasks));

    expect(posOf(flat, llm('Turn 1 retried answer'))).toBeLessThan(posOf(flat, user('Task two')));
    expect(posOf(flat, user('Task two'))).toBeLessThan(posOf(flat, llm('Turn 2 answer')));
  });

  it('keeps plain two-turn conversations in order (no tools)', () => {
    const messages: WsServerMessage[] = [
      { type: 'state.change', from: 'idle', to: 'planning' },
      { type: 'llm.response', content: 'First answer.' },
      { type: 'session.complete' },
      { type: 'state.change', from: 'completed', to: 'planning' },
      { type: 'llm.response', content: 'Second answer.' },
      { type: 'session.complete' },
    ];
    const tasks: UserTask[] = [{ text: 'Task one' }, { text: 'Task two' }];
    const flat = flatten(buildDisplayItems(messages, 'Task two', 'idle', undefined, tasks));

    expect(posOf(flat, user('Task one'))).toBeLessThan(posOf(flat, llm('First answer')));
    expect(posOf(flat, llm('First answer'))).toBeLessThan(posOf(flat, user('Task two')));
    expect(posOf(flat, user('Task two'))).toBeLessThan(posOf(flat, llm('Second answer')));
  });
});
