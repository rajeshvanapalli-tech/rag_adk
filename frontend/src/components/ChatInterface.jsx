import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Helper function to convert text with URLs to clickable links
const renderTextWithLinks = (text) => {
    // URL regex pattern
    const urlPattern = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlPattern);

    return parts.map((part, index) => {
        if (part.match(urlPattern)) {
            return (
                <a
                    key={index}
                    href={part}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: '#3b82f6', textDecoration: 'underline' }}
                >
                    {part}
                </a>
            );
        }
        return part;
    });
};

const ChatInterface = ({ conversationId, onConversationUpdate }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(false);
    const [streamingMessage, setStreamingMessage] = useState('');
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, streamingMessage]);

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

    const handleSendWithStreaming = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setInput('');
        setLoading(true);
        setStreamingMessage('');

        try {
            const response = await fetch(`${API_BASE}/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: userMsg,
                    user_id: "user_1",
                    conversation_id: conversationId || "new"
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';
            let newConvId = null;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.type === 'metadata') {
                                newConvId = data.conversation_id;
                                if (newConvId && onConversationUpdate) {
                                    onConversationUpdate(newConvId);
                                }
                            } else if (data.type === 'content') {
                                fullText += data.text;
                                setStreamingMessage(fullText);
                            } else if (data.type === 'done') {
                                // Finalize message
                                setMessages(prev => [...prev, {
                                    role: 'bot',
                                    text: fullText,
                                    agent: 'RITE Intelligence'
                                }]);
                                setStreamingMessage('');
                            } else if (data.type === 'error') {
                                setMessages(prev => [...prev, {
                                    role: 'bot',
                                    text: data.message,
                                    agent: 'System'
                                }]);
                                setStreamingMessage('');
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data:', e);
                        }
                    }
                }
            }
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, {
                role: 'bot',
                text: "Sorry, I encountered an error. Please try again.",
                agent: "System"
            }]);
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
                        <div className="message-content">
                            {renderTextWithLinks(msg.text)}
                        </div>
                        {msg.role === 'bot' && (
                            <div className="message-meta">
                                <small>{msg.agent}</small>
                            </div>
                        )}
                    </div>
                ))}
                {streamingMessage && (
                    <div className="message bot">
                        <div className="message-content">
                            {renderTextWithLinks(streamingMessage)}
                            <span className="cursor">▊</span>
                        </div>
                    </div>
                )}
                {loading && !streamingMessage && <div className="message bot">Thinking...</div>}
                <div ref={messagesEndRef} />
            </div>
            <div className="input-area">
                <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && handleSendWithStreaming()}
                    placeholder="Ask anything (HR or Product)..."
                    className="chat-input"
                />
                <button className="send-btn" onClick={handleSendWithStreaming}>
                    <Send size={20} />
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;
