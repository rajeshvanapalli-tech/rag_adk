import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Search, Send, Play, Pause, Pencil, Copy, RotateCcw, Check, Square, Image as ImageIcon, X } from 'lucide-react';

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
    const [isPaused, setIsPaused] = useState(false);
    const [editingIndex, setEditingIndex] = useState(null);
    const [editText, setEditText] = useState('');
    const [copyFeedbackIdx, setCopyFeedbackIdx] = useState(null);
    const [selectedImage, setSelectedImage] = useState(null);
    const isPausedRef = useRef(false);
    const stopStreamingRef = useRef(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const handleImageSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (!file.type.startsWith('image/')) {
                alert('Please select an image file.');
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                setSelectedImage({
                    file: file,
                    preview: e.target.result,
                    base64: e.target.result, // This includes "data:image/png;base64,..."
                    mimeType: file.type
                });
            };
            reader.readAsDataURL(file);
        }
    };

    const removeImage = () => {
        setSelectedImage(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

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

    const handleSendWithStreaming = async (customMsg = null) => {
        const userMsg = customMsg || input;
        if (!userMsg.trim()) return;

        if (!customMsg) {
            setMessages(prev => {
                const newMsg = { role: 'user', text: userMsg };
                if (selectedImage) {
                    newMsg.image = selectedImage.preview;
                }
                return [...prev, newMsg];
            });
            setInput('');
            setSelectedImage(null);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }

        setLoading(true);
        setStreamingMessage('');
        setIsPaused(false);
        isPausedRef.current = false;
        stopStreamingRef.current = false;

        try {
            const response = await fetch(`${API_BASE}/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: userMsg,
                    image: selectedImage ? selectedImage.base64 : null,
                    mime_type: selectedImage ? selectedImage.mimeType : null,
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
                        // Handle Pause Logic
                        while (isPausedRef.current) {
                            await new Promise(r => setTimeout(r, 100));
                            if (stopStreamingRef.current) break;
                        }
                        if (stopStreamingRef.current) break;

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
            if (err.name === 'AbortError') {
                console.log('Stream stopped by user');
            } else {
                console.error(err);
                setMessages(prev => [...prev, {
                    role: 'bot',
                    text: "Sorry, I encountered an error. Please try again.",
                    agent: "System"
                }]);
            }
        } finally {
            setLoading(false);
            setStreamingMessage('');
            setIsPaused(false);
            isPausedRef.current = false;
        }
    };

    const handleStop = () => {
        stopStreamingRef.current = true;
        setIsPaused(false);
        isPausedRef.current = false;
    };

    const togglePause = () => {
        const newState = !isPaused;
        setIsPaused(newState);
        isPausedRef.current = newState;
    };


    const handleCopy = (text, idx) => {
        navigator.clipboard.writeText(text);
        setCopyFeedbackIdx(idx);
        setTimeout(() => setCopyFeedbackIdx(null), 2000);
    };

    const startEditing = (idx, text) => {
        setEditingIndex(idx);
        setEditText(text);
    };

    const handleUpdateEdit = () => {
        if (!editText.trim()) return;
        const newMessages = messages.slice(0, editingIndex);
        setMessages(newMessages);
        setEditingIndex(null);
        handleSendWithStreaming(editText);
    };

    if (initialLoading) {
        return <div className="chat-container"><div className="loading">Loading conversation...</div></div>;
    }

    return (
        <div className="chat-container">
            <div className="messages-list">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        <div className="message-content-wrapper">
                            {editingIndex === idx ? (
                                <div className="edit-container">
                                    <textarea
                                        value={editText}
                                        onChange={e => setEditText(e.target.value)}
                                        className="edit-textarea"
                                    />
                                    <div className="edit-actions">
                                        <button className="edit-btn update" onClick={handleUpdateEdit}>Update</button>
                                        <button className="edit-btn cancel" onClick={() => setEditingIndex(null)}>Cancel</button>
                                    </div>
                                </div>
                            ) : (
                                <div className="message-content">
                                    {msg.image && (
                                        <div className="message-image">
                                            <img src={msg.image} alt="User upload" style={{ maxWidth: '200px', borderRadius: '8px', marginBottom: '8px' }} />
                                        </div>
                                    )}
                                    {renderTextWithLinks(msg.text)}
                                    <div className="message-actions">
                                        {msg.role === 'user' && (
                                            <button className="action-icon" onClick={() => startEditing(idx, msg.text)} title="Edit prompt">
                                                <Pencil size={16} />
                                            </button>
                                        )}
                                        <button className="action-icon" onClick={() => handleCopy(msg.text, idx)} title="Copy content">
                                            {copyFeedbackIdx === idx ? <Check size={16} /> : <Copy size={16} />}
                                        </button>
                                    </div>
                                </div>
                            )}
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
                        <div className="message-content-wrapper">
                            <div className="message-content">
                                {renderTextWithLinks(streamingMessage)}
                                <span className="cursor">▊</span>
                            </div>
                        </div>
                    </div>
                )}
                {loading && !streamingMessage && <div className="message bot">Thinking...</div>}
                <div ref={messagesEndRef} />
            </div>
            <div className="input-area">
                <div className="input-wrapper">
                    <div className="input-prefix" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                            className="icon-btn"
                            onClick={() => fileInputRef.current?.click()}
                            title="Upload Image"
                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}
                        >
                            <ImageIcon size={20} color="#94a3b8" />
                        </button>
                        <input
                            type="file"
                            ref={fileInputRef}
                            style={{ display: 'none' }}
                            accept="image/*"
                            onChange={handleImageSelect}
                        />
                    </div>
                    {selectedImage && (
                        <div className="image-preview-mini" style={{
                            position: 'absolute',
                            bottom: '100%',
                            left: '20px',
                            background: '#1e293b',
                            padding: '8px',
                            borderRadius: '8px 8px 0 0',
                            border: '1px solid #334155',
                            borderBottom: 'none',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                        }}>
                            <img src={selectedImage.preview} alt="Preview" style={{ width: '40px', height: '40px', objectFit: 'cover', borderRadius: '4px' }} />
                            <button onClick={removeImage} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}>
                                <X size={16} />
                            </button>
                        </div>
                    )}
                    <input
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyPress={e => e.key === 'Enter' && !loading && handleSendWithStreaming()}
                        placeholder="Search HR Policies or Products..."
                        className="chat-input"
                        disabled={loading && !isPaused}
                    />
                    <div className="input-actions">
                        {loading ? (
                            <>
                                <button className="input-action-btn" onClick={togglePause} title={isPaused ? "Resume" : "Pause"}>
                                    {isPaused ? <Play size={20} /> : <Pause size={20} />}
                                </button>
                                <button className="input-action-btn stop" onClick={handleStop} title="Stop generation">
                                    <Square size={18} fill="currentColor" />
                                </button>
                            </>
                        ) : (
                            <button className="send-btn" onClick={() => handleSendWithStreaming()} disabled={!input.trim()} title="Send Message">
                                <Send size={18} color="white" fill="white" />
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
