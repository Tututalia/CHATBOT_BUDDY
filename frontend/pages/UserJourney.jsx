import React, { useState, useEffect } from "react";
import { useAdminData } from "../AdminDataContext";

export default function UserJourney() {
  const { records } = useAdminData();
  const [userProfile, setUserProfile] = useState(null);
  const [orderHistory, setOrderHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [feedbackMap, setFeedbackMap] = useState({}); // { product_id: rating }
  const [hoverMap, setHoverMap] = useState({}); // { product_id: hoveredStar }
  const [submittingFeedback, setSubmittingFeedback] = useState({}); // { product_id: true/false }

  useEffect(() => {
    // Add fade-in animation CSS
    const style = document.createElement("style");
    style.textContent = `
      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(20px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      .animate-fadeIn {
        animation: fadeIn 0.6s ease-out forwards;
        opacity: 0;
      }
    `;
    document.head.appendChild(style);

    return () => document.head.removeChild(style);
  }, []);

  useEffect(() => {
    // Get the logged-in customer ID from localStorage
    const loggedInCustomerId = localStorage.getItem("loggedInCustomerId");

    if (!loggedInCustomerId) {
      setError("No customer logged in");
      setLoading(false);
      return;
    }

    // Fetch customer profile from backend
    const roleId = localStorage.getItem("userRole") || "1";
    fetch(`http://localhost:8000/api/customer/${loggedInCustomerId}/${roleId}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
        } else {
          setUserProfile(data);
        }
      })
      .catch((err) => {
        console.error("Error fetching customer profile:", err);
        setError("Failed to load customer profile");
      });

    // Fetch customer orders from backend
    fetch(`http://localhost:8000/api/customer/${loggedInCustomerId}/orders`)
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
        } else {
          const orders = data.order_history || [];
          setOrderHistory(orders);
          // Pre-populate feedbackMap from existing feedback in order data
          const existingFeedback = {};
          orders.forEach((o) => {
            if (
              o.feedback != null &&
              o.feedback !== "" &&
              !existingFeedback[o.product_id]
            ) {
              existingFeedback[o.product_id] = parseInt(o.feedback, 10);
            }
          });
          setFeedbackMap(existingFeedback);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching order history:", err);
        setError("Failed to load order history");
        setLoading(false);
      });
  }, []);

  // Fallback to context data if backend fails
  const user = userProfile || records?.users?.find((u) => u.id === "u1");
  const products =
    orderHistory.length > 0 ? orderHistory : records?.products || [];

  if (loading) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading customer profile...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                <p className="font-semibold">Error</p>
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-8">
          <p className="text-gray-600">No customer data available...</p>
        </div>
      </div>
    );
  }

  // Calculate product quantities from purchases (for order history)
  const productMap = {};
  const latestPurchaseDateMap = {};

  const parsePurchaseTime = (rawDate) => {
    if (!rawDate || typeof rawDate !== "string") return 0;
    const trimmed = rawDate.trim();
    if (!trimmed) return 0;

    // Backend often stores as "YYYY-MM-DD HH:MM:SS"; convert to ISO-like for consistent parsing.
    const normalized =
      trimmed.length >= 19 && trimmed[10] === " "
        ? `${trimmed.slice(0, 10)}T${trimmed.slice(11)}`
        : trimmed;

    const t = new Date(normalized).getTime();
    return Number.isFinite(t) ? t : 0;
  };

  if (orderHistory && orderHistory.length > 0) {
    orderHistory.forEach((product) => {
      const pid = product.product_id;
      productMap[pid] = (productMap[pid] || 0) + 1;

      const rawDate = product.purchase_date;
      const purchaseTime = parsePurchaseTime(rawDate);
      latestPurchaseDateMap[pid] = Math.max(
        latestPurchaseDateMap[pid] || 0,
        purchaseTime,
      );
    });
  }

  const orderedProductIds = Object.keys(productMap).sort(
    (a, b) => (latestPurchaseDateMap[b] || 0) - (latestPurchaseDateMap[a] || 0),
  );

  // Get initials for avatar
  const getInitials = (name) => {
    return (
      name
        ?.split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase() || "A"
    );
  };

  // Download invoice as PDF for a given product order
  const downloadInvoice = (prod) => {
    const customerName = user?.customer_name || user?.name || "Customer";
    const phone = user?.phone || "N/A";
    const address = user?.address || "N/A";
    const transactionId = prod.transaction_id || "N/A";
    const productName = prod.product_name || "Product";
    const category = prod.category || "";
    const qty = prod.quantity || productMap[prod.product_id] || 1;
    const originalPrice =
      prod.original_price != null ? prod.original_price : prod.price;
    const discountAmount =
      prod.discount_amount != null ? Number(prod.discount_amount) : 0;
    const loyaltyApplied =
      prod.loyalty_applied != null ? Number(prod.loyalty_applied) : 0;
    const netAmount = prod.final_price != null ? prod.final_price : prod.price;
    const productDesc = `${productName}${category ? " (" + category + ")" : ""}${prod.size ? " — Size: " + prod.size : ""} × ${qty}`;
    const logoUrl = window.location.origin + "/images/abfrl-icon.png";

    const invoiceHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ABFRL Purchase Invoice</title>
<style>
    body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f8f3ea; }
    .invoice-container { width: 900px; margin: 30px auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 8px solid #d2232a; }
    .header { text-align: center; border-bottom: 2px solid #f1d2b3; padding-bottom: 15px; }
    .logo { height: 80px; }
    .invoice-title { font-size: 26px; font-weight: bold; color: #d2232a; margin-top: 10px; }
    .invoice-id { margin-top: 5px; font-size: 14px; color: #444; }
    .customer-section { margin-top: 25px; background: #fff4e6; padding: 15px; border-radius: 6px; }
    .customer-section h3 { margin-top: 0; color: #c41e3a; }
    .invoice-table { width: 100%; border-collapse: collapse; margin-top: 25px; }
    .invoice-table th { background: linear-gradient(to right, #f5c28b, #f7e2c4); padding: 12px; text-align: left; font-size: 14px; border-bottom: 2px solid #d2232a; }
    .invoice-table td { padding: 10px; border-bottom: 1px solid #eee; font-size: 14px; }
    .invoice-table tr:hover { background-color: #fff9f0; }
    .total-row td { font-weight: bold; background: #fff4e6; }
    .footer { margin-top: 30px; padding-top: 15px; border-top: 2px solid #f1d2b3; font-size: 13px; color: #444; }
    .footer-title { font-weight: bold; color: #d2232a; margin-bottom: 8px; }
    .contact-info { margin-top: 10px; line-height: 1.6; }
    @media print { body { background: #fff; } .invoice-container { box-shadow: none; margin: 0 auto; } }
</style>
</head>
<body>
<div class="invoice-container">
    <div class="header">
        <img src="${logoUrl}" class="logo" alt="Aditya Birla Logo">
        <div class="invoice-title">ABFRL Purchase Invoice</div>
        <div class="invoice-id">Invoice ID: <strong>${transactionId}</strong></div>
    </div>
    <div class="customer-section">
        <h3>Customer Details</h3>
        <p><strong>Name:</strong> ${customerName}</p>
        <p><strong>Phone:</strong> ${phone}</p>
        <p><strong>Address:</strong> ${address}</p>
    </div>
    <table class="invoice-table">
        <thead>
            <tr>
                <th>Product Description</th>
                <th>Actual Price</th>
                <th>Discount Amount</th>
                <th>Loyalty Points Applied</th>
                <th>NET Amount</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>${productDesc}</td>
                <td>\u20B9 ${Number(originalPrice * qty).toLocaleString("en-IN")}</td>
                <td>\u20B9 ${Number(discountAmount).toLocaleString("en-IN")}</td>
                <td>\u20B9 ${Number(loyaltyApplied).toLocaleString("en-IN")}</td>
                <td>\u20B9 ${Number(netAmount).toLocaleString("en-IN")}</td>
            </tr>
            <tr class="total-row">
                <td colspan="4" style="text-align:right;">Grand Total</td>
                <td>\u20B9 ${Number(netAmount).toLocaleString("en-IN")}</td>
            </tr>
        </tbody>
    </table>
    <div class="footer">
        <div class="footer-title">Registered Address</div>
        Ecospace Business Park, Block 4A, 8th Floor, New Town, Kolkata, West Bengal \u2013 700156
        <div class="contact-info">
            <strong>Phone</strong><br>
            Online related queries: 8105060501<br>
            Store related queries: 1800 425 3050<br><br>
            <strong>Email</strong><br>
            For store related queries: customerservice@abfrl.adityabirla.com<br>
            For online enquiries: happytohelp@abfrl.in
        </div>
    </div>
</div>
<script>window.onload=function(){window.print();}</script>
</body>
</html>`;

    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(invoiceHtml);
      printWindow.document.close();
    }
  };

  return (
    <div className="bg-[#f5f5f5] min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-12">
        {/* Customer Profile Section */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 w-14 h-14 rounded-2xl flex items-center justify-center">
              <svg
                className="w-8 h-8 text-white"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-600 to-orange-700">
                Customer Profile
              </h1>
              <p className="text-gray-600">
                View purchase history and loyalty details
              </p>
            </div>
          </div>

          {/* Profile Card */}
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl p-8 shadow-lg">
            <div className="grid grid-cols-2 gap-8">
              {/* Left Column - Customer Info */}
              <div>
                <p className="text-xs uppercase tracking-wide text-gray-500 mb-3 font-semibold">
                  CUSTOMER INFORMATION
                </p>
                <div className="flex items-start gap-3 mb-4">
                  {/* Avatar with tier badge overlay */}
                  <div className="relative flex-shrink-0">
                    <div className="bg-gradient-to-br from-orange-600 to-orange-700 w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      {getInitials(user.customer_name || user.name)}
                    </div>
                    {/* Tier badge overlaid on avatar */}
                    {user.customer_type &&
                      (() => {
                        const tierMap = {
                          tier_1: {
                            label: "Diamond",
                            ring: "ring-blue-300",
                            bg: "bg-gradient-to-br from-blue-100 to-cyan-100",
                            icon: (
                              <svg
                                className="w-3 h-3"
                                viewBox="0 0 24 24"
                                fill="none"
                              >
                                <path
                                  d="M6 3L1 10L12 21L23 10L18 3H6Z"
                                  fill="url(#diamondGrad)"
                                  stroke="#3B82F6"
                                  strokeWidth="2"
                                  strokeLinejoin="round"
                                />
                                <defs>
                                  <linearGradient
                                    id="diamondGrad"
                                    x1="1"
                                    y1="3"
                                    x2="23"
                                    y2="21"
                                  >
                                    <stop offset="0%" stopColor="#93C5FD" />
                                    <stop offset="50%" stopColor="#60A5FA" />
                                    <stop offset="100%" stopColor="#3B82F6" />
                                  </linearGradient>
                                </defs>
                              </svg>
                            ),
                          },
                          tier_2: {
                            label: "Gold",
                            ring: "ring-yellow-400",
                            bg: "bg-gradient-to-br from-yellow-100 to-amber-100",
                            icon: (
                              <svg
                                className="w-3 h-3"
                                viewBox="0 0 24 24"
                                fill="none"
                              >
                                <path
                                  d="M12 2L15 8.5L22 9.5L17 14.5L18 21.5L12 18L6 21.5L7 14.5L2 9.5L9 8.5L12 2Z"
                                  fill="url(#goldGrad)"
                                  stroke="#D97706"
                                  strokeWidth="1.5"
                                  strokeLinejoin="round"
                                />
                                <defs>
                                  <linearGradient
                                    id="goldGrad"
                                    x1="2"
                                    y1="2"
                                    x2="22"
                                    y2="22"
                                  >
                                    <stop offset="0%" stopColor="#FCD34D" />
                                    <stop offset="50%" stopColor="#F59E0B" />
                                    <stop offset="100%" stopColor="#D97706" />
                                  </linearGradient>
                                </defs>
                              </svg>
                            ),
                          },
                          tier_3: {
                            label: "Silver",
                            ring: "ring-gray-300",
                            bg: "bg-gradient-to-br from-gray-100 to-slate-100",
                            icon: (
                              <svg
                                className="w-3 h-3"
                                viewBox="0 0 24 24"
                                fill="none"
                              >
                                <path
                                  d="M12 2L15 8.5L22 9.5L17 14.5L18 21.5L12 18L6 21.5L7 14.5L2 9.5L9 8.5L12 2Z"
                                  fill="url(#silverGrad)"
                                  stroke="#9CA3AF"
                                  strokeWidth="1.5"
                                  strokeLinejoin="round"
                                />
                                <defs>
                                  <linearGradient
                                    id="silverGrad"
                                    x1="2"
                                    y1="2"
                                    x2="22"
                                    y2="22"
                                  >
                                    <stop offset="0%" stopColor="#E5E7EB" />
                                    <stop offset="50%" stopColor="#D1D5DB" />
                                    <stop offset="100%" stopColor="#9CA3AF" />
                                  </linearGradient>
                                </defs>
                              </svg>
                            ),
                          },
                        };
                        const tier = tierMap[user.customer_type];
                        if (!tier) return null;
                        return (
                          <div
                            className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full ${tier.bg} ring-2 ${tier.ring} ring-offset-1 flex items-center justify-center shadow`}
                          >
                            {tier.icon}
                          </div>
                        );
                      })()}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl font-bold text-gray-800">
                        {user.customer_name || user.name || "Loading..."}
                      </span>
                      {/* Tier label next to name */}
                      {user.customer_type &&
                        (() => {
                          const tierLabels = {
                            tier_1: {
                              label: "Diamond",
                              text: "text-blue-600",
                              bg: "bg-blue-50",
                              border: "border-blue-200",
                            },
                            tier_2: {
                              label: "Gold",
                              text: "text-amber-600",
                              bg: "bg-amber-50",
                              border: "border-amber-200",
                            },
                            tier_3: {
                              label: "Silver",
                              text: "text-gray-500",
                              bg: "bg-gray-100",
                              border: "border-gray-200",
                            },
                          };
                          const tier = tierLabels[user.customer_type];
                          if (!tier) return null;
                          return (
                            <span
                              className={`text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${tier.bg} ${tier.text} border ${tier.border}`}
                            >
                              {tier.label}
                            </span>
                          );
                        })()}
                    </div>
                    {/* Phone Number */}
                    {user.phone && (
                      <div className="flex items-center gap-2 text-gray-600 mb-2">
                        <svg
                          className="w-4 h-4 text-orange-600"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
                        </svg>
                        <span className="text-sm font-medium">
                          {user.phone}
                        </span>
                      </div>
                    )}
                    {/* Address */}
                    {user.address && (
                      <div className="flex items-start gap-2 text-gray-600">
                        <svg
                          className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span className="text-sm font-medium">
                          {user.address}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column - Loyalty Points and Customer ID */}
              <div className="grid grid-cols-2 gap-6">
                {/* Loyalty Points */}
                <div className="text-center">
                  <p className="text-xs uppercase tracking-wide text-gray-500 mb-3 font-semibold">
                    LOYALTY POINTS
                  </p>
                  <div className="inline-flex items-center gap-2 bg-white border-3 border-green-500 rounded-2xl px-6 py-3">
                    <svg
                      className="w-6 h-6 text-green-600"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    <span className="text-3xl font-bold text-green-600">
                      {user.loyalty_points || user.loyaltyPoints || 0}
                    </span>
                  </div>
                </div>

                {/* User ID */}
                <div className="text-center">
                  <p className="text-xs uppercase tracking-wide text-gray-500 mb-3 font-semibold">
                    CUSTOMER ID
                  </p>
                  <div className="inline-flex items-center gap-2 bg-white border-3 border-orange-500 rounded-2xl px-6 py-3">
                    <span className="text-2xl text-orange-600 font-bold">
                      #
                    </span>
                    <span className="text-2xl font-bold text-orange-600">
                      {user.customer_id || user.id || "00001"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Order History Section */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 w-14 h-14 rounded-2xl flex items-center justify-center">
              <svg
                className="w-8 h-8 text-white"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-600 to-orange-700">
              Order History
            </h2>
          </div>

          {/* Product Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {orderHistory && orderHistory.length > 0 ? (
              orderedProductIds.map((pid, index) => {
                const prod = orderHistory
                  .filter((p) => p.product_id === pid)
                  .reduce((latest, current) => {
                    if (!latest) return current;
                    const latestTime = parsePurchaseTime(latest.purchase_date);
                    const currentTime = parsePurchaseTime(
                      current.purchase_date,
                    );
                    return currentTime >= latestTime ? current : latest;
                  }, null);
                if (!prod) return null;

                return (
                  <div
                    key={pid}
                    className="bg-white border-3 border-yellow-400 rounded-2xl overflow-hidden shadow-lg relative transform transition-all duration-500 hover:scale-105 hover:shadow-2xl hover:-translate-y-2 animate-fadeIn"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    {/* Return Status Badge - Top Left */}
                    {prod.return_status && (
                      <div className="absolute top-4 left-4 z-10">
                        <span
                          className={`inline-flex items-center gap-1.5 text-white text-xs font-bold px-3.5 py-2 rounded-full shadow-lg tracking-wide uppercase ${
                            prod.return_status.toLowerCase() === "returned"
                              ? "bg-green-600"
                              : "bg-red-600"
                          }`}
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth={2.5}
                            viewBox="0 0 24 24"
                          >
                            {prod.return_status.toLowerCase() === "returned" ? (
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M5 13l4 4L19 7"
                              />
                            ) : (
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
                              />
                            )}
                          </svg>
                          {prod.return_status === "Initiated"
                            ? "Return Initiated"
                            : ` ${prod.return_status}`}
                        </span>
                      </div>
                    )}

                    {/* Quantity Badge */}
                    <div className="absolute top-4 right-4 z-10">
                      <div className="bg-gradient-to-br from-orange-600 to-orange-700 text-white px-4 py-2 rounded-full flex items-center gap-1 font-bold shadow-lg transform transition-transform duration-300 hover:scale-110 hover:rotate-3">
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                          />
                        </svg>
                        <span>x{productMap[pid]}</span>
                      </div>
                    </div>

                    {/* Product Image */}
                    <div
                      className="bg-gray-100 p-8 flex items-center justify-center overflow-hidden"
                      style={{ minHeight: "280px" }}
                    >
                      {prod.image_reference ? (
                        <img
                          src={prod.image_reference}
                          alt={prod.product_name}
                          className="max-h-64 object-contain transform transition-transform duration-500 hover:scale-110"
                        />
                      ) : (
                        <div className="w-full h-64 bg-gray-200 flex items-center justify-center text-gray-400 rounded-lg">
                          <div className="text-center">
                            <svg
                              className="w-16 h-16 mx-auto mb-4 text-gray-300"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                                clipRule="evenodd"
                              />
                            </svg>
                            <p className="text-sm">{prod.product_name}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Product Details */}
                    <div className="p-6">
                      <h3 className="text-lg font-bold text-gray-800 mb-2">
                        {prod.product_name}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2">
                        Category: {prod.category}
                      </p>
                      {prod.original_price != null &&
                      prod.original_price !== prod.price ? (
                        <div className="mb-3">
                          <span className="text-sm text-gray-400 line-through mr-2">
                            ₹{prod.original_price}
                          </span>
                          <span className="text-xl font-bold text-green-600">
                            ₹{prod.price}
                          </span>
                        </div>
                      ) : (
                        <p className="text-xl font-bold text-green-600 mb-3">
                          ₹{prod.price}
                        </p>
                      )}
                      {/* Purchase Date */}
                      {prod.purchase_date && (
                        <div className="mb-3 flex items-center gap-2 text-sm text-gray-600">
                          <svg
                            className="w-4 h-4 text-orange-600"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="font-medium">
                            Purchased: {prod.purchase_date}
                          </span>
                        </div>
                      )}
                      {/* <div className="mt-3">
                        <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                          {prod.season}
                        </span>
                      </div> */}

                      {/* Star Feedback Section */}
                      <div className="mt-3 mb-1">
                        {(() => {
                          const existingRating = feedbackMap[pid];
                          const isSubmitting = submittingFeedback[pid];
                          const hovered = hoverMap[pid] || 0;

                          const handleStarClick = async (starValue) => {
                            if (existingRating || isSubmitting) return; // Already rated or submitting
                            setSubmittingFeedback((prev) => ({
                              ...prev,
                              [pid]: true,
                            }));
                            try {
                              const loggedInCustomerId =
                                localStorage.getItem("loggedInCustomerId");
                              const res = await fetch(
                                "http://localhost:8000/api/orders/feedback",
                                {
                                  method: "POST",
                                  headers: {
                                    "Content-Type": "application/json",
                                  },
                                  body: JSON.stringify({
                                    customer_id: loggedInCustomerId,
                                    product_id: pid,
                                    feedback: starValue,
                                  }),
                                },
                              );
                              const result = await res.json();
                              if (res.ok) {
                                setFeedbackMap((prev) => ({
                                  ...prev,
                                  [pid]: starValue,
                                }));
                              } else {
                                console.error("Feedback error:", result.detail);
                              }
                            } catch (err) {
                              console.error("Failed to submit feedback:", err);
                            } finally {
                              setSubmittingFeedback((prev) => ({
                                ...prev,
                                [pid]: false,
                              }));
                            }
                          };

                          return (
                            <div className="flex items-center gap-2">
                              <div className="flex gap-0.5">
                                {[1, 2, 3, 4, 5].map((star) => {
                                  const filled = existingRating
                                    ? star <= existingRating
                                    : star <= hovered;
                                  return (
                                    <button
                                      key={star}
                                      type="button"
                                      disabled={
                                        !!existingRating || isSubmitting
                                      }
                                      onClick={() => handleStarClick(star)}
                                      onMouseEnter={() => {
                                        if (!existingRating)
                                          setHoverMap((prev) => ({
                                            ...prev,
                                            [pid]: star,
                                          }));
                                      }}
                                      onMouseLeave={() => {
                                        if (!existingRating)
                                          setHoverMap((prev) => ({
                                            ...prev,
                                            [pid]: 0,
                                          }));
                                      }}
                                      className={`focus:outline-none transition-transform duration-150 ${
                                        existingRating
                                          ? "cursor-default"
                                          : "cursor-pointer hover:scale-125"
                                      }`}
                                    >
                                      <svg
                                        className={`w-6 h-6 transition-colors duration-200 ${
                                          filled
                                            ? "text-yellow-400 drop-shadow-sm"
                                            : "text-gray-300"
                                        }`}
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                      >
                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                      </svg>
                                    </button>
                                  );
                                })}
                              </div>
                              {!existingRating && (
                                <span className="text-xs text-gray-400 italic">
                                  Awaiting Feedback
                                </span>
                              )}
                              {isSubmitting && (
                                <span className="text-xs text-orange-500">
                                  Saving...
                                </span>
                              )}
                            </div>
                          );
                        })()}
                      </div>

                      {/* Download Invoice Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          downloadInvoice(prod);
                        }}
                        className="mt-4 w-full flex items-center justify-center gap-2 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white text-sm font-semibold py-2.5 px-4 rounded-xl shadow-md transition-all duration-300 hover:shadow-lg hover:scale-[1.02] active:scale-95"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                        Download Invoice
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="col-span-full bg-white rounded-2xl p-12 text-center text-gray-500">
                <svg
                  className="w-16 h-16 mx-auto mb-4 text-gray-300"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
                </svg>
                <p className="text-lg font-semibold mb-2">No orders found</p>
                <p>This customer hasn't made any purchases yet.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chat Button */}
      {/* <div className="fixed bottom-8 right-8">
        <button className="bg-gradient-to-br from-orange-600 to-orange-700 text-white w-16 h-16 rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform">
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div> */}
    </div>
  );
}
