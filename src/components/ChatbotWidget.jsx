import React, { useState, useEffect, useRef } from 'react';
import './ChatbotWidget.css';

const getChatApiUrl = () => {
  const url = (import.meta.env?.VITE_CHAT_API_URL || '').trim();
  if (url) return url;
  // Fallback for local development only
  if (typeof window !== 'undefined' && window.location?.hostname === 'localhost') {
    return 'http://localhost:8000/api/chat';
  }
  return '/api/chat';
};

const RobotSVG = ({ state, isDark }) => {
  const bodyColor = isDark ? '#3cad6d' : '#2e8555';
  const eyeColor = isDark ? '#f8f9fa' : '#1a1a2e';
  const screenColor = isDark ? '#1a1a2e' : '#e8f5e9';

  return (
    <svg
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`robot-svg robot-${state}`}
      role="img"
      aria-label={`Robot assistant - ${state}`}
    >
      <defs>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Antenna */}
      <line
        x1="32"
        y1="4"
        x2="32"
        y2="0"
        stroke={bodyColor}
        strokeWidth="2"
        strokeLinecap="round"
        className="antenna"
      />
      <circle
        cx="32"
        cy="-2"
        r="3"
        fill={bodyColor}
        className={`antenna-ball ${state === 'thinking' ? 'pulse' : ''}`}
      />

      {/* Head */}
      <rect
        x="12"
        y="8"
        width="40"
        height="32"
        rx="8"
        fill={bodyColor}
        className={`robot-head ${state === 'thinking' ? 'thinking-wobble' : ''} ${state === 'idle' ? 'idle-float' : ''}`}
        filter="url(#softGlow)"
      />

      {/* Screen face */}
      <rect
        x="16"
        y="14"
        width="32"
        height="20"
        rx="4"
        fill={screenColor}
        className="robot-screen"
      />

      {/* Eyes - different states */}
      {state === 'idle' && (
        <>
          <ellipse
            cx="24"
            cy="24"
            rx="4"
            ry="5"
            fill={eyeColor}
            className="eye blink"
          />
          <ellipse
            cx="40"
            cy="24"
            rx="4"
            ry="5"
            fill={eyeColor}
            className="eye blink"
            style={{ animationDelay: '0.3s' }}
          />
        </>
      )}

      {state === 'hover' && (
        <>
          <ellipse
            cx="24"
            cy="24"
            rx="5"
            ry="6"
            fill={eyeColor}
            className="eye hover-pop"
          />
          <ellipse
            cx="40"
            cy="24"
            rx="5"
            ry="6"
            fill={eyeColor}
            className="eye hover-pop"
            style={{ animationDelay: '0.1s' }}
          />
        </>
      )}

      {state === 'thinking' && (
        <>
          <ellipse
            cx="24"
            cy="24"
            rx="3"
            ry="3"
            fill={eyeColor}
            className="eye thinking-spin"
          />
          <ellipse
            cx="40"
            cy="24"
            rx="3"
            ry="3"
            fill={eyeColor}
            className="eye thinking-spin"
            style={{ animationDelay: '0.2s' }}
          />
          {/* Processing indicator */}
          <g className="processing-dots">
            <circle cx="24" cy="42" r="2.5" fill={bodyColor} opacity="0.6">
              <animate
                attributeName="opacity"
                values="0.6;1;0.6"
                dur="1s"
                repeatCount="indefinite"
              />
            </circle>
            <circle cx="32" cy="42" r="2.5" fill={bodyColor} opacity="0.6">
              <animate
                attributeName="opacity"
                values="0.6;1;0.6"
                dur="1s"
                repeatCount="indefinite"
                begin="0.15s"
              />
            </circle>
            <circle cx="40" cy="42" r="2.5" fill={bodyColor} opacity="0.6">
              <animate
                attributeName="opacity"
                values="0.6;1;0.6"
                dur="1s"
                repeatCount="indefinite"
                begin="0.3s"
              />
            </circle>
          </g>
        </>
      )}

      {state === 'speaking' && (
        <>
          <ellipse
            cx="24"
            cy="24"
            rx="4"
            ry="2"
            fill={eyeColor}
            className="eye speaking"
          />
          <ellipse
            cx="40"
            cy="24"
            rx="4"
            ry="2"
            fill={eyeColor}
            className="eye speaking"
            style={{ animationDelay: '0.1s' }}
          />
          {/* Sound waves */}
          <g className="sound-waves">
            <path d="M50 30 Q58 24 50 18" stroke={bodyColor} strokeWidth="2" fill="none" opacity="0.7">
              <animate attributeName="opacity" values="0.7;0;0.7" dur="1.5s" repeatCount="indefinite" />
            </path>
            <path d="M52 30 Q62 24 52 18" stroke={bodyColor} strokeWidth="2" fill="none" opacity="0.5">
              <animate attributeName="opacity" values="0.5;0;0.5" dur="1.5s" repeatCount="indefinite" begin="0.2s" />
            </path>
          </g>
        </>
      )}

      {/* Body */}
      <rect
        x="18"
        y="40"
        width="28"
        height="20"
        rx="4 4 8 8"
        fill={bodyColor}
        className="robot-body"
        filter="url(#softGlow)"
      />

      {/* Arms */}
      <g className="arms">
        <path
          d="M10 44 Q4 48 10 52"
          stroke={bodyColor}
          strokeWidth="5"
          strokeLinecap="round"
          fill="none"
          className={`arm-left ${state === 'hover' ? 'wave' : ''} ${state === 'speaking' ? 'gesture' : ''}`}
        />
        <path
          d="M54 44 Q60 48 54 52"
          stroke={bodyColor}
          strokeWidth="5"
          strokeLinecap="round"
          fill="none"
          className={`arm-right ${state === 'hover' ? 'wave' : ''} ${state === 'speaking' ? 'gesture' : ''}`}
        />
      </g>

      {/* Legs */}
      <g className="legs">
        <rect x="22" y="58" width="6" height="10" rx="2" fill={bodyColor} className={`leg ${state === 'idle' ? 'idle-tap' : ''}`} />
        <rect x="36" y="58" width="6" height="10" rx="2" fill={bodyColor} className={`leg ${state === 'idle' ? 'idle-tap' : ''}`} style={{ animationDelay: '0.5s' }} />
      </g>

      {/* Chest indicator */}
      <circle
        cx="32"
        cy="50"
        r="4"
        fill={state === 'thinking' ? '#ffa500' : state === 'speaking' ? '#4ade80' : '#4ade80'}
        className={`chest-light ${state === 'thinking' ? 'pulse-fast' : state === 'speaking' ? 'pulse-slow' : 'pulse'}`}
      />
    </svg>
  );
};

const ChatbotWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [robotState, setRobotState] = useState('idle');
  const [isLoading, setIsLoading] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);
  const messagesEndRef = useRef(null);
  const widgetRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    setMounted(true);
    const updateTheme = () => {
      setIsDark(document.documentElement.getAttribute('data-theme') === 'dark');
    };
    updateTheme();
    const observer = new MutationObserver(updateTheme);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    const question = input.trim();
    setInput('');
    setIsLoading(true);
    setRobotState('thinking');

    try {
      const apiUrl = getChatApiUrl();
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (!response.ok) {
        const detail = data?.detail || response.statusText || 'Unknown error';
        throw new Error(`API error ${response.status}: ${detail}`);
      }

      const botMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        confidence: data.confidence,
      };
      setMessages(prev => [...prev, botMessage]);
      setRobotState('speaking');
      setTimeout(() => setRobotState('idle'), 2000);
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `⚠️ ${error.message || 'Sorry, I encountered an error. Please try again later.'}`,
      };
      setMessages(prev => [...prev, errorMessage]);
      setRobotState('idle');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setRobotState('hover');
      setTimeout(() => setRobotState('idle'), 500);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  if (!mounted) {
    return null;
  }

  return (
    <div className="chatbot-widget" ref={widgetRef}>
      {/* Toggle Button */}
      <button
        className={`chatbot-toggle ${isOpen ? 'open' : ''}`}
        onClick={toggleChat}
        aria-label={isOpen ? 'Close chat' : 'Open chat with AI assistant'}
        aria-expanded={isOpen}
      >
        <RobotSVG state={robotState} isDark={isDark} />
        {!isOpen && <span className="notification-badge" aria-hidden="true" />}
      </button>

      {/* Chat Panel */}
      <div
        className={`chatbot-panel ${isOpen ? 'open' : ''}`}
        role="dialog"
        aria-label="AI Textbook Assistant"
        aria-modal="true"
      >
        <div className="chatbot-header">
          <div className="header-content">
            <RobotSVG state="idle" isDark={isDark} />
            <div>
              <h3>AI Textbook Assistant</h3>
              <span className="subtitle">Ask me about Physical AI & Robotics</span>
            </div>
          </div>
          <button
            className="close-button"
            onClick={toggleChat}
            aria-label="Close chat"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="chatbot-messages" role="log" aria-live="polite">
          {messages.length === 0 && (
            <div className="welcome-message">
              <p>Hello! I'm your Physical AI & Humanoid Robotics textbook assistant.</p>
              <p>Ask me about:</p>
              <ul>
                <li>Module 1: ROS 2 Nervous System (Weeks 1-5)</li>
                <li>Module 2: Digital Twin (Weeks 6-7)</li>
                <li>Module 3: NVIDIA Isaac AI Brain (Weeks 8-10)</li>
                <li>Module 4: Vision-Language-Action (Weeks 11-13)</li>
              </ul>
              <p className="hint">I only answer from the textbook content.</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-bubble">
                <div className="message-content">{msg.content}</div>
                {msg.sources && msg.sources.length > 0 && (
                  <details className="sources">
                    <summary>📚 Sources ({msg.sources.length})</summary>
                    <ul>
                      {msg.sources.map((src, i) => (
                        <li key={i}>
                          <strong>{src.title}</strong> › {src.section}
                          <br />
                          <small>{src.module}</small>
                        </li>
                      ))}
                    </ul>
                    {msg.confidence !== undefined && (
                      <div className="confidence">
                        Confidence: {(msg.confidence * 100).toFixed(0)}%
                      </div>
                    )}
                  </details>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant loading">
              <div className="message-bubble">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chatbot-input" onSubmit={handleSend}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the textbook..."
            rows={1}
            disabled={isLoading}
            aria-label="Your question"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            aria-label="Send message"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatbotWidget;