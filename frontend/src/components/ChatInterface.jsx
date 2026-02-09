import { useState, useEffect } from 'react';
import axios from 'axios';
import { Send } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const ChatInterface = ({ conversationId, onConversationUpdate }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(false);

    // Load conversation when ID changes
    useEffect(() => {
        if (conversationId) {
            loadConversation(conversationId);
        } else {
            // New chat state
            setMessages([
                { role: 'bot', text: "Hello! I am your RITE Intelligence Assistant. I can help with HR Policies or Product details. How can I help you?", agent: "System" }
            ]);
        }
    }, [conversationId]);

    const loadConversation = async (id) => {
        setInitialLoading(true);
        try {
            const response = await axios.get(`${API_BASE}/conversations/${id}`);
            const history = response.data.messages || [];

            // Transform to UI format
            const uiMessages = history.map(msg => ({
                role: msg.role === 'user' ? 'user' : 'bot',
                text: msg.text,
                agent: msg.role === 'assistant' ? 'Assistant' : 'User'
            }));

            setMessages(uiMessages);
        } catch (err) {
            console.error(err);
        } finally {
            setInitialLoading(false);
        }
    };

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setInput('');
        setLoading(true);

        try {
            const response = await axios.post(`${API_BASE}/chat`, {
                query: userMsg,
                user_id: "user_1",
                conversation_id: conversationId || "new"
            });

            const botResponse = response.data.response || "No response.";
            const agentName = response.data.agent || "Assistant";
            const newConvId = response.data.conversation_id;

            if (newConvId && onConversationUpdate) {
                onConversationUpdate(newConvId);
            }

            setMessages(prev => [...prev, { role: 'bot', text: botResponse, agent: agentName }]);
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, { role: 'bot', text: "Sorry, I encountered an error. Please try again.", agent: "System" }]);
        } finally {
            setLoading(false);
        }
    };

    if (initialLoading) {
        return <div className="chat-container"><div className="loading">Loading conversation...</div></div>;
    }

    return (
        <div className="chat-container">
            <div className="messages-list">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        <div className="message-content">{msg.text}</div>
                        {msg.role === 'bot' && (
                            <div className="message-meta">
                                <small>{msg.agent}</small>
                            </div>
                        )}
                    </div>
                ))}
                {loading && <div className="message bot">Thinking...</div>}
            </div>
            <div className="input-area">
                <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && handleSend()}
                    placeholder="Ask anything (HR or Product)..."
                    className="chat-input"
                />
                <button className="send-btn" onClick={handleSend}>
                    <Send size={20} />
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;
