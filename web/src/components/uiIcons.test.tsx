// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, beforeAll, vi } from 'vitest';
import { render } from '@testing-library/react';
import MessageList from './MessageList';
import StateChip from './StateChip';

// jsdom doesn't implement scrollIntoView (used by MessageList's autoscroll effect).
beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn();
});

// Emoji + decorative glyph ranges (agent reply content is excluded from the
// icon swap — only hardcoded UI decoration must be iconified).
const EMOJI_RE = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}]/u;

describe('UI emoji replaced by lucide icons', () => {
  it('renders attachment chips with an icon instead of the 📄 emoji', () => {
    const { container } = render(
      <MessageList
        messages={[]}
        task=""
        agentState="idle"
        userTasks={[{ text: 'check this', files: [{ name: 'notes.txt', size: 1024 }] }]}
      />,
    );

    const chip = container.querySelector('.message-list__attachments-icon');
    expect(chip).toBeTruthy();
    expect(chip!.querySelector('svg')).toBeTruthy();
    expect(container.textContent).not.toMatch(EMOJI_RE);
  });

  it('renders every state chip with an icon and no emoji in the label', () => {
    const states = ['planning', 'executing', 'observing', 'correcting', 'awaiting_human', 'completed', 'error', 'idle'];
    for (const state of states) {
      const { container, unmount } = render(<StateChip state={state} isActive={false} />);
      expect(container.querySelector('.state-chip')).toBeTruthy();
      expect(container.querySelector('.state-chip svg')).toBeTruthy();
      expect(container.textContent).not.toMatch(EMOJI_RE);
      unmount();
    }
  });
});
