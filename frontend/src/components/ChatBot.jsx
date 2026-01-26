import React, { useState, useRef, useEffect } from "react";
import "./ChatBot.css";

export default function ChatBot({ customerId = "CUST001" }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      type: "ai",
      text: "Hello! 👋 I'm your AI shopping assistant. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentTimeline, setAgentTimeline] = useState([]);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const timelineEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const scrollTimelineToBottom = () => {
    timelineEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    scrollTimelineToBottom();
  }, [agentTimeline]);

  const toggleChatbot = () => {
    setIsOpen(!isOpen);
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      type: "user",
      text: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    // Add to agent timeline
    setAgentTimeline((prev) => [
      ...prev,
      {
        action: "User Query",
        timestamp: new Date().toLocaleTimeString(),
        status: "completed",
      },
    ]);

    try {
      const payload = {
        customer_id: customerId,
        message: inputValue,
        conversation_history: messages.map((m) => ({
          role: m.type === "user" ? "user" : "assistant",
          content: m.text,
        })),
      };

      console.log("Sending message to backend:", inputValue);
      console.log("Full payload:", JSON.stringify(payload, null, 2));

      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      console.log("Response status:", response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error response from backend:", errorData);
        throw new Error(
          `HTTP error! status: ${response.status}, detail: ${JSON.stringify(errorData)}`,
        );
      }

      const data = await response.json();
      console.log("Received data:", data);

      // Add AI response
      const aiMessage = {
        type: "ai",
        text: data.response || "No response received",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);

      // Add agent calls to timeline
      if (data.agent_calls && data.agent_calls.length > 0) {
        const newTimelineEntries = data.agent_calls.map((agentName) => ({
          action: agentName.replace(/_/g, " ").replace(/agent/gi, "Agent"),
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        }));
        setAgentTimeline((prev) => [...prev, ...newTimelineEntries]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = {
        type: "ai",
        text: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = async () => {
    // Clear local state
    setMessages([
      {
        type: "ai",
        text: "Hello! 👋 I'm your AI shopping assistant. How can I help you today?",
        timestamp: new Date(),
      },
    ]);
    setAgentTimeline([]);

    // Clear history in backend database
    try {
      await fetch(`http://localhost:8000/api/chat/history/${customerId}`, {
        method: "DELETE",
      });
      console.log("Chat history cleared from database");
    } catch (error) {
      console.error("Error clearing chat history:", error);
    }
  };

  return (
    <>
      {/* Chatbot Icon */}
      <div className="chatbot-icon" onClick={toggleChatbot}>
        <div className="bot-avatar">
          <span className="bot-emoji">🤖</span>
        </div>
        {!isOpen && <div className="pulse-ring"></div>}
      </div>

      {/* Chatbot Window */}
      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-container">
            {/* Left Panel - Agent Timeline */}
            <div className="agent-timeline-panel">
              <div className="timeline-header">
                <span className="timeline-icon">⚡</span>
                <h3>Agent Timeline</h3>
              </div>
              <div className="timeline-subtitle">Live Orchestration Log</div>

              <div className="timeline-content">
                {agentTimeline.length === 0 ? (
                  <div className="timeline-empty">
                    Waiting to start journey...
                  </div>
                ) : (
                  agentTimeline.map((entry, index) => (
                    <div key={index} className="timeline-entry">
                      <div className="timeline-dot"></div>
                      <div className="timeline-info">
                        <div className="timeline-action">{entry.action}</div>
                        <div className="timeline-time">{entry.timestamp}</div>
                      </div>
                    </div>
                  ))
                )}
                <div ref={timelineEndRef} />
              </div>
            </div>

            {/* Right Panel - Chat Interface */}
            <div className="chat-interface-panel">
              <div className="chat-header">
                <div className="header-content">
                  <span className="bot-icon">🤖</span>
                  <div className="header-text">
                    <h3>AI Orchestrator</h3>
                    <p>Multi-agent automation simulation</p>
                  </div>
                </div>
                <div className="header-actions">
                  <span className="status-badge">
                    {isLoading ? "In Progress" : "Active"}
                  </span>
                  <button
                    className="clear-btn"
                    onClick={clearChat}
                    title="Clear chat"
                  >
                    🗑️
                  </button>
                  <button className="close-btn" onClick={toggleChatbot}>
                    ✕
                  </button>
                </div>
              </div>

              <div className="chat-messages" ref={chatContainerRef}>
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`message ${message.type === "user" ? "user-message" : "ai-message"}`}
                  >
                    <div className="message-content">
                      <div className="message-text">{message.text}</div>
                      <div className="message-time">
                        {message.timestamp.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="message ai-message">
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="chat-input-container">
                <div className="input-wrapper">
                  <input
                    type="text"
                    className="chat-input"
                    placeholder="Enter Query..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading}
                  />
                  <button
                    className="send-btn"
                    onClick={sendMessage}
                    disabled={!inputValue.trim() || isLoading}
                  >
                    Search
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
