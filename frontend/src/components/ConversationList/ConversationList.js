
import React from 'react';
import './ConversationList.css';
const ConversationList = ({ conversations, onSelectConversation, activeConversationId, onLogout, user, onNewChat }) => {
  return (
    <div className="conversation-sidebar">
      <header className="sidebar-header">
        <div className="user-info">
          <h3>Chats</h3>
          <span>{user.username}</span>
        </div>
        <button onClick={onLogout} className="logout-btn-sidebar">Logout</button>
      </header>
      <div className="new-chat-action">
        <button onClick={onNewChat}>+ New Chat</button>
      </div>
      <div className="conversation-list">
        {conversations.map(convo => {
          // For 1-on-1 chats, display the other user's name. For group chats, display the group name.
          const displayName = convo.is_group_chat ? convo.name || "Unknown Group": convo.participants.find(p => p.username !== user.username)?.username || "Unknown User";
          return (
            <div 
              key={convo.id} 
              className={`conversation-item ${convo.id === activeConversationId ? 'active' : ''}`}
              onClick={() => onSelectConversation(convo)}
            >
              <span>{displayName}</span>
              {/* Display a blue dot if the conversation has unread messages */}
              {convo.has_unread && <span className="unread-dot"></span>}
            </div>
          )
        })}
      </div>
    </div>
  );
};

export default ConversationList;