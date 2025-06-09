import React, { useState, useEffect } from 'react';
import { getUsers, createConversation } from '../../services/api';
import './NewConversationModal.css';

const NewConversationModal = ({ onClose, onConversationCreated }) => {
    const [users, setUsers] = useState([]);
    const [selectedUsers, setSelectedUsers] = useState([]);
    const [groupName, setGroupName] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchUsers = async () => {
            try {
                const response = await getUsers();
                setUsers(response.data);
            } catch (err) {
                setError('Failed to fetch users.');
            }
        };
        fetchUsers();
    }, []);

    const handleUserSelect = (userId) => {
        setSelectedUsers(prev =>
            prev.includes(userId) ? prev.filter(id => id !== userId) : [...prev, userId]
        );
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (selectedUsers.length === 0) {
            setError('Please select at least one user.');
            return;
        }
        
        try {
            const name = selectedUsers.length > 1 ? groupName : null;
            const response = await createConversation(selectedUsers, name);
            onConversationCreated(response.data);
        } catch (err) {
            setError('Failed to create conversation.');
        }
    };

    return (
        <div className="modal-backdrop">
            <div className="modal-content">
                <h2>Start a New Chat</h2>
                {error && <p className="error-message">{error}</p>}
                <form onSubmit={handleSubmit}>
                    <div className="user-list">
                        {users.map(user => (
                            <div key={user.id} className="user-select-item">
                                <input
                                    type="checkbox"
                                    id={`user-${user.id}`}
                                    checked={selectedUsers.includes(user.id)}
                                    onChange={() => handleUserSelect(user.id)}
                                />
                                <label htmlFor={`user-${user.id}`}>{user.username}</label>
                            </div>
                        ))}
                    </div>
                    {selectedUsers.length > 1 && (
                        <input
                            type="text"
                            placeholder="Group Name (optional)"
                            value={groupName}
                            onChange={(e) => setGroupName(e.target.value)}
                            className="group-name-input"
                        />
                    )}
                    <div className="modal-actions">
                        <button type="submit" className="btn-primary">Create Chat</button>
                        <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default NewConversationModal;