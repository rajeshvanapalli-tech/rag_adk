import { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, Clock, Plus, Search, Trash2 } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const ChatHistory = ({ onSelectConversation, onNewChat, currentConversationId, refreshTrigger }) => {
    const [conversations, setConversations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const fetchConversations = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_BASE}/conversations`);
            setConversations(response.data.conversations || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // Fetch on mount or when triggered
    useEffect(() => {
        fetchConversations();
    }, [refreshTrigger]);

    // Filter conversations
    const filteredConversations = conversations.filter(conv =>
        (conv.title || "").toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleDelete = async (e, conversationId) => {
        e.stopPropagation(); // Prevent selecting the chat when deleting
        if (!window.confirm("Are you sure you want to delete this conversation?")) return;

        try {
            await axios.delete(`${API_BASE}/conversations/${conversationId}`);
            setConversations(prev => prev.filter(c => c.id !== conversationId));
            if (currentConversationId === conversationId) {
                onNewChat(); // Reset the chat interface if the current chat was deleted
            }
        } catch (err) {
            console.error("Failed to delete conversation", err);
            alert("Failed to delete conversation. Please try again.");
        }
    };

    return (
        <div className="history-panel">
            <div className="history-header">
                <h3><Clock size={16} /> Recent Chats</h3>
                <button className="new-chat-btn" onClick={onNewChat}>
                    <Plus size={16} /> New Chat
                </button>
            </div>

            <div className="history-search-bar">
                <Search size={14} color="#94a3b8" />
                <input
                    type="text"
                    placeholder="Search chats..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search-input"
                />
            </div>

            <div className="history-results">
                {loading && <div className="loading">Loading...</div>}

                {!loading && filteredConversations.length === 0 && (
                    <div className="no-result-text">
                        {conversations.length === 0 ? "No prior conversations." : "No matches found."}
                    </div>
                )}

                {filteredConversations.map((conv) => (
                    <div
                        key={conv.id}
                        className={`history-item ${currentConversationId === conv.id ? 'active' : ''}`}
                        onClick={() => onSelectConversation(conv.id)}
                    >
                        <MessageSquare size={14} className="icon" />
                        <div className="history-info">
                            <p className="history-title">{conv.title || "Untitled Chat"}</p>
                            <span className="history-date">
                                {new Date(conv.updated_at * 1000).toLocaleDateString()}
                            </span>
                        </div>
                        <button
                            className="delete-btn"
                            onClick={(e) => handleDelete(e, conv.id)}
                            title="Delete Chat"
                        >
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ChatHistory;
