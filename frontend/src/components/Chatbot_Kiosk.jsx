import React, { useEffect, useRef, useState } from "react";
import "./ChatBot_Kisok.css";

const KIOSK_API_URL = "http://localhost:8000/api/kiosk/chat";
const CUSTOMER_PROFILE_API_BASE = "http://localhost:8000/api/customer";
const MULTI_PRODUCTS_API_BASE = "http://localhost:8000/api/products/multiple";
const CART_UPDATE_QTY_API = "http://localhost:8000/api/cart/update-quantity";
const CHAT_API_URL = "http://localhost:8000/api/chat";
const FALLBACK_IMAGE_SRC = "/images/abfrl-icon.png";

const TRANSFER_MESSAGE =
  "✅ Great news! Your online session has been seamlessly transferred to our in-store system.\n\n" +
  "Have you already picked up your product from the store? If so, I'd be happy to help you complete the purchase right away. " +
  "Otherwise, feel free to explore more options or let me know how I can assist you today!";

export default function Chatbot_Kiosk({ customerId }) {
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [customerName, setCustomerName] = useState("Guest");
  const [welcomeShown, setWelcomeShown] = useState(false);
  const [paymentModal, setPaymentModal] = useState({
    open: false,
    method: null,
    upiId: "",
    cardName: "",
    cardNumber: "",
    cardExpiry: "",
    cardCvv: "",
  });
  const lastAgentCartFetchAtRef = useRef(0);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const timelineEndRef = useRef(null);
  const [isTimelineOpen, setIsTimelineOpen] = useState(true);
  const [agentTimeline, setAgentTimeline] = useState([]);
  const seenTimelineToolsRef = useRef(new Set());

  const [barcodePanelOpen, setBarcodePanelOpen] = useState(false);
  const [barcodeItemCode, setBarcodeItemCode] = useState("");
  const [barcodeQty, setBarcodeQty] = useState(1);

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

  const formatLocalTime = (date = new Date()) => {
    try {
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch {
      return new Date().toLocaleTimeString();
    }
  };

  const getAgentShortName = (agentLabel) => {
    if (!agentLabel || typeof agentLabel !== "string") return "Agent";
    const first = agentLabel.trim().split(/\s+/)[0];
    return first || "Agent";
  };

  const normalizeTimelineStatus = (status) => {
    const s = (status || "").toString().toLowerCase();
    if (s === "completed" || s === "success" || s === "done")
      return "completed";
    if (s === "error" || s === "failed") return "error";
    if (s === "in_progress" || s === "in-progress" || s === "running")
      return "in-progress";
    return status || "";
  };

  const pushTimelineEntry = ({
    action,
    tool = "system",
    status = "completed",
    logs = [],
  }) => {
    const timestamp = formatLocalTime();
    const key = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

    setAgentTimeline((prev) => [
      ...prev,
      {
        key,
        action,
        tool,
        status: normalizeTimelineStatus(status),
        timestamp,
        logs,
      },
    ]);
  };

  const ensureToolTimelineOnce = ({
    tool,
    action,
    status = "completed",
    logs = [],
  }) => {
    if (!tool) {
      pushTimelineEntry({ action, tool: "system", status, logs });
      return;
    }
    if (seenTimelineToolsRef.current.has(tool)) return;
    seenTimelineToolsRef.current.add(tool);
    pushTimelineEntry({ action, tool, status, logs });
  };

  const addMessage = (message) => {
    setMessages((prev) => [...prev, message]);
  };

  const upsertLatestCartMessage = ({
    cartItems,
    total_amount,
    total_savings,
  }) => {
    setMessages((prev) => {
      const copy = [...prev];
      const lastIdx = [...copy]
        .map((m, i) => ({ m, i }))
        .reverse()
        .find((x) => x.m?.type === "cartItems")?.i;
      const next = {
        type: "cartItems",
        cartItems,
        total_amount,
        total_savings,
        timestamp: new Date(),
      };
      if (lastIdx == null) return [...copy, next];
      copy[lastIdx] = { ...copy[lastIdx], ...next };
      return copy;
    });
  };

  const appendCartMessage = ({ cartItems, total_amount, total_savings }) => {
    setMessages((prev) => [
      ...prev,
      {
        type: "cartItems",
        cartItems,
        total_amount,
        total_savings,
        timestamp: new Date(),
      },
    ]);
  };

  const formatINR = (value) => {
    const n = Number(value);
    if (!Number.isFinite(n)) return "—";
    return `₹${Math.round(n).toLocaleString()}`;
  };

  const normalizeImageSrc = (ref) => {
    if (!ref || typeof ref !== "string") return FALLBACK_IMAGE_SRC;
    const r = ref.trim();
    if (!r) return FALLBACK_IMAGE_SRC;
    if (/^https?:\/\//i.test(r)) return r;
    if (r.startsWith("/")) return r;
    if (r.startsWith("images/")) return `/${r}`;
    return `/images/${r}`;
  };

  const parseMoney = (raw) => {
    if (raw == null) return null;
    const s = String(raw).replace(/,/g, "");
    const m = s.match(/(-?\d+(?:\.\d+)?)/);
    if (!m) return null;
    const n = Number(m[1]);
    return Number.isFinite(n) ? n : null;
  };

  const parseCartSummary = (text) => {
    if (!text) return null;
    if (!/You have the following items in your cart:/i.test(text)) return null;

    const items = [];
    const itemRegex =
      /\n(\d+)\.\s*Order ID:\s*([^\n]+)\n([\s\S]*?)(?=\n\d+\.\s*Order ID:|\n=+\n\*\*Total Amount to Pay:|\n\*\*Total Amount to Pay:|$)/g;
    let match;
    while ((match = itemRegex.exec(text)) !== null) {
      const idx = match[1];
      const orderId = match[2].trim();
      const block = match[3] || "";

      const productName = (
        block.match(/\bProduct:\s*([^\n]+)/i)?.[1] || ""
      ).trim();
      const category = (
        block.match(/\bCategory:\s*([^\n]+)/i)?.[1] || ""
      ).trim();
      const productId = (
        block.match(/\bProduct ID:\s*([^\n]+)/i)?.[1] || ""
      ).trim();
      const storeName = (
        block.match(/\bStore:\s*([^\n]+?)\s*\(ID:/i)?.[1] || ""
      ).trim();
      const storeId = (block.match(/\(ID:\s*([^\)\n]+)\)/i)?.[1] || "").trim();

      const originalPrice =
        parseMoney(block.match(/\bOriginal Price:\s*₹?\s*([^\n]+)/i)?.[1]) ??
        parseMoney(block.match(/\bPrice:\s*₹?\s*([^\n]+)/i)?.[1]);

      const discountPercent =
        parseMoney(block.match(/\bDiscount:\s*([^%\n]+)%/i)?.[1]) ?? 0;

      const discountedPrice =
        parseMoney(
          block.match(/\bDiscounted Price:\s*₹?\s*([^\n\*]+)/i)?.[1],
        ) ?? originalPrice;

      const quantity =
        parseMoney(block.match(/\bQuantity:\s*([^\n]+)/i)?.[1]) ?? 1;

      const itemTotalFromText = parseMoney(
        block.match(/\bItem Total:\s*₹?\s*([^\n]+)/i)?.[1],
      );

      const unitPrice = discountedPrice ?? originalPrice ?? 0;
      const itemTotal =
        itemTotalFromText ?? (Number(unitPrice) || 0) * (Number(quantity) || 1);

      const computedSavings =
        originalPrice != null && discountedPrice != null
          ? Math.max(0, (originalPrice - discountedPrice) * quantity)
          : 0;

      items.push({
        index: idx,
        order_id: orderId,
        product_name: productName || "Item",
        category: category || "",
        product_id: productId || "",
        store_name: storeName || "",
        store_id: storeId || "",
        original_price: originalPrice ?? unitPrice,
        price: unitPrice,
        discount: discountPercent || 0,
        quantity: quantity || 1,
        savings: computedSavings,
        item_total: itemTotal,
        image_reference: null,
      });
    }

    const totalAmount =
      parseMoney(
        text.match(/\*\*Total Amount to Pay:\s*₹\s*([^\*\n]+)\*\*/i)?.[1],
      ) ?? items.reduce((acc, item) => acc + (Number(item.item_total) || 0), 0);

    const totalSavings = items.reduce(
      (acc, item) => acc + (Number(item.savings) || 0),
      0,
    );

    if (items.length === 0) return null;
    return {
      cartItems: items,
      total_amount: totalAmount,
      total_savings: totalSavings,
    };
  };

  const hydrateCartItemsWithProducts = async (cartItems) => {
    const ids = (cartItems || [])
      .map((i) => i.product_id)
      .filter((x) => x && typeof x === "string");
    const uniqueIds = Array.from(new Set(ids));
    if (uniqueIds.length === 0) return;

    // If the cart items are already rich enough (e.g., returned by view_cart_agent),
    // skip fetching product payloads.
    const needsHydration = (cartItems || []).some((item) => {
      if (!item) return false;
      const nameMissing = !item.product_name || item.product_name === "Item";
      const categoryMissing = !item.category;
      const imgMissing = !item.image_reference;
      return nameMissing || categoryMissing || imgMissing;
    });
    if (!needsHydration) return;

    try {
      const res = await fetch(
        `${MULTI_PRODUCTS_API_BASE}/${encodeURIComponent(uniqueIds.join("|"))}`,
      );
      const data = await res.json();
      const products = Array.isArray(data?.products) ? data.products : [];
      const byId = new Map(products.map((p) => [p.product_id, p]));

      setMessages((prev) =>
        prev.map((m) => {
          if (m?.type !== "cartItems" || !Array.isArray(m.cartItems)) return m;
          const updated = m.cartItems.map((item) => {
            const p = byId.get(item.product_id);
            if (!p) return item;
            return {
              ...item,
              product_name:
                item.product_name && item.product_name !== "Item"
                  ? item.product_name
                  : p.product_name,
              category: item.category || p.category,
              image_reference:
                p.image_reference || item.image_reference || null,
            };
          });
          return { ...m, cartItems: updated };
        }),
      );
    } catch {
      // Non-blocking; keep placeholders
    }
  };

  const fetchAgentCart = async ({ throttleMs = 800, raw = false } = {}) => {
    if (!customerId) return null;
    const now = Date.now();
    if (now - lastAgentCartFetchAtRef.current < throttleMs) return null;
    lastAgentCartFetchAtRef.current = now;

    try {
      const res = await fetch(CHAT_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "view cart",
          customer_id: customerId,
        }),
      });
      const data = await res.json();

      if (raw) return data;

      if (data?.cart_items && Array.isArray(data.cart_items)) {
        return {
          cartItems: data.cart_items.map((i) => ({
            ...i,
            image_reference: i.image_reference || null,
          })),
          total_amount: data.total_amount,
          total_savings: data.total_savings,
        };
      }
      return null;
    } catch {
      return null;
    }
  };

  const isCartIntent = (text) => {
    const t = (text || "").toString().trim().toLowerCase();
    if (!t) return false;
    // Keep this tight to avoid accidental matches on unrelated messages.
    return (
      /\b(show|view|open|display|see|check|get)\b[\s\S]*\b(cart|basket)\b/.test(
        t,
      ) ||
      /^cart\b/.test(t) ||
      /\bmy\s+cart\b/.test(t) ||
      /\bcart\s+items\b/.test(t)
    );
  };

  const triggerViewCart = async () => {
    if (!customerId) return;
    setIsLoading(true);
    try {
      pushTimelineEntry({
        action: "User Query",
        tool: "system",
        status: "completed",
      });

      pushTimelineEntry({
        action: "view_cart_agent",
        tool: "view_cart_agent",
        status: "in-progress",
        logs: [
          {
            time: formatLocalTime(),
            text: `system → view_cart_agent: customer_id=${customerId}`,
            variant: "system",
          },
        ],
      });

      const payload = await fetchAgentCart({ throttleMs: 0, raw: true });

      if (payload?.cart_items && Array.isArray(payload.cart_items)) {
        const cart = {
          cartItems: payload.cart_items.map((i) => ({
            ...i,
            image_reference: i.image_reference || null,
          })),
          total_amount: payload.total_amount,
          total_savings: payload.total_savings,
        };

        pushTimelineEntry({
          action: "view_cart_agent",
          tool: "view_cart_agent",
          status: "completed",
          logs: [
            {
              time: formatLocalTime(),
              text: `view_cart_agent → user: items=${cart.cartItems.length}, total=${formatINR(cart.total_amount || 0)}`,
              variant: "system",
            },
          ],
        });

        // For an explicit user request, append a new cart card so it visibly appears.
        appendCartMessage(cart);
        return;
      }

      // Fallback: if /api/chat returns plain text, try to parse it.
      const responseText = payload?.response || payload?.message || "";
      const cartSummary = parseCartSummary(responseText);
      if (cartSummary) {
        pushTimelineEntry({
          action: "view_cart_agent",
          tool: "view_cart_agent",
          status: "completed",
          logs: [
            {
              time: formatLocalTime(),
              text: `view_cart_agent → user: items=${cartSummary.cartItems.length}, total=${formatINR(cartSummary.total_amount || 0)}`,
              variant: "system",
            },
          ],
        });

        // Only show text fallback when we couldn't get structured cart_items.
        // (If cartSummary exists, we still prefer the cart card UI.)
        appendCartMessage(cartSummary);
        hydrateCartItemsWithProducts(cartSummary.cartItems);
        return;
      }

      // If we get here, agent didn't return cart data.
      addMessage({
        type: "ai",
        text: "I couldn’t fetch your cart right now. Please try again in a moment.",
        timestamp: new Date(),
      });
    } catch {
      addMessage({
        type: "ai",
        text: "Sorry, something went wrong while fetching your cart.",
        timestamp: new Date(),
      });
      pushTimelineEntry({
        action: "view_cart_agent",
        tool: "view_cart_agent",
        status: "error",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const parsePaymentSuccess = (text) => {
    if (!text) return null;
    if (!/Payment Successful/i.test(text)) return null;

    const method = (
      text.match(/Payment Method:\s*([^\n]+)/i)?.[1] || ""
    ).trim();
    const totalPaid = parseMoney(
      text.match(/Total Amount Paid:\s*₹\s*([^\n]+)/i)?.[1],
    );
    const itemsPaidBlock =
      text.match(/Items Paid:\s*\n([\s\S]*?)\n\nTotal Amount Paid:/i)?.[1] ||
      "";
    const itemsPaid = itemsPaidBlock
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    return { method, totalPaid, itemsPaid };
  };

  const renderRichText = (text) => {
    if (!text) return null;
    const lines = String(text).split("\n");

    const renderBoldInline = (line, keyPrefix) => {
      const parts = line.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
      return parts.map((part, idx) => {
        const m = part.match(/^\*\*([^*]+)\*\*$/);
        if (m) {
          return <strong key={`${keyPrefix}-b-${idx}`}>{m[1]}</strong>;
        }
        return (
          <React.Fragment key={`${keyPrefix}-t-${idx}`}>{part}</React.Fragment>
        );
      });
    };

    return (
      <>
        {lines.map((line, i) => (
          <React.Fragment key={`l-${i}`}>
            {renderBoldInline(line, `l-${i}`)}
            {i < lines.length - 1 ? <br /> : null}
          </React.Fragment>
        ))}
      </>
    );
  };

  const fetchCustomerName = async () => {
    if (!customerId) return "Guest";
    try {
      // Use same endpoint as main chatbot: /api/customer/{customer_id}/{role_id}
      const res = await fetch(`${CUSTOMER_PROFILE_API_BASE}/${customerId}/1`);
      const data = await res.json();
      return data?.customer_name || "Guest";
    } catch {
      return "Guest";
    }
  };

  const fetchKioskResponseText = async (message) => {
    const res = await fetch(KIOSK_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, customer_id: customerId }),
    });
    const data = await res.json();
    const responseText =
      typeof data === "string" ? data : data.response || data.message || "";
    return responseText;
  };

  const refreshCartSilently = async () => {
    if (!customerId) return;
    try {
      // Prefer structured agent cart (includes product_id + image_reference)
      const agentCart = await fetchAgentCart();
      if (agentCart) {
        upsertLatestCartMessage(agentCart);
        return;
      }

      const responseText = await fetchKioskResponseText("__kiosk_start__");
      const cartSummary = parseCartSummary(responseText);
      if (!cartSummary) return;
      upsertLatestCartMessage(cartSummary);
      hydrateCartItemsWithProducts(cartSummary.cartItems);
    } catch {
      // ignore
    }
  };

  const triggerPaymentFlow = async () => {
    if (isLoading) return;
    await sendToBackend("proceed to payment");
  };

  const handleBarcodeQtyChange = (delta) => {
    setBarcodeQty((prev) => Math.max(1, Number(prev || 1) + delta));
  };

  const submitBarcodeAddToCart = async (event) => {
    event?.preventDefault?.();
    const itemCode = (barcodeItemCode || "").trim();
    const qty = Math.max(1, Number(barcodeQty || 1));
    if (!customerId || !itemCode || isLoading) return;

    setIsLoading(true);
    pushTimelineEntry({
      action: "add_to_cart_agent",
      tool: "add_to_cart_agent",
      status: "in-progress",
      logs: [
        {
          time: formatLocalTime(),
          text: `system → add_to_cart_agent: product_id=${itemCode}, quantity=${qty}`,
          variant: "system",
        },
      ],
    });

    try {
      const res = await fetch(CHAT_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `add to cart product id ${itemCode} quantity ${qty}`,
          customer_id: customerId,
        }),
      });
      const data = await res.json();
      const responseText =
        typeof data === "string" ? data : data.response || data.message || "";

      if (responseText) {
        addMessage({
          type: "ai",
          text: responseText,
          timestamp: new Date(),
        });
      }

      await refreshCartSilently();

      setBarcodePanelOpen(false);
      setBarcodeItemCode("");
      setBarcodeQty(1);
      pushTimelineEntry({
        action: "add_to_cart_agent",
        tool: "add_to_cart_agent",
        status: "completed",
      });
    } catch {
      addMessage({
        type: "ai",
        text: "Sorry, I couldn't add that item. Please try again.",
        timestamp: new Date(),
      });
      pushTimelineEntry({
        action: "add_to_cart_agent",
        tool: "add_to_cart_agent",
        status: "error",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveFromCart = async (orderId, productName) => {
    if (!customerId || !orderId) return;
    setIsLoading(true);
    pushTimelineEntry({
      action: `Remove from Cart${productName ? `: ${productName}` : ""}`,
      tool: "remove_from_cart_agent",
      status: "in-progress",
      logs: [
        {
          time: formatLocalTime(),
          text: `system → remove_from_cart_agent: order_id=${orderId}`,
          variant: "system",
        },
      ],
    });

    try {
      await fetch(CHAT_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `Remove item ${orderId} from cart`,
          customer_id: customerId,
        }),
      });
      await refreshCartSilently();
    } catch {
      addMessage({
        type: "ai",
        text: "Sorry, there was an error removing the item. Please try again.",
        timestamp: new Date(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateCartQuantity = async (
    orderId,
    productName,
    currentQuantity,
    delta,
  ) => {
    if (!orderId) return;
    const newQuantity = Math.max(1, (Number(currentQuantity) || 1) + delta);

    setIsLoading(true);
    pushTimelineEntry({
      action: `Update Quantity${productName ? `: ${productName}` : ""}`,
      tool: "view_cart_agent",
      status: "in-progress",
      logs: [
        {
          time: formatLocalTime(),
          text: `system → cart/update-quantity: order_id=${orderId}, quantity=${newQuantity}`,
          variant: "system",
        },
      ],
    });

    try {
      const res = await fetch(CART_UPDATE_QTY_API, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_id: orderId, quantity: newQuantity }),
      });
      const data = await res.json();
      if (!data?.success) {
        addMessage({
          type: "ai",
          text: data?.error || "Failed to update quantity. Please try again.",
          timestamp: new Date(),
        });
      }

      // Update locally for responsiveness
      setMessages((prev) =>
        prev.map((m) => {
          if (m?.type !== "cartItems" || !Array.isArray(m.cartItems)) return m;
          return {
            ...m,
            cartItems: m.cartItems.map((it) =>
              it.order_id === orderId ? { ...it, quantity: newQuantity } : it,
            ),
          };
        }),
      );

      await refreshCartSilently();
    } catch {
      addMessage({
        type: "ai",
        text: "Sorry, there was an error updating the quantity. Please try again.",
        timestamp: new Date(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const parseOrderSelections = (text) => {
    if (!text || !text.includes("You have the following items in your cart")) {
      return null;
    }

    const orders = [];
    const orderRegex = /\n(\d+)\.\s*Order ID:\s*([^\n]+)/g;
    let match;
    while ((match = orderRegex.exec(text)) !== null) {
      orders.push({
        index: match[1],
        orderId: match[2].trim(),
      });
    }

    return orders.length > 0 ? orders : null;
  };

  const parsePaymentPrompt = (text) => {
    if (!text) return false;
    return /choose payment method|please type your payment method|select a valid payment method/i.test(
      text,
    );
  };

  const parseCompletion = (text) => {
    if (!text) return false;
    return /Payment Successful|Pickup Confirmed|Order Complete|Orders Complete/i.test(
      text,
    );
  };

  const renderResponse = (response) => {
    if (!response) return;

    const responseText =
      typeof response === "string"
        ? response
        : response.response || response.message || "";

    const cartSummary = parseCartSummary(responseText);
    const paymentSuccess = parsePaymentSuccess(responseText);

    let contentHandled = false;

    // Lightweight kiosk timeline mapping (UI parity with main chatbot)
    if (/welcome|kiosk/i.test(responseText)) {
      ensureToolTimelineOnce({
        tool: "system",
        action: "Master Orchestrator",
        status: "completed",
      });
    }

    if (cartSummary) {
      ensureToolTimelineOnce({
        tool: "view_cart_agent",
        action: "View Cart Agent",
        status: "completed",
        logs: [
          {
            time: formatLocalTime(),
            text: `system → view_cart_agent: fetched ${cartSummary.cartItems.length} pending offline orders`,
            variant: "system",
          },
          {
            time: formatLocalTime(),
            text: `view_cart_agent → user: total ${formatINR(cartSummary.total_amount)}`,
            variant: "system",
          },
        ],
      });

      upsertLatestCartMessage(cartSummary);
      hydrateCartItemsWithProducts(cartSummary.cartItems);
      contentHandled = true;
    }

    // Kiosk UX: do not force order-by-order selection here.
    // The cart card itself will ask to proceed with payment.

    if (parsePaymentPrompt(responseText) && !parseCompletion(responseText)) {
      ensureToolTimelineOnce({
        tool: "payment_agent",
        action: "Payment Agent",
        status: "completed",
        logs: [
          {
            time: formatLocalTime(),
            text: "system → payment_agent: requesting payment method",
            variant: "system",
          },
          {
            time: formatLocalTime(),
            text: "payment_agent → user: awaiting method selection",
            variant: "system",
          },
        ],
      });
      addMessage({
        type: "paymentOptions",
        timestamp: new Date(),
      });
      contentHandled = true;
    }

    if (paymentSuccess) {
      const logs = [
        {
          time: formatLocalTime(),
          text: `system → payment_agent: method ${paymentSuccess.method || "selected"}`,
          variant: "system",
        },
      ];
      if (paymentSuccess.totalPaid != null) {
        logs.push({
          time: formatLocalTime(),
          text: `payment_agent → user: payment confirmed (${formatINR(paymentSuccess.totalPaid)})`,
          variant: "system",
        });
      }
      if (paymentSuccess.itemsPaid.length > 0) {
        logs.push({
          time: formatLocalTime(),
          text: `payment_agent: items paid → ${paymentSuccess.itemsPaid.slice(0, 2).join("; ")}${paymentSuccess.itemsPaid.length > 2 ? "…" : ""}`,
          variant: "system",
        });
      }

      ensureToolTimelineOnce({
        tool: "payment_agent",
        action: "Payment Agent",
        status: "completed",
        logs,
      });

      addMessage({
        type: "ai",
        text: responseText,
        timestamp: new Date(),
      });
      contentHandled = true;
    }

    if (parseCompletion(responseText)) {
      ensureToolTimelineOnce({
        tool: "fulfillment_agent",
        action: "Fulfillment Agent",
        status: "completed",
        logs: [
          {
            time: formatLocalTime(),
            text: "system → fulfillment_agent: mark pickup ready",
            variant: "system",
          },
          {
            time: formatLocalTime(),
            text: "fulfillment_agent → user: pickup confirmed",
            variant: "system",
          },
        ],
      });
      addMessage({
        type: "status",
        text: "Session complete. Please proceed to the store counter.",
        timestamp: new Date(),
      });
      contentHandled = true;
    }

    if (!contentHandled && responseText) {
      addMessage({
        type: "ai",
        text: responseText,
        timestamp: new Date(),
      });
    }
  };

  const sendToBackend = async (message) => {
    if (!customerId) return;

    setIsLoading(true);
    try {
      pushTimelineEntry({
        action: "User Query",
        tool: "system",
        status: "completed",
      });

      const res = await fetch(KIOSK_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          customer_id: customerId,
        }),
      });

      const data = await res.json();
      renderResponse(data);
    } catch (error) {
      addMessage({
        type: "ai",
        text: "Sorry, something went wrong. Please ask staff for assistance.",
        timestamp: new Date(),
      });
      pushTimelineEntry({
        action: "System",
        tool: "system",
        status: "error",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const startSession = async () => {
    if (hasStarted || !customerId) return;
    setHasStarted(true);

    // Show welcome + transfer card once per kiosk open.
    if (!welcomeShown) {
      const name = await fetchCustomerName();
      setCustomerName(name);
      addMessage({
        type: "welcomeBack",
        text: `Welcome back, ${name}! 👋`,
        timestamp: new Date(),
      });
      addMessage({
        type: "transfer",
        text: TRANSFER_MESSAGE,
        timestamp: new Date(),
      });
      setWelcomeShown(true);
    }

    // Prime kiosk state for payment flow
    await sendToBackend("__kiosk_start__");

    // Also hydrate cart via agent payload for images + product_id
    const agentCart = await fetchAgentCart({ throttleMs: 0 });
    if (agentCart) {
      upsertLatestCartMessage(agentCart);
    }
  };

  useEffect(() => {
    if (isOpen) {
      startSession();
    }
  }, [isOpen, customerId]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const messageText = inputValue.trim();
    setInputValue("");
    addMessage({
      type: "user",
      text: messageText,
      timestamp: new Date(),
    });

    // Important: cart should always show, even if kiosk flow is waiting for order selection.
    if (isCartIntent(messageText)) {
      await triggerViewCart();
      return;
    }

    await sendToBackend(messageText);
  };

  const handleQuickReply = async (text) => {
    if (isLoading) return;
    addMessage({
      type: "user",
      text,
      timestamp: new Date(),
    });
    await sendToBackend(text);
  };

  const sendPaymentMethod = async ({ label, value }) => {
    if (isLoading) return;
    addMessage({
      type: "user",
      text: label,
      timestamp: new Date(),
    });
    await sendToBackend(value);
  };

  const openPaymentModal = (method) => {
    setPaymentModal((prev) => ({
      ...prev,
      open: true,
      method,
      upiId: "",
      cardName: "",
      cardNumber: "",
      cardExpiry: "",
      cardCvv: "",
    }));
  };

  const closePaymentModal = () => {
    setPaymentModal((prev) => ({
      ...prev,
      open: false,
      method: null,
    }));
  };

  const canSubmitPaymentModal = () => {
    if (!paymentModal.open || !paymentModal.method) return false;
    if (paymentModal.method === "upi") {
      return paymentModal.upiId.trim().length > 0;
    }
    if (
      paymentModal.method === "credit card" ||
      paymentModal.method === "debit card"
    ) {
      const digits = paymentModal.cardNumber.replace(/\D/g, "");
      return (
        paymentModal.cardName.trim().length > 0 &&
        digits.length >= 12 &&
        paymentModal.cardExpiry.trim().length >= 4 &&
        paymentModal.cardCvv.replace(/\D/g, "").length >= 3
      );
    }
    return false;
  };

  const submitPaymentModal = async () => {
    if (!paymentModal.method) return;
    const method = paymentModal.method;
    closePaymentModal();

    if (method === "upi") {
      await sendPaymentMethod({ label: "UPI", value: "upi" });
      return;
    }
    if (method === "credit card") {
      await sendPaymentMethod({ label: "Credit Card", value: "credit card" });
      return;
    }
    if (method === "debit card") {
      await sendPaymentMethod({ label: "Debit Card", value: "debit card" });
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <button className="kiosk-launch-button" onClick={() => setIsOpen(true)}>
        Open Kiosk Assistant
      </button>
    );
  }

  return (
    <div className="kiosk-window">
      <div className="kiosk-container">
        {/* Hamburger Menu Button (Timeline) */}
        <button
          className={`kiosk-timeline-hamburger ${isTimelineOpen ? "open" : ""}`}
          onClick={() => setIsTimelineOpen(!isTimelineOpen)}
          title={isTimelineOpen ? "Hide Timeline" : "Show Timeline"}
        >
          <span className="kiosk-hamburger-line"></span>
          <span className="kiosk-hamburger-line"></span>
          <span className="kiosk-hamburger-line"></span>
        </button>

        {/* Left Panel - Timeline (Kiosk parity) */}
        <div
          className={`kiosk-timeline-panel ${isTimelineOpen ? "" : "collapsed"}`}
        >
          <div className="kiosk-timeline-header">
            <span className="kiosk-timeline-icon">⚡</span>
            <div className="kiosk-timeline-header-badges">
              <span className="kiosk-web-badge">Kiosk</span>
              <span className="kiosk-status-badge">
                <span className="kiosk-status-label">Status: </span>
                <span className="kiosk-status-value">
                  {isLoading ? "Processing" : "Active"}
                </span>
              </span>
            </div>
            <button
              className="kiosk-timeline-close-btn"
              onClick={() => setIsTimelineOpen(false)}
            >
              ✕
            </button>
          </div>
          <div className="kiosk-timeline-subtitle">Live Orchestration Log</div>

          <div className="kiosk-timeline-content">
            {agentTimeline.length === 0 ? (
              <div className="kiosk-timeline-empty">
                Waiting for agent activity...
              </div>
            ) : (
              agentTimeline.map((entry, index) => (
                <div
                  key={entry.key || index}
                  className={`kiosk-timeline-entry ${entry.status || ""}`}
                >
                  <div className="kiosk-timeline-dot-container">
                    <div className="kiosk-timeline-dot"></div>
                    {index < agentTimeline.length - 1 && (
                      <div className="kiosk-timeline-line"></div>
                    )}
                  </div>
                  <div className="kiosk-timeline-card">
                    <div className="kiosk-timeline-card-header">
                      <div className="kiosk-timeline-card-title">
                        <div className="kiosk-timeline-action">
                          {entry.action}
                        </div>
                        {entry.status && entry.action !== "User Query" && (
                          <span
                            className={`kiosk-timeline-status-pill ${entry.status || ""}`}
                          >
                            {entry.status === "completed"
                              ? "Completed"
                              : entry.status === "error"
                                ? "Error"
                                : "In Progress"}
                          </span>
                        )}
                      </div>
                      <span className="kiosk-agent-badge">
                        {entry.tool ? entry.tool : "system"}
                      </span>
                    </div>
                    <div className="kiosk-timeline-agent-type">
                      Master Orchestrator
                    </div>
                    <div className="kiosk-timeline-timestamps">
                      {(entry.logs && entry.logs.length > 0
                        ? entry.logs
                        : [
                            {
                              time: entry.timestamp,
                              text: `System → ${getAgentShortName(entry.action)}`,
                              variant: "system",
                            },
                            {
                              time: entry.timestamp,
                              text: `${getAgentShortName(entry.action)} → User`,
                              variant: "system",
                            },
                          ]
                      ).map((log, i) => (
                        <div key={i} className="kiosk-timeline-time-entry">
                          <span className="kiosk-timeline-time">
                            {log.time}
                          </span>
                          <span
                            className={`kiosk-timeline-flow ${log.variant === "system" ? "system" : ""}`}
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
        <div className="kiosk-chat-interface-panel">
          <div className="kiosk-chat-header">
            <div className="kiosk-header-content">
              <div className="kiosk-bot-icon-wrapper">
                <span className="kiosk-bot-icon">🏪</span>
              </div>
              <div className="kiosk-header-text">
                <h3>Store Kiosk Assistant</h3>
                <p>In-store checkout support</p>
              </div>
            </div>
            <div className="kiosk-header-actions">
              <div className="kiosk-action-tools">
                <span className="kiosk-action-tools-label">Action Tools</span>
                <button
                  className="kiosk-action-tools-btn primary"
                  onClick={triggerPaymentFlow}
                  disabled={isLoading}
                  type="button"
                >
                  Go For Payment
                </button>
                <button
                  className="kiosk-action-tools-btn"
                  onClick={() => setBarcodePanelOpen((prev) => !prev)}
                  disabled={isLoading}
                  type="button"
                >
                  Bar Code ID
                </button>

                {barcodePanelOpen && (
                  <form
                    className="kiosk-barcode-panel"
                    onSubmit={submitBarcodeAddToCart}
                  >
                    <div className="kiosk-barcode-field">
                      <label className="kiosk-barcode-label">Item Code</label>
                      <input
                        className="kiosk-barcode-input"
                        type="text"
                        value={barcodeItemCode}
                        onChange={(e) => setBarcodeItemCode(e.target.value)}
                        placeholder="e.g. PRD033"
                        disabled={isLoading}
                      />
                    </div>

                    <div className="kiosk-barcode-field">
                      <label className="kiosk-barcode-label">Quantity</label>
                      <div className="kiosk-barcode-qty-controls">
                        <button
                          type="button"
                          className="kiosk-barcode-qty-btn"
                          onClick={() => handleBarcodeQtyChange(-1)}
                          disabled={isLoading || barcodeQty <= 1}
                        >
                          −
                        </button>
                        <span className="kiosk-barcode-qty-value">
                          {barcodeQty}
                        </span>
                        <button
                          type="button"
                          className="kiosk-barcode-qty-btn"
                          onClick={() => handleBarcodeQtyChange(1)}
                          disabled={isLoading}
                        >
                          +
                        </button>
                      </div>
                    </div>

                    <div className="kiosk-barcode-actions">
                      <button
                        type="submit"
                        className="kiosk-barcode-submit"
                        disabled={isLoading || !barcodeItemCode.trim()}
                      >
                        Add To Cart
                      </button>
                    </div>
                  </form>
                )}
              </div>
              <button
                className="kiosk-close-btn"
                onClick={() => setIsOpen(false)}
              >
                ✕
              </button>
            </div>
          </div>

          <div className="kiosk-chat-messages" ref={chatContainerRef}>
            {messages.map((message, index) => {
              if (message.type === "welcomeBack") {
                return (
                  <div
                    key={`wb-${index}`}
                    className="kiosk-message kiosk-ai-message"
                  >
                    <div className="kiosk-message-content kiosk-welcome-card">
                      <div className="kiosk-welcome-title">{message.text}</div>
                      <div className="kiosk-welcome-subtitle">
                        Your in-store assistant is ready.
                      </div>
                    </div>
                  </div>
                );
              }

              if (message.type === "transfer") {
                return (
                  <div
                    key={`tr-${index}`}
                    className="kiosk-message kiosk-ai-message"
                  >
                    <div className="kiosk-message-content kiosk-transfer-card">
                      <div className="kiosk-transfer-text">
                        {renderRichText(message.text)}
                      </div>
                    </div>
                  </div>
                );
              }

              if (
                message.type === "cartItems" &&
                Array.isArray(message.cartItems)
              ) {
                return (
                  <div
                    key={`cart-${index}`}
                    className="kiosk-message kiosk-ai-message"
                  >
                    <div className="kiosk-message-content kiosk-cart-items-container">
                      <div className="kiosk-cart-header-section">
                        <span className="kiosk-cart-icon">🛒</span>
                        <h4>Your Cart ({message.cartItems.length} items)</h4>
                      </div>

                      <div className="kiosk-cart-grid">
                        {message.cartItems.map((item) => {
                          const originalPrice =
                            item.original_price ?? item.price;
                          const discountPrice = item.price ?? originalPrice;
                          const discount = item.discount || 0;
                          const hasDiscount =
                            discount > 0 &&
                            originalPrice != null &&
                            discountPrice != null &&
                            Number(originalPrice) !== Number(discountPrice);
                          const quantity = item.quantity || 1;
                          const totalAmount =
                            (Number(discountPrice) || 0) * quantity;

                          return (
                            <div
                              key={
                                item.order_id ||
                                `${item.product_id}-${Math.random()}`
                              }
                              className="kiosk-cart-item-card"
                            >
                              <div className="kiosk-cart-item-top">
                                <div className="kiosk-cart-image-wrapper">
                                  <img
                                    src={normalizeImageSrc(
                                      item.image_reference,
                                    )}
                                    alt={item.product_name}
                                    className="kiosk-cart-image"
                                    onError={(e) => {
                                      e.currentTarget.onerror = null;
                                      e.currentTarget.src = FALLBACK_IMAGE_SRC;
                                    }}
                                  />
                                  {hasDiscount && (
                                    <span className="kiosk-cart-badge">
                                      {discount}% OFF
                                    </span>
                                  )}
                                </div>
                                <div className="kiosk-cart-item-info">
                                  <div className="kiosk-cart-item-name">
                                    {item.product_name}
                                  </div>
                                  {item.category ? (
                                    <div className="kiosk-cart-item-meta">
                                      Category: {item.category}
                                    </div>
                                  ) : null}
                                  {item.store_name || item.store_id ? (
                                    <div className="kiosk-cart-item-meta">
                                      Store: {item.store_name || item.store_id}
                                    </div>
                                  ) : null}

                                  <div className="kiosk-cart-pricing">
                                    {hasDiscount ? (
                                      <>
                                        <span className="kiosk-cart-original">
                                          {formatINR(originalPrice)}
                                        </span>
                                        <span className="kiosk-cart-price">
                                          {formatINR(discountPrice)}
                                        </span>
                                      </>
                                    ) : (
                                      <span className="kiosk-cart-price">
                                        {formatINR(discountPrice)}
                                      </span>
                                    )}
                                  </div>

                                  <div className="kiosk-cart-qty-total">
                                    <div className="kiosk-cart-qty-controls">
                                      <span className="kiosk-cart-qty-label">
                                        Qty:
                                      </span>
                                      <button
                                        className="kiosk-cart-qty-btn"
                                        onClick={() =>
                                          handleUpdateCartQuantity(
                                            item.order_id,
                                            item.product_name,
                                            quantity,
                                            -1,
                                          )
                                        }
                                        disabled={isLoading || quantity <= 1}
                                        title="Decrease"
                                      >
                                        −
                                      </button>
                                      <span className="kiosk-cart-qty-value">
                                        {quantity}
                                      </span>
                                      <button
                                        className="kiosk-cart-qty-btn"
                                        onClick={() =>
                                          handleUpdateCartQuantity(
                                            item.order_id,
                                            item.product_name,
                                            quantity,
                                            1,
                                          )
                                        }
                                        disabled={isLoading}
                                        title="Increase"
                                      >
                                        +
                                      </button>
                                    </div>
                                    <div className="kiosk-cart-total">
                                      Total: {formatINR(totalAmount)}
                                    </div>
                                  </div>

                                  <div className="kiosk-cart-actions-row">
                                    <button
                                      className="kiosk-cart-remove-btn"
                                      onClick={() =>
                                        handleRemoveFromCart(
                                          item.order_id,
                                          item.product_name,
                                        )
                                      }
                                      disabled={isLoading}
                                      title="Remove from cart"
                                    >
                                      🗑 Remove
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      <div className="kiosk-cart-summary">
                        <div className="kiosk-cart-summary-row">
                          <span>Total amount</span>
                          <strong>
                            {formatINR(message.total_amount || 0)}
                          </strong>
                        </div>
                        {Number(message.total_savings) > 0 ? (
                          <div className="kiosk-cart-summary-row savings">
                            <span>Total savings</span>
                            <strong>{formatINR(message.total_savings)}</strong>
                          </div>
                        ) : null}
                        <div className="kiosk-cart-summary-hint">
                          Would you like to proceed with payment?
                        </div>

                        <div className="kiosk-cart-cta-row">
                          <button
                            className="kiosk-cart-cta primary"
                            onClick={() =>
                              handleQuickReply("proceed to payment")
                            }
                            disabled={isLoading}
                          >
                            Proceed to payment
                          </button>
                          <button
                            className="kiosk-cart-cta"
                            onClick={() => handleQuickReply("no")}
                            disabled={isLoading}
                          >
                            Not now
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              }

              if (message.type === "paymentOptions") {
                return (
                  <div
                    key={`payment-${index}`}
                    className="kiosk-message kiosk-ai-message"
                  >
                    <div className="kiosk-message-content kiosk-card">
                      <div className="kiosk-card-header">
                        Choose payment method
                      </div>
                      <div className="kiosk-card-body kiosk-payment-grid">
                        {[
                          { label: "UPI", value: "upi" },
                          { label: "Credit Card", value: "credit card" },
                          { label: "Debit Card", value: "debit card" },
                          {
                            label: "Cash on Delivery",
                            value: "cash on delivery",
                          },
                        ].map((method) => (
                          <button
                            key={method.value}
                            className="kiosk-payment-btn"
                            onClick={() => {
                              if (method.value === "cash on delivery") {
                                sendPaymentMethod({
                                  label: method.label,
                                  value: method.value,
                                });
                                return;
                              }
                              openPaymentModal(method.value);
                            }}
                          >
                            {method.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              }

              return (
                <div
                  key={index}
                  className={`kiosk-message ${message.type === "user" ? "kiosk-user-message" : "kiosk-ai-message"}`}
                >
                  <div className="kiosk-message-content">
                    <div className="kiosk-message-text">
                      {renderRichText(message.text)}
                    </div>
                    <div className="kiosk-message-time">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              );
            })}
            {isLoading && (
              <div className="kiosk-message kiosk-ai-message">
                <div className="kiosk-message-content">
                  <div className="kiosk-typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="kiosk-chat-input-container">
            <div className="kiosk-input-wrapper">
              <input
                type="text"
                className="kiosk-chat-input"
                placeholder="Type a response or choose an option..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
              />
              <button className="kiosk-mic-btn" title="Voice input" disabled>
                🎤
              </button>
              <button
                className="kiosk-send-btn"
                onClick={handleSend}
                disabled={!inputValue.trim() || isLoading}
                title="Send"
              >
                ➤
              </button>
            </div>
          </div>

          {paymentModal.open ? (
            <div
              className="kiosk-payment-modal-overlay"
              onClick={(e) => {
                if (e.target === e.currentTarget) closePaymentModal();
              }}
              role="dialog"
              aria-modal="true"
              aria-label="Payment details"
            >
              <div className="kiosk-payment-modal">
                <div className="kiosk-payment-modal-header">
                  <div className="kiosk-payment-modal-title">
                    {paymentModal.method === "upi"
                      ? "Enter your UPI ID to complete payment"
                      : paymentModal.method === "credit card"
                        ? "Enter card details to complete payment"
                        : "Enter card details to complete payment"}
                  </div>
                  <button
                    type="button"
                    className="kiosk-payment-modal-close"
                    onClick={closePaymentModal}
                    aria-label="Close"
                  >
                    ✕
                  </button>
                </div>

                <div className="kiosk-payment-modal-body">
                  <div className="kiosk-payment-secure-banner">
                    🔒 Secured by 256-bit SSL Encryption
                  </div>

                  {paymentModal.method === "upi" ? (
                    <div className="kiosk-payment-form">
                      <label className="kiosk-payment-label" htmlFor="upiId">
                        UPI ID
                      </label>
                      <input
                        id="upiId"
                        className="kiosk-payment-input"
                        placeholder="yourname@upi"
                        value={paymentModal.upiId}
                        onChange={(e) =>
                          setPaymentModal((prev) => ({
                            ...prev,
                            upiId: e.target.value,
                          }))
                        }
                        disabled={isLoading}
                        autoFocus
                      />
                      <div className="kiosk-payment-hint">
                        Enter your UPI ID (e.g., user@okaxis)
                      </div>
                    </div>
                  ) : (
                    <div className="kiosk-payment-form">
                      <label className="kiosk-payment-label" htmlFor="cardName">
                        Name on card
                      </label>
                      <input
                        id="cardName"
                        className="kiosk-payment-input"
                        placeholder="Your name"
                        value={paymentModal.cardName}
                        onChange={(e) =>
                          setPaymentModal((prev) => ({
                            ...prev,
                            cardName: e.target.value,
                          }))
                        }
                        disabled={isLoading}
                        autoFocus
                      />

                      <label
                        className="kiosk-payment-label"
                        htmlFor="cardNumber"
                      >
                        Card number
                      </label>
                      <input
                        id="cardNumber"
                        className="kiosk-payment-input"
                        placeholder="1234 5678 9012 3456"
                        inputMode="numeric"
                        value={paymentModal.cardNumber}
                        onChange={(e) =>
                          setPaymentModal((prev) => ({
                            ...prev,
                            cardNumber: e.target.value,
                          }))
                        }
                        disabled={isLoading}
                      />

                      <div className="kiosk-payment-row">
                        <div>
                          <label
                            className="kiosk-payment-label"
                            htmlFor="cardExpiry"
                          >
                            Expiry
                          </label>
                          <input
                            id="cardExpiry"
                            className="kiosk-payment-input"
                            placeholder="MM/YY"
                            inputMode="numeric"
                            value={paymentModal.cardExpiry}
                            onChange={(e) =>
                              setPaymentModal((prev) => ({
                                ...prev,
                                cardExpiry: e.target.value,
                              }))
                            }
                            disabled={isLoading}
                          />
                        </div>
                        <div>
                          <label
                            className="kiosk-payment-label"
                            htmlFor="cardCvv"
                          >
                            CVV
                          </label>
                          <input
                            id="cardCvv"
                            className="kiosk-payment-input"
                            placeholder="123"
                            inputMode="numeric"
                            value={paymentModal.cardCvv}
                            onChange={(e) =>
                              setPaymentModal((prev) => ({
                                ...prev,
                                cardCvv: e.target.value,
                              }))
                            }
                            disabled={isLoading}
                          />
                        </div>
                      </div>
                      <div className="kiosk-payment-hint">
                        Use test details for demo only.
                      </div>
                    </div>
                  )}

                  <button
                    type="button"
                    className="kiosk-payment-submit"
                    onClick={submitPaymentModal}
                    disabled={!canSubmitPaymentModal() || isLoading}
                  >
                    Pay securely
                  </button>

                  <div className="kiosk-payment-footer">
                    ✓ Safe & secure · ✓ Instant payment
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
