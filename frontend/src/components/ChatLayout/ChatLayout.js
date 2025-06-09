import React, { useState, useEffect, useCallback } from 'react';
import ConversationList from '../ConversationList/ConversationList';
import ChatWindow from '../ChatWindow/ChatWindow';
import NewConversationModal from '../NewConversationModal/NewConversationModal';
import { getConversations, markConversationAsRead } from '../../services/api';
import './ChatLayout.css';

const ChatLayout = ({ user, onLogout }) => {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchConversations = useCallback(async () => {
    try {
      const response = await getConversations();
      setConversations(response.data);
    } catch (error) {
      console.error("Failed to fetch conversations", error);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);
  
  const handleSelectConversation = async (conversation) => {
    setActiveConversation(conversation);
    // If the conversation was unread, mark it as read on the backend
    if (conversation.has_unread) {
      try {
        await markConversationAsRead(conversation.id);
        // Refresh the conversation list to update the UI
        fetchConversations();
      } catch (error) {
        console.error("Failed to mark conversation as read", error);
      }
    }
  };

  const handleConversationCreated = (newConversation) => {
    fetchConversations();
    setActiveConversation(newConversation);
    setIsModalOpen(false);
  };
  
  // A new callback to handle incoming messages and update the conversation list
  const handleNewMessage = useCallback((newMessage) => {
      const convoExists = conversations.some(c => c.id === newMessage.conversation_id);

      if (convoExists) {
        // If the conversation exists, update its unread status
        setConversations(prevConvos => 
            prevConvos.map(convo => {
                if (convo.id === newMessage.conversation_id && convo.id !== activeConversation?.id) {
                    return { ...convo, has_unread: true };
                }
                return convo;
            })
        );
      } else {
        // If it's a new conversation, re-fetch the entire list
        fetchConversations();
      }
  }, [conversations, activeConversation, fetchConversations]);

  return (
    <div className="chat-layout">
      <ConversationList 
        conversations={conversations} 
        onSelectConversation={handleSelectConversation}
        activeConversationId={activeConversation?.id}
        onLogout={onLogout}
        user={user}
        onNewChat={() => setIsModalOpen(true)}
      />
      <ChatWindow 
        key={activeConversation ? activeConversation.id : 'placeholder'}
        conversation={activeConversation}
        user={user}
        onNewMessage={handleNewMessage}
      />
      {isModalOpen && (
        <NewConversationModal 
          onClose={() => setIsModalOpen(false)}
          onConversationCreated={handleConversationCreated}
        />
      )}
    </div>
  );
};

export default ChatLayout;