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

function countOf(items: DisplayItem[], pred: (d: DisplayItem) => boolean): number {
  return items.filter(pred).length;
}

const user = (content: string) => (d: DisplayItem) =>
  d.kind === 'user' && (d.data as { content: string }).content === content;
const llm = (needle: string) => (d: DisplayItem) =>
  d.kind === 'llm' && (d.data as { content: string }).content.includes(needle);
const tool = () => (d: DisplayItem) => d.kind === 'tool';

/**
 * WS event stream of a two-turn conversation where turn 1 uses a tool.
 * The backend echoes each submitted task as a ``user.message`` event right
 * before the turn's first state transition — the stream is self-describing.
 */
function twoTurnEchoMessages(): WsServerMessage[] {
  return [
    // ---- turn 1 ----
    { type: 'user.message', content: 'Task one' },
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
    { type: 'user.message', content: 'Task two' },
    { type: 'state.change', from: 'completed', to: 'planning' },
    { type: 'llm.response', content: 'Turn 2 answer.' },
    { type: 'session.complete' },
  ];
}

describe('buildDisplayItems — multi-turn ordering', () => {
  it('renders user bubbles from user.message stream events alone (no userTasks)', () => {
    // The stream is the source of truth for user-message placement: even
    // when the side-channel userTasks list is unavailable, every submitted
    // task must appear exactly where the server echoed it.
    const flat = flatten(buildDisplayItems(twoTurnEchoMessages(), 'Task two', 'idle'));

    expect(posOf(flat, user('Task one'))).toBeLessThan(posOf(flat, tool()));
    expect(posOf(flat, tool())).toBeLessThan(posOf(flat, llm('Turn 1 final answer')));
    expect(posOf(flat, llm('Turn 1 final answer'))).toBeLessThan(posOf(flat, user('Task two')));
    expect(posOf(flat, user('Task two'))).toBeLessThan(posOf(flat, llm('Turn 2 answer')));
  });

  it('keeps each turn as one block with userTasks present: no duplicated user bubbles', () => {
    // Regression: both user messages are already in userTasks when the walk
    // runs. The mid-turn observing→planning transition of turn 1 must NOT
    // emit the second user message — turn 2 starts at its own echo.
    const tasks: UserTask[] = [{ text: 'Task one' }, { text: 'Task two' }];
    const flat = flatten(buildDisplayItems(twoTurnEchoMessages(), 'Task two', 'idle', undefined, tasks));

    expect(posOf(flat, user('Task one'))).toBeLessThan(posOf(flat, tool()));
    expect(posOf(flat, tool())).toBeLessThan(posOf(flat, llm('Turn 1 final answer')));
    expect(posOf(flat, llm('Turn 1 final answer'))).toBeLessThan(posOf(flat, user('Task two')));
    expect(posOf(flat, user('Task two'))).toBeLessThan(posOf(flat, llm('Turn 2 answer')));
    expect(countOf(flat, user('Task one'))).toBe(1);
    expect(countOf(flat, user('Task two'))).toBe(1);
  });

  it('splice regression: a dropped connection must not misplace the next user message', () => {
    // The connection died while turn 1's final answer was in flight, then the
    // user submitted turn 2 on the reconnected (fresh) session. The retained
    // stream therefore splices turn 2's idle→planning right after turn 1's
    // tool result. User 2 must appear exactly once, at its echo position —
    // never re-emitted by a state-transition heuristic.
    const messages: WsServerMessage[] = [
      { type: 'user.message', content: 'Task one' },
      { type: 'state.change', from: 'idle', to: 'planning' },
      { type: 'state.change', from: 'planning', to: 'executing' },
      { type: 'tool.invoke', tool: 'read_file', args: { path: 'a.md' } },
      { type: 'state.change', from: 'executing', to: 'observing' },
      { type: 'tool.result', tool_name: 'read_file', exit_code: 0, stdout: 'hi' },
      { type: 'state.change', from: 'observing', to: 'planning' },
      // ---- connection dropped; reconnect boots a fresh session ----
      { type: 'user.message', content: 'Task two' },
      { type: 'state.change', from: 'idle', to: 'planning' },
      { type: 'llm.response', content: 'Turn 2 answer.' },
      { type: 'session.complete' },
    ];
    const tasks: UserTask[] = [{ text: 'Task one' }, { text: 'Task two' }];
    const flat = flatten(buildDisplayItems(messages, 'Task two', 'idle', undefined, tasks));

    expect(posOf(flat, user('Task one'))).toBeLessThan(posOf(flat, tool()));
    expect(posOf(flat, tool())).toBeLessThan(posOf(flat, user('Task two')));
    expect(posOf(flat, user('Task two'))).toBeLessThan(posOf(flat, llm('Turn 2 answer')));
    expect(countOf(flat, user('Task one'))).toBe(1);
    expect(countOf(flat, user('Task two'))).toBe(1);
  });

  it('does not emit the next user message at a correcting→planning retry', () => {
    const messages: WsServerMessage[] = [
      { type: 'user.message', content: 'Task one' },
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
      { type: 'user.message', content: 'Task two' },
      { type: 'state.change', from: 'completed', to: 'planning' },
      { type: 'llm.response', content: 'Turn 2 answer.' },
      { type: 'session.complete' },
    ];
    const tasks: UserTask[] = [{ text: 'Task one' }, { text: 'Task two' }];
    const flat = flatten(buildDisplayItems(messages, 'Task two', 'idle', undefined, tasks));

    expect(posOf(flat, llm('Turn 1 retried answer'))).toBeLessThan(posOf(flat, user('Task two')));
    expect(posOf(flat, user('Task two'))).toBeLessThan(posOf(flat, llm('Turn 2 answer')));
    expect(countOf(flat, user('Task two'))).toBe(1);
  });

  it('shows a submitted task optimistically at the end until its echo arrives', () => {
    // Turn 2 was submitted while the server hasn't echoed it yet: it must
    // render below all existing content (never interleaved into turn 1).
    const messages: WsServerMessage[] = [
      { type: 'user.message', content: 'Task one' },
      { type: 'state.change', from: 'idle', to: 'planning' },
      { type: 'state.change', from: 'planning', to: 'executing' },
      { type: 'tool.invoke', tool: 'read_file', args: { path: 'a.md' } },
      { type: 'state.change', from: 'executing', to: 'observing' },
      { type: 'tool.result', tool_name: 'read_file', exit_code: 0, stdout: 'hi' },
    ];
    const tasks: UserTask[] = [{ text: 'Task one' }, { text: 'Task two' }];
    const flat = flatten(buildDisplayItems(messages, 'Task two', 'idle', undefined, tasks));

    expect(posOf(flat, tool())).toBeLessThan(posOf(flat, user('Task two')));
    expect(countOf(flat, user('Task one'))).toBe(1);
    expect(countOf(flat, user('Task two'))).toBe(1);
  });
});
