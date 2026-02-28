import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./ChatBot_Kisok.css";

const KIOSK_API_URL = "http://localhost:8000/api/kiosk/chat";
const CUSTOMER_PROFILE_API_BASE = "http://localhost:8000/api/customer";
const MULTI_PRODUCTS_API_BASE = "http://localhost:8000/api/products/multiple";
const CART_UPDATE_QTY_API = "http://localhost:8000/api/cart/update-quantity";
const CART_UPDATE_SIZE_API = "http://localhost:8000/api/cart/update-size";
const CHAT_API_URL = "http://localhost:8000/api/chat";
const WS_CHAT_URL = "ws://localhost:8000/ws/chat";
const FALLBACK_IMAGE_SRC = "/images/abfrl-icon.png";

const TRANSFER_MESSAGE =
  "✅ Great news! Your online session has been seamlessly transferred to our in-store system.\n\n" +
  "Have you already picked up your product from the store? If so, I'd be happy to help you complete the purchase right away. " +
  "Otherwise, feel free to explore more options or let me know how I can assist you today!";

export default function Chatbot_Kiosk({ customerId }) {
  const navigate = useNavigate();
  const location = useLocation();
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

  const isOpenRef = useRef(true);
  const wsRef = useRef(null);
  const wsReadyRef = useRef(false);
  const wsPendingRef = useRef(new Map());
  const wsReconnectRef = useRef({ timer: null, attempt: 0 });
  const wsToolInstanceRef = useRef(new Map());
  const wsToolCountRef = useRef(new Map());

  const [barcodePanelOpen, setBarcodePanelOpen] = useState(false);
  const [isQuickActionsOpen, setIsQuickActionsOpen] = useState(false);
  const [barcodeItemCode, setBarcodeItemCode] = useState("");
  const [barcodeQty, setBarcodeQty] = useState(1);
  const [barcodeSize, setBarcodeSize] = useState("");

  const handleCloseChatbot = () => {
    setIsOpen(false);
    if (location.pathname === "/store/kiosk") {
      // Restore store keeper session that was saved before entering kiosk
      const skId = localStorage.getItem("skBackup_customerId");
      const skRole = localStorage.getItem("skBackup_userRole");
      const skData = localStorage.getItem("skBackup_storeKeeperData");
      if (skId && skRole) {
        localStorage.setItem("loggedInCustomerId", skId);
        localStorage.setItem("userRole", skRole);
        if (skData) localStorage.setItem("storeKeeperData", skData);
      }
      localStorage.removeItem("skBackup_customerId");
      localStorage.removeItem("skBackup_userRole");
      localStorage.removeItem("skBackup_storeKeeperData");
      localStorage.removeItem("kioskStoreId");
      navigate("/store");
    } else {
      navigate("/");
    }
  };

  useEffect(() => {
    if (!isOpen) {
      setIsQuickActionsOpen(false);
      setBarcodePanelOpen(false);
    }
  }, [isOpen]);

  useEffect(() => {
    if (barcodePanelOpen) setIsQuickActionsOpen(false);
  }, [barcodePanelOpen]);

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
    isOpenRef.current = Boolean(isOpen);
  }, [isOpen]);

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

  const parseWsLogLine = (raw) => {
    const text = (raw || "").toString().trim();
    if (!text) return { time: formatLocalTime(), text: "" };
    const maybeTime = text.slice(0, 8);
    if (/^\d{2}:\d{2}:\d{2}$/.test(maybeTime) && text.length > 9) {
      return { time: maybeTime, text: text.slice(9) };
    }
    return { time: formatLocalTime(), text };
  };

  const isWsUsable = () => {
    const ws = wsRef.current;
    return Boolean(wsReadyRef.current && ws && ws.readyState === 1);
  };

  const timelineKeyFor = (requestId, tool) => {
    return `${requestId || "run"}:${tool || "system"}`;
  };

  const timelineStartFromWs = ({ request_id, tool, agent, status }) => {
    const toolName = tool || "system";
    const actionLabel = agent || toolName || "Agent";
    const baseKey = timelineKeyFor(request_id, toolName);
    const nextCount = (wsToolCountRef.current.get(baseKey) || 0) + 1;
    wsToolCountRef.current.set(baseKey, nextCount);
    const entryKey = `${baseKey}:${nextCount}:${Date.now()}-${Math.random().toString(16).slice(2)}`;
    wsToolInstanceRef.current.set(baseKey, entryKey);

    setAgentTimeline((prev) => [
      ...prev,
      {
        key: entryKey,
        action: actionLabel,
        tool: toolName,
        status: normalizeTimelineStatus(status || "in-progress"),
        timestamp: formatLocalTime(),
        logs: [],
      },
    ]);
  };

  const timelineLogFromWs = ({ request_id, tool, text }) => {
    const toolName = tool || "system";
    const baseKey = timelineKeyFor(request_id, toolName);
    const entryKey = wsToolInstanceRef.current.get(baseKey);
    if (!entryKey) return;
    const { time, text: message } = parseWsLogLine(text);
    if (!message) return;

    setAgentTimeline((prev) =>
      prev.map((entry) => {
        if (entry.key !== entryKey) return entry;
        const nextLogs = Array.isArray(entry.logs) ? [...entry.logs] : [];
        nextLogs.push({ time, text: message, variant: "system" });
        return { ...entry, logs: nextLogs };
      }),
    );
  };

  const timelineEndFromWs = ({ request_id, tool, status }) => {
    const toolName = tool || "system";
    const baseKey = timelineKeyFor(request_id, toolName);
    const entryKey = wsToolInstanceRef.current.get(baseKey);
    if (!entryKey) return;

    setAgentTimeline((prev) =>
      prev.map((entry) =>
        entry.key === entryKey
          ? { ...entry, status: normalizeTimelineStatus(status || "completed") }
          : entry,
      ),
    );
  };

  const connectWsIfNeeded = () => {
    const existing = wsRef.current;
    if (existing && (existing.readyState === 0 || existing.readyState === 1)) {
      return;
    }

    try {
      const ws = new WebSocket(WS_CHAT_URL);
      wsRef.current = ws;
      wsReadyRef.current = false;

      ws.onopen = () => {
        wsReadyRef.current = true;
        wsReconnectRef.current.attempt = 0;
      };

      ws.onmessage = (event) => {
        let payload;
        try {
          payload = JSON.parse(event.data);
        } catch {
          return;
        }

        const type = payload?.type;
        if (type === "timeline_start") return timelineStartFromWs(payload);
        if (type === "timeline_log") return timelineLogFromWs(payload);
        if (type === "timeline_end") return timelineEndFromWs(payload);

        if (type === "final_response") {
          const requestId = payload?.request_id;
          const pending = requestId
            ? wsPendingRef.current.get(requestId)
            : null;
          if (!pending) return;
          wsPendingRef.current.delete(requestId);
          if (pending.timeoutId) clearTimeout(pending.timeoutId);
          pending.resolve(payload?.data);
          return;
        }

        if (type === "error") {
          const requestId = payload?.request_id;
          const pending = requestId
            ? wsPendingRef.current.get(requestId)
            : null;
          if (pending) {
            wsPendingRef.current.delete(requestId);
            if (pending.timeoutId) clearTimeout(pending.timeoutId);
            pending.reject(new Error(payload?.message || "WebSocket error"));
          }
        }
      };

      ws.onclose = () => {
        wsReadyRef.current = false;
        if (!isOpenRef.current) return;
        if (wsReconnectRef.current.timer) return;
        const attempt = (wsReconnectRef.current.attempt || 0) + 1;
        wsReconnectRef.current.attempt = attempt;
        const delay = Math.min(10000, 750 * attempt);
        wsReconnectRef.current.timer = window.setTimeout(() => {
          wsReconnectRef.current.timer = null;
          connectWsIfNeeded();
        }, delay);
      };
    } catch {
      // ignore (HTTP fallback still works)
    }
  };

  const closeWs = () => {
    try {
      if (wsReconnectRef.current.timer) {
        clearTimeout(wsReconnectRef.current.timer);
        wsReconnectRef.current.timer = null;
      }
      wsReconnectRef.current.attempt = 0;
      wsReadyRef.current = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
    } catch {
      // ignore
    } finally {
      wsRef.current = null;
    }
  };

  useEffect(() => {
    if (isOpen && customerId) {
      connectWsIfNeeded();
      return () => closeWs();
    }
    closeWs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, customerId]);

  const sendAgentMessage = async (message) => {
    if (!customerId) return null;

    connectWsIfNeeded();
    if (isWsUsable()) {
      const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      const ws = wsRef.current;
      return await new Promise((resolve, reject) => {
        const timeoutId = window.setTimeout(() => {
          const pending = wsPendingRef.current.get(requestId);
          if (!pending) return;
          wsPendingRef.current.delete(requestId);
          reject(new Error("Timed out waiting for response"));
        }, 30000);

        wsPendingRef.current.set(requestId, { resolve, reject, timeoutId });
        try {
          ws.send(
            JSON.stringify({
              request_id: requestId,
              customer_id: customerId,
              message,
            }),
          );
        } catch (e) {
          wsPendingRef.current.delete(requestId);
          clearTimeout(timeoutId);
          reject(e);
        }
      });
    }

    const res = await fetch(CHAT_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, customer_id: customerId }),
    });
    return await res.json();
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

  const getProductCategoryText = (product) => {
    if (!product) return "";
    const category =
      product.category ||
      product.product_category ||
      product.productCategory ||
      product.product?.category ||
      product.product?.product_category ||
      "";
    return String(category).trim();
  };

  const getProductNameText = (product) => {
    if (!product) return "";
    const name =
      product.product_name ||
      product.name ||
      product.title ||
      product.productName ||
      "";
    return String(name).trim();
  };

  const isAccessories = (product) => {
    const category = getProductCategoryText(product);
    const name = getProductNameText(product);
    const base = category || name;
    const c = String(base).trim().toLowerCase();

    return (
      c.includes("accessories") ||
      c.includes("accessory") ||
      c.includes("belt") ||
      c.includes("perfume") ||
      c.includes("Perfume") ||
      c.includes("wallet") ||
      c.includes("jewellery") ||
      c.includes("jewelry") ||
      c.includes("earring") ||
      c.includes("necklace") ||
      c.includes("bracelet") ||
      c.includes("bangle") ||
      c.includes("watch") ||
      c.includes("watches") ||
      c.includes("ring") ||
      c.includes("costume jewellery") ||
      c.includes("costume jewelry")
    );
  };

  const isFootwear = (product) => {
    const category = getProductCategoryText(product);
    const name = getProductNameText(product);
    const base = category || name;
    const c = String(base).trim().toLowerCase();
    return (
      c.includes("footwear") ||
      c.includes("shoes") ||
      c.includes("shoe") ||
      c.includes("derby") ||
      c.includes("loafer") ||
      c.includes("sneaker") ||
      c.includes("boot") ||
      c.includes("sandal") ||
      c.includes("slipper") ||
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
      const parsedSize = (block.match(/\bSize:\s*([^\n]+)/i)?.[1] || "").trim();
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
        size: parsedSize || "",
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

      // Use kiosk endpoint which filters by channel='offline' + store_id.
      // Do NOT use sendAgentMessage/view_cart_agent — no channel/store filter.
      const responseText = await fetchKioskResponseText("__kiosk_start__");
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
    const kioskStoreId = localStorage.getItem("kioskStoreId") || "";
    const res = await fetch(KIOSK_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        customer_id: customerId,
        store_id: kioskStoreId,
      }),
    });
    const data = await res.json();
    const responseText =
      typeof data === "string" ? data : data.response || data.message || "";
    return responseText;
  };

  const refreshCartSilently = async () => {
    if (!customerId) return;
    try {
      // Use ONLY the kiosk endpoint which filters by channel='offline' + store_id.
      // Do NOT use fetchAgentCart — it hits view_cart_agent which returns ALL
      // pending items regardless of channel or store.
      const responseText = await fetchKioskResponseText("__kiosk_start__");
      const cartSummary = parseCartSummary(responseText);
      if (!cartSummary || cartSummary.cartItems.length === 0) {
        upsertLatestCartMessage({
          cartItems: [],
          total_amount: 0,
          total_savings: 0,
        });
        return;
      }
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
    const size = (barcodeSize || "").trim();
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
      // Handle barcode add-to-cart internally: update cart UI without showing
      // the agent's "Added to cart" message in the chat.
      const sizeSuffix = size ? ` size ${size}` : "";
      const responseText = await fetchKioskResponseText(
        `add to cart product id ${itemCode} quantity ${qty}${sizeSuffix}`,
      );

      if (
        typeof responseText === "string" &&
        responseText.trim().startsWith("❌")
      ) {
        throw new Error(responseText);
      }

      await refreshCartSilently();

      setBarcodePanelOpen(false);
      setBarcodeItemCode("");
      setBarcodeQty(1);
      setBarcodeSize("");
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

  const handleSwitchToOnline = async () => {
    if (!customerId) {
      alert("Customer ID is required");
      return;
    }

    const confirmed = window.confirm(
      "Switch your in-store cart to online? You can pay for these items later from home.",
    );
    if (!confirmed) return;

    setIsLoading(true);
    pushTimelineEntry({
      action: "Switch Cart to Online",
      tool: "switch_channel_instore_to_online",
      status: "in-progress",
      logs: [
        {
          time: formatLocalTime(),
          text: `system → Switching offline cart to online for customer ${customerId}`,
          variant: "system",
        },
      ],
    });

    try {
      const response = await fetch(
        "http://localhost:8000/api/cart/switch-to-online",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            customer_id: customerId,
            store_id: localStorage.getItem("kioskStoreId") || "",
          }),
        },
      );

      const data = await response.json();
      if (data.success) {
        const itemCount = data.items_switched || 0;
        addMessage({
          type: "switchSuccess",
          timestamp: new Date(),
        });
        pushTimelineEntry({
          action: "Switch Cart to Online",
          tool: "switch_channel_instore_to_online",
          status: "completed",
        });
        // Clear the in-store cart display directly since all offline items
        // have been moved to online channel and should no longer appear.
        upsertLatestCartMessage({
          cartItems: [],
          total_amount: 0,
          total_savings: 0,
        });
      } else {
        addMessage({
          type: "ai",
          text: data.error || "❌ Failed to switch cart to online.",
          timestamp: new Date(),
        });
        pushTimelineEntry({
          action: "Switch Cart to Online",
          tool: "switch_channel_instore_to_online",
          status: "error",
        });
      }
    } catch (error) {
      console.error("Switch to online error:", error);
      addMessage({
        type: "ai",
        text: "❌ Error switching cart to online. Please try again.",
        timestamp: new Date(),
      });
      pushTimelineEntry({
        action: "Switch Cart to Online",
        tool: "switch_channel_instore_to_online",
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
      await sendAgentMessage(`Remove item ${orderId} from cart`);
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

  const handleUpdateCartSize = async (orderId, productName, newSize) => {
    if (!orderId) return;
    const sizeValue = String(newSize || "").trim();

    setIsLoading(true);
    pushTimelineEntry({
      action: `Update Size${productName ? `: ${productName}` : ""}`,
      tool: "view_cart_agent",
      status: "in-progress",
      logs: [
        {
          time: formatLocalTime(),
          text: `system → cart/update-size: order_id=${orderId}, size=${sizeValue || "(empty)"}`,
          variant: "system",
        },
      ],
    });

    // Optimistic UI update
    setMessages((prev) =>
      prev.map((m) => {
        if (m?.type !== "cartItems" || !Array.isArray(m.cartItems)) return m;
        return {
          ...m,
          cartItems: m.cartItems.map((it) =>
            it.order_id === orderId ? { ...it, size: sizeValue } : it,
          ),
        };
      }),
    );

    try {
      const res = await fetch(CART_UPDATE_SIZE_API, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_id: orderId, size: sizeValue }),
      });
      const data = await res.json();
      if (!data?.success) {
        addMessage({
          type: "ai",
          text: data?.error || "Failed to update size. Please try again.",
          timestamp: new Date(),
        });
      }

      await refreshCartSilently();
    } catch {
      addMessage({
        type: "ai",
        text: "Sorry, there was an error updating the size. Please try again.",
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
          store_id: localStorage.getItem("kioskStoreId") || "",
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

    // Prime kiosk state for payment flow.
    // welcome_node now filters by channel='offline' + store_id,
    // so only items for this specific store are shown.
    await sendToBackend("__kiosk_start__");
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
                <button
                  className="kiosk-action-tools-btn primary kiosk-quick-actions-toggle"
                  onClick={() => {
                    setBarcodePanelOpen(false);
                    setIsQuickActionsOpen((prev) => !prev);
                  }}
                  disabled={isLoading}
                  type="button"
                  aria-haspopup="menu"
                  aria-expanded={isQuickActionsOpen}
                >
                  Quick Action Tools
                </button>

                {isQuickActionsOpen && (
                  <div className="kiosk-quick-actions-menu" role="menu">
                    <button
                      className="kiosk-action-tools-btn primary"
                      onClick={() => {
                        setIsQuickActionsOpen(false);
                        triggerPaymentFlow();
                      }}
                      disabled={isLoading}
                      type="button"
                      role="menuitem"
                      style={{
                        background:
                          "linear-gradient(135deg, #ff8c00 0%, #ffa500 100%)",
                        color: "white",
                        border: "none",
                      }}
                    >
                      💳 Go For Payment
                    </button>
                    <button
                      className="kiosk-action-tools-btn primary"
                      onClick={() => {
                        setIsQuickActionsOpen(false);
                        setBarcodePanelOpen(true);
                      }}
                      disabled={isLoading}
                      type="button"
                      role="menuitem"
                      style={{
                        background:
                          "linear-gradient(135deg, #ff8c00 0%, #ffa500 100%)",
                        color: "white",
                        border: "none",
                      }}
                    >
                      📱 Scan Product
                    </button>
                  </div>
                )}

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

                    <div className="kiosk-barcode-field">
                      <label className="kiosk-barcode-label">
                        Size (optional)
                      </label>
                      <input
                        className="kiosk-barcode-input"
                        type="text"
                        value={barcodeSize}
                        onChange={(e) => setBarcodeSize(e.target.value)}
                        placeholder="e.g. M or 8"
                        disabled={isLoading}
                      />
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
              <button className="kiosk-close-btn" onClick={handleCloseChatbot}>
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

              if (message.type === "switchSuccess") {
                return (
                  <div
                    key={`sw-${index}`}
                    className="kiosk-message kiosk-ai-message"
                  >
                    <div className="kiosk-message-content kiosk-switch-success-card">
                      <div className="kiosk-switch-success-banner">
                        🎉✨ Congratulations! ✨🎉
                      </div>
                      <div className="kiosk-switch-success-title">
                        What a Brilliant Choice! 🌟
                      </div>
                      <div className="kiosk-switch-success-body">
                        We're absolutely delighted to offer you this incredible
                        flexibility! Now you can browse, explore, and add your
                        favorite products from our entire collection to your
                        cart at your leisure.
                      </div>
                      <div className="kiosk-switch-success-highlight">
                        Products successfully moved to your online cart! 🛒
                      </div>
                      <div className="kiosk-switch-success-body">
                        Feel free to continue shopping from the comfort of your
                        home and complete your payment whenever you're ready.
                        💳✨
                      </div>
                      <div className="kiosk-switch-success-note">
                        <span className="kiosk-switch-success-note-icon">
                          📌
                        </span>
                        <span>
                          <strong>Please Note:</strong> Your selected products
                          will be reserved for the next 6 hours. Beyond this
                          window, availability will be subject to real-time
                          inventory levels. We recommend completing your
                          purchase at your earliest convenience to ensure
                          availability.
                        </span>
                      </div>
                      <div className="kiosk-switch-success-footer">
                        Happy Shopping! 🎊
                      </div>
                      <div className="kiosk-message-time">
                        {message.timestamp.toLocaleTimeString()}
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

                          const accessories = isAccessories(item);
                          const sizeOptions = getSizeOptions(item);
                          const rawSize = String(item?.size || "").trim();
                          const initialSize = getDefaultSize(item);
                          const showSizeSelect = sizeOptions.length > 0;
                          const sizeValue = showSizeSelect
                            ? sizeOptions.includes(rawSize)
                              ? rawSize
                              : sizeOptions.includes(initialSize)
                                ? initialSize
                                : sizeOptions[0] || ""
                            : "";

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

                                  {showSizeSelect ? (
                                    <div className="kiosk-cart-size-row">
                                      <span className="kiosk-cart-size-label">
                                        Size:
                                      </span>
                                      <select
                                        className="kiosk-cart-size-select"
                                        value={sizeValue}
                                        disabled={isLoading}
                                        aria-label={`Select size for ${item.product_name || "item"}`}
                                        onChange={(e) =>
                                          handleUpdateCartSize(
                                            item.order_id,
                                            item.product_name,
                                            e.target.value,
                                          )
                                        }
                                      >
                                        {sizeOptions.map((s) => (
                                          <option key={s} value={s}>
                                            {s}
                                          </option>
                                        ))}
                                      </select>
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
                            💳 Proceed to payment
                          </button>
                          <button
                            className="kiosk-cart-cta primary"
                            onClick={() => handleSwitchToOnline()}
                            disabled={isLoading}
                          >
                            🌐 Switch to Online Payment
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
