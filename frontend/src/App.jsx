import { useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import ChatHistory from './components/ChatHistory';

function App() {
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleNewChat = () => {
    setCurrentConversationId(null);
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-left">
          <img src="/logo.png" alt="RITE Logo" className="logo" onError={(e) => e.target.style.display = 'none'} />
          <div className="title-group">
            <h1 className="brand-title">RITE Intelligence</h1>
            <p className="subtitle">AI Agents That Simplify Complex Workflows</p>
          </div>
        </div>
      </header>

      <div className="main-layout">
        <aside className="sidebar">
          <ChatHistory
            onSelectConversation={handleSelectConversation}
            onNewChat={handleNewChat}
            currentConversationId={currentConversationId}
            refreshTrigger={refreshTrigger}
          />
        </aside>

        <main className="chat-window">
          <ChatInterface
            conversationId={currentConversationId}
            onConversationUpdate={handleSelectConversation}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
