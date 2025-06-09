
import React, { useState, useEffect, useRef } from 'react';
import { connectWebSocket, disconnectWebSocket, sendMessage } from '../../services/socket';
import { getMessagesForConversation } from '../../services/api';
import './ChatWindow.css'; // Renamed from Chat.css


const ChatWindow = ({ conversation, user, onNewMessage }) => {
  const [allMessages, setAllMessages] = useState([]);
  const [filteredMessages, setFilteredMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [onlineUsers, setOnlineUsers] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef(null);

  // Effect 1: Fetch historical messages and set up WebSocket
  useEffect(() => {
    // Reset state when conversation changes
    setAllMessages([]);
    setFilteredMessages([]);
    setOnlineUsers(new Set());

    const fetchMessages = async () => {
      if (conversation) {
        try {
          const response = await getMessagesForConversation(conversation.id);
          setAllMessages(response.data);
        } catch (error) {
          console.error("Failed to fetch messages", error);
        }
      }
    };
    fetchMessages();

    // WebSocket connection logic
    if (conversation) {
      const token = localStorage.getItem('token');
      const onMessage = (event) => {
        const msg = JSON.parse(event.data);
        
        if (msg.type === 'online_users_list') {
            setOnlineUsers(new Set(msg.user_ids));
        } else if (msg.type === 'status') {
            setOnlineUsers(prev => {
                const newOnlineUsers = new Set(prev);
                if (msg.status === 'online') newOnlineUsers.add(msg.user_id);
                else newOnlineUsers.delete(msg.user_id);
                return newOnlineUsers;
            });
        } else if(msg.type === 'messages_read') {
            setAllMessages(prev => 
                prev.map(m => 
                    msg.message_ids.includes(m.id) ? { ...m, status: 'read' } : m
                )
            );
        } else { // It's a regular chat message
            if (msg.conversation_id === conversation.id) {
                setAllMessages(prev => [...prev, msg]);
            } else {
                onNewMessage(msg);
            }
        }
      };

      connectWebSocket(conversation.id, token, onMessage);
    }
    
    return () => {
      disconnectWebSocket();
    };
  }, [conversation, onNewMessage]);

  // Effect 2: Client-side search filtering
  useEffect(() => {
    if (!searchQuery.trim()) {
        setFilteredMessages(allMessages);
    } else {
        const lowercasedQuery = searchQuery.toLowerCase();
        const results = allMessages.filter(msg => 
            msg.content.toLowerCase().includes(lowercasedQuery)
        );
        setFilteredMessages(results);
    }
  }, [searchQuery, allMessages]);
  
  // Effect 3: Auto-scrolling
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [filteredMessages]);


  const handleSendMessage = (e) => {
    e.preventDefault();
    if (newMessage.trim() && conversation) {
      sendMessage(newMessage);
      setNewMessage('');
    }
  };

  if (!conversation) {
    return <div className="chat-window-placeholder"><h3>Welcome to ChatFlow!</h3><p>Select a conversation or start a new one.</p></div>;
  }
  
  const otherUser = conversation.is_group_chat ? null : conversation.participants.find(p => p.username !== user.username);
  const isOtherUserOnline = otherUser && onlineUsers.has(otherUser.id);


  return (
    <div className="chat-window">
      <header className="chat-header">
        <div>
          <h3>{conversation.is_group_chat ? conversation.name : otherUser?.username}</h3>
          {!conversation.is_group_chat && (
            <div className={`user-status ${isOtherUserOnline ? 'online' : 'offline'}`}>
              <span className="status-dot"></span>
              {isOtherUserOnline ? 'Online' : 'Offline'}
            </div>
          )}
        </div>
        <div className="search-form">
          <input type="text" placeholder="Search in chat..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        </div>
      </header>
      <main className="chat-messages">
        {filteredMessages.map((msg) => (
          <div key={msg.id} className={`message-item ${msg.sender.username === user.username ? 'my-message' : ''}`}>
             <div className="message-sender">{msg.sender.username}</div>
             <div className="message-content">{msg.content}</div>
             <div className="message-timestamp">{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
             {msg.sender.username === user.username && <span className="message-status">{msg.status}</span>}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>
      <footer className="chat-input-area">
        <form onSubmit={handleSendMessage} className="message-form">
          <input type="text" value={newMessage} onChange={(e) => setNewMessage(e.target.value)} placeholder="Type a message..." className="message-input" autoFocus />
          <button type="submit" className="send-btn">Send</button>
        </form>
      </footer>
    </div>
  );
};

export default ChatWindow;