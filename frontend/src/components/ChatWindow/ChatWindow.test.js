
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
  // Before each test, clear mocks to ensure isolation
  beforeEach(() => {
    jest.clearAllMocks();
    // Provide a default successful response for fetching messages
    api.getMessagesForConversation.mockResolvedValue({ data: mockMessages });
  });

  test('displays a placeholder when no conversation is selected', () => {
    render(<ChatWindow conversation={null} user={mockUser} />);
    expect(screen.getByText(/select a conversation to start chatting/i)).toBeInTheDocument();
  });

  test('fetches and displays historical messages when a conversation is selected', async () => {
    render(<ChatWindow conversation={mockConversation} user={mockUser} />);
    
    // Use `waitFor` to wait for the API call to resolve and the UI to update.
    await waitFor(() => {
      // Check that the API was called with the correct conversation ID.
      expect(api.getMessagesForConversation).toHaveBeenCalledWith('convo1');
    });

    // Check that the messages from the mock API response are rendered.
    expect(screen.getByText('Hello there!')).toBeInTheDocument();
    expect(screen.getByText('Hi! This is a test message.')).toBeInTheDocument();
  });

  test('sends a message when the form is submitted', () => {
    render(<ChatWindow conversation={mockConversation} user={mockUser} />);
    
    const input = screen.getByPlaceholderText(/type a message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    // Simulate the user typing a new message.
    fireEvent.change(input, { target: { value: 'A new message' } });
    // Simulate clicking the send button.
    fireEvent.click(sendButton);

    // Assert that the socket's sendMessage function was called with the correct message.
    expect(socket.sendMessage).toHaveBeenCalledWith('A new message');
    // Assert that the input field was cleared after sending.
    expect(input.value).toBe('');
  });

  test('filters messages correctly when using the search input', async () => {
    render(<ChatWindow conversation={mockConversation} user={mockUser} />);

    // Wait for initial messages to load
    await screen.findByText('Hello there!');

    const searchInput = screen.getByPlaceholderText(/search in chat/i);
    
    // Simulate typing a search query.
    fireEvent.change(searchInput, { target: { value: 'test' } });

    // Assert that only the message containing "test" is visible.
    expect(screen.queryByText('Hello there!')).not.toBeInTheDocument();
    expect(screen.getByText('Hi! This is a test message.')).toBeInTheDocument();
    
    // Clear the search query.
    fireEvent.change(searchInput, { target: { value: '' } });

    // Assert that both messages are visible again.
    expect(screen.getByText('Hello there!')).toBeInTheDocument();
    expect(screen.getByText('Hi! This is a test message.')).toBeInTheDocument();
  });
  
  test('displays online status correctly', async () => {
    // We need to simulate the WebSocket messages to test this.
    // The `connectWebSocket` function takes a callback to handle incoming messages.
    let onMessageCallback;
    socket.connectWebSocket.mockImplementation((convoId, token, callback) => {
        onMessageCallback = callback;
    });

    render(<ChatWindow conversation={mockConversation} user={mockUser} />);
    
    // Initially, the other user should be offline.
    expect(screen.getByText('Offline')).toBeInTheDocument();
    
    // Simulate the backend sending the initial list of online users.
    // Let's say the other user is NOT in this initial list.
    const initialOnlineList = { type: 'online_users_list', user_ids: [] };
    // We need to wrap state updates in `act` to avoid React warnings.
    await waitFor(() => {
        onMessageCallback({ data: JSON.stringify(initialOnlineList) });
    });
    expect(screen.getByText('Offline')).toBeInTheDocument();

    // Now, simulate the other user coming online.
    const statusUpdate = { type: 'status', user_id: 'user2', status: 'online' };
    await waitFor(() => {
        onMessageCallback({ data: JSON.stringify(statusUpdate) });
    });
    
    // Assert that the status has updated to "Online".
    expect(screen.getByText('Online')).toBeInTheDocument();
  });
});