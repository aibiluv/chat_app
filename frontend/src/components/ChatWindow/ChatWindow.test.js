// Polyfill scrollIntoView so jsdom won’t blow up
window.HTMLElement.prototype.scrollIntoView = jest.fn();

import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import ChatWindow from './ChatWindow';
import * as api from '../../services/api';
import * as socket from '../../services/socket';

// Mock the API and WebSocket services
jest.mock('../../services/api');
jest.mock('../../services/socket');

// Mock data for our tests
const mockUser = { username: 'testuser' };
const mockConversation = {
  id: 'convo1',
  is_group_chat: false,
  participants: [
    { id: 'user1', username: 'testuser' },
    { id: 'user2', username: 'otheruser' },
  ],
};
const mockMessages = [
  { id: 'msg1', sender: { username: 'otheruser' }, content: 'Hello there!', created_at: new Date().toISOString(), status: 'read' },
  { id: 'msg2', sender: { username: 'testuser' }, content: 'Hi! This is a test message.', created_at: new Date().toISOString(), status: 'sent' },
];

describe('ChatWindow Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getMessagesForConversation.mockResolvedValue({ data: mockMessages });
    socket.sendMessage = jest.fn();
  });

  test('displays a placeholder when no conversation is selected', () => {
    render(<ChatWindow conversation={null} user={mockUser} />);
    expect(
      screen.getByRole('heading', { name: /welcome to chatflow!/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/select a conversation or start a new one/i)
    ).toBeInTheDocument();
  });

  test('fetches and displays historical messages when a conversation is selected', async () => {
    await act(async () => {
      render(<ChatWindow conversation={mockConversation} user={mockUser} />);
    });

    await waitFor(() => {
      expect(api.getMessagesForConversation).toHaveBeenCalledWith('convo1');
    });

    await screen.findByText('Hello there!');
    expect(screen.getByText('Hello there!')).toBeInTheDocument();
    expect(
      screen.getByText('Hi! This is a test message.')
    ).toBeInTheDocument();
  });

  test('sends a message when the form is submitted', async () => {
    await act(async () => {
      render(<ChatWindow conversation={mockConversation} user={mockUser} />);
    });

    const input = screen.getByPlaceholderText(/type a message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'A new message' } });
    fireEvent.click(sendButton);

    expect(socket.sendMessage).toHaveBeenCalledWith('A new message');
    expect(input.value).toBe('');
  });

  test('filters messages correctly when using the search input', async () => {
    await act(async () => {
      render(<ChatWindow conversation={mockConversation} user={mockUser} />);
    });

    await screen.findByText('Hello there!');

    const searchInput = screen.getByPlaceholderText(/search in chat/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });

    expect(screen.queryByText('Hello there!')).not.toBeInTheDocument();
    expect(screen.getByText('Hi! This is a test message.')).toBeInTheDocument();

    fireEvent.change(searchInput, { target: { value: '' } });
    expect(screen.getByText('Hello there!')).toBeInTheDocument();
    expect(screen.getByText('Hi! This is a test message.')).toBeInTheDocument();
  });

  test('displays online status correctly', async () => {
    let onMessageCallback;
    socket.connectWebSocket.mockImplementation((convoId, token, cb) => {
      onMessageCallback = cb;
    });

    await act(async () => {
      render(<ChatWindow conversation={mockConversation} user={mockUser} />);
    });

    expect(screen.getByText('Offline')).toBeInTheDocument();

    act(() =>
      onMessageCallback({ data: JSON.stringify({ type: 'online_users_list', user_ids: [] }) })
    );
    expect(screen.getByText('Offline')).toBeInTheDocument();

    act(() =>
      onMessageCallback({ data: JSON.stringify({ type: 'status', user_id: 'user2', status: 'online' }) })
    );
    await screen.findByText('Online');
    expect(screen.getByText('Online')).toBeInTheDocument();
  });
});
