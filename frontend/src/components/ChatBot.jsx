import React, { useState, useRef, useEffect, StrictMode } from "react";
import "./ChatBot.css";
import chatbotConfig from "../../data/chatbotAgents.json";
import chatbotSchema from "../../data/chatbot.json";

export default function ChatBot({ customerId }) {
  // Helper function to get time-based greeting
  const getTimeBasedGreeting = (name) => {
    const hour = new Date().getHours();
    let greeting = "";
    let emoji = "";
    let message = "";

    if (hour >= 5 && hour < 12) {
      greeting = "Good morning";
      emoji = "☀️";
      message = "Ready for some shopping?";
    } else if (hour >= 12 && hour < 17) {
      greeting = "Good afternoon";
      emoji = "🌤️";
      message = "What can I help you find?";
    } else if (hour >= 17 && hour < 21) {
      greeting = "Good evening";
      emoji = "🌙";
      message = "Let's find something special!";
    } else {
      greeting = "Hello";
      emoji = "✨";
      message = "Welcome! How can I assist you?";
    }

    const nameText = name ? `${name}` : "there";
    return {
      greeting: `${greeting}, ${nameText}! ${emoji}`,
      message: message,
      isWelcome: true,
    };
  };

  const [isOpen, setIsOpen] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentTimeline, setAgentTimeline] = useState([]);
  const [welcomeMessage, setWelcomeMessage] = useState("");
  const [lastRecommendations, setLastRecommendations] = useState([]);
  const [productQuantities, setProductQuantities] = useState({});
  const [conversationLog, setConversationLog] = useState([]);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const timelineEndRef = useRef(null);
  const [WelcomebackMessage, setWelcomebackMessage] = useState("");
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState(null);
  const [isTimelineOpen, setIsTimelineOpen] = useState(true);
  const [historyLoaded, setHistoryLoaded] = useState(false); // Track if history was restored
  const [paymentDetails, setPaymentDetails] = useState({
    upiId: "",
    cardNumber: "",
    expiryDate: "",
    cvv: "",
  });

  // Helper function to add timeline entries sequentially with animation delay
  const addTimelineEntriesSequentially = (entries, delayMs = 500) => {
    entries.forEach((entry, index) => {
      setTimeout(() => {
        setAgentTimeline((prev) => [...prev, entry]);
      }, index * delayMs);
    });
  };
  const render = (response) => {
    // Handle timeline from backend
    if (response.timeline && Array.isArray(response.timeline)) {
      const newTimelineEntries = response.timeline.map((entry) => ({
        action: entry.agent,
        timestamp: new Date().toLocaleTimeString(),
        status: "completed",
      }));
      addTimelineEntriesSequentially(newTimelineEntries, 400);
    }

    let contentHandled = false;

    // Handle cart items from view_cart_agent
    if (response.cart_items && Array.isArray(response.cart_items)) {
      setAgentTimeline((prev) => [
        ...prev,
        {
          action: "View Cart Agent",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
      ]);

      // Display cart items as product cards
      if (response.cart_items.length > 0) {
        console.log("Rendering cart items:", response.cart_items);
        const cartCardsMessage = {
          type: "cartItems",
          cartItems: response.cart_items,
          total_amount: response.total_amount,
          total_savings: response.total_savings,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, cartCardsMessage]);
      } else {
        const aiMessage = {
          type: "ai",
          text: "Your cart is currently empty.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMessage]);
      }
      contentHandled = true;
    }

    // Handle payment method selection from payment_agent (check independently, not else-if)
    if (
      response.agent_calls &&
      response.agent_calls.includes("payment_agent")
    ) {
      // Check if the last message is already a paymentMethods to avoid duplicates
      setMessages((prev) => {
        const lastMessage = prev[prev.length - 1];
        // Don't add payment methods again if already showing or if user just selected a method
        if (lastMessage?.type === "paymentMethods") {
          return prev;
        }

        const paymentMethodsMessage = {
          type: "paymentMethods",
          text: response.response,
          timestamp: new Date(),
        };
        return [...prev, paymentMethodsMessage];
      });
      contentHandled = true;
    }

    // Handle purchase method selection from choose_channel_agent (only if not already handled by payment_agent)
    if (
      !contentHandled &&
      response.agent_calls &&
      response.agent_calls.includes("choose_channel_agent")
    ) {
      const purchaseMethodsMessage = {
        type: "purchaseMethods",
        text: response.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, purchaseMethodsMessage]);
      contentHandled = true;
    }

    // Handle product cards from recommendation agent
    if (
      !contentHandled &&
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
      contentHandled = true;
    }

    // Fallback for text-only responses
    if (!contentHandled && response.response) {
      console.log("fallback");
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
        const product =
          lastRecommendations && lastRecommendations.length > 0
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
                total,
              },
              prompt:
                "Would you like to add more products or proceed to view your cart?",
            },
            timestamp: new Date(),
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
  };
  // Load welcome message from imported config
  useEffect(() => {
    setWelcomeMessage(
      chatbotConfig.welcome_message ||
        "Hello! 👋 I'm your AI shopping assistant. How can I help you today?",
    );
  }, []);

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

  // Auto-scroll to bottom when chatbot is opened and history is restored
  useEffect(() => {
    if (isOpen && historyLoaded && messages.length > 0) {
      // Use a slight delay to ensure DOM is rendered
      setTimeout(() => {
        scrollToBottom();
      }, 500);
    }
  }, [isOpen, historyLoaded, messages]);

  // Combined effect: Check history first, then decide whether to show welcome or restore history
  useEffect(() => {
    const initializeChat = async () => {
      if (!welcomeMessage || !customerId) return;

      try {
        // Import APIs
        const { gethistory, getCustomerProfile } =
          await import("../services/chatApi.js");

        // Fetch customer profile first
        let fetchedName = "Guest";
        try {
          const profileData = await getCustomerProfile(customerId);
          fetchedName = profileData?.customer_name || "Guest";
        } catch (error) {
          console.error("Error fetching customer name:", error);
        }
        setCustomerName(fetchedName);

        // Check for existing chat history
        const historyResponse = await gethistory(customerId);
        console.log("History response:", historyResponse);

        // If there's chat history, restore it
        if (historyResponse?.payload && historyResponse.payload.length > 0) {
          setHistoryLoaded(true);

          // Start with welcome back card
          const timeGreeting = getTimeBasedGreeting(fetchedName);
          const welcomeBackText = `Welcome back, ${fetchedName}! 👋\n\nWe've restored your previous conversation. Continue your shopping journey!`;

          const initialMessages = [
            {
              type: "ai",
              text: welcomeBackText,
              timestamp: new Date(),
              isWelcomeCard: true,
            },
          ];

          // Add all restored messages
          historyResponse.payload.forEach((item) => {
            console.log("Restoring item:", item);

            // Add user message
            initialMessages.push({
              type: "user",
              text: item.payload.message,
              timestamp: new Date(),
            });

            // Add AI response based on response type
            const response = item.response;

            if (response.cart_items && Array.isArray(response.cart_items)) {
              if (response.cart_items.length > 0) {
                initialMessages.push({
                  type: "cartItems",
                  cartItems: response.cart_items,
                  total_amount: response.total_amount,
                  total_savings: response.total_savings,
                  timestamp: new Date(),
                });
              } else {
                initialMessages.push({
                  type: "ai",
                  text: "Your cart is currently empty.",
                  timestamp: new Date(),
                });
              }
            } else if (response.agent_calls?.includes("choose_channel_agent")) {
              initialMessages.push({
                type: "purchaseMethods",
                text: response.response,
                timestamp: new Date(),
              });
            } else if (
              response.agent_calls?.includes("payment_agent") &&
              response.agent_calls.length === 1
            ) {
              initialMessages.push({
                type: "paymentMethods",
                text: response.response,
                timestamp: new Date(),
              });
            } else if (
              response.responses?.recommendation &&
              Array.isArray(response.responses.recommendation)
            ) {
              setLastRecommendations(response.responses.recommendation);
              initialMessages.push({
                type: "productCards",
                productCards: response.responses.recommendation,
                timestamp: new Date(),
              });
            } else if (response.response) {
              initialMessages.push({
                type: "ai",
                text: response.response,
                timestamp: new Date(),
              });
            }
          });

          // Set all messages at once
          setMessages(initialMessages);

          // Scroll to bottom after messages are loaded
          setTimeout(() => {
            scrollToBottom();
          }, 1000);
        } else {
          // No history - show fresh welcome message
          const timeGreeting = getTimeBasedGreeting(fetchedName);
          const personalizedMessage = `${timeGreeting.greeting}\n\n${timeGreeting.message}\n\n${welcomeMessage}`;

          setMessages([
            {
              type: "ai",
              text: personalizedMessage,
              timestamp: new Date(),
              isWelcomeCard: true,
            },
          ]);
        }
      } catch (error) {
        console.error("Error initializing chat:", error);
        // Fallback to welcome message
        const timeGreeting = getTimeBasedGreeting("Guest");
        const personalizedMessage = `${timeGreeting.greeting}\n\n${timeGreeting.message}\n\n${welcomeMessage}`;

        setMessages([
          {
            type: "ai",
            text: personalizedMessage,
            timestamp: new Date(),
            isWelcomeCard: true,
          },
        ]);
      }
    };

    initializeChat();
  }, [welcomeMessage, customerId]);

  // Log conversation history whenever it updates
  useEffect(() => {
    if (conversationLog.length > 0) {
      console.log("=== Conversation Log ===");
      console.log("Total exchanges:", conversationLog.length);
      console.log("Full log:", conversationLog);
      console.log("Latest entry:", conversationLog[conversationLog.length - 1]);
      console.log("========================");
    }
  }, [conversationLog]);

  const toggleChatbot = () => {
    setIsOpen(!isOpen);
  };

  const wsRef = useRef(null);

  const formatLocalTime = (date = new Date()) => {
    try {
      return date.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch {
      return date.toLocaleTimeString();
    }
  };

  const parseWsLine = (line) => {
    if (!line || typeof line !== "string") {
      return { time: formatLocalTime(), text: "" };
    }

    // Backend prefixes log lines with HH:MM:SS via _ws_line()
    const match = line.match(/^\s*(\d{1,2}:\d{2}:\d{2})\s+(.*)$/);
    if (match) {
      return { time: match[1], text: match[2] };
    }

    return { time: formatLocalTime(), text: line.trim() };
  };

  const normalizeTimelineStatus = (status) => {
    const s = (status || "").toString().toLowerCase();
    if (s === "completed" || s === "success" || s === "done")
      return "completed";
    if (s === "error" || s === "failed") return "error";
    if (s === "in_progress" || s === "in-progress" || s === "running") {
      return "in-progress";
    }
    return status || "";
  };

  const getAgentShortName = (agentLabel) => {
    if (!agentLabel || typeof agentLabel !== "string") return "Agent";
    const first = agentLabel.trim().split(/\s+/)[0];
    return first || "Agent";
  };

  const ensureTimelineEntry = ({ key, tool, agentLabel, status }) => {
    const shortName = getAgentShortName(agentLabel);
    const localTime = formatLocalTime();

    setAgentTimeline((prev) => {
      const existingIndex = prev.findIndex((e) => e && e.key === key);
      if (existingIndex !== -1) {
        // Keep the latest status if we learn it later.
        const existing = prev[existingIndex];
        const nextStatus = normalizeTimelineStatus(status || existing?.status);
        if (nextStatus && nextStatus !== existing?.status) {
          const next = [...prev];
          next[existingIndex] = { ...existing, status: nextStatus };
          return next;
        }
        return prev;
      }

      return [
        ...prev,
        {
          key,
          action: agentLabel || tool || "Agent",
          tool: tool || "",
          status: normalizeTimelineStatus(status) || "in-progress",
          logs: [
            {
              time: localTime,
              text: `System → ${shortName}`,
              variant: "system",
            },
            {
              time: localTime,
              text: `${shortName} → User`,
              variant: "system",
            },
          ],
        },
      ];
    });
  };

  const appendTimelineLog = ({ key, tool, agentLabel, line }) => {
    setAgentTimeline((prev) => {
      const existingIndex = prev.findIndex((e) => e && e.key === key);
      let next = prev;

      if (existingIndex === -1) {
        // If logs arrive before the start event, create the entry.
        const shortName = getAgentShortName(agentLabel || tool);
        const localTime = formatLocalTime();
        next = [
          ...prev,
          {
            key,
            action: agentLabel || tool || "Agent",
            tool: tool || "",
            status: "in-progress",
            logs: [
              {
                time: localTime,
                text: `System → ${shortName}`,
                variant: "system",
              },
              {
                time: localTime,
                text: `${shortName} → User`,
                variant: "system",
              },
            ],
          },
        ];
      }

      const idx = existingIndex === -1 ? next.length - 1 : existingIndex;
      const entry = next[idx];
      const { time, text } = parseWsLine(line);
      const updated = {
        ...entry,
        logs: [...(entry.logs || []), { time, text, variant: "log" }],
      };

      const out = [...next];
      out[idx] = updated;
      return out;
    });
  };

  const endTimelineEntry = ({ key, status }) => {
    setAgentTimeline((prev) => {
      const idx = prev.findIndex((e) => e && e.key === key);
      if (idx === -1) return prev;
      const entry = prev[idx];
      const nextStatus = normalizeTimelineStatus(status) || "completed";
      if (entry.status === nextStatus) return prev;
      const out = [...prev];
      out[idx] = { ...entry, status: nextStatus };
      return out;
    });
  };

  const chatWithAgentViaWebSocket = (customerId, messageText) => {
    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${scheme}://${window.location.hostname}:8000/ws/chat`;

    // Close any previous run's socket (timeline only)
    try {
      if (wsRef.current) {
        wsRef.current.close();
      }
    } catch {
      // ignore
    }

    return new Promise((resolve, reject) => {
      let finalResponse = null;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            request_id: requestId,
            customer_id: customerId,
            message: messageText,
          }),
        );
      };

      ws.onerror = () => {
        reject(new Error("WebSocket connection error"));
      };

      ws.onmessage = (event) => {
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }

        if (msg && msg.request_id && msg.request_id !== requestId) {
          return;
        }

        const type = msg?.type;
        if (type === "timeline_start") {
          const tool = msg?.tool || "";
          const agentLabel = msg?.agent || tool;
          const key = `${requestId}:${tool || agentLabel}`;
          ensureTimelineEntry({
            key,
            tool,
            agentLabel,
            status: msg?.status,
          });
          return;
        }

        if (type === "timeline_log") {
          const tool = msg?.tool || "";
          const agentLabel = msg?.agent || tool;
          const key = `${requestId}:${tool || agentLabel}`;
          const line = msg?.text || msg?.message || msg?.log || "";
          appendTimelineLog({ key, tool, agentLabel, line });
          return;
        }

        if (type === "timeline_end") {
          const tool = msg?.tool || "";
          const agentLabel = msg?.agent || tool;
          const key = `${requestId}:${tool || agentLabel}`;
          endTimelineEntry({ key, status: msg?.status });
          return;
        }

        if (type === "final_response") {
          finalResponse = msg?.data || null;
          return;
        }

        if (type === "run_end") {
          try {
            ws.close();
          } catch {
            // ignore
          }
          resolve(
            finalResponse || {
              response: "",
              agent_calls: [],
            },
          );
          return;
        }

        if (type === "error") {
          try {
            ws.close();
          } catch {
            // ignore
          }
          reject(new Error(msg?.message || "WebSocket error"));
          return;
        }
      };
    });
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

    try {
      const response = await chatWithAgentViaWebSocket(
        customerId,
        userMessage.text,
      );

      // Track raw payload and response for this turn
      const newLogEntry = {
        payload: {
          customer_id: customerId,
          message: userMessage.text,
        },
        response,
      };

      // Build updated conversation log with the new entry
      const updatedConversationLog = [...conversationLog, newLogEntry];
      setConversationLog(updatedConversationLog);

      // Check if post_purchase_agent was called - if yes, don't save (backend already cleared it)
      const isPostPurchase =
        response.agent_calls &&
        response.agent_calls.includes("post_purchase_agent");

      // Save entire conversation log to database (skip if post-purchase to avoid overwriting the cleared payload)
      if (!isPostPurchase) {
        try {
          console.log("Saving full conversation log to database...", {
            customer_id: customerId,
            entries: updatedConversationLog.length,
          });
          const saveResponse = await fetch(
            "http://localhost:8000/api/payload/save",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                customer_id: customerId,
                payload: updatedConversationLog,
              }),
            },
          );
          const saveResult = await saveResponse.json();
          console.log("Payload save result:", saveResult);
          if (!saveResult.success) {
            console.error("Failed to save payload:", saveResult.error);
          }
        } catch (error) {
          console.error("Error saving payload to database:", error);
        }
      } else {
        console.log(
          "Post-purchase detected - skipping payload save (backend cleared it)",
        );
        // Clear local conversationLog since purchase is complete
        // setConversationLog([]);
      }

      console.log("Backend response:", response);

      // Handle cart items from view_cart_agent
      if (response.cart_items && Array.isArray(response.cart_items)) {
        setAgentTimeline((prev) => [
          ...prev,
          {
            action: "View Cart Agent",
            timestamp: new Date().toLocaleTimeString(),
            status: "completed",
          },
        ]);

        // Display cart items as product cards
        if (response.cart_items.length > 0) {
          const cartCardsMessage = {
            type: "cartItems",
            cartItems: response.cart_items,
            total_amount: response.total_amount,
            total_savings: response.total_savings,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, cartCardsMessage]);
        } else {
          const aiMessage = {
            type: "ai",
            text: "Your cart is currently empty.",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, aiMessage]);
        }
      }
      // Handle purchase method selection from choose_channel_agent
      else if (
        response.agent_calls &&
        response.agent_calls.includes("choose_channel_agent")
      ) {
        const purchaseMethodsMessage = {
          type: "purchaseMethods",
          text: response.response,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, purchaseMethodsMessage]);
      }
      // Handle payment method selection from payment_agent (only when it's the sole agent)
      else if (
        response.agent_calls &&
        response.agent_calls.includes("payment_agent") &&
        response.agent_calls.length === 1 // Only show payment methods when payment_agent is the only agent called
      ) {
        // Check if the last message is already a paymentMethods to avoid duplicates
        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          // Don't add payment methods again if already showing or if user just selected a method
          if (lastMessage?.type === "paymentMethods") {
            return prev;
          }

          const paymentMethodsMessage = {
            type: "paymentMethods",
            text: response.response,
            timestamp: new Date(),
          };
          return [...prev, paymentMethodsMessage];
        });
      }
      // Handle product cards from recommendation agent
      else if (
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
      } else {
        // Fallback for text-only responses
        console.log("fallback");
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
          const product =
            lastRecommendations && lastRecommendations.length > 0
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
                  total,
                },
                prompt:
                  "Would you like to add more products or proceed to view your cart?",
              },
              timestamp: new Date(),
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
    } catch (err) {
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
    // Safety check for undefined or null text
    if (!text || typeof text !== "string") {
      return { text: "", purchaseOptions: null };
    }

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

  // Parse structured LLM response (for beautiful formatting)
  const parseStructuredResponse = (text) => {
    const sections = {
      orderConfirmation: null,
      loyaltyRewards: null,
      postPurchaseSupport: null,
    };

    // Parse Order Confirmation section
    const orderMatch = text.match(
      /📦\s*\*\*Order Confirmed!\*\*([\s\S]*?)(?=🎉|\*\*Available Services|\*\*Coupon Codes|$)/i,
    );
    if (orderMatch) {
      const orderText = orderMatch[1];
      // Updated regex patterns to handle ** markdown bold syntax
      const orderIdMatch = orderText.match(/\*\*Order ID:\*\*\s*(\w+)/);
      const totalItemsMatch = orderText.match(/\*\*Total Items:\*\*\s*(\d+)/);
      const totalAmountMatch = orderText.match(
        /\*\*Total Amount:\*\*\s*₹([\d,]+)/,
      );
      const deliveryTypeMatch = orderText.match(
        /\*\*Delivery Type:\*\*\s*([^\n]+)/,
      );
      const deliveryTimeMatch = orderText.match(
        /\*\*Expected Delivery:\*\*\s*([^\n]+)/,
      );

      // Parse items
      const itemsMatch = orderText.match(
        /\*\*Your Items:\*\*([\s\S]*?)(?=\n\n|$)/,
      );
      let items = [];
      if (itemsMatch) {
        const itemLines = itemsMatch[1].trim().split("\n");
        items = itemLines
          .map((line) => {
            const itemMatch = line.match(
              /-\s*(.+?)\s*×\s*(\d+)\s*=\s*₹([\d,]+)/,
            );
            if (itemMatch) {
              return {
                name: itemMatch[1].trim(),
                quantity: parseInt(itemMatch[2]),
                price: itemMatch[3].replace(/,/g, ""),
              };
            }
            return null;
          })
          .filter(Boolean);
      }

      sections.orderConfirmation = {
        payment_status: {
          status: "Payment Successful!",
          description: "Your order has been confirmed",
        },
        order_details: {
          order_id: orderIdMatch ? orderIdMatch[1] : "N/A",
          amount_paid: totalAmountMatch
            ? parseInt(totalAmountMatch[1].replace(/,/g, ""))
            : 0,
          payment_method: "UPI",
          delivery_time: deliveryTimeMatch
            ? deliveryTimeMatch[1].trim()
            : "N/A",
        },
        items: items,
        confirmation_message: "Order confirmed and will be dispatched soon",
      };
    }

    // Parse Loyalty Rewards section
    const loyaltyMatch = text.match(
      /🎉\s*\*\*Loyalty Rewards Unlocked!\*\*([\s\S]*?)(?=\*\*Coupon Codes|\*\*Available Services|$)/i,
    );
    if (loyaltyMatch) {
      const loyaltyText = loyaltyMatch[1];
      // Updated regex to handle ** markdown bold syntax
      const pointsMatch = loyaltyText.match(
        /\*\*Points Earned:\*\*\s*(\d+)\s*points/,
      );

      // Parse coupon codes
      const couponsMatch = text.match(
        /\*\*Coupon Codes for Next Purchase:\*\*([\s\S]*?)(?=\*\*Available Services|Thank you|$)/i,
      );
      let coupons = [];
      if (couponsMatch) {
        const couponLines = couponsMatch[1].trim().split("\n");
        coupons = couponLines
          .map((line) => {
            const couponMatch = line.match(/-\s*Code:\s*`([^`]+)`\s*-\s*(.+)/);
            if (couponMatch) {
              return {
                code: couponMatch[1].trim(),
                description: couponMatch[2].trim(),
              };
            }
            return null;
          })
          .filter(Boolean);
      }

      sections.loyaltyRewards = {
        title: "Loyalty Rewards Applied!",
        description: "Your rewards have been processed and applied",
        benefits_title: "🏆 Loyalty Benefits Applied:",
        benefits: [
          {
            type: "points",
            icon: "🟢",
            title: "Loyalty Points Earned",
            description: `+${pointsMatch ? pointsMatch[1] : "0"} points added to your account`,
            value: `${pointsMatch ? pointsMatch[1] : "0"} pts`,
          },
          ...coupons.map((coupon, idx) => ({
            type: idx === 0 ? "coupon" : "offer",
            icon: idx === 0 ? "🟠" : "🔵",
            title:
              idx === 0
                ? "Coupon Applied"
                : idx === 1
                  ? "Personalized Offer"
                  : "Bonus Offer",
            description: coupon.description,
            value: coupon.code,
          })),
        ],
      };
    }

    // Parse Available Services section - improved matching
    const servicesMatch = text.match(
      /\*\*Available Services:\*\*([\s\S]*?)(?=Thank you|$)/i,
    );
    if (servicesMatch) {
      const servicesText = servicesMatch[1];
      const services = [];

      // Check if any service indicators exist
      const hasTrackOrder =
        servicesText.includes("Track Order") || servicesText.includes("📄");
      const hasFeedback =
        servicesText.includes("Leave Feedback") || servicesText.includes("⭐");
      const hasSupport =
        servicesText.includes("Customer Support") ||
        servicesText.includes("📧");
      const hasReturn =
        servicesText.includes("Return") ||
        servicesText.includes("Exchange") ||
        servicesText.includes("🔄");

      if (hasReturn) {
        services.push({
          type: "returns",
          icon: "🔴",
          name: "Returns & Exchanges",
          description: "30-day hassle-free return policy",
          status: "Active",
        });
      }

      if (hasTrackOrder) {
        services.push({
          type: "shipment",
          icon: "🔵",
          name: "Shipment Tracking",
          description: "Real-time delivery updates via SMS & email",
          status: "Enabled",
        });
      }

      if (hasFeedback) {
        services.push({
          type: "feedback",
          icon: "🟡",
          name: "Feedback System",
          description: "Share your experience & earn reward points",
          status: "Ready",
        });
      }

      if (hasSupport) {
        services.push({
          type: "support",
          icon: "🟢",
          name: "24/7 Customer Support",
          description: "Live chat, email & phone support available",
          status: "Online",
        });
      }

      if (services.length > 0) {
        sections.postPurchaseSupport = {
          title: "Post-Purchase Support Activated!",
          description: "We're here to help you throughout your journey",
          services_title: "🔹 Available Support Services:",
          services: services,
        };
      }
    }

    return sections;
  };

  // Handle purchase method button clicks
  const handlePurchaseMethodClick = (method) => {
    if (method === "Buy Online") {
      setInputValue("I want to buy online");
      setTimeout(() => sendMessage(), 100);
    } else if (method === "Nearest Store") {
      const userMessage = {
        type: "user",
        text: "I want to pick up from nearest store",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      chatWithAgentViaWebSocket(
        customerId,
        "I want to pick up from nearest offline store",
      )
        .then((data) => {
          // If backend returns storeSelection, show it
          if (data && data.storeSelection) {
            const storeMessage = {
              type: "storeSelection",
              title: data.storeSelection.title,
              stores: data.storeSelection.stores,
              timestamp: new Date(),
            };

            setMessages((prev) => [...prev, storeMessage]);
          } else if (data && data.response) {
            // Otherwise, just show the response
            const aiMessage = {
              type: "ai",
              text: data.response,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, aiMessage]);
          }
        })
        .catch((err) => {
          console.error("Error fetching store selection:", err);
          const errorMessage = {
            type: "ai",
            text: "Sorry, I couldn't fetch nearby stores. Please try again later.",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, errorMessage]);
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setInputValue(`I want to ${method.toLowerCase()}`);
      setTimeout(() => sendMessage(), 100);
    }
  };

  // Handle payment method button clicks
  const handlePaymentMethodClick = (method) => {
    // For Cash on Delivery, submit immediately without showing a form
    if (method === "cash on delivery") {
      handleCashOnDeliverySubmit();
    } else {
      setSelectedPaymentMethod(method);
    }
  };

  const handleCashOnDeliverySubmit = async () => {
    const paymentMessage = "I want to pay via Cash on Delivery";
    const paymentMethodDisplay = "Cash on Delivery";

    // Add user message showing payment selection
    const userMessage = {
      type: "user",
      text: `Payment Method: ${paymentMethodDisplay}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    setIsLoading(true);

    try {
      const response = await chatWithAgentViaWebSocket(
        customerId,
        paymentMessage,
      );

      console.log("Payment response:", response);

      // Handle fulfillment response
      if (response.response) {
        const aiMessage = {
          type: "ai",
          text: response.response,
          timestamp: new Date(),
        };

        // Check if response contains structured data for order confirmation
        if (response.structured_data) {
          aiMessage.structuredData = response.structured_data;
        }

        setMessages((prev) => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error("Error processing payment:", error);
      const errorMessage = {
        type: "ai",
        text: "Sorry, there was an error processing your payment. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToPaymentMethods = () => {
    setSelectedPaymentMethod(null);
    setPaymentDetails({
      upiId: "",
      cardNumber: "",
      expiryDate: "",
      cvv: "",
    });
  };

  const handlePaymentDetailsChange = (field, value) => {
    setPaymentDetails((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePaymentFormSubmit = async () => {
    let paymentMessage = "";
    let paymentMethodDisplay = "";

    if (selectedPaymentMethod === "upi") {
      paymentMessage = `I want to pay via UPI with ID: ${paymentDetails.upiId}`;
      paymentMethodDisplay = `UPI (${paymentDetails.upiId})`;
    } else if (selectedPaymentMethod === "credit card") {
      paymentMessage = `I want to pay via Credit Card ending in ${paymentDetails.cardNumber.replace(/\s/g, "").slice(-4)}`;
      paymentMethodDisplay = `Credit Card ending in ${paymentDetails.cardNumber.replace(/\s/g, "").slice(-4)}`;
    } else if (selectedPaymentMethod === "debit card") {
      paymentMessage = `I want to pay via Debit Card ending in ${paymentDetails.cardNumber.replace(/\s/g, "").slice(-4)}`;
      paymentMethodDisplay = `Debit Card ending in ${paymentDetails.cardNumber.replace(/\s/g, "").slice(-4)}`;
    } else if (selectedPaymentMethod === "cash on delivery") {
      paymentMessage = "I want to pay via Cash on Delivery";
      paymentMethodDisplay = "Cash on Delivery";
    }

    // Add user message showing payment selection
    const userMessage = {
      type: "user",
      text: `Payment Method: ${paymentMethodDisplay}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Reset form
    setSelectedPaymentMethod(null);
    setPaymentDetails({
      upiId: "",
      cardNumber: "",
      expiryDate: "",
      cvv: "",
    });

    setIsLoading(true);

    try {
      const response = await chatWithAgentViaWebSocket(
        customerId,
        paymentMessage,
      );

      console.log("Payment response:", response);

      // Handle fulfillment response
      if (response.response) {
        const aiMessage = {
          type: "ai",
          text: response.response,
          timestamp: new Date(),
        };

        // Check if response contains structured data for order confirmation
        if (response.structured_data) {
          aiMessage.structuredData = response.structured_data;
        }

        setMessages((prev) => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error("Error processing payment:", error);
      const errorMessage = {
        type: "ai",
        text: "Sorry, there was an error processing your payment. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
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

      addTimelineEntriesSequentially(timelineEntries, 400);
    }
  };

  // Handle store selection
  const handleStoreSelect = (storeName) => {
    const userMessage = {
      type: "user",
      text: `I selected ${storeName}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setAgentTimeline((prev) => [
      ...prev,
      {
        action: "User Query",
        timestamp: new Date().toLocaleTimeString(),
        status: "completed",
      },
    ]);

    chatWithAgentViaWebSocket(
      customerId,
      `I want to pick up my order from ${storeName}`,
    )
      .then((data) => {
        if (data && data.storeSelection) {
          const storeMessage = {
            type: "storeSelection",
            title: data.storeSelection.title,
            stores: data.storeSelection.stores,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, storeMessage]);
          return;
        }

        // Parse fulfillment agent response for beautiful formatting
        console.log(data);
        const sections = parseStructuredResponse((data && data.response) || "");
        const aiMessage = {
          type: "ai",
          text: (data && data.response) || "Your order is ready for pickup!",
          timestamp: new Date(),
          ...sections,
          ...(data && data.storeHandoff
            ? { storeHandoff: data.storeHandoff }
            : {}),
        };
        setMessages((prev) => [...prev, aiMessage]);
        setAgentTimeline((prev) => [
          ...prev,
          {
            action: "Fulfillment Agent",
            timestamp: new Date().toLocaleTimeString(),
            status: "completed",
          },
        ]);
      })
      .catch((err) => {
        setMessages((prev) => [
          ...prev,
          {
            type: "ai",
            text: "Error processing store handoff.",
            timestamp: new Date(),
          },
        ]);
      })
      .finally(() => setIsLoading(false));
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
          addTimelineEntriesSequentially(newTimelineEntries, 400);
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
      const currentQty = prev[productId] || 0;
      const newQty = Math.max(0, Math.min(99, currentQty + delta));
      return { ...prev, [productId]: newQty };
    });
  };

  const handleRemoveFromCart = async (orderId, productName) => {
    setIsLoading(true);

    // Add to agent timeline (silent operation)
    setAgentTimeline((prev) => [
      ...prev,
      {
        action: "Remove from Cart",
        timestamp: new Date().toLocaleTimeString(),
        status: "in-progress",
      },
    ]);

    try {
      // Direct API call to remove item without LLM interaction
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `Remove item ${orderId} from cart`,
          customer_id: customerId,
        }),
      });

      const data = await response.json();

      // Update timeline status
      setAgentTimeline((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].status = "completed";
        return updated;
      });

      // Silently refresh cart display without adding messages
      handleViewCart(true);
    } catch (error) {
      console.error("Error removing from cart:", error);

      // Update timeline with error
      setAgentTimeline((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].status = "error";
        return updated;
      });

      // Show error in chat
      const errorMessage = {
        type: "ai",
        text: "Sorry, there was an error removing the item. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const handleUpdateCartQuantity = async (
    orderId,
    productName,
    currentQuantity,
    delta,
  ) => {
    const newQuantity = Math.max(1, currentQuantity + delta);

    try {
      setIsLoading(true);

      const response = await fetch(
        "http://localhost:8000/api/cart/update-quantity",
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            order_id: orderId,
            quantity: newQuantity,
          }),
        },
      );

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
                    total_amount: price * newQuantity,
                  };
                }
                return item;
              });

              return {
                ...message,
                cartItems: updatedCartItems,
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

  const handleViewCart = async (silent = false) => {
    if (!silent) {
      const userMessage = {
        type: "user",
        text: "please show my items in the cart",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Add to agent timeline
      setAgentTimeline((prev) => [
        ...prev,
        {
          action: "User Query",
          timestamp: new Date().toLocaleTimeString(),
          status: "completed",
        },
      ]);
    }

    setIsLoading(true);

    try {
      const data = await chatWithAgentViaWebSocket(
        customerId,
        "please show my items in the cart",
      );
      console.log("Cart data:", data);
      // If backend returns cart items, display as product cards
      if (
        data.cart_items &&
        Array.isArray(data.cart_items) &&
        data.cart_items.length > 0
      ) {
        const cartCardsMessage = {
          type: "cartItems",
          cartItems: data.cart_items,
          total_amount: data.total_amount,
          total_items: data.total_items,
          total_savings: data.total_savings,
          timestamp: new Date(),
        };

        // Replace the last cart items message if in silent mode, otherwise append
        if (silent) {
          console.log("silent", cartCardsMessage);
          setMessages((prev) => {
            const lastCartIndex = prev
              .map((m) => m.type)
              .lastIndexOf("cartItems");
            if (lastCartIndex !== -1) {
              const updated = [...prev];
              updated[lastCartIndex] = cartCardsMessage;
              return updated;
            }
            return [...prev, cartCardsMessage];
          });
        } else {
          console.log("not silent", cartCardsMessage);
          setMessages((prev) => [...prev, cartCardsMessage]);

          // Add follow-up message asking about next steps
          setTimeout(() => {
            const followUpMessage = {
              type: "ai",
              text: "Would you like to proceed with the payment or want to add more products? 🛒",
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, followUpMessage]);
          }, 300);
        }
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

  const handleAddToCart = async (product, isBulkAdd = false) => {
    const quantity = productQuantities[product.product_id];

    // Don't add if quantity is 0 or undefined
    if (!quantity || quantity === 0) {
      return;
    }

    // Only show user message if it's not a bulk add
    if (!isBulkAdd) {
      const userMessage = {
        type: "user",
        text: `Add ${quantity} x ${product.product_name} to cart`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setInputValue("");
      setIsLoading(true);
    }

    try {
      const data = await chatWithAgentViaWebSocket(
        customerId,
        `Add ${quantity} units of product ${product.product_id} to cart`,
      );

      // Only show success message if it's not a bulk add
      if (!isBulkAdd) {
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
      }

      // Reset quantity for this product
      setProductQuantities((prev) => {
        const updated = { ...prev };
        delete updated[product.product_id];
        return updated;
      });

      return true; // Success
    } catch (error) {
      console.error("Error adding to cart:", error);

      // Only show error message if it's not a bulk add
      if (!isBulkAdd) {
        const errorMessage = {
          type: "ai",
          text: "Sorry, there was an error adding the item to cart. Please try again.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        setIsLoading(false);
      }

      return false; // Failure
    }

    if (!isBulkAdd) {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    // Clear local state with personalized time-based greeting
    const timeGreeting = getTimeBasedGreeting(customerName);
    const greetingText = `${timeGreeting.greeting}\n\n${timeGreeting.message}\n\n${welcomeMessage}`;

    setMessages([
      {
        type: "ai",
        text: greetingText,
        timestamp: new Date(),
        isWelcomeCard: true,
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
            {/* Hamburger Menu Button */}
            <button
              className={`timeline-hamburger ${isTimelineOpen ? "open" : ""}`}
              onClick={() => setIsTimelineOpen(!isTimelineOpen)}
              title={isTimelineOpen ? "Hide Timeline" : "Show Timeline"}
            >
              <span className="hamburger-line"></span>
              <span className="hamburger-line"></span>
              <span className="hamburger-line"></span>
            </button>

            {/* Left Panel - Agent Timeline */}
            <div
              className={`agent-timeline-panel ${isTimelineOpen ? "" : "collapsed"}`}
            >
              <div className="timeline-header">
                <span className="timeline-icon">⚡</span>
                <div className="timeline-header-actions">
                  <span className="web-badge">Web</span>
                  <span className="status-badge">
                    <span className="status-label">Status: </span>
                    <span className="status-value">
                      {isLoading ? "Processing" : "Active"}
                    </span>
                  </span>
                </div>
                <button
                  className="timeline-close-btn"
                  onClick={() => setIsTimelineOpen(false)}
                >
                  ✕
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
                    <div
                      key={entry.key || index}
                      className={`timeline-entry ${entry.status || ""}`}
                    >
                      <div className="timeline-dot-container">
                        <div className="timeline-dot"></div>
                        {index < agentTimeline.length - 1 && (
                          <div className="timeline-line"></div>
                        )}
                      </div>
                      <div className="timeline-card">
                        <div className="timeline-card-header">
                          <div className="timeline-card-title">
                            <div className="timeline-action">
                              {entry.action}
                            </div>
                            {entry.status && entry.action !== "User Query" && (
                              <span
                                className={`timeline-status-pill ${
                                  entry.status || ""
                                }`}
                              >
                                {entry.status === "completed"
                                  ? "Completed"
                                  : entry.status === "error"
                                    ? "Error"
                                    : "In Progress"}
                              </span>
                            )}
                          </div>
                          <span className="agent-badge">
                            {entry.tool
                              ? entry.tool
                              : entry.action &&
                                  entry.action.toLowerCase().includes("agent")
                                ? `${entry.action
                                    .replace(/\s*agent\s*$/i, "")
                                    .trim()
                                    .toLowerCase()
                                    .replace(/\s+/g, "_")}_agent`
                                : "system"}
                          </span>
                        </div>
                        <div className="timeline-agent-type">
                          Master Orchestrator
                        </div>
                        <div className="timeline-timestamps">
                          {(entry.logs && entry.logs.length > 0
                            ? entry.logs
                            : [
                                {
                                  time: entry.timestamp,
                                  text: `System → ${getAgentShortName(
                                    entry.action,
                                  )}`,
                                  variant: "system",
                                },
                                {
                                  time: entry.timestamp,
                                  text: `${getAgentShortName(
                                    entry.action,
                                  )} → User`,
                                  variant: "system",
                                },
                              ]
                          ).map((log, i) => (
                            <div key={i} className="timeline-time-entry">
                              <span className="timeline-time">{log.time}</span>
                              <span
                                className={`timeline-flow ${
                                  log.variant === "system" ? "system" : ""
                                }`}
                              >
                                {log.text}
                              </span>
                            </div>
                          ))}
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
                    <h3>RetailBuddy</h3>
                    <p>In-store multi-agent automation</p>
                  </div>
                </div>
                <div className="header-actions">
                  <div className="action-tools">
                    <span className="action-tools-label">Action Tools</span>
                    <div className="action-tools-buttons">
                      <button
                        className="action-tool-btn"
                        onClick={() => {
                          setInputValue("proceed");
                          setTimeout(() => sendMessage(), 0);
                        }}
                        disabled={isLoading}
                        title="Go For Payment"
                      >
                        Go For Payment
                      </button>
                      <button
                        className="action-tool-btn"
                        onClick={() => handleViewCart(false)}
                        disabled={isLoading}
                        title="View Cart"
                      >
                        View Cart
                      </button>
                      <button
                        className="action-tool-btn"
                        onClick={() => {
                          setInputValue("post purchase support");
                          setTimeout(() => sendMessage(), 0);
                        }}
                        disabled={isLoading}
                        title="Post Purchase Support"
                      >
                        Post Purchase Support
                      </button>
                    </div>
                  </div>
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

                  // Parse structured response for AI messages
                  const structuredData =
                    message.type === "ai"
                      ? parseStructuredResponse(message.text)
                      : {
                          orderConfirmation: null,
                          loyaltyRewards: null,
                          postPurchaseSupport: null,
                        };

                  // Check if this is a welcome message
                  const isWelcomeMessage = message.isWelcomeCard && index === 0;

                  return (
                    <div
                      key={index}
                      className={`message ${message.type === "user" ? "user-message" : "ai-message"} ${isWelcomeMessage ? "welcome-message-special" : ""}`}
                    >
                      {isWelcomeMessage ? (
                        <div className="welcome-gradient-card">
                          <div className="welcome-card-inner">
                            <div className="welcome-icon-container">
                              <div className="welcome-bot-icon">🤖</div>
                            </div>
                            <div className="welcome-card-content">
                              <div className="message-text">
                                {displayText.split("\n").map((line, i) => (
                                  <div
                                    key={i}
                                    className={i === 0 ? "greeting-line" : ""}
                                  >
                                    {line}
                                    {i < displayText.split("\n").length - 1 && (
                                      <br />
                                    )}
                                  </div>
                                ))}
                              </div>
                              <div className="welcome-suggestions">
                                <p>💡 Browse products</p>
                                <p>💡 Check your cart</p>
                                <p>💡 View special offers</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="message-content">
                          {/* Agent Header */}
                          {message.type === "ai" && message.agent && (
                            <div className="agent-header">
                              <span className="agent-label">
                                {message.agent.charAt(0).toUpperCase() +
                                  message.agent.slice(1).replace("_", " ")}{" "}
                                • {message.agent}
                              </span>
                            </div>
                          )}

                          {/* Render Order Confirmation if parsed */}
                          {structuredData.orderConfirmation && (
                            <div className="fulfillment-agent-section">
                              <div className="agent-section-title">
                                Your delivery has been scheduled!
                              </div>

                              <div className="order-confirmation-container">
                                <div className="payment-success-badge">
                                  <span className="success-icon">✓</span>
                                  <div className="success-text">
                                    <h4>
                                      {
                                        structuredData.orderConfirmation
                                          .payment_status.status
                                      }
                                    </h4>
                                    <p>
                                      {
                                        structuredData.orderConfirmation
                                          .payment_status.description
                                      }
                                    </p>
                                  </div>
                                </div>

                                <div className="order-details-grid">
                                  <div className="order-detail-item">
                                    <span className="detail-label">
                                      Order ID
                                    </span>
                                    <span className="detail-value">
                                      #
                                      {
                                        structuredData.orderConfirmation
                                          .order_details.order_id
                                      }
                                    </span>
                                  </div>
                                  <div className="order-detail-item">
                                    <span className="detail-label">
                                      Amount Paid
                                    </span>
                                    <span className="detail-value amount">
                                      ₹
                                      {structuredData.orderConfirmation.order_details.amount_paid.toLocaleString()}
                                    </span>
                                  </div>
                                  <div className="order-detail-item">
                                    <span className="detail-label">
                                      Payment Method
                                    </span>
                                    <span className="detail-value">
                                      {
                                        structuredData.orderConfirmation
                                          .order_details.payment_method
                                      }
                                    </span>
                                  </div>
                                  <div className="order-detail-item">
                                    <span className="detail-label">
                                      Delivery Time
                                    </span>
                                    <span className="detail-value delivery">
                                      {
                                        structuredData.orderConfirmation
                                          .order_details.delivery_time
                                      }
                                    </span>
                                  </div>
                                </div>

                                <div className="order-confirmation-footer">
                                  ✓{" "}
                                  {
                                    structuredData.orderConfirmation
                                      .confirmation_message
                                  }
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Render Loyalty Rewards if parsed */}
                          {structuredData.loyaltyRewards && (
                            <div className="loyalty-agent-section">
                              <div className="loyalty-rewards-container">
                                <div className="loyalty-header">
                                  <span className="loyalty-icon">🎁</span>
                                  <div className="loyalty-header-text">
                                    <h4>
                                      {structuredData.loyaltyRewards.title}
                                    </h4>
                                    <p>
                                      {
                                        structuredData.loyaltyRewards
                                          .description
                                      }
                                    </p>
                                  </div>
                                </div>

                                <div className="loyalty-benefits-title">
                                  {structuredData.loyaltyRewards.benefits_title}
                                </div>

                                <div className="loyalty-benefits-list">
                                  {structuredData.loyaltyRewards.benefits.map(
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
                            </div>
                          )}

                          {/* Render Post Purchase Support if parsed */}
                          {structuredData.postPurchaseSupport && (
                            <div className="post-purchase-agent-section">
                              <div className="post-purchase-container">
                                <div className="post-purchase-header">
                                  <span className="post-purchase-icon">💬</span>
                                  <div className="post-purchase-header-text">
                                    <h4>
                                      {structuredData.postPurchaseSupport.title}
                                    </h4>
                                    <p>
                                      {
                                        structuredData.postPurchaseSupport
                                          .description
                                      }
                                    </p>
                                  </div>
                                </div>

                                <div className="services-title">
                                  {
                                    structuredData.postPurchaseSupport
                                      .services_title
                                  }
                                </div>

                                <div className="services-list">
                                  {structuredData.postPurchaseSupport.services.map(
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

                                <div className="post-purchase-footer">
                                  <div className="quick-actions-title">
                                    🚀 Quick Actions:
                                  </div>
                                  <div className="quick-actions-grid">
                                    <button className="quick-action-btn track-btn">
                                      <span className="action-icon">📦</span>
                                      <div className="action-text">
                                        <div className="action-title">
                                          Track Order
                                        </div>
                                        <div className="action-subtitle">
                                          Real-time updates
                                        </div>
                                      </div>
                                    </button>
                                    <button className="quick-action-btn support-btn">
                                      <span className="action-icon">💬</span>
                                      <div className="action-text">
                                        <div className="action-title">
                                          Get Support
                                        </div>
                                        <div className="action-subtitle">
                                          Chat with us
                                        </div>
                                      </div>
                                    </button>
                                    <button className="quick-action-btn return-btn">
                                      <span className="action-icon">📦</span>
                                      <div className="action-text">
                                        <div className="action-title">
                                          Return Item
                                        </div>
                                        <div className="action-subtitle">
                                          Easy returns
                                        </div>
                                      </div>
                                    </button>
                                    <button className="quick-action-btn rate-btn">
                                      <span className="action-icon">⭐</span>
                                      <div className="action-text">
                                        <div className="action-title">
                                          Rate Order
                                        </div>
                                        <div className="action-subtitle">
                                          Share feedback
                                        </div>
                                      </div>
                                    </button>
                                  </div>
                                  <div className="help-text">
                                    💡 Need help? We're just one click away!
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Hide plain text for purchaseMethods and paymentMethods and structured messages */}
                          {message.type !== "purchaseMethods" &&
                            message.type !== "paymentMethods" &&
                            !structuredData.orderConfirmation &&
                            !structuredData.loyaltyRewards &&
                            !structuredData.postPurchaseSupport && (
                              <div className="message-text">{displayText}</div>
                            )}

                          {/* Render Purchase Methods */}
                          {message.type === "purchaseMethods" && (
                            <>
                              {/* Instructional message before purchase method selection */}
                              <div className="purchase-instruction-message">
                                <p>
                                  Before payment, select the mode by which you
                                  want to purchase:
                                </p>
                              </div>

                              <div className="purchase-methods-container">
                                <div className="purchase-methods-header">
                                  <span className="purchase-icon">📦</span>
                                  <h4>Choose Purchase Method</h4>
                                </div>
                                <div className="purchase-methods-buttons">
                                  <button
                                    className="purchase-method-btn online-btn"
                                    onClick={() =>
                                      handlePurchaseMethodClick("Buy Online")
                                    }
                                  >
                                    <span className="btn-icon">🏠</span>
                                    <div className="btn-text">
                                      <div className="btn-title">
                                        Buy Online
                                      </div>
                                      <div className="btn-subtitle">
                                        Home Delivery
                                      </div>
                                    </div>
                                  </button>
                                  <button
                                    className="purchase-method-btn offline-btn"
                                    onClick={() =>
                                      handlePurchaseMethodClick("Nearest Store")
                                    }
                                  >
                                    <span className="btn-icon">🏪</span>
                                    <div className="btn-text">
                                      <div className="btn-title">
                                        Nearest Store
                                      </div>
                                      <div className="btn-subtitle">
                                        Store Pickup
                                      </div>
                                    </div>
                                  </button>
                                </div>
                              </div>
                            </>
                          )}

                          {/* Render Payment Methods */}
                          {message.type === "paymentMethods" && (
                            <div className="payment-methods-container">
                              <div className="payment-methods-header">
                                <span className="payment-icon">💳</span>
                                <h4>Choose Payment Method</h4>
                              </div>
                              <div className="payment-methods-grid">
                                <button
                                  className="payment-method-card upi-card"
                                  onClick={() =>
                                    handlePaymentMethodClick("upi")
                                  }
                                >
                                  <div className="payment-icon-wrapper">
                                    <span className="payment-emoji">+</span>
                                  </div>
                                  <div className="payment-method-name">UPI</div>
                                </button>
                                <button
                                  className="payment-method-card credit-card"
                                  onClick={() =>
                                    handlePaymentMethodClick("credit card")
                                  }
                                >
                                  <div className="payment-icon-wrapper">
                                    <span className="payment-emoji">💳</span>
                                  </div>
                                  <div className="payment-method-name">
                                    Credit Card
                                  </div>
                                </button>
                                <button
                                  className="payment-method-card debit-card"
                                  onClick={() =>
                                    handlePaymentMethodClick("debit card")
                                  }
                                >
                                  <div className="payment-icon-wrapper">
                                    <span className="payment-emoji">💳</span>
                                  </div>
                                  <div className="payment-method-name">
                                    Debit Card
                                  </div>
                                </button>
                                <button
                                  className="payment-method-card cod-card"
                                  onClick={() =>
                                    handlePaymentMethodClick("cash on delivery")
                                  }
                                >
                                  <div className="payment-icon-wrapper">
                                    <span className="payment-emoji">💵</span>
                                  </div>
                                  <div className="payment-method-name">
                                    Cash on Delivery
                                  </div>
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Payment Detail Forms */}
                          {message.type === "paymentMethods" &&
                            selectedPaymentMethod === "upi" && (
                              <div className="payment-detail-form">
                                <div
                                  className="payment-back-link"
                                  onClick={handleBackToPaymentMethods}
                                >
                                  ← Back to payment methods
                                </div>
                                <div className="payment-form-content">
                                  <h3>Enter your UPI ID to complete payment</h3>
                                  <div className="payment-security-badge">
                                    <span className="security-icon">🔒</span>
                                    <span className="security-text">
                                      Secured by 256-bit SSL Encryption
                                    </span>
                                  </div>
                                  <div className="payment-form-group">
                                    <label className="payment-form-label">
                                      UPI ID
                                    </label>
                                    <input
                                      type="text"
                                      className="payment-form-input"
                                      placeholder="yourname@upi"
                                      value={paymentDetails.upiId}
                                      onChange={(e) =>
                                        handlePaymentDetailsChange(
                                          "upiId",
                                          e.target.value,
                                        )
                                      }
                                      onKeyPress={(e) => {
                                        if (
                                          e.key === "Enter" &&
                                          paymentDetails.upiId.trim()
                                        ) {
                                          handlePaymentFormSubmit();
                                        }
                                      }}
                                    />
                                    <div className="payment-input-hint">
                                      Enter your UPI ID (e.g., 9876543210@paytm)
                                    </div>
                                  </div>
                                  <button
                                    className="payment-submit-btn"
                                    onClick={handlePaymentFormSubmit}
                                    disabled={!paymentDetails.upiId.trim()}
                                  >
                                    <span className="btn-lock-icon">🔒</span>{" "}
                                    Pay Securely
                                  </button>
                                  <div className="payment-trust-badges">
                                    <span className="trust-badge">
                                      ✓ Safe & Secure
                                    </span>
                                    <span className="trust-badge">
                                      ✓ Instant Payment
                                    </span>
                                  </div>
                                </div>
                              </div>
                            )}

                          {message.type === "paymentMethods" &&
                            (selectedPaymentMethod === "credit card" ||
                              selectedPaymentMethod === "debit card") && (
                              <div className="payment-detail-form">
                                <div
                                  className="payment-back-link"
                                  onClick={handleBackToPaymentMethods}
                                >
                                  ← Back to payment methods
                                </div>
                                <div className="payment-form-content">
                                  <h3>
                                    Enter{" "}
                                    {selectedPaymentMethod === "credit card"
                                      ? "Credit"
                                      : "Debit"}{" "}
                                    Card Details
                                  </h3>
                                  <div className="payment-security-badge">
                                    <span className="security-icon">🔒</span>
                                    <span className="security-text">
                                      Secured by 256-bit SSL Encryption
                                    </span>
                                  </div>
                                  <div className="payment-form-group">
                                    <label className="payment-form-label">
                                      Card Number
                                    </label>
                                    <div className="payment-input-wrapper">
                                      <input
                                        type="text"
                                        className="payment-form-input"
                                        placeholder="1234 5678 9012 3456"
                                        value={paymentDetails.cardNumber}
                                        onChange={(e) => {
                                          const value = e.target.value.replace(
                                            /\s/g,
                                            "",
                                          );
                                          if (
                                            value.length <= 16 &&
                                            /^\d*$/.test(value)
                                          ) {
                                            const formatted =
                                              value
                                                .match(/.{1,4}/g)
                                                ?.join(" ") || value;
                                            handlePaymentDetailsChange(
                                              "cardNumber",
                                              formatted,
                                            );
                                          }
                                        }}
                                      />
                                      <span className="card-type-icon">💳</span>
                                    </div>
                                  </div>
                                  <div className="payment-form-row">
                                    <div className="payment-form-group payment-form-half">
                                      <label className="payment-form-label">
                                        Expiry Date
                                      </label>
                                      <input
                                        type="text"
                                        className="payment-form-input"
                                        placeholder="MM/YY"
                                        value={paymentDetails.expiryDate}
                                        onChange={(e) => {
                                          let value = e.target.value.replace(
                                            /\D/g,
                                            "",
                                          );
                                          if (value.length >= 2) {
                                            value =
                                              value.slice(0, 2) +
                                              "/" +
                                              value.slice(2, 4);
                                          }
                                          if (value.length <= 5) {
                                            handlePaymentDetailsChange(
                                              "expiryDate",
                                              value,
                                            );
                                          }
                                        }}
                                      />
                                    </div>
                                    <div className="payment-form-group payment-form-half">
                                      <label className="payment-form-label">
                                        CVV
                                      </label>
                                      <div className="cvv-input-wrapper">
                                        <input
                                          type="password"
                                          className="payment-form-input"
                                          placeholder="•••"
                                          maxLength="3"
                                          value={paymentDetails.cvv}
                                          onChange={(e) => {
                                            const value =
                                              e.target.value.replace(/\D/g, "");
                                            if (value.length <= 3) {
                                              handlePaymentDetailsChange(
                                                "cvv",
                                                value,
                                              );
                                            }
                                          }}
                                        />
                                        <span
                                          className="cvv-help-icon"
                                          title="3 digits on the back of your card"
                                        >
                                          ❓
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                  <button
                                    className="payment-submit-btn"
                                    onClick={handlePaymentFormSubmit}
                                    disabled={
                                      !paymentDetails.cardNumber.replace(
                                        /\s/g,
                                        "",
                                      ).length ||
                                      !paymentDetails.expiryDate ||
                                      !paymentDetails.cvv
                                    }
                                  >
                                    <span className="btn-lock-icon">🔒</span>{" "}
                                    Pay Securely Now
                                  </button>
                                  <div className="payment-trust-badges">
                                    <span className="trust-badge">
                                      ✓ PCI DSS Compliant
                                    </span>
                                    <span className="trust-badge">
                                      ✓ 100% Secure
                                    </span>
                                  </div>
                                </div>
                              </div>
                            )}

                          {/* Render Post Purchase Support */}
                          {message.postPurchaseSupport && (
                            <div className="post-purchase-container">
                              <div className="post-purchase-header">
                                <span className="post-purchase-icon">💬</span>
                                <div className="post-purchase-header-text">
                                  <h4>{message.postPurchaseSupport.title}</h4>
                                  <p>
                                    {message.postPurchaseSupport.description}
                                  </p>
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
                                ✓{" "}
                                {message.orderConfirmation.confirmation_message}
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
                                        message.storeHandoff
                                          .store_handoff_details.store_name
                                      }
                                    </span>
                                  </div>
                                  <div className="handoff-row">
                                    <span className="handoff-icon">👤</span>
                                    <span className="handoff-text">
                                      {
                                        message.storeHandoff
                                          .store_handoff_details.manager
                                      }
                                    </span>
                                  </div>
                                  <div className="handoff-row">
                                    <span className="availability-badge">
                                      ✅{" "}
                                      {
                                        message.storeHandoff
                                          .store_handoff_details.availability
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
                          {/* Render Store Selection */}
                          {message.type === "storeSelection" && (
                            <div className="store-selection-container">
                              <h4 className="store-selection-title">
                                {message.title || "Select a store"}
                              </h4>

                              {message.stores.map((store, idx) => (
                                <div key={idx} className="store-card">
                                  <div className="store-card-header">
                                    <span className="store-name">
                                      {store.store_name}
                                    </span>
                                    <span className="store-status">
                                      {store.availability}
                                    </span>
                                  </div>

                                  <div className="store-card-actions">
                                    {/* Distance */}
                                    <div className="store-action">
                                      <span className="action-icon">📍</span>
                                      <span>
                                        {store.distance.toFixed(2)} km
                                      </span>
                                    </div>

                                    {/* View on Map */}
                                    <a
                                      href={store.map_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="store-action map-link"
                                    >
                                      <span className="action-icon">🗺️</span>
                                      View on Map
                                    </a>
                                  </div>

                                  <button
                                    className="select-store-btn"
                                    onClick={() =>
                                      handleStoreSelect(store.store_name)
                                    }
                                  >
                                    Select Store
                                  </button>
                                </div>
                              ))}
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
                                  {message.purchaseMethods.map(
                                    (method, idx) => (
                                      <button
                                        key={idx}
                                        className={`purchase-method-btn ${method.method === "Buy Online" ? "online-btn" : "offline-btn"}`}
                                        onClick={() =>
                                          handlePurchaseMethodClick(
                                            method.method,
                                          )
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
                                    ),
                                  )}
                                </div>
                              </div>
                            )}

                          {/* Render product cards if present */}
                          {message.productCards &&
                            message.productCards.length > 0 && (
                              <div className="products-section">
                                <div className="products-header">
                                  <h4 className="products-title">
                                    🛍️ Recommended Products
                                  </h4>
                                  {(() => {
                                    const selectedCount = message.productCards
                                      .slice(0, 3)
                                      .filter(
                                        (p) =>
                                          productQuantities[p.product_id] &&
                                          productQuantities[p.product_id] > 0,
                                      ).length;
                                    const totalQuantity = message.productCards
                                      .slice(0, 3)
                                      .reduce(
                                        (sum, p) =>
                                          sum +
                                          (productQuantities[p.product_id] ||
                                            0),
                                        0,
                                      );
                                    return selectedCount > 0 ? (
                                      <button
                                        className="bulk-add-to-cart-btn"
                                        onClick={async () => {
                                          const productsToAdd =
                                            message.productCards
                                              .slice(0, 3)
                                              .filter(
                                                (p) =>
                                                  productQuantities[
                                                    p.product_id
                                                  ] &&
                                                  productQuantities[
                                                    p.product_id
                                                  ] > 0,
                                              );

                                          if (productsToAdd.length === 0)
                                            return;

                                          setIsLoading(true);

                                          // Show user message for bulk add
                                          const productNames = productsToAdd
                                            .map((p) => {
                                              const qty =
                                                productQuantities[p.product_id];
                                              return `${qty}x ${p.product_name}`;
                                            })
                                            .join(", ");

                                          const userMessage = {
                                            type: "user",
                                            text: `Add ${productNames} to cart`,
                                            timestamp: new Date(),
                                          };
                                          setMessages((prev) => [
                                            ...prev,
                                            userMessage,
                                          ]);

                                          // Add products sequentially to avoid race conditions
                                          let successCount = 0;
                                          for (const product of productsToAdd) {
                                            const success =
                                              await handleAddToCart(
                                                product,
                                                true,
                                              );
                                            if (success) successCount++;
                                            // Small delay between additions
                                            await new Promise((resolve) =>
                                              setTimeout(resolve, 500),
                                            );
                                          }

                                          // Show single summary message
                                          if (successCount > 0) {
                                            const aiMessage = {
                                              type: "ai",
                                              text: `Products have been added to cart successfully. You can now proceed to pay.`,
                                              timestamp: new Date(),
                                            };
                                            setMessages((prev) => [
                                              ...prev,
                                              aiMessage,
                                            ]);

                                            // Add View Cart button
                                            const viewCartMessage = {
                                              type: "viewCartPrompt",
                                              timestamp: new Date(),
                                            };
                                            setMessages((prev) => [
                                              ...prev,
                                              viewCartMessage,
                                            ]);
                                          } else {
                                            const errorMessage = {
                                              type: "ai",
                                              text: "Sorry, there was an error adding items to cart. Please try again.",
                                              timestamp: new Date(),
                                            };
                                            setMessages((prev) => [
                                              ...prev,
                                              errorMessage,
                                            ]);
                                          }

                                          setIsLoading(false);
                                        }}
                                      >
                                        <span className="cart-icon">🛒</span>
                                        <span className="btn-text">
                                          Add to Cart ({totalQuantity} items)
                                        </span>
                                      </button>
                                    ) : null;
                                  })()}
                                </div>
                                <div className="product-cards-container">
                                  {message.productCards
                                    .slice(0, 3)
                                    .map((product) => {
                                      const quantity =
                                        productQuantities[product.product_id] ||
                                        0;
                                      const isSelected = quantity > 0;
                                      return (
                                        <div
                                          key={product.product_id}
                                          className={`product-card ${
                                            isSelected ? "selected" : ""
                                          }`}
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
                                            {isSelected && (
                                              <div className="selected-overlay">
                                                <span className="selected-badge">
                                                  ✓ Selected
                                                </span>
                                              </div>
                                            )}
                                          </div>
                                          <div className="product-info">
                                            <h4 className="product-name">
                                              {product.product_name}
                                            </h4>
                                            <div className="product-pricing">
                                              {product.discount &&
                                              product.discount > 0 ? (
                                                <>
                                                  <span className="original-price">
                                                    ₹
                                                    {product.price.toLocaleString()}
                                                  </span>
                                                  <span className="discount-price">
                                                    ₹
                                                    {product.discount_price.toLocaleString()}
                                                  </span>
                                                  <span className="discount-badge">
                                                    {product.discount}% off
                                                  </span>
                                                </>
                                              ) : (
                                                <p className="product-price">
                                                  ₹
                                                  {product.price.toLocaleString()}
                                                </p>
                                              )}
                                            </div>
                                            <div className="quantity-controls">
                                              <button
                                                className="qty-btn"
                                                onClick={() =>
                                                  handleQuantityChange(
                                                    product.product_id,
                                                    -1,
                                                  )
                                                }
                                                disabled={quantity === 0}
                                              >
                                                −
                                              </button>
                                              <span className="qty-value">
                                                {quantity}
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
                                          </div>
                                        </div>
                                      );
                                    })}
                                </div>
                              </div>
                            )}

                          {/* Render cart items as product cards */}
                          {message.type === "cartItems" &&
                            message.cartItems &&
                            message.cartItems.length > 0 && (
                              <div className="cart-items-container">
                                <div className="cart-header-section">
                                  <span className="cart-icon">🛒</span>
                                  <h4>
                                    Your Cart ({message.cartItems.length} items)
                                  </h4>
                                </div>
                                <div className="product-cards-container">
                                  {message.cartItems.map((item) => {
                                    // Calculate values for display
                                    const originalPrice =
                                      item.original_price || item.price;
                                    const discountPrice = item.price;
                                    const discount = item.discount || 0;
                                    const hasDiscount =
                                      discount > 0 &&
                                      originalPrice !== discountPrice;
                                    const savings = item.savings || 0;
                                    const totalAmount =
                                      discountPrice * item.quantity;

                                    return (
                                      <div
                                        key={item.order_id || item.product_id}
                                        className="product-card cart-item-card"
                                      >
                                        <button
                                          className="cart-item-delete-btn"
                                          onClick={() =>
                                            handleRemoveFromCart(
                                              item.order_id,
                                              item.product_name,
                                            )
                                          }
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
                                          {hasDiscount && (
                                            <span className="product-badge trending">
                                              {discount}% OFF
                                            </span>
                                          )}
                                        </div>
                                        <div className="product-info">
                                          <h4 className="product-name">
                                            {item.product_name}
                                          </h4>
                                          <p className="product-id-text">
                                            ID: {item.product_id}
                                          </p>

                                          {/* Price Display with Discount */}
                                          <div className="product-pricing">
                                            {hasDiscount ? (
                                              <>
                                                <span className="original-price">
                                                  ₹
                                                  {Math.round(
                                                    originalPrice,
                                                  ).toLocaleString()}
                                                </span>
                                                <span className="discount-price">
                                                  ₹
                                                  {Math.round(
                                                    discountPrice,
                                                  ).toLocaleString()}
                                                </span>
                                                <span className="discount-badge">
                                                  ({discount}% off)
                                                </span>
                                              </>
                                            ) : (
                                              <span className="discount-price">
                                                ₹
                                                {Math.round(
                                                  discountPrice,
                                                ).toLocaleString()}
                                              </span>
                                            )}
                                          </div>

                                          {/* Quantity Controls */}
                                          <div className="cart-item-details">
                                            <span className="detail-label">
                                              Quantity:
                                            </span>
                                            <div className="quantity-controls">
                                              <button
                                                className="quantity-btn minus-btn"
                                                onClick={() =>
                                                  handleUpdateCartQuantity(
                                                    item.order_id,
                                                    item.product_name,
                                                    item.quantity,
                                                    -1,
                                                  )
                                                }
                                                disabled={item.quantity <= 1}
                                              >
                                                −
                                              </button>
                                              <span className="quantity-value">
                                                {item.quantity}
                                              </span>
                                              <button
                                                className="quantity-btn plus-btn"
                                                onClick={() =>
                                                  handleUpdateCartQuantity(
                                                    item.order_id,
                                                    item.product_name,
                                                    item.quantity,
                                                    1,
                                                  )
                                                }
                                              >
                                                +
                                              </button>
                                            </div>
                                          </div>

                                          {/* Total and Savings */}
                                          <div className="cart-item-total-section">
                                            {hasDiscount && savings > 0 && (
                                              <div className="cart-savings">
                                                <span className="savings-icon">
                                                  💰
                                                </span>
                                                <span className="savings-text">
                                                  Saved: ₹
                                                  {Math.round(
                                                    savings,
                                                  ).toLocaleString()}
                                                </span>
                                              </div>
                                            )}
                                            <div className="cart-item-total">
                                              <span className="total-label">
                                                Total:
                                              </span>
                                              <span className="total-value">
                                                ₹
                                                {Math.round(
                                                  totalAmount,
                                                ).toLocaleString()}
                                              </span>
                                            </div>
                                          </div>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>

                                {/* Personalized cart intro message */}
                                <div className="cart-intro-message">
                                  <p>
                                    Here is your cart! Total value is{" "}
                                    <strong>
                                      ₹
                                      {Math.round(
                                        message.total_amount || 0,
                                      ).toLocaleString()}
                                    </strong>
                                    .
                                    {message.total_savings > 0 && (
                                      <span className="savings-highlight">
                                        {" "}
                                        You're saving ₹
                                        {Math.round(
                                          message.total_savings,
                                        ).toLocaleString()}
                                        ! 💰
                                      </span>
                                    )}
                                  </p>
                                  <p className="proceed-prompt">
                                    Would you like to proceed to payment? 🛍️
                                  </p>
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
                                onClick={() =>
                                  setInputValue("show me more products")
                                }
                              >
                                Continue Shopping
                              </button>
                            </div>
                          )}

                          {/* Render Add-to-Cart confirmation card */}
                          {message.type === "cartConfirmation" &&
                            message.data && (
                              <div className="cart-confirmation-container">
                                <div className="cart-confirmation-card">
                                  <div className="cart-header">
                                    <span className="cart-icon">🛒</span>
                                    <h4>{message.data.message}</h4>
                                  </div>
                                  <div className="cart-details-grid">
                                    <div className="cart-detail-item">
                                      <span className="detail-label">
                                        Product
                                      </span>
                                      <span className="detail-value">
                                        {message.data.product.product_name} (
                                        {message.data.product.product_id})
                                      </span>
                                    </div>
                                    <div className="cart-detail-item">
                                      <span className="detail-label">
                                        Quantity
                                      </span>
                                      <span className="detail-value">
                                        {message.data.product.quantity}
                                      </span>
                                    </div>
                                    <div className="cart-detail-item">
                                      <span className="detail-label">
                                        Price
                                      </span>
                                      <span className="detail-value amount">
                                        ₹
                                        {Number(
                                          message.data.product.price_per_unit,
                                        ).toLocaleString()}
                                      </span>
                                    </div>
                                    <div className="cart-detail-item">
                                      <span className="detail-label">
                                        Total
                                      </span>
                                      <span className="detail-value amount">
                                        ₹
                                        {Number(
                                          message.data.product.total,
                                        ).toLocaleString()}
                                      </span>
                                    </div>
                                  </div>
                                  <div className="cart-actions">
                                    <button
                                      className="cart-btn primary"
                                      onClick={() => setInputValue("view cart")}
                                    >
                                      View Cart
                                    </button>
                                    <button
                                      className="cart-btn"
                                      onClick={() => setInputValue("add more")}
                                    >
                                      Add More
                                    </button>
                                  </div>
                                  <p className="cart-prompt">
                                    {message.data.prompt}
                                  </p>
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
                      )}
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

                {/* Display Conversation Log Responses */}
                {/* {conversationLog.length > 0 && (
                  <div className="conversation-log-display">
                    <div className="log-display-header">
                      <span className="log-header-icon">📊</span>
                      <h3>Response History</h3>
                      <span className="log-badge">{conversationLog.length}</span>
                    </div>
                    
                    {conversationLog.map((logEntry, logIdx) => {
                      const resp = logEntry.response;
                      
                      return (
                        <div key={logIdx} className="log-response-section">
                          <div className="log-response-header">
                            <div className="log-query-label">
                              <span className="query-icon">❓</span>
                              Query: "{logEntry.payload.message}"
                            </div>
                          </div>

                          {/* Display product cards from recommendation response *\/}
                          {resp.responses?.recommendation && resp.responses.recommendation.length > 0 && (
                            <div className="product-cards-container log-products">
                              {resp.responses.recommendation.slice(0, 3).map((product) => (
                                <div key={product.product_id} className="product-card">
                                  <div className="product-image-wrapper">
                                    <img
                                      src={product.image_reference || "/images/placeholder.png"}
                                      alt={product.product_name}
                                      className="product-image"
                                      onError={(e) => {
                                        e.target.src = "/images/placeholder.png";
                                      }}
                                    />
                                    {product.quantity > 0 && product.quantity < 10 && (
                                      <span className="product-badge trending">Low Stock</span>
                                    )}
                                  </div>
                                  <div className="product-info">
                                    <h4 className="product-name">{product.product_name}</h4>
                                    <div className="product-pricing">
                                      {product.discount && product.discount > 0 ? (
                                        <>
                                          <span className="original-price">
                                            ₹{product.price.toLocaleString()}
                                          </span>
                                          <span className="discount-price">
                                            ₹{product.discount_price.toLocaleString()}
                                          </span>
                                          <span className="discount-badge">
                                            ({product.discount}% off)
                                          </span>
                                        </>
                                      ) : (
                                        <p className="product-price">
                                          ₹{product.price.toLocaleString()}
                                        </p>
                                      )}
                                    </div>
                                    <div className="quantity-controls">
                                      <button
                                        className="qty-btn"
                                        onClick={() => handleQuantityChange(product.product_id, -1)}
                                      >
                                        −
                                      </button>
                                      <span className="qty-value">
                                        {productQuantities[product.product_id] || 1}
                                      </span>
                                      <button
                                        className="qty-btn"
                                        onClick={() => handleQuantityChange(product.product_id, 1)}
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

                          {/* Display cart items *\/}
                          {resp.cart_items && resp.cart_items.length > 0 && (
                            <div className="cart-items-container">
                              <div className="cart-header-section">
                                <span className="cart-icon">🛒</span>
                                <h4>Cart ({resp.cart_items.length} items)</h4>
                              </div>
                              <div className="product-cards-container">
                                {resp.cart_items.map((item) => {
                                  const originalPrice = item.original_price || item.price;
                                  const discountedPrice = item.price_per_unit || item.price;
                                  const hasDiscount = item.discount && item.discount > 0;
                                  const totalAmount = item.total_amount || (discountedPrice * item.quantity);

                                  return (
                                    <div key={item.order_id} className="cart-product-card">
                                      <div className="product-image-wrapper">
                                        <img
                                          src={item.image_reference || "/images/placeholder.png"}
                                          alt={item.product_name}
                                          className="product-image"
                                          onError={(e) => {
                                            e.target.src = "/images/placeholder.png";
                                          }}
                                        />
                                      </div>
                                      <div className="cart-product-info">
                                        <h4 className="product-name">{item.product_name}</h4>
                                        <div className="product-pricing">
                                          {hasDiscount ? (
                                            <>
                                              <span className="original-price">
                                                ₹{originalPrice.toLocaleString()}
                                              </span>
                                              <span className="discount-price">
                                                ₹{discountedPrice.toLocaleString()}
                                              </span>
                                              <span className="discount-badge">
                                                ({item.discount}% off)
                                              </span>
                                            </>
                                          ) : (
                                            <p className="product-price">
                                              ₹{discountedPrice.toLocaleString()}
                                            </p>
                                          )}
                                        </div>
                                        <div className="cart-quantity-section">
                                          <div className="quantity-controls cart-qty">
                                            <button
                                              className="qty-btn"
                                              onClick={() =>
                                                handleUpdateCartQuantity(
                                                  item.order_id,
                                                  item.product_name,
                                                  item.quantity,
                                                  -1
                                                )
                                              }
                                            >
                                              −
                                            </button>
                                            <span className="qty-value">{item.quantity}</span>
                                            <button
                                              className="qty-btn"
                                              onClick={() =>
                                                handleUpdateCartQuantity(
                                                  item.order_id,
                                                  item.product_name,
                                                  item.quantity,
                                                  1
                                                )
                                              }
                                            >
                                              +
                                            </button>
                                          </div>
                                          <div className="item-total">
                                            Total: ₹{totalAmount.toLocaleString()}
                                          </div>
                                        </div>
                                        <button
                                          className="remove-from-cart-btn"
                                          onClick={() =>
                                            handleRemoveFromCart(item.order_id, item.product_name)
                                          }
                                        >
                                          🗑️ Remove
                                        </button>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                              {resp.total_amount && (
                                <div className="cart-summary">
                                  <div className="summary-row total">
                                    <span>Total Amount:</span>
                                    <span className="total-value">
                                      ₹{resp.total_amount.toLocaleString()}
                                    </span>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Display text response if no special content *\/}
                          {resp.response && !resp.responses?.recommendation && !resp.cart_items && (
                            <div className="log-text-response">
                              <div className="response-bubble">
                                {resp.response}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )} */}
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
