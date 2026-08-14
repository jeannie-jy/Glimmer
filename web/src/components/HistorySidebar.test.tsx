// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react';
import HistorySidebar from './HistorySidebar';

const historyEntry = (id: string, task: string) => ({
  id,
  task,
  state: 'completed',
  status: 'completed',
  created_at: '2026-08-14T00:00:00',
  finished_at: null,
});

function stubHistory(sessions: unknown[]) {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true,
    json: async () => ({ sessions }),
  })));
}

describe('HistorySidebar delete', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('deletes a conversation via the trash button and removes it from the list', async () => {
    stubHistory([historyEntry('a1', 'Fix the bug'), historyEntry('a2', 'Second chat')]);
    const onDelete = vi.fn(async () => {});
    render(
      <HistorySidebar
        activeSessionId=""
        onSelect={() => {}}
        onNewSession={() => {}}
        onDelete={onDelete}
      />,
    );

    const row = (await screen.findByText('Fix the bug')).closest('li')!;
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true);
    fireEvent.click(within(row).getByRole('button', { name: /delete conversation/i }));

    expect(confirm).toHaveBeenCalled();
    expect(onDelete).toHaveBeenCalledWith('a1');
    await waitFor(() => expect(screen.queryByText('Fix the bug')).toBeNull());
    // The other conversation stays in the list.
    expect(screen.getByText('Second chat')).toBeTruthy();
  });

  it('keeps the conversation when the user cancels the confirmation', async () => {
    stubHistory([historyEntry('a1', 'Fix the bug')]);
    const onDelete = vi.fn(async () => {});
    render(
      <HistorySidebar
        activeSessionId=""
        onSelect={() => {}}
        onNewSession={() => {}}
        onDelete={onDelete}
      />,
    );

    const row = (await screen.findByText('Fix the bug')).closest('li')!;
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    fireEvent.click(within(row).getByRole('button', { name: /delete conversation/i }));

    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getByText('Fix the bug')).toBeTruthy();
  });
});
