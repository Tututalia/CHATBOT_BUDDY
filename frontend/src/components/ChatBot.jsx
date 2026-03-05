import React, { useState, useRef, useEffect, StrictMode } from "react";
import "./ChatBot.css";
import chatbotConfig from "../../data/chatbotAgents.json";
import chatbotSchema from "../../data/chatbot.json";
import VirtualTryOnModal from "./VirtualTryOnModal";

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
  const [customerGender, setCustomerGender] = useState("");
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isQuickActionsOpen, setIsQuickActionsOpen] = useState(false);
  const [agentTimeline, setAgentTimeline] = useState([]);
  const [welcomeMessage, setWelcomeMessage] = useState("");
  const [lastRecommendations, setLastRecommendations] = useState([]);
  const [productReviews, setProductReviews] = useState({});
  const [productQuantities, setProductQuantities] = useState({});
  const [productSizes, setProductSizes] = useState({});
  const [conversationLog, setConversationLog] = useState([]);
  const [isRefundLoading, setIsRefundLoading] = useState(false);
  const [refundModal, setRefundModal] = useState({
    open: false,
    message: "",
  });
  const [isRefundGuidelinesOpen, setIsRefundGuidelinesOpen] = useState(false);
  const [pendingRefundOrder, setPendingRefundOrder] = useState(null); // Tracks order awaiting return reason
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
  const [loyaltyApplied, setLoyaltyApplied] = useState(false);
  const [loyaltyPointsUsed, setLoyaltyPointsUsed] = useState(0);
  const [loyaltyProcessing, setLoyaltyProcessing] = useState(false);
  const [paymentFailModal, setPaymentFailModal] = useState({ open: false });
  const [wishlistedIds, setWishlistedIds] = useState(new Set());
  const [cartCount, setCartCount] = useState(0);
  const [cartBlink, setCartBlink] = useState(false);
  const [zoomedImage, setZoomedImage] = useState(null);
  const [virtualTryOnProduct, setVirtualTryOnProduct] = useState(null);

  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const ttsAudioRef = useRef(null);
  const voiceLanguageRef = useRef("en"); // tracks detected voice language: "en", "hi", "bn"

  // Helper: speak assistant response text via OpenAI TTS
  const speakResponse = async (text) => {
    if (!isVoiceEnabled) return;
    if (!text || !text.trim()) return;
    // Strip markdown/emoji artifacts for cleaner speech
    const cleanText = text
      .replace(/[*_~`#>|\-]{1,3}/g, "")
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(
        /[\u{1F600}-\u{1F9FF}\u{2600}-\u{2B55}\u{1FA00}-\u{1FAFF}\u{200D}\u{FE0F}]/gu,
        "",
      )
      .trim();
    if (!cleanText) return;
    try {
      // Stop any currently playing TTS audio
      if (ttsAudioRef.current) {
        ttsAudioRef.current.pause();
        ttsAudioRef.current = null;
      }
      const res = await fetch("http://localhost:8000/api/text-to-speech", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: cleanText,
          customer_id: customerId,
          language: "en",
        }),
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        ttsAudioRef.current = audio;
        audio.onended = () => {
          URL.revokeObjectURL(url);
          ttsAudioRef.current = null;
        };
        audio.play().catch((e) => console.error("TTS playback error:", e));
      }
    } catch (err) {
      console.error("TTS error:", err);
    }
  };

  // Helper: generate a concise TTS summary from the agent response
  const getTtsSummary = (response) => {
    if (!response) return "";
    const agents = response.agent_calls || [];

    // Store selection — nearest stores shown
    if (response.storeSelection) {
      const count = response.storeSelection.stores?.length || 0;
      return `Here are ${count} store options nearest to your location. Kindly select one.`;
    }

    // Cart items viewed
    if (response.cart_items && Array.isArray(response.cart_items)) {
      const count = response.cart_items.length;
      if (count === 0) return "Your cart is currently empty.";
      const total = response.total_amount
        ? `₹${Math.round(response.total_amount)}`
        : "";
      return `Your cart has ${count} item${count > 1 ? "s" : ""}${total ? " totalling " + total : ""}. You can update quantities or proceed to checkout.`;
    }

    // Purchase channel selection
    if (agents.includes("choose_channel_agent")) {
      return "How would you like to receive your order? You can buy online with home delivery or pick up from the nearest store.";
    }

    // Payment methods
    if (agents.includes("payment_agent")) {
      return "Please select your preferred payment method to complete the order.";
    }

    // Product recommendations
    if (response.responses?.recommendation?.length > 0) {
      const count = response.responses.recommendation.length;
      const defaultMsg = response.responses?.default || "";
      // Use the default message if it's short enough, otherwise summarize
      if (defaultMsg && defaultMsg.length <= 200) return defaultMsg;
      return `I found ${count} product${count > 1 ? "s" : ""} for you. Take a look and let me know if you'd like to add any to your cart.`;
    }

    // Fulfillment agent (order confirmation etc.)
    if (agents.includes("fulfillment_agent")) {
      return "Your order details have been processed. Please check the details on screen.";
    }

    // Loyalty agent
    if (agents.includes("loyalty_agent")) {
      return "Your loyalty points have been updated.";
    }

    // Post-purchase
    if (agents.includes("post_purchase_agent")) {
      return "Thank you for your purchase! Your order summary is on screen.";
    }

    // Add to cart confirmation
    if (agents.includes("add_to_cart_agent")) {
      return "Item has been added to your cart successfully.";
    }

    // Generic fallback — use response text but truncate
    const fallback = response.responses?.default || response.response || "";
    if (!fallback) return "";
    // If text is short and clean, use it
    if (fallback.length <= 200) return fallback;
    // Otherwise extract first sentence
    const firstSentence = fallback.match(/^[^.!?\n]+[.!?]/);
    return firstSentence ? firstSentence[0] : fallback.slice(0, 150) + "...";
  };

  // Fetch cart count from backend
  const fetchCartCount = async () => {
    if (!customerId) return;
    try {
      const res = await fetch(
        `http://localhost:8000/api/cart/pending/${customerId}`,
      );
      const data = await res.json();
      setCartCount(data.total_items || 0);
    } catch (err) {
      console.error("Error fetching cart count:", err);
    }
  };

  // Trigger blink animation whenever cartCount changes
  useEffect(() => {
    if (cartCount > 0) {
      setCartBlink(true);
      const timer = setTimeout(() => setCartBlink(false), 1200);
      return () => clearTimeout(timer);
    }
  }, [cartCount]);

  // Load wishlist on mount / when customerId changes
  useEffect(() => {
    if (!customerId) return;
    fetch(`http://localhost:8000/api/wishlist/${customerId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.product_ids) setWishlistedIds(new Set(data.product_ids));
      })
      .catch(() => {});
  }, [customerId]);

  const handleWishlistToggle = async (productId) => {
    try {
      const res = await fetch("http://localhost:8000/api/wishlist/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          product_id: productId,
        }),
      });
      const data = await res.json();
      setWishlistedIds((prev) => {
        const next = new Set(prev);
        if (data.wishlisted) next.add(productId);
        else next.delete(productId);
        return next;
      });
    } catch (err) {
      console.error("Wishlist toggle failed", err);
    }
  };

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
        setLoyaltyApplied(false);
        setLoyaltyPointsUsed(0);
        const cartCardsMessage = {
          type: "cartItems",
          cartItems: response.cart_items,
          total_amount: response.total_amount,
          total_savings: response.total_savings,
          available_loyalty_points: response.available_loyalty_points || 0,
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

    // Handle store selection tiles from fulfillment_agent
    if (!contentHandled && response.storeSelection) {
      const storeMessage = {
        type: "storeSelection",
        title: response.storeSelection.title,
        stores: response.storeSelection.stores,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, storeMessage]);
      contentHandled = true;
    }

    // Handle product cards from recommendation agent
    if (
      !contentHandled &&
      response.responses &&
      response.responses.recommendation &&
      Array.isArray(response.responses.recommendation) &&
      response.responses.recommendation.length > 0
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

    // Handle empty recommendations (no products found) — show the default text message
    if (
      !contentHandled &&
      response.responses &&
      response.responses.default &&
      (!response.responses.recommendation ||
        response.responses.recommendation.length === 0)
    ) {
      const aiMessage = {
        type: "ai",
        text: response.responses.default,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
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

  const fetchReviewsByProductIds = async (productIds) => {
    try {
      const ids = Array.from(
        new Set(
          (productIds || [])
            .filter((id) => typeof id === "string" && id.trim().length > 0)
            .map((id) => id.trim()),
        ),
      );
      if (ids.length === 0) return;

      // Only request the IDs we don't already have.
      const missing = ids.filter(
        (id) => typeof productReviews?.[id] !== "number",
      );
      if (missing.length === 0) return;

      const idsParam = encodeURIComponent(missing.join("|"));
      const res = await fetch(
        `http://localhost:8000/api/feedback/multiple/${idsParam}`,
      );
      if (!res.ok) return;
      const data = await res.json();
      if (!data || typeof data !== "object" || !data.reviews) return;

      setProductReviews((prev) => ({
        ...prev,
        ...data.reviews,
      }));
    } catch (e) {
      // Silent fail: reviews are optional UI enhancement
    }
  };

  useEffect(() => {
    if (!lastRecommendations || lastRecommendations.length === 0) return;
    fetchReviewsByProductIds(lastRecommendations.map((p) => p?.product_id));
  }, [lastRecommendations]);

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

  useEffect(() => {
    if (!isOpen) setIsQuickActionsOpen(false);
  }, [isOpen]);

  // Fetch cart count when chatbot opens or customerId changes
  useEffect(() => {
    if (isOpen && customerId) {
      fetchCartCount();
    }
  }, [isOpen, customerId]);

  // Silent return-monitoring agent: runs when chatbot opens (batch for all customers)
  useEffect(() => {
    if (isOpen) {
      fetch("http://localhost:8000/api/orders/return-monitoring", {
        method: "POST",
      }).catch(() => {});
    }
  }, [isOpen]);

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
        let fetchedGender = "";
        try {
          const profileData = await getCustomerProfile(customerId);
          fetchedName = profileData?.customer_name || "Guest";
          fetchedGender = profileData?.gender || "";
        } catch (error) {
          console.error("Error fetching customer name:", error);
        }
        setCustomerName(fetchedName);
        setCustomerGender(fetchedGender);

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
                  available_loyalty_points:
                    response.available_loyalty_points || 0,
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

        // Check for pending cart items and show reminder
        try {
          const cartRes = await fetch(
            `http://localhost:8000/api/cart/pending/${customerId}`,
          );
          const cartData = await cartRes.json();
          if (cartData.cart_items && cartData.cart_items.length > 0) {
            setTimeout(() => {
              setMessages((prev) => [
                ...prev,
                {
                  type: "pendingCartReminder",
                  cartItems: cartData.cart_items,
                  total_items: cartData.total_items,
                  total_amount: cartData.total_amount,
                  timestamp: new Date(),
                },
              ]);
            }, 600);
          }
        } catch (cartErr) {
          console.error("Error checking pending cart:", cartErr);
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

  const chatWithAgentViaWebSocket = (customerId, messageText, extraPayload) => {
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
            ...(extraPayload && typeof extraPayload === "object"
              ? extraPayload
              : {}),
          }),
        );
      };

      ws.onerror = () => {
        reject(new Error("WebSocket connection error"));
      };

      ws.onclose = (event) => {
        // If the socket closed before we got a run_end or error, reject the promise
        if (!finalResponse) {
          reject(new Error("WebSocket closed unexpectedly"));
        }
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

    // --- Handle pending refund: user is providing return reason ---
    if (pendingRefundOrder) {
      const returnReason = inputValue.trim();
      const order = pendingRefundOrder;
      const transactionId = order?.transaction_id;
      const productName = order?.product_name || "Product";

      // Show user message
      setMessages((prev) => [
        ...prev,
        { type: "user", text: returnReason, timestamp: new Date() },
      ]);
      setInputValue("");
      setIsLoading(true);

      try {
        const res = await fetch(
          "http://localhost:8000/api/orders/initiate-return",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              transaction_id: transactionId,
              return_reason: returnReason,
            }),
          },
        );
        const data = await res.json();

        if (data.success) {
          // Reason accepted — clear pending order and show confirmation
          setPendingRefundOrder(null);

          // Pause for a couple of seconds before showing confirmation in chat
          await new Promise((resolve) => setTimeout(resolve, 2500));

          setMessages((prev) => [
            ...prev,
            {
              type: "ai",
              text: [
                `✅ **Your refund request has been initiated successfully.**`,
                ``,
                `**Product:** ${productName}  •  **Order ID:** ${transactionId}`,
                `**Reason:** ${returnReason}`,
                ``,
                `**What happens next:**`,
                `• Our pickup partner will collect the item within 2–3 business days.`,
                `• After pickup and verification, the refund will be processed to your original payment method.`,
                ``,
                `Please keep the product packed and ready (tags/invoice if available).`,
              ].join("\n"),
              timestamp: new Date(),
            },
          ]);
        } else if (data.invalid_reason) {
          // Reason rejected — keep pendingRefundOrder so user can retry
          setMessages((prev) => [
            ...prev,
            {
              type: "ai",
              text: [
                `⚠️ **Your return reason was not specific enough.**`,
                ``,
                `Please provide a **valid product-related reason** such as:`,
                `• 📏 **Size/Fit issue** — too small, too big, doesn't fit`,
                `• 🔧 **Defective/Damaged** — broken, torn, scratched`,
                `• 🎨 **Wrong item/color** — received incorrect product`,
                `• 🧵 **Quality issue** — poor fabric, bad stitching`,
                `• 🤦 **Ordered by mistake** — accidental purchase`,
                `• 📦 **Packaging damaged** — box damaged, seal broken`,
                ``,
                `Please type your reason below:`,
              ].join("\n"),
              timestamp: new Date(),
            },
          ]);
        } else {
          // Other errors — clear pending order
          setPendingRefundOrder(null);
          setMessages((prev) => [
            ...prev,
            {
              type: "ai",
              text: `⚠️ ${data.error || "Failed to initiate return. Please try again."}`,
              timestamp: new Date(),
            },
          ]);
        }
      } catch (e) {
        setPendingRefundOrder(null);
        setMessages((prev) => [
          ...prev,
          {
            type: "ai",
            text: "❌ Something went wrong while processing your return. Please try again.",
            timestamp: new Date(),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
      return;
    }
    // --- End pending refund handling ---

    // --- Fast path: "show my cart items" triggers instant cart load ---
    const _cartFastInput = inputValue.trim().toLowerCase();
    if (
      _cartFastInput === "show my cart items" ||
      _cartFastInput === "please show my cart items" ||
      _cartFastInput === "show my cart" ||
      _cartFastInput === "show cart items" ||
      _cartFastInput === "view my cart" ||
      _cartFastInput === "show my card items" ||
      _cartFastInput === "show my card item" ||
      _cartFastInput === "view cart"
    ) {
      setInputValue("");
      await handleViewCart();
      return;
    }
    // --- End fast path ---

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
          setLoyaltyApplied(false);
          setLoyaltyPointsUsed(0);
          const cartCardsMessage = {
            type: "cartItems",
            cartItems: response.cart_items,
            total_amount: response.total_amount,
            total_savings: response.total_savings,
            available_loyalty_points: response.available_loyalty_points || 0,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, cartCardsMessage]);

          // Render autonomous upsell recommendations if present
          if (
            response.upsell &&
            response.upsell.responses &&
            response.upsell.responses.recommendation &&
            response.upsell.responses.recommendation.length > 0
          ) {
            const upsellCategory =
              response.upsell.upsell_category || "accessories";
            setLastRecommendations(response.upsell.responses.recommendation);
            fetchReviewsByProductIds(
              response.upsell.responses.recommendation.map(
                (p) => p?.product_id,
              ),
            );
            setTimeout(() => {
              const upsellHeaderMessage = {
                type: "ai",
                isUpsellHeader: true,
                text: `🔥🎯 **Great choice!** We handpicked these **${upsellCategory}** just for you — they'd go perfectly with your picks! 👇✨`,
                timestamp: new Date(),
              };
              setMessages((prev) => [...prev, upsellHeaderMessage]);

              const upsellCardsMessage = {
                type: "productCards",
                productCards: response.upsell.responses.recommendation,
                timestamp: new Date(),
              };
              setMessages((prev) => [...prev, upsellCardsMessage]);
            }, 400);
          }
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
      // Handle store selection tiles from fulfillment_agent
      else if (response.storeSelection) {
        const storeMessage = {
          type: "storeSelection",
          title: response.storeSelection.title,
          stores: response.storeSelection.stores,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, storeMessage]);
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

      // Speak a concise TTS summary of the assistant response
      const ttsText = getTtsSummary(response);
      if (ttsText) {
        speakResponse(ttsText);
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
    fetchCartCount();
  };

  const formatOrderDate = (rawDate) => {
    if (!rawDate) return "";
    try {
      const parsed = new Date(rawDate);
      if (Number.isNaN(parsed.getTime())) return String(rawDate);
      return parsed.toLocaleString();
    } catch {
      return String(rawDate);
    }
  };

  const handleRefundQuickAction = async () => {
    if (isLoading || isRefundLoading) return;
    setIsRefundLoading(true);

    // Emit live timeline entries for Return Agent flow
    const returnKey = `${Date.now()}:return_agent`;
    ensureTimelineEntry({
      key: returnKey,
      tool: "return_agent",
      agentLabel: "Return Agent",
      status: "in_progress",
    });
    setTimeout(() => {
      appendTimelineLog({
        key: returnKey,
        tool: "return_agent",
        agentLabel: "Return Agent",
        line: `[${formatLocalTime()}] Master Orchestrator → Return Agent`,
      });
    }, 200);
    setTimeout(() => {
      appendTimelineLog({
        key: returnKey,
        tool: "return_agent",
        agentLabel: "Return Agent",
        line: `[${formatLocalTime()}] Fetching recent orders (last 7 days)`,
      });
    }, 500);

    try {
      const res = await fetch(
        `http://localhost:8000/api/customer/${customerId}/orders/recent?days=7`,
      );
      const data = await res.json();
      const orders = Array.isArray(data?.order_history)
        ? data.order_history
        : [];

      appendTimelineLog({
        key: returnKey,
        tool: "return_agent",
        agentLabel: "Return Agent",
        line: `[${formatLocalTime()}] Found ${orders.length} eligible order(s)`,
      });
      setTimeout(() => {
        appendTimelineLog({
          key: returnKey,
          tool: "return_agent",
          agentLabel: "Return Agent",
          line: `[${formatLocalTime()}] Return Agent → Master Orchestrator`,
        });
        endTimelineEntry({ key: returnKey, status: "completed" });
      }, 400);

      setMessages((prev) => [
        ...prev,
        {
          type: "refundOrders",
          orders,
          timestamp: new Date(),
        },
      ]);
    } catch (e) {
      appendTimelineLog({
        key: returnKey,
        tool: "return_agent",
        agentLabel: "Return Agent",
        line: `[${formatLocalTime()}] Failed to fetch recent orders`,
      });
      endTimelineEntry({ key: returnKey, status: "error" });

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text: "Sorry, I couldn't fetch your last 7 days orders right now.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsRefundLoading(false);
    }
  };

  const handleLocateUs = async () => {
    if (isLoading || isRefundLoading) return;
    setIsRefundLoading(true);

    // Emit live timeline entries for Locate Us Agent flow
    const locateKey = `${Date.now()}:locate_us_agent`;
    ensureTimelineEntry({
      key: locateKey,
      tool: "locate_us_agent",
      agentLabel: "Locate Us Agent",
      status: "in_progress",
    });
    setTimeout(() => {
      appendTimelineLog({
        key: locateKey,
        tool: "locate_us_agent",
        agentLabel: "Locate Us Agent",
        line: `[${formatLocalTime()}] Master Orchestrator → Locate Us Agent`,
      });
    }, 200);
    setTimeout(() => {
      appendTimelineLog({
        key: locateKey,
        tool: "locate_us_agent",
        agentLabel: "Locate Us Agent",
        line: `[${formatLocalTime()}] Fetching store distances & map data`,
      });
    }, 500);

    try {
      const res = await fetch(
        `http://localhost:8000/api/stores/locate/${customerId}`,
      );
      const data = await res.json();
      const stores = Array.isArray(data?.stores) ? data.stores : [];

      appendTimelineLog({
        key: locateKey,
        tool: "locate_us_agent",
        agentLabel: "Locate Us Agent",
        line: `[${formatLocalTime()}] Found ${stores.length} store location(s)`,
      });
      setTimeout(() => {
        appendTimelineLog({
          key: locateKey,
          tool: "locate_us_agent",
          agentLabel: "Locate Us Agent",
          line: `[${formatLocalTime()}] Locate Us Agent → Master Orchestrator`,
        });
        endTimelineEntry({ key: locateKey, status: "completed" });
      }, 400);

      setMessages((prev) => [
        ...prev,
        {
          type: "storeLocator",
          stores,
          timestamp: new Date(),
        },
      ]);
    } catch (e) {
      appendTimelineLog({
        key: locateKey,
        tool: "locate_us_agent",
        agentLabel: "Locate Us Agent",
        line: `[${formatLocalTime()}] Failed to fetch store locations`,
      });
      endTimelineEntry({ key: locateKey, status: "error" });

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text: "Sorry, I couldn't fetch store locations right now. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsRefundLoading(false);
    }
  };

  const handleCustomerSupport = () => {
    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      { type: "user", text: "Customer Support", timestamp: new Date() },
    ]);

    // Add timeline entry
    const csKey = `${Date.now()}:customer_support`;
    ensureTimelineEntry({
      key: csKey,
      tool: "post_purchase_agent",
      agentLabel: "Post-Purchase Agent",
      status: "in_progress",
    });
    setTimeout(() => {
      appendTimelineLog({
        key: csKey,
        tool: "post_purchase_agent",
        agentLabel: "Post-Purchase Agent",
        line: `[${formatLocalTime()}] Showing customer support contact info`,
      });
      endTimelineEntry({ key: csKey, status: "completed" });
    }, 300);

    // Add contact support card
    setMessages((prev) => [
      ...prev,
      { type: "contactSupport", timestamp: new Date() },
    ]);
  };

  const openRefundModal = (order) => {
    const productName = order?.product_name
      ? String(order.product_name)
      : "this product";
    const transactionId = order?.transaction_id
      ? String(order.transaction_id)
      : null;

    // Store the order awaiting a return reason
    setPendingRefundOrder(order);

    // Ask user for return reason via chatbot message with valid reason guidance
    setMessages((prev) => [
      ...prev,
      {
        type: "ai",
        text: [
          `🔄 You have selected **${productName}**${transactionId ? ` (Order ID: ${transactionId})` : ""} for return/refund.`,
          ``,
          `Please provide a **specific product-related reason** for your return. Accepted reasons include:`,
          `• 📏 Size/Fit issue`,
          `• 🔧 Defective or damaged product`,
          `• 🎨 Wrong item or color received`,
          `• 🧵 Quality issue (fabric, stitching, etc.)`,
          `• 🤦 Ordered by mistake`,
          `• 📦 Packaging damaged`,
          ``,
          `⚠️ _Generic reasons like "I want my money back" will not be accepted._`,
        ].join("\n"),
        timestamp: new Date(),
      },
    ]);
  };

  const closeRefundModal = () => {
    setRefundModal((prev) => ({ ...prev, open: false }));
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
      storePickupConfirmation: null,
      loyaltyRewards: null,
      postPurchaseSupport: null,
    };

    const cleanedText = (text || "")
      .replace(/\[SYSTEM:[^\]]*\]/gi, "")
      .replace(/\r\n/g, "\n")
      .trim();

    // Parse Order Confirmation section
    const orderMatch = text.match(
      /📦\s*\*\*Order Confirmed!\*\*([\s\S]*?)(?=🎉|\*\*Available Services|\*\*Coupon Codes|$)/i,
    );
    if (orderMatch) {
      const orderText = orderMatch[1];
      // Flexible regex patterns to handle both **bold:** and plain formats
      const orderIdMatch = orderText.match(
        /(?:\*\*)?Order\s*ID:?(?:\*\*)?\s*(\w+)/i,
      );
      const totalItemsMatch = orderText.match(
        /(?:\*\*)?Total\s*Items:?(?:\*\*)?\s*(\d+)/i,
      );
      const totalAmountMatch = orderText.match(
        /(?:\*\*)?(?:Total\s*)?Amount:?(?:\*\*)?\s*₹([\d,]+)/i,
      );
      const deliveryTypeMatch = orderText.match(
        /(?:\*\*)?Delivery\s*Type:?(?:\*\*)?\s*([^\n]+)/i,
      );
      const deliveryTimeMatch = orderText.match(
        /(?:\*\*)?Expected\s*Delivery:?(?:\*\*)?\s*([^\n]+)/i,
      );

      // Parse items
      const itemsMatch = orderText.match(
        /(?:\*\*)?Your\s*Items:?(?:\*\*)?([\s\S]*?)(?=\n\n|$)/i,
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

    // Parse In-Store Pickup Confirmation section (fulfillment agent - offline flow)
    // Expected (example): "🏬 **In-Store Pickup Confirmed!**\n\nOrder ID: ..."
    const hasPickupConfirmation = /in-store\s+pickup\s+confirmed/i.test(
      cleanedText,
    );
    if (hasPickupConfirmation) {
      const pickupOrderIdMatch = cleanedText.match(
        /Order\s*ID\s*:\s*([A-Za-z0-9_-]+)/i,
      );
      const pickupStoreIdMatch = cleanedText.match(
        /Store\s*ID\s*:\s*([A-Za-z0-9_-]+)/i,
      );
      const pickupTotalItemsMatch = cleanedText.match(
        /Total\s*Items\s*:\s*(\d+)/i,
      );
      const pickupTotalAmountMatch = cleanedText.match(
        /Total\s*Amount\s*:\s*₹?\s*([\d,]+)/i,
      );
      const pickupStoreMatch = cleanedText.match(
        /Pickup\s*Store\s*:\s*([^\n]+)/i,
      );
      const pickupAddressMatch = cleanedText.match(
        /Store\s*Address\s*:\s*([^\n]+)/i,
      );
      const pickupStatusMatch = cleanedText.match(/Status\s*:\s*([^\n]+)/i);

      const itemsSectionMatch = cleanedText.match(
        /\*\*?Your\s*Items\*\*?:?\s*([\s\S]*?)(?=\n\s*\n|Please\s+visit|Thank\s+you|$)/i,
      );

      const items = (itemsSectionMatch ? itemsSectionMatch[1] : "")
        .split("\n")
        .map((l) => l.trim())
        .filter((l) => l.startsWith("-"))
        .map((l) => l.replace(/^[-\s]+/, "").trim())
        .filter(Boolean);

      sections.storePickupConfirmation = {
        title: "In-Store Pickup Confirmed!",
        order_id: pickupOrderIdMatch ? pickupOrderIdMatch[1] : "N/A",
        store_id: pickupStoreIdMatch ? pickupStoreIdMatch[1] : "N/A",
        total_items: pickupTotalItemsMatch
          ? parseInt(pickupTotalItemsMatch[1], 10)
          : null,
        total_amount: pickupTotalAmountMatch
          ? parseInt(pickupTotalAmountMatch[1].replace(/,/g, ""), 10)
          : null,
        pickup_store: pickupStoreMatch ? pickupStoreMatch[1].trim() : "",
        store_address: pickupAddressMatch ? pickupAddressMatch[1].trim() : "",
        status: pickupStatusMatch ? pickupStatusMatch[1].trim() : "",
        items,
      };
    }

    // Parse Loyalty Rewards section
    const loyaltyMatch = text.match(
      /🎉\s*(?:\*\*)?Loyalty Rewards Unlocked!?(?:\*\*)?([\s\S]*?)(?=(?:\*\*)?Coupon Codes|(?:\*\*)?Available Services|$)/i,
    );
    if (loyaltyMatch) {
      const loyaltyText = loyaltyMatch[1];
      // Flexible regex to handle both **Points Earned:** and Points Earned: formats
      const pointsMatch = loyaltyText.match(
        /(?:\*\*)?Points\s*Earned:?(?:\*\*)?\s*(\d+)\s*points/i,
      );

      // Parse coupon codes
      const couponsMatch = text.match(
        /(?:\*\*)?Coupon Codes for Next Purchase:?(?:\*\*)?([\s\S]*?)(?=(?:\*\*)?Available Services|Thank you|$)/i,
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
      /(?:\*\*)?Available Services:?(?:\*\*)?([\s\S]*?)(?=Thank you|$)/i,
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
  const handlePurchaseMethodClick = async (method) => {
    if (method === "Buy Online") {
      const onlineText = "I want to buy online";
      const userMsg = {
        type: "user",
        text: onlineText,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInputValue("");
      setIsLoading(true);
      try {
        const data = await chatWithAgentViaWebSocket(customerId, onlineText);
        if (
          data.agent_calls &&
          data.agent_calls.includes("payment_agent") &&
          data.agent_calls.length === 1
        ) {
          setMessages((prev) => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage?.type === "paymentMethods") return prev;
            return [
              ...prev,
              {
                type: "paymentMethods",
                text: data.response,
                timestamp: new Date(),
              },
            ];
          });
        } else if (data.response) {
          setMessages((prev) => [
            ...prev,
            { type: "ai", text: data.response, timestamp: new Date() },
          ]);
        }
      } catch (err) {
        console.error("Error in Buy Online:", err);
        setMessages((prev) => [
          ...prev,
          {
            type: "ai",
            text: "Sorry, I encountered an error. Please try again.",
            timestamp: new Date(),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
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
        loyaltyApplied && loyaltyPointsUsed > 0
          ? { loyalty_points_used: loyaltyPointsUsed }
          : undefined,
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

    // Capture payment method before resetting
    const currentPaymentMethod = selectedPaymentMethod;

    // Reset form
    setSelectedPaymentMethod(null);
    setPaymentDetails({
      upiId: "",
      cardNumber: "",
      expiryDate: "",
      cvv: "",
    });

    setIsLoading(true);

    // Hardcoded credit card payment failure
    if (currentPaymentMethod === "credit card") {
      setTimeout(() => {
        setPaymentFailModal({ open: true });
        setIsLoading(false);
      }, 2000);
      return;
    }

    try {
      const response = await chatWithAgentViaWebSocket(
        customerId,
        paymentMessage,
        loyaltyApplied && loyaltyPointsUsed > 0
          ? { loyalty_points_used: loyaltyPointsUsed }
          : undefined,
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

  const isAccessories = (product) => {
    const category =
      (product && (product.category || product.product_category)) || "";
    const c = String(category).trim().toLowerCase();

    return (
      c.includes("accessories") ||
      c.includes("accessory") ||
      c.includes("belt") ||
      c.includes("perfume") ||
      c.includes("wallet") ||
      c.includes("costume jewellery") ||
      c.includes("Handbags & Bags") ||
      c.includes("bags") ||
      c.includes("costume jewelry")
    );
  };

  const isFootwear = (product) => {
    const category = (product && product.category) || "";
    const c = String(category).toLowerCase();
    return (
      c.includes("footwear") ||
      c.includes("shoes") ||
      c.includes("shoe") ||
      c.includes("Sneakers") ||
      c.includes("sandals") ||
      c.includes("Boots") ||
      c.includes("boots") ||
      c.includes("Heels") ||
      c.includes("Formal Shoes") ||
      c.includes("Casual Shoes") ||
      c.includes("Sports Shoes") ||
      c.includes("heels")
    );
  };

  const getDefaultSize = (product) => {
    if (!product || isAccessories(product)) return "";
    return isFootwear(product) ? "8" : "M";
  };

  const getSizeOptions = (product) => {
    if (!product || isAccessories(product)) return [];
    if (isFootwear(product)) {
      return Array.from({ length: 9 }, (_, i) => String(i + 4)); // 4..12
    }
    return ["S", "M", "L", "XL", "XXL"];
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
      fetchCartCount();
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
        // If loyalty was applied, unapply since totals changed
        if (loyaltyApplied && loyaltyPointsUsed > 0) {
          try {
            await fetch("http://localhost:8000/api/cart/unapply-loyalty", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                customer_id: customerId,
                apply: false,
                cart_total: loyaltyPointsUsed,
              }),
            });
          } catch (e) {
            /* best-effort */
          }
          setLoyaltyApplied(false);
          setLoyaltyPointsUsed(0);
        }
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

              const newTotalAmount = updatedCartItems.reduce(
                (sum, i) =>
                  sum + (i.price || i.price_per_unit || 0) * i.quantity,
                0,
              );

              return {
                ...message,
                cartItems: updatedCartItems,
                total_amount: newTotalAmount,
                loyalty_applied: false,
                loyalty_points_used: 0,
                payable_amount: newTotalAmount,
              };
            }
            return message;
          });
        });
        fetchCartCount();
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

  const handleShowWishlist = async () => {
    setIsLoading(true);

    // Show user message
    const userMessage = {
      type: "user",
      text: "Show my wishlist",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Emit timeline entries
    const wlKey = `${Date.now()}:wishlist_agent`;
    ensureTimelineEntry({
      key: wlKey,
      tool: "wishlist_agent",
      agentLabel: "Wishlist Agent",
      status: "in_progress",
    });
    setTimeout(() => {
      appendTimelineLog({
        key: wlKey,
        tool: "wishlist_agent",
        agentLabel: "Wishlist Agent",
        line: `[${formatLocalTime()}] Master Orchestrator → Wishlist Agent`,
      });
    }, 300);
    setTimeout(() => {
      appendTimelineLog({
        key: wlKey,
        tool: "wishlist_agent",
        agentLabel: "Wishlist Agent",
        line: `[${formatLocalTime()}] Fetching wishlist products & checking availability`,
      });
    }, 600);

    try {
      const res = await fetch(
        `http://localhost:8000/api/wishlist/${customerId}/products`,
      );
      const data = await res.json();

      setTimeout(() => {
        appendTimelineLog({
          key: wlKey,
          tool: "wishlist_agent",
          agentLabel: "Wishlist Agent",
          line: `[${formatLocalTime()}] Wishlist Agent → Master Orchestrator`,
        });
      }, 900);
      setTimeout(() => {
        endTimelineEntry({ key: wlKey, status: "completed" });
      }, 1200);

      if (data.products && data.products.length > 0) {
        // Fetch reviews for wishlist products
        fetchReviewsByProductIds(data.products.map((p) => p.product_id));

        const headerMessage = {
          type: "ai",
          text: `❤️ **Your Wishlist** — ${data.products.length} product${data.products.length > 1 ? "s" : ""} saved. Select quantity and add to cart!`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, headerMessage]);

        const wishlistCardsMessage = {
          type: "productCards",
          productCards: data.products,
          isWishlist: true,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, wishlistCardsMessage]);

        // TTS voice prompt for wishlist
        speakResponse(
          `Your wishlist has ${data.products.length} product${data.products.length > 1 ? "s" : ""}. Select quantity and add to cart!`,
        );
      } else {
        const emptyMessage = {
          type: "ai",
          text: "Your wishlist is empty. Browse products and tap 🤍 to add items to your wishlist!",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, emptyMessage]);
        speakResponse(
          "Your wishlist is empty. Browse products and tap the heart icon to add items.",
        );
      }
    } catch (error) {
      console.error("Error fetching wishlist products:", error);
      setTimeout(() => {
        endTimelineEntry({ key: wlKey, status: "error" });
      }, 900);
      const errorMessage = {
        type: "ai",
        text: "Sorry, I couldn't fetch your wishlist right now. Please try again.",
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

    // Emit timeline entry for View Cart Agent
    const cartKey = `${Date.now()}:view_cart_agent`;
    if (!silent) {
      ensureTimelineEntry({
        key: cartKey,
        tool: "view_cart_agent",
        agentLabel: "View Cart Agent",
        status: "in_progress",
      });
      appendTimelineLog({
        key: cartKey,
        tool: "view_cart_agent",
        agentLabel: "View Cart Agent",
        line: `${formatLocalTime()} Master Orchestrator → View Cart Agent`,
      });
      appendTimelineLog({
        key: cartKey,
        tool: "view_cart_agent",
        agentLabel: "View Cart Agent",
        line: `${formatLocalTime()} Fetching pending cart items`,
      });
    }

    try {
      // Direct REST call for fast cart loading (bypasses LLM pipeline)
      const response = await fetch(
        `http://localhost:8000/api/cart/pending/${customerId}`,
      );
      const data = await response.json();
      console.log("Cart data:", data);
      setCartCount(data.total_items || 0);

      if (!silent) {
        appendTimelineLog({
          key: cartKey,
          tool: "view_cart_agent",
          agentLabel: "View Cart Agent",
          line: `${formatLocalTime()} ✅ Found ${data.total_items || 0} item(s) in cart`,
        });
        appendTimelineLog({
          key: cartKey,
          tool: "view_cart_agent",
          agentLabel: "View Cart Agent",
          line: `${formatLocalTime()} View Cart Agent → Master Orchestrator`,
        });
        endTimelineEntry({ key: cartKey, status: "completed" });
      }
      // If backend returns cart items, display as product cards
      if (
        data.cart_items &&
        Array.isArray(data.cart_items) &&
        data.cart_items.length > 0
      ) {
        fetchReviewsByProductIds(data.cart_items.map((i) => i?.product_id));
        setLoyaltyApplied(false);
        setLoyaltyPointsUsed(0);
        const cartCardsMessage = {
          type: "cartItems",
          cartItems: data.cart_items,
          total_amount: data.total_amount,
          total_items: data.total_items,
          total_savings: data.total_savings,
          available_loyalty_points: data.available_loyalty_points || 0,
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

          // TTS voice prompt for cart view
          const itemCount = data.cart_items.length;
          const totalAmt = data.total_amount
            ? `₹${Math.round(data.total_amount)}`
            : "";
          speakResponse(
            `Your cart has ${itemCount} item${itemCount > 1 ? "s" : ""}${totalAmt ? " totalling " + totalAmt : ""}. You can update quantities or proceed to checkout.`,
          );

          // Trigger autonomous upsell chain via REST (non-blocking)
          (async () => {
            try {
              // Timeline: Upsell Agent
              const upsellKey = `${Date.now()}:upsell_agent`;
              ensureTimelineEntry({
                key: upsellKey,
                tool: "upsell_agent",
                agentLabel: "Upsell Agent",
                status: "in_progress",
              });
              appendTimelineLog({
                key: upsellKey,
                tool: "upsell_agent",
                agentLabel: "Upsell Agent",
                line: `${formatLocalTime()} View Cart Agent → Upsell Agent`,
              });
              appendTimelineLog({
                key: upsellKey,
                tool: "upsell_agent",
                agentLabel: "Upsell Agent",
                line: `${formatLocalTime()} Analyzing cart for cross-sell opportunities`,
              });

              const upsellRes = await fetch(
                `http://localhost:8000/api/cart/upsell/${customerId}`,
              );
              const upsellData = await upsellRes.json();

              endTimelineEntry({ key: upsellKey, status: "completed" });

              if (
                upsellData.upsell &&
                upsellData.upsell.responses &&
                upsellData.upsell.responses.recommendation &&
                upsellData.upsell.responses.recommendation.length > 0
              ) {
                // Timeline: Inventory Agent (upsell search)
                const invKey = `${Date.now()}:inventory_agent_upsell`;
                ensureTimelineEntry({
                  key: invKey,
                  tool: "inventory_agent",
                  agentLabel: "Inventory Agent",
                  status: "in_progress",
                });
                appendTimelineLog({
                  key: invKey,
                  tool: "inventory_agent",
                  agentLabel: "Inventory Agent",
                  line: `${formatLocalTime()} Upsell Agent → Inventory Agent`,
                });
                appendTimelineLog({
                  key: invKey,
                  tool: "inventory_agent",
                  agentLabel: "Inventory Agent",
                  line: `${formatLocalTime()} ✅ Found ${upsellData.upsell.responses.recommendation.length} upsell product(s)`,
                });
                endTimelineEntry({ key: invKey, status: "completed" });

                // Timeline: Recommendation Agent
                const recKey = `${Date.now()}:recommendation_agent_upsell`;
                ensureTimelineEntry({
                  key: recKey,
                  tool: "recommendation_agent",
                  agentLabel: "Recommendation Agent",
                  status: "in_progress",
                });
                appendTimelineLog({
                  key: recKey,
                  tool: "recommendation_agent",
                  agentLabel: "Recommendation Agent",
                  line: `${formatLocalTime()} Inventory Agent → Recommendation Agent`,
                });
                appendTimelineLog({
                  key: recKey,
                  tool: "recommendation_agent",
                  agentLabel: "Recommendation Agent",
                  line: `${formatLocalTime()} ✅ Prepared upsell recommendations`,
                });
                endTimelineEntry({ key: recKey, status: "completed" });

                const upsellCategory =
                  upsellData.upsell.upsell_category || "accessories";
                setLastRecommendations(
                  upsellData.upsell.responses.recommendation,
                );
                fetchReviewsByProductIds(
                  upsellData.upsell.responses.recommendation.map(
                    (p) => p?.product_id,
                  ),
                );

                setTimeout(() => {
                  const upsellHeaderMessage = {
                    type: "ai",
                    isUpsellHeader: true,
                    text: `🔥🎯 **Great choice!** We handpicked these **${upsellCategory}** just for you — they'd go perfectly with your picks! 👇✨`,
                    timestamp: new Date(),
                  };
                  setMessages((prev) => [...prev, upsellHeaderMessage]);

                  const upsellCardsMessage = {
                    type: "productCards",
                    productCards: upsellData.upsell.responses.recommendation,
                    timestamp: new Date(),
                  };
                  setMessages((prev) => [...prev, upsellCardsMessage]);
                }, 400);
              } else {
                // No upsell results — show follow-up
                setTimeout(() => {
                  const followUpMessage = {
                    type: "ai",
                    text: "Would you like to proceed with the payment or want to add more products? 🛒",
                    timestamp: new Date(),
                  };
                  setMessages((prev) => [...prev, followUpMessage]);
                }, 300);
              }
            } catch (upsellErr) {
              console.error("Upsell fetch error:", upsellErr);
              // Fallback follow-up on upsell failure
              setTimeout(() => {
                const followUpMessage = {
                  type: "ai",
                  text: "Would you like to proceed with the payment or want to add more products? 🛒",
                  timestamp: new Date(),
                };
                setMessages((prev) => [...prev, followUpMessage]);
              }, 300);
            }
          })();
        }
      } else {
        const aiMessage = {
          type: "ai",
          text: data.response || "Your cart is currently empty.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMessage]);
        if (!silent) speakResponse("Your cart is currently empty.");
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

  const handleToggleLoyalty = async (
    checked,
    originalTotal,
    availablePoints,
  ) => {
    setLoyaltyProcessing(true);
    try {
      if (checked) {
        // Apply loyalty points
        const res = await fetch(
          "http://localhost:8000/api/cart/apply-loyalty",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              customer_id: customerId,
              apply: true,
              cart_total: originalTotal,
            }),
          },
        );
        const result = await res.json();
        if (result.success) {
          setLoyaltyApplied(true);
          setLoyaltyPointsUsed(result.points_used);
          // Update the cart message in-place with new total
          setMessages((prev) =>
            prev.map((m) => {
              if (m.type === "cartItems") {
                return {
                  ...m,
                  loyalty_applied: true,
                  loyalty_points_used: result.points_used,
                  loyalty_remaining: result.remaining_points,
                  payable_amount: result.new_total,
                  available_loyalty_points: result.remaining_points,
                };
              }
              return m;
            }),
          );
        }
      } else {
        // Unapply loyalty points – restore them back to customer
        const pointsToRestore = loyaltyPointsUsed;
        const res = await fetch(
          "http://localhost:8000/api/cart/unapply-loyalty",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              customer_id: customerId,
              apply: false,
              cart_total: pointsToRestore, // pass points to restore
            }),
          },
        );
        const result = await res.json();
        if (result.success) {
          setLoyaltyApplied(false);
          setLoyaltyPointsUsed(0);
          setMessages((prev) =>
            prev.map((m) => {
              if (m.type === "cartItems") {
                return {
                  ...m,
                  loyalty_applied: false,
                  loyalty_points_used: 0,
                  loyalty_remaining: result.remaining_points,
                  payable_amount: m.total_amount,
                  available_loyalty_points: result.remaining_points,
                };
              }
              return m;
            }),
          );
        }
      }
    } catch (err) {
      console.error("Error toggling loyalty:", err);
    }
    setLoyaltyProcessing(false);
  };

  const handleAddToCart = async (product, isBulkAdd = false) => {
    const quantity = productQuantities[product.product_id];

    // Don't add if quantity is 0 or undefined
    if (!quantity || quantity === 0) {
      return false;
    }

    const selectedSize = isAccessories(product)
      ? null
      : productSizes[product.product_id] || getDefaultSize(product);

    // ─── Bulk Add: direct REST call for reliable, deterministic cart insertion ───
    if (isBulkAdd) {
      // Emit timeline entry for this product
      const cartKey = `${Date.now()}:add_to_cart_agent:${product.product_id}`;
      ensureTimelineEntry({
        key: cartKey,
        tool: "add_to_cart_agent",
        agentLabel: "Add to Cart Agent",
        status: "in_progress",
      });
      appendTimelineLog({
        key: cartKey,
        tool: "add_to_cart_agent",
        agentLabel: "Add to Cart Agent",
        line: `${formatLocalTime()} Master Orchestrator → Add to Cart Agent`,
      });
      appendTimelineLog({
        key: cartKey,
        tool: "add_to_cart_agent",
        agentLabel: "Add to Cart Agent",
        line: `${formatLocalTime()} Adding ${quantity}x ${product.product_name} (${product.product_id})`,
      });

      try {
        const response = await fetch("http://localhost:8000/api/cart/add", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            product_id: product.product_id,
            quantity,
            customer_id: customerId,
            size: selectedSize || null,
          }),
        });

        if (!response.ok) {
          console.error("Bulk add-to-cart failed: HTTP", response.status);
          appendTimelineLog({
            key: cartKey,
            tool: "add_to_cart_agent",
            agentLabel: "Add to Cart Agent",
            line: `${formatLocalTime()} ❌ Failed to add ${product.product_name}`,
          });
          endTimelineEntry({ key: cartKey, status: "error" });
          return false;
        }

        const data = await response.json();
        if (!data.success) {
          console.error("Bulk add-to-cart failed:", data.error);
          appendTimelineLog({
            key: cartKey,
            tool: "add_to_cart_agent",
            agentLabel: "Add to Cart Agent",
            line: `${formatLocalTime()} ❌ ${data.error || "Failed to add item"}`,
          });
          endTimelineEntry({ key: cartKey, status: "error" });
          return false;
        }

        // Log success and close timeline entry
        appendTimelineLog({
          key: cartKey,
          tool: "add_to_cart_agent",
          agentLabel: "Add to Cart Agent",
          line: `${formatLocalTime()} ✅ Added ${quantity}x ${product.product_name} to cart`,
        });
        appendTimelineLog({
          key: cartKey,
          tool: "add_to_cart_agent",
          agentLabel: "Add to Cart Agent",
          line: `${formatLocalTime()} Add to Cart Agent → Master Orchestrator`,
        });
        endTimelineEntry({ key: cartKey, status: "completed" });

        // Reset quantity for this product
        setProductQuantities((prev) => {
          const updated = { ...prev };
          delete updated[product.product_id];
          return updated;
        });

        // Reset size for this product
        setProductSizes((prev) => {
          const updated = { ...prev };
          delete updated[product.product_id];
          return updated;
        });

        fetchCartCount();
        return true;
      } catch (error) {
        console.error("Bulk add-to-cart error:", error);
        appendTimelineLog({
          key: cartKey,
          tool: "add_to_cart_agent",
          agentLabel: "Add to Cart Agent",
          line: `${formatLocalTime()} ❌ Network error adding ${product.product_name}`,
        });
        endTimelineEntry({ key: cartKey, status: "error" });
        return false;
      }
    }

    // ─── Individual Add: WebSocket / LLM agent pipeline (preserves timeline) ───
    const userMessage = {
      type: "user",
      text: `Add ${quantity} x ${product.product_name} to cart`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const data = await chatWithAgentViaWebSocket(
        customerId,
        `Add ${quantity} units of product ${product.product_id} to cart`,
        selectedSize ? { size: selectedSize } : undefined,
      );

      const aiMessage = {
        type: "ai",
        text: data.response || "Item added to cart successfully!",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);

      // Speak cart addition confirmation
      speakResponse(`${product.product_name} has been added to your cart.`);

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

      // Reset size for this product (keeps UI consistent for next recommendation turn)
      setProductSizes((prev) => {
        const updated = { ...prev };
        delete updated[product.product_id];
        return updated;
      });

      fetchCartCount();
      return true; // Success
    } catch (error) {
      console.error("Error adding to cart:", error);

      const errorMessage = {
        type: "ai",
        text: "Sorry, there was an error adding the item to cart. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsLoading(false);

      return false; // Failure
    }
  };

  // ============ Voice Recording (Speech-to-Text) ============
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Stop all tracks to release the microphone
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });

        if (audioBlob.size === 0) return;

        setIsTranscribing(true);
        try {
          const formData = new FormData();
          formData.append("audio", audioBlob, "recording.webm");

          const res = await fetch("http://localhost:8000/api/speech-to-text", {
            method: "POST",
            body: formData,
          });

          if (res.ok) {
            const data = await res.json();
            // Store the detected language for TTS responses
            if (data.detected_language) {
              voiceLanguageRef.current = data.detected_language;
            }
            // Use the translated English text as input for the agent
            const textForInput = data.text || "";
            if (textForInput) {
              setInputValue((prev) =>
                prev ? prev + " " + textForInput : textForInput,
              );
            }
          } else {
            console.error("Speech-to-text failed:", res.status);
          }
        } catch (err) {
          console.error("Speech-to-text error:", err);
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied:", err);
      alert(
        "Microphone access is required for voice input. Please allow microphone permission.",
      );
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
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
    setLoyaltyApplied(false);
    setLoyaltyPointsUsed(0);
  };

  return (
    <>
      {/* Image Zoom Overlay */}
      {zoomedImage && (
        <div
          className="image-zoom-overlay"
          onClick={() => setZoomedImage(null)}
        >
          <div className="image-zoom-container">
            <img
              src={zoomedImage.src}
              alt={zoomedImage.alt}
              className="image-zoom-img"
              onClick={(e) => {
                e.stopPropagation();
                setZoomedImage(null);
              }}
            />
            <div className="image-zoom-caption">{zoomedImage.alt}</div>
            <button
              className="image-zoom-close"
              onClick={() => setZoomedImage(null)}
              aria-label="Close zoom"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Virtual Try-On Modal */}
      {virtualTryOnProduct && (
        <VirtualTryOnModal
          product={virtualTryOnProduct}
          onClose={() => setVirtualTryOnProduct(null)}
        />
      )}

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
            {paymentFailModal.open && (
              <div
                className="payment-fail-modal-overlay"
                role="dialog"
                aria-modal="true"
                aria-label="Payment failed"
                onClick={(e) => {
                  if (e.target === e.currentTarget)
                    setPaymentFailModal({ open: false });
                }}
              >
                <div className="payment-fail-modal">
                  <div className="payment-fail-modal-icon">❌</div>
                  <div className="payment-fail-modal-title">
                    Payment Failed!
                  </div>
                  <div className="payment-fail-modal-body">
                    Your Credit Card transaction could not be processed. The
                    payment was declined by your bank. Please try again with a
                    different payment method or contact your bank for
                    assistance.
                  </div>
                  <div className="payment-fail-modal-actions">
                    <button
                      type="button"
                      className="payment-fail-modal-btn"
                      onClick={() => {
                        setPaymentFailModal({ open: false });
                        // Re-show payment method options (UPI, Credit Card, Debit Card, COD)
                        setSelectedPaymentMethod(null);
                        const retryMessage = {
                          type: "paymentMethods",
                          text: "Please select a payment method to try again.",
                          timestamp: new Date(),
                        };
                        setMessages((prev) => [...prev, retryMessage]);
                      }}
                      autoFocus
                    >
                      🔄 Pay Again
                    </button>
                  </div>
                </div>
              </div>
            )}

            {refundModal.open && (
              <div
                className="refund-modal-overlay"
                role="dialog"
                aria-modal="true"
                aria-label="Refund confirmation"
                onClick={(e) => {
                  if (e.target === e.currentTarget) closeRefundModal();
                }}
              >
                <div className="refund-modal">
                  <div className="refund-modal-header">
                    <div className="refund-modal-title">Refund Initiated</div>
                    <button
                      type="button"
                      className="refund-modal-close"
                      onClick={closeRefundModal}
                      aria-label="Close"
                    >
                      ✕
                    </button>
                  </div>
                  <div className="refund-modal-body">{refundModal.message}</div>
                  <div className="refund-modal-actions">
                    <button
                      type="button"
                      className="refund-modal-ok"
                      onClick={closeRefundModal}
                      autoFocus
                    >
                      OK
                    </button>
                  </div>
                </div>
              </div>
            )}

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
                  <button
                    className="header-cart-icon-btn"
                    onClick={() => handleViewCart(false)}
                    disabled={isLoading}
                    title="View Cart"
                  >
                    <img
                      className="header-cart-img"
                      src="/images/shopping-cart.png"
                      alt="Cart"
                    />
                    <span
                      className={`header-cart-badge${cartBlink ? " blink" : ""}`}
                    >
                      {cartCount}
                    </span>
                  </button>
                  <div className="action-tools">
                    <button
                      className="action-tool-btn quick-actions-toggle"
                      onClick={() => setIsQuickActionsOpen((prev) => !prev)}
                      disabled={isLoading}
                      title="Quick Action Tools"
                      aria-haspopup="menu"
                      aria-expanded={isQuickActionsOpen}
                    >
                      Quick Action Tools
                    </button>

                    {isQuickActionsOpen && (
                      <div className="quick-actions-menu" role="menu">
                        <button
                          className="action-tool-btn quick-action-cart"
                          onClick={() => {
                            setIsQuickActionsOpen(false);
                            handleViewCart(false);
                          }}
                          disabled={isLoading}
                          title="View Cart"
                          role="menuitem"
                        >
                          🛒 View Cart
                        </button>
                        <span
                          className="quick-actions-separator"
                          aria-hidden="true"
                        ></span>
                        <button
                          className="action-tool-btn quick-action-payment"
                          onClick={async () => {
                            setIsQuickActionsOpen(false);
                            const proceedText = "proceed";
                            const userMsg = {
                              type: "user",
                              text: proceedText,
                              timestamp: new Date(),
                            };
                            setMessages((prev) => [...prev, userMsg]);
                            setInputValue("");
                            setIsLoading(true);
                            try {
                              const data = await chatWithAgentViaWebSocket(
                                customerId,
                                proceedText,
                              );
                              if (
                                data.agent_calls &&
                                data.agent_calls.includes(
                                  "choose_channel_agent",
                                )
                              ) {
                                const purchaseMethodsMessage = {
                                  type: "purchaseMethods",
                                  text: data.response,
                                  timestamp: new Date(),
                                };
                                setMessages((prev) => [
                                  ...prev,
                                  purchaseMethodsMessage,
                                ]);
                                speakResponse(
                                  "How would you like to receive your order? You can buy online with home delivery or pick up from the nearest store.",
                                );
                              } else if (
                                data.agent_calls &&
                                data.agent_calls.includes("payment_agent") &&
                                data.agent_calls.length === 1
                              ) {
                                setMessages((prev) => {
                                  const lastMessage = prev[prev.length - 1];
                                  if (lastMessage?.type === "paymentMethods")
                                    return prev;
                                  return [
                                    ...prev,
                                    {
                                      type: "paymentMethods",
                                      text: data.response,
                                      timestamp: new Date(),
                                    },
                                  ];
                                });
                                speakResponse(
                                  "Please select your preferred payment method to complete the order.",
                                );
                              } else if (data.response) {
                                setMessages((prev) => [
                                  ...prev,
                                  {
                                    type: "ai",
                                    text: data.response,
                                    timestamp: new Date(),
                                  },
                                ]);
                                speakResponse(getTtsSummary(data));
                              }
                            } catch (err) {
                              console.error("Error in Go For Payment:", err);
                              setMessages((prev) => [
                                ...prev,
                                {
                                  type: "ai",
                                  text: "Sorry, I encountered an error. Please try again.",
                                  timestamp: new Date(),
                                },
                              ]);
                            } finally {
                              setIsLoading(false);
                            }
                          }}
                          disabled={isLoading}
                          title="Go For Payment"
                          role="menuitem"
                        >
                          💳 Go For Payment
                        </button>
                        <span
                          className="quick-actions-separator"
                          aria-hidden="true"
                        ></span>
                        <button
                          className="action-tool-btn quick-action-support"
                          onClick={() => {
                            setIsQuickActionsOpen(false);

                            // Emit live timeline entries for Post Purchase Agent
                            const ppKey = `${Date.now()}:post_purchase_agent`;
                            ensureTimelineEntry({
                              key: ppKey,
                              tool: "post_purchase_agent",
                              agentLabel: "Post-Purchase Agent",
                              status: "in_progress",
                            });
                            setTimeout(() => {
                              appendTimelineLog({
                                key: ppKey,
                                tool: "post_purchase_agent",
                                agentLabel: "Post-Purchase Agent",
                                line: `[${formatLocalTime()}] Master Orchestrator → Post-Purchase Agent`,
                              });
                            }, 300);
                            setTimeout(() => {
                              appendTimelineLog({
                                key: ppKey,
                                tool: "post_purchase_agent",
                                agentLabel: "Post-Purchase Agent",
                                line: `[${formatLocalTime()}] Preparing post-purchase support`,
                              });
                            }, 700);
                            setTimeout(() => {
                              appendTimelineLog({
                                key: ppKey,
                                tool: "post_purchase_agent",
                                agentLabel: "Post-Purchase Agent",
                                line: `[${formatLocalTime()}] Loading return, support & feedback services`,
                              });
                            }, 1100);
                            setTimeout(() => {
                              appendTimelineLog({
                                key: ppKey,
                                tool: "post_purchase_agent",
                                agentLabel: "Post-Purchase Agent",
                                line: `[${formatLocalTime()}] Post-Purchase Agent → Master Orchestrator`,
                              });
                            }, 1500);
                            setTimeout(() => {
                              endTimelineEntry({
                                key: ppKey,
                                status: "completed",
                              });
                            }, 1800);

                            setMessages((prev) => [
                              ...prev,
                              {
                                type: "postPurchaseActions",
                                timestamp: new Date(),
                              },
                            ]);
                            speakResponse(
                              "Here are your post-purchase support options. You can request a return, contact support, or leave feedback.",
                            );
                          }}
                          disabled={isLoading}
                          title="Post Purchase Support"
                          role="menuitem"
                        >
                          🎧 Post Purchase Support
                        </button>
                        <div className="quick-actions-separator"></div>
                        <button
                          className="action-tool-btn quick-action-wishlist"
                          onClick={handleShowWishlist}
                          disabled={isLoading}
                          title="Show Wishlist"
                          role="menuitem"
                        >
                          ❤️ Show Wishlist
                        </button>
                      </div>
                    )}
                  </div>
                  <button className="close-btn" onClick={toggleChatbot}>
                    ✕
                  </button>
                </div>
              </div>

              <div className="chat-messages" ref={chatContainerRef}>
                {(() => {
                  // Find the index of the last paymentMethods message
                  var lastPaymentMethodsIndex = -1;
                  for (let i = messages.length - 1; i >= 0; i--) {
                    if (messages[i].type === "paymentMethods") {
                      lastPaymentMethodsIndex = i;
                      break;
                    }
                  }
                  return null;
                })()}
                {messages.map((message, index) => {
                  const isLatestPaymentMethods =
                    message.type === "paymentMethods" &&
                    (() => {
                      for (let i = messages.length - 1; i >= 0; i--) {
                        if (messages[i].type === "paymentMethods")
                          return i === index;
                      }
                      return false;
                    })();
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
                          storePickupConfirmation: null,
                          loyaltyRewards: null,
                          postPurchaseSupport: null,
                        };

                  // Check if this is a welcome message
                  const isWelcomeMessage = message.isWelcomeCard && index === 0;

                  // Skip viewCartPrompt messages (buttons removed, available via quick actions)
                  if (message.type === "viewCartPrompt") return null;

                  return (
                    <div
                      key={index}
                      className={`message ${message.type === "user" ? "user-message" : "ai-message"} ${isWelcomeMessage ? "welcome-message-special" : ""} ${message.type === "postPurchaseActions" || message.type === "refundOrders" || message.type === "storeLocator" || message.type === "contactSupport" ? "wide-message" : ""}`}
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
                          {message.type === "refundOrders" && (
                            <div className="refund-orders-card">
                              <div className="refund-orders-header">
                                <div className="refund-orders-title">
                                  <span
                                    className="refund-orders-icon"
                                    aria-hidden="true"
                                  >
                                    🧾
                                  </span>
                                  <div className="refund-orders-title-text">
                                    <h4>Orders eligible for refund</h4>
                                    <p>Select an order to initiate refund</p>
                                  </div>
                                </div>

                                <div className="refund-orders-header-actions">
                                  <button
                                    type="button"
                                    className="refund-guidelines-btn"
                                    aria-label={
                                      isRefundGuidelinesOpen
                                        ? "Hide refund guidelines"
                                        : "Show refund guidelines"
                                    }
                                    title={
                                      isRefundGuidelinesOpen
                                        ? "Hide refund guidelines"
                                        : "Refund guidelines"
                                    }
                                    onClick={() =>
                                      setIsRefundGuidelinesOpen((prev) => !prev)
                                    }
                                  >
                                    📋
                                  </button>
                                </div>
                              </div>

                              {isRefundGuidelinesOpen && (
                                <div
                                  className="refund-guidelines-panel"
                                  role="note"
                                >
                                  <div className="refund-guidelines-title">
                                    REFUND POLICY
                                  </div>
                                  <ul className="refund-guidelines-list">
                                    <li>
                                      Refunds are eligible for purchases made
                                      between 24 hours and 7 days ago. Items
                                      purchased within the last 24 hours are not
                                      eligible for return.
                                    </li>
                                    <li>
                                      Items should be unused, in original
                                      condition, and include all original
                                      packaging/tags.
                                    </li>
                                    <li>
                                      Keep your invoice / order ID ready for
                                      verification.
                                    </li>
                                    <li>
                                      Once approved, refunds are processed to
                                      the original payment method (timing may
                                      vary by bank/UPI/card).
                                    </li>
                                    <li>
                                      If the product is damaged/incorrect,
                                      select the order and start a
                                      refund—support may ask for photos.
                                    </li>
                                  </ul>
                                </div>
                              )}

                              {Array.isArray(message.orders) &&
                              message.orders.length > 0 ? (
                                <div className="refund-orders-list">
                                  {message.orders.map((order, idx) => (
                                    <div
                                      key={order?.transaction_id || idx}
                                      className="refund-order-item"
                                    >
                                      <div className="refund-order-thumb">
                                        <img
                                          src={
                                            order?.image_reference ||
                                            "/images/placeholder.png"
                                          }
                                          alt={order?.product_name || "Product"}
                                          className="refund-order-thumb-img"
                                          onError={(e) => {
                                            e.target.src =
                                              "/images/placeholder.png";
                                          }}
                                        />
                                      </div>
                                      <div className="refund-order-info">
                                        <div className="refund-order-name">
                                          {order?.product_name || "Product"}
                                        </div>
                                        <div className="refund-order-meta">
                                          <span>
                                            Qty: {order?.quantity ?? "-"}
                                          </span>
                                          <span>
                                            Price: ₹{order?.price ?? "-"}
                                          </span>
                                          <span>
                                            Date:{" "}
                                            {formatOrderDate(
                                              order?.purchase_date,
                                            )}
                                          </span>
                                        </div>
                                      </div>

                                      <button
                                        className="refund-init-btn"
                                        type="button"
                                        disabled={
                                          order?.return_status &&
                                          order.return_status.toLowerCase() !==
                                            ""
                                        }
                                        onClick={() => {
                                          openRefundModal(order);
                                        }}
                                      >
                                        {order?.return_status
                                          ? ` ${order.return_status}`
                                          : "Return"}
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div className="refund-orders-empty">
                                  No eligible orders found. Only purchases made
                                  between 24 hours and 7 days ago are eligible
                                  for return.
                                </div>
                              )}
                            </div>
                          )}

                          {message.type === "storeLocator" && (
                            <div className="store-locator-section">
                              <div className="store-locator-container">
                                <div className="store-locator-header">
                                  <span className="store-locator-icon">📍</span>
                                  <div className="store-locator-header-text">
                                    <h4>Store Locator</h4>
                                    <p>Find our stores nearest to you</p>
                                  </div>
                                </div>

                                {Array.isArray(message.stores) &&
                                message.stores.length > 0 ? (
                                  <div className="store-locator-table-wrap">
                                    <table className="store-locator-table">
                                      <thead>
                                        <tr>
                                          <th>#</th>
                                          <th>Store Name</th>
                                          <th>Distance</th>
                                          <th>Locate on Map</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {message.stores.map((store, idx) => (
                                          <tr key={idx}>
                                            <td className="store-rank">
                                              {idx + 1}
                                            </td>
                                            <td className="store-name-cell">
                                              <span className="store-name-icon">
                                                🏬
                                              </span>
                                              {store.store_name}
                                            </td>
                                            <td className="store-distance-cell">
                                              <span className="distance-badge">
                                                {store.distance} km
                                              </span>
                                            </td>
                                            <td className="store-map-cell">
                                              {store.map_url ? (
                                                <a
                                                  href={store.map_url}
                                                  target="_blank"
                                                  rel="noopener noreferrer"
                                                  className="map-link-btn"
                                                >
                                                  🗺️ Open Map
                                                </a>
                                              ) : (
                                                <span className="map-unavailable">
                                                  —
                                                </span>
                                              )}
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                ) : (
                                  <div className="store-locator-empty">
                                    No store locations found for your area.
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {message.type === "contactSupport" && (
                            <div className="contact-support-section">
                              <div className="contact-support-card">
                                {/* Address */}
                                <div className="cs-block">
                                  <div className="cs-block-header">
                                    <h4 className="cs-block-title">Address</h4>
                                    <span className="cs-block-icon">📍</span>
                                  </div>
                                  <p className="cs-block-text">
                                    Aditya Birla Fashion and Retail Ltd, Piramal
                                    Agastya Corporate Park, Building
                                    &lsquo;A&rsquo;, 4th and 5th Floor, Unit No.
                                    401, 403, 501, 502, L.B.S. Road, Kurla,
                                    Mumbai &ndash; 400 070.
                                  </p>
                                </div>
                                <div className="cs-divider" />
                                {/* Phone */}
                                <div className="cs-block">
                                  <div className="cs-block-header">
                                    <h4 className="cs-block-title">Phone</h4>
                                    <span className="cs-block-icon">📞</span>
                                  </div>
                                  <div className="cs-phone-row">
                                    <span className="cs-phone-label">
                                      Online related queries
                                    </span>
                                    <a
                                      href="tel:8105060501"
                                      className="cs-phone-number"
                                    >
                                      8105060501
                                    </a>
                                  </div>
                                  <div className="cs-phone-row">
                                    <span className="cs-phone-label">
                                      Store related queries
                                    </span>
                                    <a
                                      href="tel:18004253050"
                                      className="cs-phone-number"
                                    >
                                      1800 425 3050
                                    </a>
                                  </div>
                                </div>
                                <div className="cs-divider" />
                                {/* Email */}
                                <div className="cs-block">
                                  <div className="cs-block-header">
                                    <h4 className="cs-block-title">Email</h4>
                                    <span className="cs-block-icon">✉️</span>
                                  </div>
                                  <div className="cs-email-group">
                                    <p className="cs-email-label">
                                      For store related queries
                                    </p>
                                    <a
                                      href="mailto:customerservice@abfrl.adityabirla.com"
                                      className="cs-email-link"
                                    >
                                      customerservice@abfrl.adityabirla.com
                                    </a>
                                  </div>
                                  <div className="cs-email-group">
                                    <p className="cs-email-label">
                                      For online enquiries
                                    </p>
                                    <a
                                      href="mailto:happytohelp@abfrl.in"
                                      className="cs-email-link"
                                    >
                                      happytohelp@abfrl.in
                                    </a>
                                  </div>
                                  <div className="cs-email-group">
                                    <p className="cs-email-label">
                                      For corporate orders
                                    </p>
                                    <a
                                      href="mailto:corporate.sales@abfrl.adityabirla.com"
                                      className="cs-email-link"
                                    >
                                      corporate.sales@abfrl.adityabirla.com
                                    </a>
                                  </div>
                                  <div className="cs-email-group">
                                    <p className="cs-email-label">
                                      For franchisee
                                    </p>
                                    <a
                                      href="mailto:franchiseenquiry@abfrl.adityabirla.com"
                                      className="cs-email-link"
                                    >
                                      franchiseenquiry@abfrl.adityabirla.com
                                    </a>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {message.type === "postPurchaseActions" && (
                            <div className="post-purchase-agent-section">
                              <div className="post-purchase-container post-purchase-actions-card">
                                <div className="post-purchase-header">
                                  <span className="post-purchase-icon">🎧</span>
                                  <div className="post-purchase-header-text">
                                    <h4>Post Purchase Agent</h4>
                                    <p>Select an option to continue</p>
                                  </div>
                                </div>

                                <div className="pp-actions-grid">
                                  <button
                                    className="pp-action-card pp-return-card"
                                    onClick={() => {
                                      handleRefundQuickAction();
                                    }}
                                    disabled={isLoading || isRefundLoading}
                                    type="button"
                                  >
                                    <div className="pp-icon-wrapper">
                                      <span className="pp-emoji">💸</span>
                                    </div>
                                    <div className="pp-action-name">Return</div>
                                  </button>
                                  <button
                                    className="pp-action-card pp-support-card"
                                    onClick={() => {
                                      handleCustomerSupport();
                                    }}
                                    disabled={isLoading || isRefundLoading}
                                    type="button"
                                  >
                                    <div className="pp-icon-wrapper">
                                      <span className="pp-emoji">💬</span>
                                    </div>
                                    <div className="pp-action-name">
                                      Customer Support
                                    </div>
                                  </button>
                                  <button
                                    className="pp-action-card pp-feedback-card"
                                    onClick={() => {
                                      setInputValue("feedback");
                                      setTimeout(() => sendMessage(), 0);
                                    }}
                                    disabled={isLoading || isRefundLoading}
                                    type="button"
                                  >
                                    <div className="pp-icon-wrapper">
                                      <span className="pp-emoji">⭐</span>
                                    </div>
                                    <div className="pp-action-name">
                                      Feedback
                                    </div>
                                  </button>
                                  <button
                                    className="pp-action-card pp-locate-card"
                                    onClick={() => {
                                      handleLocateUs();
                                    }}
                                    disabled={isLoading || isRefundLoading}
                                    type="button"
                                  >
                                    <div className="pp-icon-wrapper">
                                      <span className="pp-emoji">📍</span>
                                    </div>
                                    <div className="pp-action-name">
                                      Locate Us on Map
                                    </div>
                                  </button>
                                </div>
                              </div>
                            </div>
                          )}

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

                          {/* Render Store Pickup Confirmation if parsed */}
                          {structuredData.storePickupConfirmation && (
                            <div className="fulfillment-agent-section">
                              <div className="agent-section-title">
                                Store pickup is confirmed!
                              </div>

                              <div className="pickup-confirmation-container">
                                <div className="pickup-header">
                                  <div className="pickup-header-left">
                                    <div className="pickup-icon">🏬</div>
                                    <div className="pickup-header-text">
                                      <h4>
                                        {
                                          structuredData.storePickupConfirmation
                                            .title
                                        }
                                      </h4>
                                      <p>
                                        Show the Order ID at the store kiosk to
                                        collect your items.
                                      </p>
                                    </div>
                                  </div>

                                  {structuredData.storePickupConfirmation
                                    .status && (
                                    <div className="pickup-status-pill">
                                      {
                                        structuredData.storePickupConfirmation
                                          .status
                                      }
                                    </div>
                                  )}
                                </div>

                                <div className="pickup-details-grid">
                                  <div className="pickup-detail-item">
                                    <span className="detail-label">
                                      Order ID
                                    </span>
                                    <span className="detail-value">
                                      #
                                      {
                                        structuredData.storePickupConfirmation
                                          .order_id
                                      }
                                    </span>
                                  </div>
                                  <div className="pickup-detail-item">
                                    <span className="detail-label">
                                      Store ID
                                    </span>
                                    <span className="detail-value">
                                      {
                                        structuredData.storePickupConfirmation
                                          .store_id
                                      }
                                    </span>
                                  </div>
                                  <div className="pickup-detail-item">
                                    <span className="detail-label">
                                      Total Amount
                                    </span>
                                    <span className="detail-value amount orange">
                                      {structuredData.storePickupConfirmation
                                        .total_amount != null
                                        ? `₹${structuredData.storePickupConfirmation.total_amount.toLocaleString()}`
                                        : "—"}
                                    </span>
                                  </div>
                                  <div className="pickup-detail-item">
                                    <span className="detail-label">
                                      Total Items
                                    </span>
                                    <span className="detail-value">
                                      {structuredData.storePickupConfirmation
                                        .total_items != null
                                        ? structuredData.storePickupConfirmation
                                            .total_items
                                        : "—"}
                                    </span>
                                  </div>
                                  <div className="pickup-detail-item">
                                    <span className="detail-label">
                                      Pickup Store
                                    </span>
                                    <span className="detail-value">
                                      {
                                        structuredData.storePickupConfirmation
                                          .pickup_store
                                      }
                                    </span>
                                  </div>
                                </div>

                                {structuredData.storePickupConfirmation
                                  .store_address && (
                                  <div className="pickup-address">
                                    <div className="pickup-address-label">
                                      Store Address
                                    </div>
                                    <div className="pickup-address-value">
                                      {
                                        structuredData.storePickupConfirmation
                                          .store_address
                                      }
                                    </div>
                                  </div>
                                )}

                                {structuredData.storePickupConfirmation.items &&
                                  structuredData.storePickupConfirmation.items
                                    .length > 0 && (
                                    <div className="pickup-items">
                                      <div className="pickup-items-title">
                                        Your Items
                                      </div>
                                      <div className="pickup-items-list">
                                        {structuredData.storePickupConfirmation.items.map(
                                          (item, idx) => (
                                            <div
                                              key={idx}
                                              className="pickup-item-row"
                                            >
                                              <span className="pickup-item-dot">
                                                •
                                              </span>
                                              <span className="pickup-item-text">
                                                {item}
                                              </span>
                                            </div>
                                          ),
                                        )}
                                      </div>
                                    </div>
                                  )}
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
                            !structuredData.storePickupConfirmation &&
                            !structuredData.loyaltyRewards &&
                            !structuredData.postPurchaseSupport && (
                              <div
                                className={`message-text${message.isUpsellHeader ? " upsell-header-text" : ""}`}
                              >
                                {displayText}
                              </div>
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
                          {message.type === "paymentMethods" &&
                            !isLatestPaymentMethods && (
                              <div className="payment-methods-container payment-methods-expired">
                                <div className="payment-methods-header">
                                  <span className="payment-icon">💳</span>
                                  <h4>Payment method selection expired</h4>
                                </div>
                              </div>
                            )}
                          {message.type === "paymentMethods" &&
                            isLatestPaymentMethods && (
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
                                    <div className="payment-method-name">
                                      UPI
                                    </div>
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
                                      handlePaymentMethodClick(
                                        "cash on delivery",
                                      )
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
                            isLatestPaymentMethods &&
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
                            isLatestPaymentMethods &&
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
                                    <span
                                      className={`store-status ${
                                        (store.availability || "")
                                          .toString()
                                          .toLowerCase()
                                          .includes("available")
                                          ? "available"
                                          : "unavailable"
                                      }`}
                                    >
                                      {store.availability}
                                    </span>
                                  </div>

                                  <div className="store-card-actions">
                                    <div
                                      className="store-action store-distance"
                                      title="Distance from you"
                                    >
                                      <span className="action-icon">📍</span>
                                      <span>
                                        {Number.isFinite(store.distance)
                                          ? store.distance.toFixed(2)
                                          : store.distance}{" "}
                                        km
                                      </span>
                                    </div>

                                    <a
                                      href={store.map_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="store-action map-btn"
                                      role="button"
                                      aria-label={`View ${store.store_name} on map`}
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
                                    {message.isWishlist
                                      ? "❤️ Your Wishlist"
                                      : "🛍️ Recommended Products"}
                                  </h4>
                                  {(() => {
                                    const selectedCount = (
                                      message.isWishlist
                                        ? message.productCards
                                        : message.productCards.slice(0, 4)
                                    ).filter(
                                      (p) =>
                                        productQuantities[p.product_id] &&
                                        productQuantities[p.product_id] > 0,
                                    ).length;
                                    const totalQuantity = (
                                      message.isWishlist
                                        ? message.productCards
                                        : message.productCards.slice(0, 4)
                                    ).reduce(
                                      (sum, p) =>
                                        sum +
                                        (productQuantities[p.product_id] || 0),
                                      0,
                                    );
                                    return selectedCount > 0 ? (
                                      <button
                                        className="bulk-add-to-cart-btn"
                                        onClick={async () => {
                                          const productsToAdd = (
                                            message.isWishlist
                                              ? message.productCards
                                              : message.productCards.slice(0, 4)
                                          ).filter(
                                            (p) =>
                                              productQuantities[p.product_id] &&
                                              productQuantities[p.product_id] >
                                                0,
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

                                          // Add products sequentially via direct REST API
                                          let successCount = 0;
                                          const failedProducts = [];
                                          for (const product of productsToAdd) {
                                            const success =
                                              await handleAddToCart(
                                                product,
                                                true,
                                              );
                                            if (success) {
                                              successCount++;
                                            } else {
                                              failedProducts.push(
                                                product.product_name,
                                              );
                                            }
                                          }

                                          // Show single summary message
                                          if (successCount > 0) {
                                            // TTS: speak all added product names at once
                                            const addedNames = productsToAdd
                                              .filter(
                                                (p) =>
                                                  !failedProducts.includes(
                                                    p.product_name,
                                                  ),
                                              )
                                              .map((p) => p.product_name);
                                            if (addedNames.length === 1) {
                                              speakResponse(
                                                `${addedNames[0]} has been added to your cart.`,
                                              );
                                            } else if (addedNames.length > 1) {
                                              const nameList =
                                                addedNames
                                                  .slice(0, -1)
                                                  .join(", ") +
                                                " and " +
                                                addedNames[
                                                  addedNames.length - 1
                                                ];
                                              speakResponse(
                                                `${nameList} have been added to your cart.`,
                                              );
                                            }
                                            let summaryText =
                                              successCount ===
                                              productsToAdd.length
                                                ? `All ${successCount} product(s) have been added to cart successfully. You can now proceed to pay.`
                                                : `${successCount} of ${productsToAdd.length} product(s) added to cart. Failed: ${failedProducts.join(", ")}. You can try adding the failed items again.`;
                                            const aiMessage = {
                                              type: "ai",
                                              text: summaryText,
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
                                  {(message.isWishlist
                                    ? message.productCards
                                    : message.productCards.slice(0, 4)
                                  ).map((product) => {
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
                                          <button
                                            className="vto-tryon-btn"
                                            title="Virtual Trial Room"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              setVirtualTryOnProduct(product);
                                            }}
                                          >
                                            👗
                                            <span className="vto-tryon-tooltip">
                                              Virtual Trial Room
                                            </span>
                                          </button>
                                          <img
                                            src={
                                              product.image_reference ||
                                              "/images/placeholder.png"
                                            }
                                            alt={product.product_name}
                                            className="product-image zoomable-image"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              setZoomedImage({
                                                src:
                                                  product.image_reference ||
                                                  "/images/placeholder.png",
                                                alt: product.product_name,
                                              });
                                            }}
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
                                          <h4 className="product-name product-name-row">
                                            <span className="product-name-text">
                                              {product.product_name}
                                            </span>
                                            {typeof productReviews?.[
                                              product.product_id
                                            ] === "number" && (
                                              <span className="product-rating">
                                                ⭐{" "}
                                                {Number(
                                                  productReviews[
                                                    product.product_id
                                                  ],
                                                ).toFixed(2)}
                                              </span>
                                            )}
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
                                            <button
                                              className={`wishlist-heart-btn${
                                                wishlistedIds.has(
                                                  product.product_id,
                                                )
                                                  ? " wishlisted"
                                                  : ""
                                              }`}
                                              title={
                                                wishlistedIds.has(
                                                  product.product_id,
                                                )
                                                  ? "Remove from wishlist"
                                                  : "Add to wishlist"
                                              }
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                handleWishlistToggle(
                                                  product.product_id,
                                                );
                                              }}
                                            >
                                              {wishlistedIds.has(
                                                product.product_id,
                                              )
                                                ? "❤️"
                                                : "🤍"}
                                            </button>
                                          </div>
                                          <div className="qty-size-row">
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

                                            {!isAccessories(product) && (
                                              <div className="size-control">
                                                <select
                                                  className="size-select"
                                                  value={
                                                    productSizes[
                                                      product.product_id
                                                    ] || getDefaultSize(product)
                                                  }
                                                  onChange={(e) =>
                                                    setProductSizes((prev) => ({
                                                      ...prev,
                                                      [product.product_id]:
                                                        e.target.value,
                                                    }))
                                                  }
                                                  aria-label="Select size"
                                                >
                                                  {getSizeOptions(product).map(
                                                    (opt) => (
                                                      <option
                                                        key={opt}
                                                        value={opt}
                                                      >
                                                        {opt}
                                                      </option>
                                                    ),
                                                  )}
                                                </select>
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            )}

                          {/* Pending cart reminder on chatbot open */}
                          {message.type === "pendingCartReminder" &&
                            message.cartItems &&
                            message.cartItems.length > 0 && (
                              <div className="pending-cart-reminder">
                                <div className="pending-cart-reminder-header">
                                  <span className="pending-cart-reminder-icon">
                                    🛍️
                                  </span>
                                  <div className="pending-cart-reminder-text">
                                    <h4>
                                      Your handpicked favorites are waiting!
                                    </h4>
                                    <p>
                                      You've got{" "}
                                      <strong>
                                        {message.total_items} amazing{" "}
                                        {message.total_items === 1
                                          ? "item"
                                          : "items"}
                                      </strong>{" "}
                                      in your cart worth{" "}
                                      <strong>
                                        ₹
                                        {Math.round(
                                          message.total_amount,
                                        ).toLocaleString()}
                                      </strong>{" "}
                                      — don't let them slip away!
                                    </p>
                                  </div>
                                </div>
                                <div className="pending-cart-reminder-items">
                                  {message.cartItems.slice(0, 4).map((item) => (
                                    <div
                                      key={item.order_id || item.product_id}
                                      className="pending-cart-mini-item"
                                    >
                                      <img
                                        src={
                                          item.image_reference ||
                                          "/images/placeholder.png"
                                        }
                                        alt={item.product_name}
                                        className="pending-cart-mini-img"
                                        onError={(e) => {
                                          e.target.src =
                                            "/images/placeholder.png";
                                        }}
                                      />
                                      <span className="pending-cart-mini-name">
                                        {item.product_name}
                                      </span>
                                    </div>
                                  ))}
                                  {message.cartItems.length > 4 && (
                                    <div className="pending-cart-mini-more">
                                      +{message.cartItems.length - 4} more
                                    </div>
                                  )}
                                </div>
                                <button
                                  className="pending-cart-checkout-btn"
                                  onClick={() => handleViewCart()}
                                >
                                  🛒 View Cart &amp; Checkout
                                </button>
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
                                    const sizeValue =
                                      item.size ??
                                      item.selected_size ??
                                      item.product_size ??
                                      "";

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
                                          <h4 className="product-name product-name-row">
                                            <span className="product-name-text">
                                              {item.product_name}
                                            </span>
                                            {typeof productReviews?.[
                                              item.product_id
                                            ] === "number" && (
                                              <span className="product-rating">
                                                ⭐{" "}
                                                {Number(
                                                  productReviews[
                                                    item.product_id
                                                  ],
                                                ).toFixed(2)}
                                              </span>
                                            )}
                                          </h4>
                                          <p className="product-id-text">
                                            ID: {item.product_id}
                                          </p>
                                          {sizeValue ? (
                                            <p className="product-id-text">
                                              Size: {sizeValue}
                                            </p>
                                          ) : null}

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

                                  {/* Loyalty Points Section */}
                                  {(message.available_loyalty_points > 0 ||
                                    message.loyalty_applied) && (
                                    <div className="loyalty-points-section">
                                      <div className="loyalty-points-header">
                                        <span className="loyalty-icon">🎁</span>
                                        <span className="loyalty-label">
                                          Available Loyalty Points:{" "}
                                          <strong>
                                            {message.available_loyalty_points ??
                                              0}
                                          </strong>
                                        </span>
                                      </div>
                                      <label className="loyalty-checkbox-label">
                                        <input
                                          type="checkbox"
                                          className="loyalty-checkbox"
                                          checked={
                                            message.loyalty_applied || false
                                          }
                                          disabled={loyaltyProcessing}
                                          onChange={(e) =>
                                            handleToggleLoyalty(
                                              e.target.checked,
                                              message.total_amount,
                                              message.available_loyalty_points,
                                            )
                                          }
                                        />
                                        <span className="loyalty-checkbox-text">
                                          Use my loyalty points
                                          {loyaltyProcessing &&
                                            " (processing...)"}
                                        </span>
                                      </label>
                                      {message.loyalty_applied &&
                                        message.loyalty_points_used > 0 && (
                                          <div className="loyalty-applied-summary">
                                            <div className="loyalty-deduction">
                                              <span>Loyalty Discount:</span>
                                              <span className="loyalty-deduction-amount">
                                                − ₹
                                                {Math.round(
                                                  message.loyalty_points_used,
                                                ).toLocaleString()}
                                              </span>
                                            </div>
                                            <div className="loyalty-payable">
                                              <span>Total Payable:</span>
                                              <span className="loyalty-payable-amount">
                                                ₹
                                                {Math.round(
                                                  message.payable_amount ??
                                                    message.total_amount,
                                                ).toLocaleString()}
                                              </span>
                                            </div>
                                          </div>
                                        )}
                                    </div>
                                  )}

                                  <p className="proceed-prompt">
                                    Would you like to proceed to payment? 🛍️
                                  </p>
                                  <div className="cart-go-payment-wrapper">
                                    <button
                                      className="cart-go-payment-btn"
                                      disabled={isLoading}
                                      onClick={async () => {
                                        const proceedText = "proceed";
                                        const userMsg = {
                                          type: "user",
                                          text: proceedText,
                                          timestamp: new Date(),
                                        };
                                        setMessages((prev) => [
                                          ...prev,
                                          userMsg,
                                        ]);
                                        setInputValue("");
                                        setIsLoading(true);
                                        try {
                                          const data =
                                            await chatWithAgentViaWebSocket(
                                              customerId,
                                              proceedText,
                                            );
                                          if (
                                            data.agent_calls &&
                                            data.agent_calls.includes(
                                              "choose_channel_agent",
                                            )
                                          ) {
                                            setMessages((prev) => [
                                              ...prev,
                                              {
                                                type: "purchaseMethods",
                                                text: data.response,
                                                timestamp: new Date(),
                                              },
                                            ]);
                                            speakResponse(
                                              "How would you like to receive your order? You can buy online with home delivery or pick up from the nearest store.",
                                            );
                                          } else if (
                                            data.agent_calls &&
                                            data.agent_calls.includes(
                                              "payment_agent",
                                            ) &&
                                            data.agent_calls.length === 1
                                          ) {
                                            setMessages((prev) => {
                                              const lastMessage =
                                                prev[prev.length - 1];
                                              if (
                                                lastMessage?.type ===
                                                "paymentMethods"
                                              )
                                                return prev;
                                              return [
                                                ...prev,
                                                {
                                                  type: "paymentMethods",
                                                  text: data.response,
                                                  timestamp: new Date(),
                                                },
                                              ];
                                            });
                                            speakResponse(
                                              "Please select your preferred payment method to complete the order.",
                                            );
                                          } else if (data.response) {
                                            setMessages((prev) => [
                                              ...prev,
                                              {
                                                type: "ai",
                                                text: data.response,
                                                timestamp: new Date(),
                                              },
                                            ]);
                                            speakResponse(getTtsSummary(data));
                                          }
                                        } catch (err) {
                                          console.error(
                                            "Error in Go For Payment:",
                                            err,
                                          );
                                          setMessages((prev) => [
                                            ...prev,
                                            {
                                              type: "ai",
                                              text: "Sorry, I encountered an error. Please try again.",
                                              timestamp: new Date(),
                                            },
                                          ]);
                                        } finally {
                                          setIsLoading(false);
                                        }
                                      }}
                                    >
                                      💳 Go For Payment
                                    </button>
                                  </div>
                                </div>
                              </div>
                            )}

                          {/* View Cart Prompt removed - available via quick actions menu */}

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
                                      className="product-image zoomable-image"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setZoomedImage({
                                          src: product.image_reference || "/images/placeholder.png",
                                          alt: product.product_name,
                                        });
                                      }}
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
                                  const sizeValue = item.size ?? item.selected_size ?? item.product_size ?? "";

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
                                        {sizeValue ? (
                                          <p className="product-id-text">Size: {sizeValue}</p>
                                        ) : null}
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
                  <button
                    className={`voice-mic-toggle${isVoiceEnabled ? " active" : ""}`}
                    title={
                      isVoiceEnabled
                        ? "Voice assistance on"
                        : "Voice assistance off"
                    }
                    onClick={() => {
                      const next = !isVoiceEnabled;
                      setIsVoiceEnabled(next);
                      if (!next && ttsAudioRef.current) {
                        ttsAudioRef.current.pause();
                        ttsAudioRef.current = null;
                      }
                      if (!next && isRecording) {
                        stopRecording();
                      }
                    }}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      width="22"
                      height="22"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <rect x="9" y="1" width="6" height="12" rx="3" />
                      <path d="M5 10a7 7 0 0 0 14 0" />
                      <line x1="12" y1="17" x2="12" y2="21" />
                      <line x1="8" y1="21" x2="16" y2="21" />
                      {!isVoiceEnabled && (
                        <line
                          x1="3"
                          y1="3"
                          x2="21"
                          y2="21"
                          className="mic-strikethrough"
                        />
                      )}
                    </svg>
                  </button>
                  <input
                    type="text"
                    className="chat-input"
                    placeholder="Type your message here..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading}
                  />
                  {isVoiceEnabled && (
                    <button
                      className={`mic-btn${isRecording ? " recording" : ""}`}
                      title={
                        isRecording
                          ? "Stop recording"
                          : isTranscribing
                            ? "Transcribing..."
                            : "Voice input"
                      }
                      onClick={isRecording ? stopRecording : startRecording}
                      disabled={isLoading || isTranscribing}
                    >
                      {isTranscribing ? "⏳" : isRecording ? "⏹" : "🎤"}
                    </button>
                  )}
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
