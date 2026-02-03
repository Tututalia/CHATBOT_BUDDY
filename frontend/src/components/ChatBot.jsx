import React, { useState, useRef, useEffect } from "react";
import "./ChatBot.css";
import chatbotConfig from "../../data/chatbotAgents.json";
import chatbotSchema from "../../data/chatbot.json";

export default function ChatBot({ customerId = "CUST001" }) {
  const [isOpen, setIsOpen] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentTimeline, setAgentTimeline] = useState([]);
  const [welcomeMessage, setWelcomeMessage] = useState("");
  const [lastRecommendations, setLastRecommendations] = useState([]);
  const [productQuantities, setProductQuantities] = useState({});
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const timelineEndRef = useRef(null);

  // Load welcome message from imported config
  useEffect(() => {
    setWelcomeMessage(
      chatbotConfig.welcome_message ||
        "Hello! 👋 I'm your AI shopping assistant. How can I help you today?",
    );
  }, []);

  // Set initial welcome message (no backend call)
  useEffect(() => {
    if (welcomeMessage) {
      const mockCustomerName = "Guest";
      setCustomerName(mockCustomerName);

      const personalizedMessage = `Hello ${mockCustomerName}! 👋\n\n${welcomeMessage}`;

      setMessages([
        {
          type: "ai",
          text: personalizedMessage,
          timestamp: new Date(),
        },
      ]);
    }
  }, [welcomeMessage]);

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
    const userInput = inputValue.toLowerCase();
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
      const { chatWithAgent } = await import("../services/chatApi.js");
      const response = await chatWithAgent(customerId, userMessage.text, []);

      console.log("Backend response:", response);

      // Handle timeline from backend
      if (response.timeline && Array.isArray(response.timeline)) {
        const newTimelineEntries = response.timeline.map((entry) => ({
          action: entry.agent,
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        }));
        setAgentTimeline((prev) => [...prev, ...newTimelineEntries]);
      }

      // Handle product cards from recommendation agent
      if (
        response.responses &&
        response.responses.recommendation &&
        Array.isArray(response.responses.recommendation)
      ) {
        // Track last recommendations for downstream UI (e.g., add-to-cart confirmation)
        setLastRecommendations(response.responses.recommendation);
        const productCardsMessage = {
          type: "productCards",
          productCards: response.responses.recommendation,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, productCardsMessage]);
      } else if (response.response.length==0) {
        // Fallback for text-only responses
       if(response.cart_items!=undefined)
        { 
      setAgentTimeline((prev) => [
        ...prev,
        {
          action: "View Cart Agent",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
      ]);

      // If backend returns cart items, display as product cards
      if (response.cart_items && Array.isArray(response.cart_items) && response.cart_items.length > 0) {
        const cartCardsMessage = {
          type: "cartItems",
          cartItems: response.cart_items,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, cartCardsMessage]);
      } else {
       
        const aiMessage = {
          type: "ai",
          text: response.response || "Your cart is currently empty.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMessage]);
      } }else{ 
         console.log("fallback")
         const aiMessage = {
          type: "ai",
          text: response.response,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMessage]);

        // If backend confirmed add-to-cart in plain text, also render a structured confirmation card
        if (/Added to Cart/i.test(response.response)) {
          const qtyMatch = userMessage.text.match(/\b(\d+)\b/);
          const quantity = qtyMatch ? parseInt(qtyMatch[1], 10) : 1;
          const product = lastRecommendations && lastRecommendations.length > 0
            ? lastRecommendations[0]
            : null;
          if (product) {
            const total = (product.price || 0) * quantity;
            const cartConfirmMessage = {
              type: "cartConfirmation",
              data: {
                message: "✅ Added to Cart!",
                product: {
                  product_id: product.product_id,
                  product_name: product.product_name,
                  quantity,
                  price_per_unit: product.price,
                  total
                },
                prompt: "Would you like to add more products or proceed to view your cart?"
              },
              timestamp: new Date()
            };
            setMessages((prev) => [...prev, cartConfirmMessage]);
            setAgentTimeline((prev) => [
              ...prev,
              {
                action: "Add to Cart Agent",
                timestamp: new Date().toLocaleTimeString(),
                status: "completed",
              },
            ]);
          }
        }
      }
    }
      

        

    }  catch (err) {
      console.error("Error calling agent:", err);
      const errorMessage = {
        type: "ai",
        text: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
    setIsLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Parse message text and extract purchase options if present
  const parseMessageContent = (text) => {
    const purchaseOptionsMatch = text.match(/<!--PURCHASE_OPTIONS:(.*?)-->/);
    if (purchaseOptionsMatch) {
      try {
        const options = JSON.parse(purchaseOptionsMatch[1]);
        const cleanText = text
          .replace(/<!--PURCHASE_OPTIONS:.*?-->/, "")
          .trim();
        return { text: cleanText, purchaseOptions: options };
      } catch (e) {
        console.error("Error parsing purchase options:", e);
        return { text, purchaseOptions: null };
      }
    }
    return { text, purchaseOptions: null };
  };

  // Handle purchase method button clicks
  const handlePurchaseMethodClick = (method) => {
    if (method === "Buy Online") {
      setInputValue("I want to buy online");
      setTimeout(() => sendMessage(), 100);
    } else {
      // For Nearest Store, show store selection from Inventory Agent
      const agent = chatbotConfig.agents.find(
        (a) => a.id === "inventory_agent",
      );
      if (agent && agent.responses.store_selection) {
        const userMessage = {
          type: "user",
          text: "I want to pick up from nearest store",
          timestamp: new Date(),
        };

        const aiMessage = {
          type: "ai",
          text: agent.responses.store_selection.message,
          timestamp: new Date(),
          storeSelection: agent.responses.store_selection,
        };

        setMessages((prev) => [...prev, userMessage, aiMessage]);
        setAgentTimeline((prev) => [
          ...prev,
          {
            action: "Inventory Agent",
            timestamp: new Date().toLocaleTimeString(),
            status: "completed",
          },
        ]);
      }
    }
  };

  // Handle payment submission
  const handlePaymentSubmit = (upiId) => {
    const userMessage = {
      type: "user",
      text: `UPI Payment: ${upiId}`,
      timestamp: new Date(),
    };

    // Get agent responses
    const fulfillmentAgent = chatbotConfig.agents.find(
      (a) => a.id === "fulfillment_agent",
    );
    const loyaltyAgent = chatbotConfig.agents.find(
      (a) => a.id === "loyalty_agent",
    );
    const postPurchaseAgent = chatbotConfig.agents.find(
      (a) => a.id === "post_purchase_agent",
    );

    if (
      fulfillmentAgent &&
      fulfillmentAgent.responses.online_order_confirmation
    ) {
      const confirmationData =
        fulfillmentAgent.responses.online_order_confirmation;

      const fulfillmentMessage = {
        type: "ai",
        text: confirmationData.message,
        timestamp: new Date(),
        orderConfirmation: confirmationData,
      };

      // Add loyalty message
      const loyaltyMessage =
        loyaltyAgent && loyaltyAgent.responses.loyalty_applied
          ? {
              type: "ai",
              text: "",
              timestamp: new Date(),
              loyaltyRewards: loyaltyAgent.responses.loyalty_applied,
            }
          : null;

      // Add post purchase message
      const postPurchaseMessage =
        postPurchaseAgent && postPurchaseAgent.responses.support_activated
          ? {
              type: "ai",
              text: "",
              timestamp: new Date(),
              postPurchaseSupport:
                postPurchaseAgent.responses.support_activated,
            }
          : null;

      const messages = [userMessage, fulfillmentMessage];
      if (loyaltyMessage) messages.push(loyaltyMessage);
      if (postPurchaseMessage) messages.push(postPurchaseMessage);

      setMessages((prev) => [...prev, ...messages]);

      const timelineEntries = [
        {
          action: "User Query",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
        {
          action: "Fulfillment Agent",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
      ];

      if (loyaltyMessage) {
        timelineEntries.push({
          action: "Loyalty Agent",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        });
      }

      if (postPurchaseMessage) {
        timelineEntries.push({
          action: "Post Purchase Agent",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        });
      }

      setAgentTimeline((prev) => [...prev, ...timelineEntries]);
    }
  };

  // Handle store selection
  const handleStoreSelect = (storeName) => {
    const userMessage = {
      type: "user",
      text: `I selected ${storeName}`,
      timestamp: new Date(),
    };

    // Get fulfillment agent response
    const fulfillmentAgent = chatbotConfig.agents.find(
      (a) => a.id === "fulfillment_agent",
    );
    if (fulfillmentAgent && fulfillmentAgent.responses.store_handoff) {
      const handoffData = fulfillmentAgent.responses.store_handoff;

      const aiMessage = {
        type: "ai",
        text: "",
        timestamp: new Date(),
        storeHandoff: handoffData,
      };

      setMessages((prev) => [...prev, userMessage, aiMessage]);
      setAgentTimeline((prev) => [
        ...prev,
        {
          action: "User Query",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
        {
          action: "Fulfillment Agent",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
      ]);
    }
  };

  // Handle purchase option button clicks
  const handlePurchaseOption = async (option, productId, productName) => {
    let messageText = "";
    if (option === "online") {
      messageText = `I want to buy ${productName} online`;
    } else if (option === "offline") {
      messageText = `I want to pick up ${productName} from a store`;
    }

    // Set the input and auto-send
    setInputValue(messageText);

    // Wait a bit for state to update, then send
    setTimeout(async () => {
      if (!messageText.trim() || isLoading) return;

      const userMessage = {
        type: "user",
        text: messageText,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInputValue("");
      setIsLoading(true);

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
          message: messageText,
          conversation_history: messages.map((m) => ({
            role: m.type === "user" ? "user" : "assistant",
            content: m.text,
          })),
        };

        const response = await fetch("http://localhost:8000/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        const aiMessage = {
          type: "ai",
          text: data.response || "No response received",
          timestamp: new Date(),
          productCards: data.product_cards || [],
        };

        setMessages((prev) => [...prev, aiMessage]);

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
    }, 100);
  };

  const handleQuantityChange = (productId, delta) => {
    setProductQuantities((prev) => {
      const currentQty = prev[productId] || 1;
      const newQty = Math.max(1, Math.min(99, currentQty + delta));
      return { ...prev, [productId]: newQty };
    });
  };

  const handleRemoveFromCart = async (orderId, productName) => {
    const userMessage = {
      type: "user",
      text: `Remove ${productName} from cart`,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
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
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `Remove item ${orderId} from cart`,
          customer_id: customerId,
        }),
      });

      const data = await response.json();

      setAgentTimeline((prev) => [
        ...prev,
        {
          action: "Remove from Cart Agent",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
      ]);

      const aiMessage = {
        type: "ai",
        text: data.response || "Item removed from cart successfully!",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);

      // Auto-refresh cart after removal
      setTimeout(() => handleViewCart(), 1000);
    } catch (error) {
      console.error("Error removing from cart:", error);
      const errorMessage = {
        type: "ai",
        text: "Sorry, there was an error removing the item. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const handleUpdateCartQuantity = async (orderId, productName, currentQuantity, delta) => {
    const newQuantity = Math.max(1, currentQuantity + delta);
    
    try {
      setIsLoading(true);
      
      const response = await fetch("http://localhost:8000/api/cart/update-quantity", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          order_id: orderId,
          quantity: newQuantity,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Update the cart items in the existing message
        setMessages((prevMessages) => {
          return prevMessages.map((message) => {
            if (message.type === "cartItems" && message.cartItems) {
              // Update the specific item in the cart
              const updatedCartItems = message.cartItems.map((item) => {
                if (item.order_id === orderId) {
                  const price = item.price || item.price_per_unit;
                  return {
                    ...item,
                    quantity: newQuantity,
                    total_amount: price * newQuantity
                  };
                }
                return item;
              });
              
              return {
                ...message,
                cartItems: updatedCartItems
              };
            }
            return message;
          });
        });
      } else {
        const errorMessage = {
          type: "ai",
          text: data.error || "Failed to update quantity. Please try again.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error("Error updating cart quantity:", error);
      const errorMessage = {
        type: "ai",
        text: "Sorry, there was an error updating the quantity. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const handleViewCart = async () => {
    const userMessage = {
      type: "user",
      text: "View my cart",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
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
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "view cart",
          customer_id: customerId,
        }),
      });

      const data = await response.json();

      setAgentTimeline((prev) => [
        ...prev,
        {
          action: "View Cart Agent",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
      ]);

      // If backend returns cart items, display as product cards
      if (data.cart_items && Array.isArray(data.cart_items) && data.cart_items.length > 0) {
        const cartCardsMessage = {
          type: "cartItems",
          cartItems: data.cart_items,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, cartCardsMessage]);
      } else {
        const aiMessage = {
          type: "ai",
          text: data.response || "Your cart is currently empty.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error("Error viewing cart:", error);
      const errorMessage = {
        type: "ai",
        text: "Sorry, there was an error loading your cart. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const handleAddToCart = async (product) => {
    const quantity = productQuantities[product.product_id] || 1;
    const userMessage = {
      type: "user",
      text: `Add ${quantity} x ${product.product_name} to cart`,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    // Add to agent timeline
    setAgentTimeline((prev) => [
      ...prev,
      {
        action: "Add to Cart Request",
        timestamp: new Date().toLocaleTimeString(),
        status: "completed",
      },
    ]);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `Add ${quantity} units of product ${product.product_id} to cart`,
          customer_id: customerId,
        }),
      });

      const data = await response.json();

      setAgentTimeline((prev) => [
        ...prev,
        {
          action: "Add to Cart Agent",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
      ]);

      const aiMessage = {
        type: "ai",
        text: data.response || "Item added to cart successfully!",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);

      // Add View Cart button after successful add to cart
      const viewCartMessage = {
        type: "viewCartPrompt",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, viewCartMessage]);

      // Reset quantity for this product
      setProductQuantities((prev) => {
        const updated = { ...prev };
        delete updated[product.product_id];
        return updated;
      });
    } catch (error) {
      console.error("Error adding to cart:", error);
      const errorMessage = {
        type: "ai",
        text: "Sorry, there was an error adding the item to cart. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const clearChat = () => {
    // Clear local state with personalized greeting from JSON
    const greetingText =
      customerName && welcomeMessage
        ? `Hello ${customerName}! 👋\n\n${welcomeMessage}`
        : welcomeMessage ||
          "Hello! 👋 I'm your AI shopping assistant. How can I help you today?";

    setMessages([
      {
        type: "ai",
        text: greetingText,
        timestamp: new Date(),
      },
    ]);
    setAgentTimeline([]);
    setProductQuantities({});
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
                <button className="back-btn" onClick={toggleChatbot}>
                  ◀ Back
                </button>
              </div>
              <div className="timeline-subtitle">Live Orchestration Log</div>

              <div className="timeline-content">
                {agentTimeline.length === 0 ? (
                  <div className="timeline-empty">
                    Waiting for agent activity...
                  </div>
                ) : (
                  agentTimeline.map((entry, index) => (
                    <div key={index} className="timeline-entry">
                      <div className="timeline-dot-container">
                        <div className="timeline-dot"></div>
                        {index < agentTimeline.length - 1 && (
                          <div className="timeline-line"></div>
                        )}
                      </div>
                      <div className="timeline-card">
                        <div className="timeline-card-header">
                          <div className="timeline-action">{entry.action}</div>
                          <span className="agent-badge">
                            {entry.action.toLowerCase().includes("agent")
                              ? entry.action.split(" ")[0].toLowerCase() +
                                "_agent"
                              : "system"}
                          </span>
                        </div>
                        <div className="timeline-agent-type">
                          Master Orchestrator
                        </div>
                        <div className="timeline-timestamps">
                          <div className="timeline-time-entry">
                            <span className="timeline-time">
                              {entry.timestamp}
                            </span>
                            <span className="timeline-flow">
                              System → {entry.action.split(" ")[0]}
                            </span>
                          </div>
                          <div className="timeline-time-entry">
                            <span className="timeline-time">
                              {entry.timestamp}
                            </span>
                            <span className="timeline-flow">
                              {entry.action.split(" ")[0]} → User
                            </span>
                          </div>
                        </div>
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
                  <div className="bot-icon-wrapper">
                    <span className="bot-icon">🤖</span>
                  </div>
                  <div className="header-text">
                    <h3>AI Orchestrator</h3>
                    <p>In-store multi-agent automation</p>
                  </div>
                </div>
                <div className="header-actions">
                  <span className="web-badge">Web</span>
                  <span className="status-badge">
                    <span className="status-label">Status: </span>
                    <span className="status-value">
                      {isLoading ? "Processing" : "Active"}
                    </span>
                  </span>
                  <button className="close-btn" onClick={toggleChatbot}>
                    ✕
                  </button>
                </div>
              </div>

              <div className="chat-messages" ref={chatContainerRef}>
                {messages.map((message, index) => {
                  const { text: displayText, purchaseOptions } =
                    message.type === "ai"
                      ? parseMessageContent(message.text)
                      : { text: message.text, purchaseOptions: null };

                  return (
                    <div
                      key={index}
                      className={`message ${message.type === "user" ? "user-message" : "ai-message"}`}
                    >
                      <div className="message-content">
                        <div className="message-text">{displayText}</div>

                        {/* Render Post Purchase Support */}
                        {message.postPurchaseSupport && (
                          <div className="post-purchase-container">
                            <div className="post-purchase-header">
                              <span className="post-purchase-icon">💬</span>
                              <div className="post-purchase-header-text">
                                <h4>{message.postPurchaseSupport.title}</h4>
                                <p>{message.postPurchaseSupport.description}</p>
                              </div>
                            </div>

                            <div className="services-title">
                              {message.postPurchaseSupport.services_title}
                            </div>

                            <div className="services-list">
                              {message.postPurchaseSupport.services.map(
                                (service, idx) => (
                                  <div
                                    key={idx}
                                    className={`service-card ${service.type}`}
                                  >
                                    <div className="service-icon-wrapper">
                                      <span className="service-icon">
                                        {service.icon}
                                      </span>
                                    </div>
                                    <div className="service-content">
                                      <h5 className="service-name">
                                        {service.name}
                                      </h5>
                                      <p className="service-description">
                                        {service.description}
                                      </p>
                                    </div>
                                    <div className="service-status">
                                      {service.status}
                                    </div>
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        )}

                        {/* Render Loyalty Rewards */}
                        {message.loyaltyRewards && (
                          <div className="loyalty-rewards-container">
                            <div className="loyalty-header">
                              <span className="loyalty-icon">🎁</span>
                              <div className="loyalty-header-text">
                                <h4>{message.loyaltyRewards.title}</h4>
                                <p>{message.loyaltyRewards.description}</p>
                              </div>
                            </div>

                            <div className="loyalty-benefits-title">
                              {message.loyaltyRewards.benefits_title}
                            </div>

                            <div className="loyalty-benefits-list">
                              {message.loyaltyRewards.benefits.map(
                                (benefit, idx) => (
                                  <div
                                    key={idx}
                                    className={`loyalty-benefit-card ${benefit.type}`}
                                  >
                                    <div className="benefit-icon-wrapper">
                                      <span className="benefit-icon">
                                        {benefit.icon}
                                      </span>
                                    </div>
                                    <div className="benefit-content">
                                      <h5 className="benefit-title">
                                        {benefit.title}
                                      </h5>
                                      <p className="benefit-description">
                                        {benefit.description}
                                      </p>
                                    </div>
                                    <div className="benefit-value">
                                      {benefit.value}
                                    </div>
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        )}

                        {/* Render Order Confirmation */}
                        {message.orderConfirmation && (
                          <div className="order-confirmation-container">
                            <div className="payment-success-badge">
                              <span className="success-icon">✓</span>
                              <div className="success-text">
                                <h4>
                                  {
                                    message.orderConfirmation.payment_status
                                      .status
                                  }
                                </h4>
                                <p>
                                  {
                                    message.orderConfirmation.payment_status
                                      .description
                                  }
                                </p>
                              </div>
                            </div>

                            <div className="order-details-grid">
                              <div className="order-detail-item">
                                <span className="detail-label">Order ID</span>
                                <span className="detail-value">
                                  {
                                    message.orderConfirmation.order_details
                                      .order_id
                                  }
                                </span>
                              </div>
                              <div className="order-detail-item">
                                <span className="detail-label">
                                  Amount Paid
                                </span>
                                <span className="detail-value amount">
                                  ₹
                                  {message.orderConfirmation.order_details.amount_paid.toLocaleString()}
                                </span>
                              </div>
                              <div className="order-detail-item">
                                <span className="detail-label">
                                  Payment Method
                                </span>
                                <span className="detail-value">
                                  {
                                    message.orderConfirmation.order_details
                                      .payment_method
                                  }
                                </span>
                              </div>
                              <div className="order-detail-item">
                                <span className="detail-label">
                                  Delivery Time
                                </span>
                                <span className="detail-value delivery">
                                  {
                                    message.orderConfirmation.order_details
                                      .delivery_time
                                  }
                                </span>
                              </div>
                            </div>

                            <div className="order-confirmation-footer">
                              ✓ {message.orderConfirmation.confirmation_message}
                            </div>
                          </div>
                        )}

                        {/* Render Store Handoff */}
                        {message.storeHandoff && (
                          <div className="store-handoff-container">
                            <div className="channel-switching-banner">
                              🔄 Channel Switching:{" "}
                              {message.storeHandoff.channel_switching}
                            </div>

                            <div className="session-transfer-section">
                              <h4 className="section-title">
                                📋 Session Transfer
                              </h4>
                              <div className="session-info-grid">
                                <div className="session-info-item">
                                  <span className="info-label">
                                    🔑 Session:
                                  </span>
                                  <span className="info-value">
                                    {
                                      message.storeHandoff.session_transfer
                                        .session_id
                                    }
                                  </span>
                                </div>
                                <div className="session-info-item">
                                  <span className="info-label">
                                    👤 Customer:
                                  </span>
                                  <span className="info-value">
                                    {
                                      message.storeHandoff.session_transfer
                                        .customer_name
                                    }
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="product-section">
                              <h4 className="section-title">👚 Product</h4>
                              <div className="product-details">
                                <div className="product-name-badge">
                                  👔 {message.storeHandoff.product.name}
                                </div>
                                <div className="product-specs">
                                  <span>
                                    Size:{" "}
                                    <strong>
                                      {message.storeHandoff.product.size}
                                    </strong>
                                  </span>
                                  <span>
                                    Color:{" "}
                                    <strong>
                                      {message.storeHandoff.product.color}
                                    </strong>
                                  </span>
                                </div>
                                <div className="product-sku">
                                  {message.storeHandoff.product.sku}
                                </div>
                                <div className="product-price">
                                  ₹
                                  {message.storeHandoff.product.price.toLocaleString()}
                                </div>
                              </div>
                            </div>

                            <div className="store-handoff-section">
                              <h4 className="section-title">
                                🏪 Store Handoff
                              </h4>
                              <div className="store-handoff-details">
                                <div className="handoff-row">
                                  <span className="handoff-icon">📍</span>
                                  <span className="handoff-text">
                                    {
                                      message.storeHandoff.store_handoff_details
                                        .store_name
                                    }
                                  </span>
                                </div>
                                <div className="handoff-row">
                                  <span className="handoff-icon">👤</span>
                                  <span className="handoff-text">
                                    {
                                      message.storeHandoff.store_handoff_details
                                        .manager
                                    }
                                  </span>
                                </div>
                                <div className="handoff-row">
                                  <span className="availability-badge">
                                    ✅{" "}
                                    {
                                      message.storeHandoff.store_handoff_details
                                        .availability
                                    }
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Render Purchase Options Buttons */}
                        {purchaseOptions && (
                          <div className="purchase-options-container">
                            <div className="purchase-options-header">
                              <span className="purchase-icon">📦</span>
                              <h4>Choose Purchase Method</h4>
                            </div>
                            <div className="purchase-options-buttons">
                              {purchaseOptions.online_available && (
                                <button
                                  className="purchase-option-btn online-btn"
                                  onClick={() =>
                                    handlePurchaseOption(
                                      "online",
                                      purchaseOptions.product_id,
                                      purchaseOptions.product_name,
                                    )
                                  }
                                >
                                  <span className="btn-icon">🖥️</span>
                                  <div className="btn-text">
                                    <span className="btn-title">
                                      Buy Online
                                    </span>
                                    <span className="btn-subtitle">
                                      Home Delivery
                                    </span>
                                  </div>
                                </button>
                              )}
                              {purchaseOptions.offline_available && (
                                <button
                                  className="purchase-option-btn offline-btn"
                                  onClick={() =>
                                    handlePurchaseOption(
                                      "offline",
                                      purchaseOptions.product_id,
                                      purchaseOptions.product_name,
                                    )
                                  }
                                >
                                  <span className="btn-icon">🏪</span>
                                  <div className="btn-text">
                                    <span className="btn-title">
                                      Nearest Store
                                    </span>
                                    <span className="btn-subtitle">
                                      Store Pickup
                                    </span>
                                  </div>
                                </button>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Render Store Selection */}
                        {message.storeSelection && (
                          <div className="store-selection-container">
                            <div className="store-selection-header">
                              <span className="store-icon">🏪</span>
                              <h4>{message.storeSelection.title}</h4>
                            </div>
                            <div className="store-options">
                              {message.storeSelection.stores.map(
                                (store, idx) => (
                                  <div
                                    key={idx}
                                    className="store-option-card"
                                    onClick={() =>
                                      handleStoreSelect(store.store_name)
                                    }
                                  >
                                    <div className="store-info">
                                      <h5 className="store-name">
                                        {store.store_name}
                                      </h5>
                                      <p className="store-manager">
                                        {store.manager}
                                      </p>
                                    </div>
                                    <span
                                      className={`store-badge ${store.availability.toLowerCase()}`}
                                    >
                                      {store.availability}
                                    </span>
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        )}

                        {/* Render Purchase Method Buttons */}
                        {message.purchaseMethods &&
                          message.purchaseMethods.length > 0 && (
                            <div className="purchase-methods-container">
                              <div className="purchase-methods-header">
                                <span className="purchase-icon">📦</span>
                                <h4>Choose Purchase Method</h4>
                              </div>
                              <div className="purchase-methods-buttons">
                                {message.purchaseMethods.map((method, idx) => (
                                  <button
                                    key={idx}
                                    className={`purchase-method-btn ${method.method === "Buy Online" ? "online-btn" : "offline-btn"}`}
                                    onClick={() =>
                                      handlePurchaseMethodClick(method.method)
                                    }
                                  >
                                    <span className="btn-icon">
                                      {method.method === "Buy Online"
                                        ? "🖥️"
                                        : "🏪"}
                                    </span>
                                    <div className="btn-text">
                                      <span className="btn-title">
                                        {method.method}
                                      </span>
                                      <span className="btn-subtitle">
                                        {method.description}
                                      </span>
                                    </div>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                        {/* Render product cards if present */}
                        {message.productCards &&
                          message.productCards.length > 0 && (
                            <div className="product-cards-container">
                              {message.productCards.slice(0, 3).map((product) => (
                                <div
                                  key={product.product_id}
                                  className="product-card"
                                >
                                  <div className="product-image-wrapper">
                                    <img
                                      src={
                                        product.image_reference ||
                                        "/images/placeholder.png"
                                      }
                                      alt={product.product_name}
                                      className="product-image"
                                      onError={(e) => {
                                        e.target.src =
                                          "/images/placeholder.png";
                                      }}
                                    />
                                    {product.quantity > 0 &&
                                      product.quantity < 10 && (
                                        <span className="product-badge trending">
                                          Low Stock
                                        </span>
                                      )}
                                  </div>
                                  <div className="product-info">
                                    <h4 className="product-name">
                                      {product.product_name}
                                    </h4>
                                    <p className="product-price">
                                      ₹{product.price.toLocaleString()}
                                    </p>
                                    <div className="quantity-controls">
                                      <button
                                        className="qty-btn"
                                        onClick={() =>
                                          handleQuantityChange(
                                            product.product_id,
                                            -1,
                                          )
                                        }
                                      >
                                        −
                                      </button>
                                      <span className="qty-value">
                                        {productQuantities[product.product_id] || 1}
                                      </span>
                                      <button
                                        className="qty-btn"
                                        onClick={() =>
                                          handleQuantityChange(
                                            product.product_id,
                                            1,
                                          )
                                        }
                                      >
                                        +
                                      </button>
                                    </div>
                                    <button
                                      className="add-to-cart-btn"
                                      onClick={() => handleAddToCart(product)}
                                    >
                                      Add to Cart
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                        {/* Render cart items as product cards */}
                        {message.type === "cartItems" && message.cartItems && message.cartItems.length > 0 && (
                          <div className="cart-items-container">
                            <div className="cart-header-section">
                              <span className="cart-icon">🛒</span>
                              <h4>Your Cart ({message.cartItems.length} items)</h4>
                            </div>
                            <div className="product-cards-container">
                              {message.cartItems.map((item) => (
                                <div
                                  key={item.order_id || item.product_id}
                                  className="product-card cart-item-card"
                                >
                                  <button
                                    className="cart-item-delete-btn"
                                    onClick={() => handleRemoveFromCart(item.order_id, item.product_name)}
                                    title="Remove from cart"
                                  >
                                    🗑️
                                  </button>
                                  <div className="product-image-wrapper">
                                    <img
                                      src={
                                        item.image_reference ||
                                        "/images/placeholder.png"
                                      }
                                      alt={item.product_name}
                                      className="product-image"
                                      onError={(e) => {
                                        e.target.src =
                                          "/images/placeholder.png";
                                      }}
                                    />
                                    <span className="cart-quantity-badge">
                                      Qty: {item.quantity}
                                    </span>
                                  </div>
                                  <div className="product-info">
                                    <h4 className="product-name">
                                      {item.product_name}
                                    </h4>
                                    <p className="product-price">
                                      ₹{(item.price || item.price_per_unit)?.toLocaleString()}
                                    </p>
                                    <div className="cart-item-details">
                                      <span className="detail-label">Quantity:</span>
                                      <div className="quantity-controls">
                                        <button
                                          className="quantity-btn minus-btn"
                                          onClick={() => handleUpdateCartQuantity(item.order_id, item.product_name, item.quantity, -1)}
                                          disabled={item.quantity <= 1}
                                        >
                                          −
                                        </button>
                                        <span className="quantity-value">{item.quantity}</span>
                                        <button
                                          className="quantity-btn plus-btn"
                                          onClick={() => handleUpdateCartQuantity(item.order_id, item.product_name, item.quantity, 1)}
                                        >
                                          +
                                        </button>
                                      </div>
                                    </div>
                                    <div className="cart-item-total">
                                      <span className="total-label">Total:</span>
                                      <span className="total-value">₹{(item.total_amount || (item.price || item.price_per_unit) * item.quantity)?.toLocaleString()}</span>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Render View Cart Prompt */}
                        {message.type === "viewCartPrompt" && (
                          <div className="view-cart-prompt">
                            <button
                              className="view-cart-btn"
                              onClick={handleViewCart}
                            >
                              🛒 View Cart
                            </button>
                            <button
                              className="continue-shopping-btn"
                              onClick={() => setInputValue("show me more products")}
                            >
                              Continue Shopping
                            </button>
                          </div>
                        )}

                        {/* Render Add-to-Cart confirmation card */}
                        {message.type === "cartConfirmation" && message.data && (
                          <div className="cart-confirmation-container">
                            <div className="cart-confirmation-card">
                              <div className="cart-header">
                                <span className="cart-icon">🛒</span>
                                <h4>{message.data.message}</h4>
                              </div>
                              <div className="cart-details-grid">
                                <div className="cart-detail-item">
                                  <span className="detail-label">Product</span>
                                  <span className="detail-value">{message.data.product.product_name} ({message.data.product.product_id})</span>
                                </div>
                                <div className="cart-detail-item">
                                  <span className="detail-label">Quantity</span>
                                  <span className="detail-value">{message.data.product.quantity}</span>
                                </div>
                                <div className="cart-detail-item">
                                  <span className="detail-label">Price</span>
                                  <span className="detail-value amount">₹{Number(message.data.product.price_per_unit).toLocaleString()}</span>
                                </div>
                                <div className="cart-detail-item">
                                  <span className="detail-label">Total</span>
                                  <span className="detail-value amount">₹{Number(message.data.product.total).toLocaleString()}</span>
                                </div>
                              </div>
                              <div className="cart-actions">
                                <button className="cart-btn primary" onClick={() => setInputValue("view cart")}>View Cart</button>
                                <button className="cart-btn" onClick={() => setInputValue("add more")}>Add More</button>
                              </div>
                              <p className="cart-prompt">{message.data.prompt}</p>
                            </div>
                          </div>
                        )}

                        {/* Render Payment Input */}
                        {message.showPaymentInput && (
                          <div className="payment-input-container">
                            <div className="payment-back-link">
                              ← Back to payment methods
                            </div>
                            <div className="payment-input-box">
                              <label className="payment-label">
                                Enter your UPI ID to complete payment
                              </label>
                              <input
                                type="text"
                                className="payment-upi-input"
                                placeholder="yourname@upi"
                                onKeyPress={(e) => {
                                  if (
                                    e.key === "Enter" &&
                                    e.target.value.trim()
                                  ) {
                                    handlePaymentSubmit(e.target.value);
                                    e.target.value = "";
                                  }
                                }}
                              />
                            </div>
                          </div>
                        )}

                        <div className="message-time">
                          {message.timestamp.toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                      </div>
                    </div>
                  );
                })}
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
                    placeholder="Type your message here..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading}
                  />
                  <button className="mic-btn" title="Voice input">
                    🎤
                  </button>
                  <button
                    className="send-btn"
                    onClick={sendMessage}
                    disabled={!inputValue.trim() || isLoading}
                    title="Send message"
                  >
                    ➤
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
