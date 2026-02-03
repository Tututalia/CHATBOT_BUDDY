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

  // Handle payment method button clicks
  const handlePaymentMethodClick = (method) => {
    setInputValue(method);
    setTimeout(() => sendMessage(), 100);
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
        text: "View my cart",
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
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "view cart",
          customer_id: customerId,
        }),
      });

      const data = await response.json();

      if (!silent) {
        setAgentTimeline((prev) => [
          ...prev,
          {
            action: "View Cart Agent",
            timestamp: new Date().toLocaleTimeString(),
            status: "completed",
          },
        ]);
      }

      // If backend returns cart items, display as product cards
      if (
        data.cart_items &&
        Array.isArray(data.cart_items) &&
        data.cart_items.length > 0
      ) {
        const cartCardsMessage = {
          type: "cartItems",
          cartItems: data.cart_items,
          timestamp: new Date(),
        };

        // Replace the last cart items message if in silent mode, otherwise append
        if (silent) {
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

                  // Parse structured response for AI messages
                  const structuredData =
                    message.type === "ai"
                      ? parseStructuredResponse(message.text)
                      : {
                          orderConfirmation: null,
                          loyaltyRewards: null,
                          postPurchaseSupport: null,
                        };

                  return (
                    <div
                      key={index}
                      className={`message ${message.type === "user" ? "user-message" : "ai-message"}`}
                    >
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
                                  <span className="detail-label">Order ID</span>
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
                                  <h4>{structuredData.loyaltyRewards.title}</h4>
                                  <p>
                                    {structuredData.loyaltyRewards.description}
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
                                  <div className="btn-title">Buy Online</div>
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
                                  <div className="btn-title">Nearest Store</div>
                                  <div className="btn-subtitle">
                                    Store Pickup
                                  </div>
                                </div>
                              </button>
                            </div>
                          </div>
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
                                onClick={() => handlePaymentMethodClick("upi")}
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
                                className="payment-method-card net-banking-card"
                                onClick={() =>
                                  handlePaymentMethodClick("net banking")
                                }
                              >
                                <div className="payment-icon-wrapper">
                                  <span className="payment-emoji">💰</span>
                                </div>
                                <div className="payment-method-name">
                                  Net Banking
                                </div>
                              </button>
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
                              {message.productCards
                                .slice(0, 3)
                                .map((product) => (
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
                                      <div className="product-pricing">
                                        {product.discount &&
                                        product.discount > 0 ? (
                                          <>
                                            <span className="original-price">
                                              ₹{product.price.toLocaleString()}
                                            </span>
                                            <span className="discount-price">
                                              ₹
                                              {product.discount_price.toLocaleString()}
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
                                          {productQuantities[
                                            product.product_id
                                          ] || 1}
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
                                    <span className="detail-label">Price</span>
                                    <span className="detail-value amount">
                                      ₹
                                      {Number(
                                        message.data.product.price_per_unit,
                                      ).toLocaleString()}
                                    </span>
                                  </div>
                                  <div className="cart-detail-item">
                                    <span className="detail-label">Total</span>
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
