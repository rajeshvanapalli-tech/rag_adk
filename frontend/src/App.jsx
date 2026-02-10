import { useState } from 'react';
import { PanelLeftOpen } from 'lucide-react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import ChatHistory from './components/ChatHistory';

function App() {
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

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
          <img
            src="/ritelogo1.png"
            alt="RITE Logo"
            className="logo"
            onClick={() => !isSidebarOpen && setIsSidebarOpen(true)}
            style={{ cursor: !isSidebarOpen ? 'pointer' : 'default' }}
          />
          <div className="title-group">
            <p className="subtitle" style={{ margin: 0, opacity: 0.9 }}>AI Agents That Simplify Complex Workflows</p>
          </div>
        </div>
      </header>

      <div className="main-layout">
        <aside
          className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}
          onClick={() => !isSidebarOpen && setIsSidebarOpen(true)}
          style={{ cursor: !isSidebarOpen ? 'pointer' : 'default' }}
        >
          <ChatHistory
            onSelectConversation={handleSelectConversation}
            onNewChat={handleNewChat}
            currentConversationId={currentConversationId}
            refreshTrigger={refreshTrigger}
            toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
            isSidebarOpen={isSidebarOpen}
          />
        </aside>

        <main
          className="chat-window"
          onClick={() => isSidebarOpen && setIsSidebarOpen(false)}
        >
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
