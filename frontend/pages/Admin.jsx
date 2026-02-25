import React, { useState, useEffect } from "react";

// Import necessary Recharts components
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

export default function Admin() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState("overview");
  const [timeRange, setTimeRange] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const transactionsPerPage = 10;
  const [aiInsights, setAiInsights] = useState(null);
  const [aiInsightsData, setAiInsightsData] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [showInsights, setShowInsights] = useState(false);

  // Fetch dashboard data from API
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `http://localhost:8000/api/admin/dashboard?time_range=${timeRange}`,
        );
        const data = await response.json();
        setDashboardData(data);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [timeRange]);

  if (loading) {
    return (
      <div className="bg-gray-50 text-gray-800 min-h-screen p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-xl">Loading dashboard data...</div>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="bg-gray-50 text-gray-800 min-h-screen p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-xl text-red-500">
            Error loading dashboard data
          </div>
        </div>
      </div>
    );
  }

  // --- Data Processing for existing components ---
  const totals = {
    customers: dashboardData.summary.total_customers,
    productsSold: dashboardData.summary.total_products_sold,
    retailStores: dashboardData.summary.total_retail_stores,
  };

  // --- 1. Data Processing for Online vs Offline Pie Chart ---
  const onlineVsOfflineData = [
    {
      name: "Online",
      value: dashboardData.transactions_overview.online.count,
    },
    {
      name: "Offline",
      value: dashboardData.transactions_overview.offline.count,
    },
  ];

  const ONLINE_OFFLINE_COLORS = ["#A52A2A", "#FFA500"]; // Maroon for Online, Orange for Offline

  // --- Calculate Top Customers for Online ---
  const onlineCustomerPurchases = {};

  dashboardData.transactions
    .filter((t) => t.mode.toLowerCase() === "online")
    .forEach((trans) => {
      if (!onlineCustomerPurchases[trans.user_name]) {
        onlineCustomerPurchases[trans.user_name] = { count: 0, amount: 0 };
      }
      onlineCustomerPurchases[trans.user_name].count += trans.qty;
      onlineCustomerPurchases[trans.user_name].amount += trans.amount;
    });

  const topOnlineCustomers = Object.entries(onlineCustomerPurchases)
    .sort((a, b) => b[1].amount - a[1].amount)
    .slice(0, 10)
    .map(([name, data]) => ({
      name: name,
      value: data.amount,
      count: data.count,
    }));

  // --- Calculate Top Customers for Offline ---
  const offlineCustomerPurchases = {};

  dashboardData.transactions
    .filter((t) => t.mode.toLowerCase() === "offline")
    .forEach((trans) => {
      if (!offlineCustomerPurchases[trans.user_name]) {
        offlineCustomerPurchases[trans.user_name] = { count: 0, amount: 0 };
      }
      offlineCustomerPurchases[trans.user_name].count += trans.qty;
      offlineCustomerPurchases[trans.user_name].amount += trans.amount;
    });

  const topOfflineCustomers = Object.entries(offlineCustomerPurchases)
    .sort((a, b) => b[1].amount - a[1].amount)
    .slice(0, 10)
    .map(([name, data]) => ({
      name: name,
      value: data.amount,
      count: data.count,
    }));

  // --- Calculate Offline Sales by Store ---
  const offlineStoreSales = {};

  dashboardData.transactions
    .filter((t) => t.mode.toLowerCase() === "offline")
    .forEach((trans) => {
      const storeName = trans.store_name || "Unknown Store";
      if (!offlineStoreSales[storeName]) {
        offlineStoreSales[storeName] = { count: 0, amount: 0 };
      }
      offlineStoreSales[storeName].count += trans.qty;
      offlineStoreSales[storeName].amount += trans.amount;
    });

  const offlineSalesByStore = Object.entries(offlineStoreSales)
    .sort((a, b) => b[1].amount - a[1].amount)
    .map(([name, data]) => ({
      name: name,
      value: data.amount,
      count: data.count,
    }));

  // Generate distinct colors for pie chart (orange/yellow shades for stores)
  const STORE_COLORS = [
    "#FFA500",
    "#FFB84D",
    "#FF8C00",
    "#FFD700",
    "#F4A460",
    "#DAA520",
    "#CD853F",
    "#D2691E",
    "#B8860B",
    "#8B4513",
    "#A0522D",
    "#D2B48C",
    "#DEB887",
    "#F5DEB3",
  ];

  const CUSTOMER_COLORS = [
    "#8B1A1A",
    "#A52A2A",
    "#C44536",
    "#D2691E",
    "#E07B39",
    "#FF8C42",
    "#FFA500",
    "#FFB84D",
    "#CD853F",
    "#D2B48C",
  ];

  // Determine which data to show based on active view
  const getPieChartData = () => {
    if (activeView === "online") return topOnlineCustomers;
    if (activeView === "offline") return offlineSalesByStore;
    return onlineVsOfflineData;
  };

  const getPieChartColors = () => {
    if (activeView === "overview") return ONLINE_OFFLINE_COLORS;
    if (activeView === "offline") return STORE_COLORS;
    return CUSTOMER_COLORS;
  };

  const pieChartData = getPieChartData();
  const pieChartColors = getPieChartColors();

  // --- 2. Data Processing for Offline Purchases per Store ---
  const storePurchases = dashboardData.offline_purchases_per_store || [];

  // --- 3. Data Processing for Transactions: Month wise ---
  const monthlyData = dashboardData.monthly_trends.map((trend) => ({
    name: trend.month,
    Online: trend.online,
    Offline: trend.offline,
  }));

  const storeId = "";

  // Pagination logic
  const totalTransactions = dashboardData.transactions.length;
  const totalPages = Math.ceil(totalTransactions / transactionsPerPage);
  const indexOfLastTransaction = currentPage * transactionsPerPage;
  const indexOfFirstTransaction = indexOfLastTransaction - transactionsPerPage;
  const currentTransactions = dashboardData.transactions.slice(
    indexOfFirstTransaction,
    indexOfLastTransaction,
  );

  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  };

  const getPageNumbers = () => {
    const pageNumbers = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pageNumbers.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) pageNumbers.push(i);
        pageNumbers.push("...");
        pageNumbers.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pageNumbers.push(1);
        pageNumbers.push("...");
        for (let i = totalPages - 3; i <= totalPages; i++) pageNumbers.push(i);
      } else {
        pageNumbers.push(1);
        pageNumbers.push("...");
        for (let i = currentPage - 1; i <= currentPage + 1; i++)
          pageNumbers.push(i);
        pageNumbers.push("...");
        pageNumbers.push(totalPages);
      }
    }

    return pageNumbers;
  };

  const fetchAIInsights = async (range) => {
    try {
      setInsightsLoading(true);
      const response = await fetch(
        `http://localhost:8000/api/admin/ai-insights?time_range=${range}`,
      );
      const data = await response.json();

      if (data.error) {
        console.error("Error fetching AI insights:", data.error);
        setAiInsights(null);
        setAiInsightsData(null);
      } else {
        setAiInsights(data.insights);
        setAiInsightsData(data);
      }
    } catch (error) {
      console.error("Error fetching AI insights:", error);
      setAiInsights(null);
      setAiInsightsData(null);
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleViewInsights = () => {
    if (!showInsights && !aiInsights) {
      fetchAIInsights(timeRange);
    }
    setShowInsights(!showInsights);
  };

  return (
    <div className="bg-gray-50 min-h-screen p-6">
      {/* Header */}
      <div className="flex items-center mb-6">
        <div className="w-12 h-12 bg-gradient-to-br from-red-800 to-orange-600 rounded-lg flex items-center justify-center mr-4">
          <svg
            className="w-8 h-8 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
          </svg>
        </div>
        <div>
          <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-700 to-orange-600">
            Operations-Revenue Dashboard
          </h2>
          <p className="text-gray-600 text-sm">
            Complete analytics and performance metrics
          </p>
        </div>
      </div>

      {/* Top Stats Grid - 3 Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="text-sm text-gray-500 mb-2">No of Customer</div>
          <div className="text-4xl font-bold text-red-700">
            {totals.customers.toLocaleString()}
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="text-sm text-gray-500 mb-2">No of Product Sold</div>
          <div className="text-4xl font-bold text-orange-600">
            {totals.productsSold.toLocaleString()}
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="text-sm text-gray-500 mb-2">No of Retail Stores</div>
          <div className="text-4xl font-bold text-orange-600">
            {totals.retailStores}
          </div>
        </div>
      </div>

      {/* New Row for Pie Chart and Store Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* 1. Total Transactions: Online vs Offline */}
        <div className="rounded-xl shadow-lg overflow-hidden">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-red-800 to-orange-600 p-6">
            <h3 className="text-xl font-semibold mb-3 text-white">
              {activeView === "overview" &&
                "Total Transactions: Online vs Offline(Past 1 Month)"}
              {activeView === "online" && "Online Sales by Top Customers"}
              {activeView === "offline" && "Offline Sales by Store"}
            </h3>
            {/* Tab-like buttons */}
            <div className="flex gap-2 bg-orange-200/30 p-1 rounded-lg">
              <button
                onClick={() => setActiveView("overview")}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeView === "overview"
                    ? "bg-white text-red-900"
                    : "bg-transparent text-white hover:bg-white/20"
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveView("online")}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeView === "online"
                    ? "bg-white text-red-900"
                    : "bg-transparent text-white hover:bg-white/20"
                }`}
              >
                Online
              </button>
              <button
                onClick={() => setActiveView("offline")}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeView === "offline"
                    ? "bg-white text-red-900"
                    : "bg-transparent text-white hover:bg-white/20"
                }`}
              >
                Offline
              </button>
            </div>
          </div>
          {/* Chart area with white background */}
          <div className="bg-white p-6">
            <div style={{ height: 340 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={pieChartColors[index % pieChartColors.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, name, props) => {
                      if (activeView === "overview") {
                        return [value, name];
                      }
                      return [
                        `₹${value.toLocaleString("en-IN")}`,
                        `${props.payload.name} (${props.payload.count} items)`,
                      ];
                    }}
                  />
                  {activeView === "overview" && <Legend />}
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Total Revenue Section */}
            <div className="mt-6 border-2 border-yellow-400 rounded-xl p-4 bg-orange-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-orange-600 to-orange-700 rounded-xl flex items-center justify-center">
                    <svg
                      className="w-8 h-8 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 uppercase tracking-wide font-semibold">
                      Total Revenue
                    </div>
                    <div className="text-3xl font-bold text-orange-700">
                      ₹
                      {(activeView === "overview"
                        ? dashboardData.summary.total_revenue
                        : activeView === "online"
                          ? dashboardData.transactions_overview.online.revenue
                          : dashboardData.transactions_overview.offline.revenue
                      ).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="bg-white px-4 py-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">
                      Transactions
                    </div>
                    <div className="text-xl font-bold text-red-700">
                      {(activeView === "overview"
                        ? dashboardData.summary.total_transactions
                        : activeView === "online"
                          ? dashboardData.transactions_overview.online.count
                          : dashboardData.transactions_overview.offline.count
                      ).toLocaleString("en-IN")}
                    </div>
                  </div>
                  <div className="bg-white px-4 py-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">Avg Value</div>
                    <div className="text-xl font-bold text-orange-600">
                      ₹
                      {(activeView === "overview"
                        ? dashboardData.summary.avg_transaction_value
                        : activeView === "online"
                          ? dashboardData.transactions_overview.online.count > 0
                            ? dashboardData.transactions_overview.online
                                .revenue /
                              dashboardData.transactions_overview.online.count
                            : 0
                          : dashboardData.transactions_overview.offline.count >
                              0
                            ? dashboardData.transactions_overview.offline
                                .revenue /
                              dashboardData.transactions_overview.offline.count
                            : 0
                      ).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 2. Offline Purchases per Store */}
        <div className="rounded-xl shadow-lg overflow-hidden">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-red-800 to-orange-600 p-6">
            <h3 className="text-xl font-semibold text-white">
              Offline Purchases per Store
            </h3>
          </div>
          {/* Table area with white background and scroll */}
          <div className="bg-white max-h-[500px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 sticky top-0">
                <tr className="text-left text-gray-700">
                  <th className="py-3 px-6 font-semibold">Store Name</th>
                  <th className="py-3 px-6 font-semibold text-right">
                    Purchases Count
                  </th>
                </tr>
              </thead>
              <tbody className="text-gray-800">
                {storePurchases.map((store, i) => (
                  <tr
                    key={i}
                    className="border-t border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <td className="py-3 px-6">{store.store_name}</td>
                    <td className="py-3 px-6 text-right">
                      <span className="bg-yellow-300 text-gray-900 px-3 py-1 rounded-full font-semibold">
                        {store.purchases_count}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* AI Insights & Recommendations Section */}
      <div className="mb-6 bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 rounded-2xl shadow-2xl overflow-hidden">
        <button
          onClick={handleViewInsights}
          className="w-full p-6 flex items-center justify-between hover:bg-white/10 transition-all duration-300"
        >
          <div className="flex items-center gap-4">
            <div className="bg-white/20 backdrop-blur-sm p-4 rounded-xl">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <div className="text-left">
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                AI Insights & Recommendations
                {insightsLoading && (
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                )}
              </h2>
              <p className="text-white/80 text-sm mt-1">
                Powered by AI • Click to {showInsights ? "hide" : "view"}{" "}
                detailed analytics
              </p>
            </div>
          </div>
          <svg
            className={`w-6 h-6 text-white transition-transform duration-300 ${showInsights ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {showInsights && (
          <div className="p-6 bg-gradient-to-br from-gray-50 to-white space-y-6">
            {insightsLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-600 mx-auto mb-4"></div>
                  <p className="text-gray-600 font-medium">
                    Generating AI insights...
                  </p>
                  <p className="text-gray-400 text-sm mt-2">
                    Analyzing store performance data
                  </p>
                </div>
              </div>
            ) : aiInsights && aiInsightsData ? (
              <>
                {/* ── 1. Performance Overview ── */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border-l-4 border-indigo-500 shadow-md">
                  <div className="flex items-start gap-3">
                    <div className="bg-indigo-500 p-2 rounded-lg mt-1">
                      <svg
                        className="w-6 h-6 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-indigo-900 mb-2">
                        Performance Overview
                      </h3>
                      <p className="text-gray-700 leading-relaxed">
                        {aiInsights.overview}
                      </p>
                    </div>
                  </div>
                </div>

                {/* ── 2. Trend Analysis ── */}
                {aiInsights.trend_analysis && (
                  <div className="bg-gradient-to-r from-purple-50 to-violet-50 p-6 rounded-xl border-l-4 border-purple-500 shadow-md">
                    <div className="flex items-start gap-3 mb-4">
                      <div className="bg-purple-500 p-2 rounded-lg mt-1">
                        <svg
                          className="w-6 h-6 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                          />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-purple-900 mb-1">
                          Trend Analysis
                        </h3>
                        <span
                          className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
                            aiInsights.trend_analysis.direction === "growth"
                              ? "bg-green-100 text-green-700"
                              : aiInsights.trend_analysis.direction ===
                                  "decline"
                                ? "bg-red-100 text-red-700"
                                : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {aiInsights.trend_analysis.direction === "growth"
                            ? "↑ Growth"
                            : aiInsights.trend_analysis.direction === "decline"
                              ? "↓ Decline"
                              : "→ Stable"}
                        </span>
                        <p className="text-gray-700 mt-2 leading-relaxed">
                          {aiInsights.trend_analysis.summary}
                        </p>
                        {aiInsights.trend_analysis.key_factors &&
                          aiInsights.trend_analysis.key_factors.length > 0 && (
                            <div className="mt-3 space-y-1">
                              <p className="text-purple-800 font-semibold text-sm">
                                Key Factors:
                              </p>
                              {aiInsights.trend_analysis.key_factors.map(
                                (factor, idx) => (
                                  <div
                                    key={idx}
                                    className="flex items-start gap-2 text-sm text-gray-600"
                                  >
                                    <span className="text-purple-500 mt-0.5">
                                      •
                                    </span>
                                    <span>{factor}</span>
                                  </div>
                                ),
                              )}
                            </div>
                          )}
                      </div>
                    </div>
                  </div>
                )}

                {/* ── 3. Store Performance Overview Grid ── */}
                {aiInsightsData.store_performance &&
                  aiInsightsData.store_performance.length > 0 && (
                    <div>
                      <div className="flex items-center gap-3 mb-4">
                        <div className="bg-gradient-to-br from-indigo-600 to-blue-500 p-2 rounded-lg">
                          <svg
                            className="w-6 h-6 text-white"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                            />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-800">
                            Store Performance Overview
                          </h3>
                          <p className="text-gray-500 text-sm">
                            {aiInsightsData.store_performance.length} stores
                            analyzed • {aiInsightsData.time_period}
                          </p>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {aiInsightsData.store_performance.map((store, idx) => (
                          <div
                            key={idx}
                            className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow"
                          >
                            <div
                              className={`px-4 py-3 ${
                                store.rating === "EXCELLENT"
                                  ? "bg-gradient-to-r from-green-500 to-emerald-500"
                                  : store.rating === "GOOD"
                                    ? "bg-gradient-to-r from-blue-500 to-indigo-500"
                                    : store.rating === "AVERAGE"
                                      ? "bg-gradient-to-r from-yellow-500 to-amber-500"
                                      : "bg-gradient-to-r from-red-500 to-rose-500"
                              }`}
                            >
                              <h4 className="text-white font-bold text-sm truncate">
                                {store.store_name}
                              </h4>
                              <div className="flex items-center justify-between mt-1">
                                <span className="text-white/80 text-xs">
                                  Manager: {store.manager}
                                </span>
                                <span className="bg-white/20 text-white text-xs px-2 py-0.5 rounded-full font-bold">
                                  {store.rating}
                                </span>
                              </div>
                            </div>
                            <div className="p-4 grid grid-cols-2 gap-3">
                              <div>
                                <p className="text-gray-400 text-xs uppercase tracking-wide">
                                  Revenue
                                </p>
                                <p className="text-gray-800 font-bold text-sm">
                                  ₹{store.revenue.toLocaleString()}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-400 text-xs uppercase tracking-wide">
                                  Orders
                                </p>
                                <p className="text-gray-800 font-bold text-sm">
                                  {store.orders.toLocaleString()}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-400 text-xs uppercase tracking-wide">
                                  AOV
                                </p>
                                <p className="text-gray-800 font-bold text-sm">
                                  ₹{store.aov.toLocaleString()}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-400 text-xs uppercase tracking-wide">
                                  Customers
                                </p>
                                <p className="text-gray-800 font-bold text-sm">
                                  {store.customers}
                                </p>
                              </div>
                              <div className="col-span-2">
                                <p className="text-gray-400 text-xs uppercase tracking-wide">
                                  Success Rate
                                </p>
                                <div className="flex items-center gap-2 mt-1">
                                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                                    <div
                                      className={`h-2 rounded-full ${
                                        store.success_rate >= 80
                                          ? "bg-green-500"
                                          : store.success_rate >= 50
                                            ? "bg-yellow-500"
                                            : "bg-red-500"
                                      }`}
                                      style={{
                                        width: `${Math.min(store.success_rate, 100)}%`,
                                      }}
                                    ></div>
                                  </div>
                                  <span className="text-xs font-semibold text-gray-600">
                                    {store.success_rate}%
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                {/* ── 4. Top Performer vs Needs Attention ── */}
                {aiInsightsData.top_performer &&
                  aiInsightsData.needs_attention && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Top Performer */}
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl shadow-md border border-green-200 overflow-hidden">
                        <div className="bg-gradient-to-r from-green-600 to-emerald-500 px-5 py-4">
                          <div className="flex items-center gap-2">
                            <svg
                              className="w-6 h-6 text-yellow-300"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                            <h3 className="text-white font-bold text-lg">
                              Top Performer
                            </h3>
                          </div>
                          <p className="text-white font-semibold text-xl mt-1">
                            {aiInsightsData.top_performer.store_name}
                          </p>
                          <p className="text-green-100 text-sm">
                            Manager: {aiInsightsData.top_performer.manager}
                          </p>
                        </div>
                        <div className="p-5 space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500 text-sm">
                              Revenue
                            </span>
                            <span className="text-green-700 font-bold">
                              ₹
                              {aiInsightsData.top_performer.revenue.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500 text-sm">
                              Orders
                            </span>
                            <span className="text-green-700 font-bold">
                              {aiInsightsData.top_performer.orders.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500 text-sm">
                              Success Rate
                            </span>
                            <span className="text-green-700 font-bold">
                              {aiInsightsData.top_performer.success_rate}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500 text-sm">
                              Customers
                            </span>
                            <span className="text-green-700 font-bold">
                              {aiInsightsData.top_performer.customers}
                            </span>
                          </div>
                          {aiInsights.top_performer_success_factors &&
                            aiInsights.top_performer_success_factors.length >
                              0 && (
                              <div className="mt-3 border-t border-green-200 pt-3">
                                <p className="text-green-800 font-semibold text-sm mb-2">
                                  Success Factors:
                                </p>
                                {aiInsights.top_performer_success_factors.map(
                                  (f, i) => (
                                    <div
                                      key={i}
                                      className="flex items-start gap-2 text-sm text-gray-600 mb-1"
                                    >
                                      <span className="text-green-500 mt-0.5">
                                        ✓
                                      </span>
                                      <span>{f}</span>
                                    </div>
                                  ),
                                )}
                              </div>
                            )}
                        </div>
                      </div>

                      {/* Needs Attention */}
                      <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-xl shadow-md border border-red-200 overflow-hidden">
                        <div className="bg-gradient-to-r from-red-600 to-orange-500 px-5 py-4">
                          <div className="flex items-center gap-2">
                            <svg
                              className="w-6 h-6 text-yellow-200"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                              />
                            </svg>
                            <h3 className="text-white font-bold text-lg">
                              Needs Attention
                            </h3>
                          </div>
                          <p className="text-white font-semibold text-xl mt-1">
                            {aiInsightsData.needs_attention.store_name}
                          </p>
                          <p className="text-red-100 text-sm">
                            Manager: {aiInsightsData.needs_attention.manager}
                          </p>
                        </div>
                        <div className="p-5 space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500 text-sm">
                              Revenue
                            </span>
                            <span className="text-red-700 font-bold">
                              ₹
                              {aiInsightsData.needs_attention.revenue.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500 text-sm">
                              Orders
                            </span>
                            <span className="text-red-700 font-bold">
                              {aiInsightsData.needs_attention.orders.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500 text-sm">
                              Success Rate
                            </span>
                            <span className="text-red-700 font-bold">
                              {aiInsightsData.needs_attention.success_rate}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-500 text-sm">
                              Customers
                            </span>
                            <span className="text-red-700 font-bold">
                              {aiInsightsData.needs_attention.customers}
                            </span>
                          </div>
                          {aiInsights.needs_attention_improvement_areas &&
                            aiInsights.needs_attention_improvement_areas
                              .length > 0 && (
                              <div className="mt-3 border-t border-red-200 pt-3">
                                <p className="text-red-800 font-semibold text-sm mb-2">
                                  Improvement Areas:
                                </p>
                                {aiInsights.needs_attention_improvement_areas.map(
                                  (f, i) => (
                                    <div
                                      key={i}
                                      className="flex items-start gap-2 text-sm text-gray-600 mb-1"
                                    >
                                      <span className="text-red-500 mt-0.5">
                                        !
                                      </span>
                                      <span>{f}</span>
                                    </div>
                                  ),
                                )}
                              </div>
                            )}
                        </div>
                      </div>
                    </div>
                  )}

                {/* ── 5. Critical: Poor Performing Stores ── */}
                {aiInsightsData.poor_stores &&
                  aiInsightsData.poor_stores.length > 0 && (
                    <div className="bg-gradient-to-r from-red-50 to-orange-50 p-6 rounded-xl border-l-4 border-red-500 shadow-md">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="bg-red-500 p-2 rounded-lg">
                          <svg
                            className="w-6 h-6 text-white"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-red-900">
                            Critical: Poor Performing Stores
                          </h3>
                          <p className="text-red-600 text-sm font-medium">
                            ⚠ URGENT ATTENTION REQUIRED —{" "}
                            {aiInsightsData.poor_stores.length} store(s)
                          </p>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {aiInsightsData.poor_stores.map((store, idx) => (
                          <div
                            key={idx}
                            className="bg-white rounded-xl border-2 border-red-200 shadow-sm overflow-hidden"
                          >
                            <div className="bg-red-100 px-4 py-3 border-b border-red-200">
                              <h4 className="text-red-900 font-bold text-sm">
                                {store.store_name}
                              </h4>
                              <p className="text-red-600 text-xs">
                                Manager: {store.manager}
                              </p>
                            </div>
                            <div className="p-4 grid grid-cols-2 gap-3">
                              <div>
                                <p className="text-gray-400 text-xs">Revenue</p>
                                <p className="text-red-700 font-bold text-sm">
                                  ₹{store.revenue.toLocaleString()}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-400 text-xs">
                                  Success Rate
                                </p>
                                <p className="text-red-700 font-bold text-sm">
                                  {store.success_rate}%
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-400 text-xs">Orders</p>
                                <p className="text-red-700 font-bold text-sm">
                                  {store.orders.toLocaleString()}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-400 text-xs">
                                  Customers
                                </p>
                                <p className="text-red-700 font-bold text-sm">
                                  {store.customers}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Immediate Actions for Poor Stores */}
                      {aiInsights.poor_store_actions &&
                        aiInsights.poor_store_actions.length > 0 && (
                          <div className="mt-5 bg-white rounded-xl p-5 border border-red-200">
                            <h4 className="text-red-900 font-bold mb-3 flex items-center gap-2">
                              <svg
                                className="w-5 h-5 text-red-600"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                                  clipRule="evenodd"
                                />
                              </svg>
                              Strategic Recommendations for Poor Performing
                              Stores
                            </h4>
                            <div className="space-y-2">
                              {aiInsights.poor_store_actions.map(
                                (action, idx) => (
                                  <div
                                    key={idx}
                                    className="flex items-start gap-3 p-3 bg-red-50 rounded-lg"
                                  >
                                    <span className="bg-red-500 text-white text-xs font-bold w-5 h-5 flex items-center justify-center rounded-full flex-shrink-0 mt-0.5">
                                      {idx + 1}
                                    </span>
                                    <p className="text-gray-700 text-sm">
                                      {action}
                                    </p>
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        )}
                    </div>
                  )}

                {/* ── 6. AI Business Insights ── */}
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-xl border-l-4 border-indigo-500 shadow-md">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="bg-gradient-to-br from-indigo-600 to-purple-600 p-2 rounded-lg">
                      <svg
                        className="w-6 h-6 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                        />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-indigo-900">
                        AI Business Insights
                      </h3>
                      <p className="text-indigo-600 text-sm">
                        Powered by GPT-4o-mini
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    {/* Market Opportunities */}
                    {aiInsights.market_opportunities &&
                      aiInsights.market_opportunities.length > 0 && (
                        <div className="bg-white rounded-xl p-5 border border-indigo-200 shadow-sm">
                          <h4 className="text-indigo-900 font-bold mb-3 flex items-center gap-2">
                            <svg
                              className="w-5 h-5 text-indigo-600"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z"
                                clipRule="evenodd"
                              />
                            </svg>
                            Market Opportunities
                          </h4>
                          <div className="space-y-2">
                            {aiInsights.market_opportunities.map((opp, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-2 text-sm text-gray-700"
                              >
                                <span className="text-indigo-500 mt-0.5 font-bold">
                                  →
                                </span>
                                <span>{opp}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                    {/* Strategic Focus Areas */}
                    {aiInsights.strategic_focus_areas &&
                      aiInsights.strategic_focus_areas.length > 0 && (
                        <div className="bg-white rounded-xl p-5 border border-purple-200 shadow-sm">
                          <h4 className="text-purple-900 font-bold mb-3 flex items-center gap-2">
                            <svg
                              className="w-5 h-5 text-purple-600"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm-3 7.57V16a2 2 0 002 2h6a2 2 0 002-2v-3.43A24.92 24.92 0 0110 15a24.92 24.92 0 01-5-1.43z"
                                clipRule="evenodd"
                              />
                            </svg>
                            Strategic Focus Areas
                          </h4>
                          <div className="space-y-2">
                            {aiInsights.strategic_focus_areas.map(
                              (area, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-start gap-2 text-sm text-gray-700"
                                >
                                  <span className="bg-purple-100 text-purple-700 text-xs font-bold w-5 h-5 flex items-center justify-center rounded-full flex-shrink-0 mt-0.5">
                                    {idx + 1}
                                  </span>
                                  <span>{area}</span>
                                </div>
                              ),
                            )}
                          </div>
                        </div>
                      )}
                  </div>
                </div>

                {/* Refresh Button */}
                <div className="flex justify-center pt-4">
                  <button
                    onClick={() => fetchAIInsights(timeRange)}
                    disabled={insightsLoading}
                    className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                    Refresh Insights
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <div className="bg-gray-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-10 h-10 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <p className="text-gray-600 font-medium">
                  Unable to generate insights
                </p>
                <p className="text-gray-400 text-sm mt-2">
                  Please try again later
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* New Row for Monthly Transactions Chart */}
      <div className="grid grid-cols-1 gap-6 mb-6">
        {/* 3. Monthly Transaction Trends */}
        <div className="rounded-xl shadow-lg overflow-hidden">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-red-800 to-orange-600 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <svg
                  className="w-7 h-7 text-white"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white">
                  Monthly Transaction Trends
                </h3>
                <p className="text-sm text-orange-100">
                  Online vs Offline sales comparison
                </p>
              </div>
            </div>
          </div>

          {/* Chart area with white background */}
          <div className="bg-white p-6">
            <div style={{ height: 350 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={monthlyData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <XAxis dataKey="name" stroke="#6B7280" />
                  <YAxis
                    allowDecimals={false}
                    stroke="#6B7280"
                    label={{
                      value: "Number of Transactions",
                      angle: -90,
                      position: "insideLeft",
                    }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                    }}
                    labelStyle={{ color: "#1F2937" }}
                  />
                  <Legend />
                  <Bar dataKey="Online" stackId="a" fill="#A52A2A" />
                  <Bar dataKey="Offline" stackId="a" fill="#FFA500" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Transaction Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
              <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-3 h-3 rounded-full bg-red-800"></div>
                  <div className="text-xs text-gray-600 uppercase tracking-wide font-semibold">
                    Online Transactions
                  </div>
                </div>
                <div className="text-4xl font-bold text-red-800">
                  {dashboardData.transactions_overview.online.count.toLocaleString(
                    "en-IN",
                  )}
                </div>
              </div>
              <div className="bg-orange-50 border-2 border-orange-200 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                  <div className="text-xs text-gray-600 uppercase tracking-wide font-semibold">
                    Offline Transactions
                  </div>
                </div>
                <div className="text-4xl font-bold text-orange-600">
                  {dashboardData.transactions_overview.offline.count.toLocaleString(
                    "en-IN",
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="grid grid-cols-1 lg:grid-cols-1 gap-6">
        <div className="rounded-xl shadow-lg overflow-hidden">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-red-800 to-orange-600 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <svg
                  className="w-7 h-7 text-white"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                  <path
                    fillRule="evenodd"
                    d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white">
                  Transaction History of ABFRL Stores across the Zone
                </h3>
              </div>
            </div>
          </div>

          {/* Table area with white background */}
          <div className="bg-white overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 border-b-2 border-gray-200">
                <tr className="text-left text-gray-600 uppercase tracking-wider text-xs font-semibold">
                  <th className="py-4 px-6">ID</th>
                  <th className="py-4 px-6">
                    <div className="flex items-center gap-2">
                      Date
                      <svg
                        className="w-4 h-4"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  </th>
                  <th className="py-4 px-6">User Name</th>
                  <th className="py-4 px-6">Product</th>
                  <th className="py-4 px-6">Qty</th>
                  <th className="py-4 px-6">Mode</th>
                  <th className="py-4 px-6">Store Name</th>
                  <th className="py-4 px-6">Status</th>
                  <th className="py-4 px-6">Amount</th>
                  <th className="py-4 px-6">Address</th>
                  <th className="py-4 px-6">Phone</th>
                </tr>
              </thead>
              <tbody className="text-gray-700">
                {currentTransactions.map((transaction, index) => (
                  <tr
                    key={transaction.id || index}
                    className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <td className="py-4 px-6 font-semibold text-red-700">
                      {transaction.id}
                    </td>
                    <td className="py-4 px-6 text-gray-600">
                      {transaction.date}
                    </td>
                    <td className="py-4 px-6 font-medium">
                      {transaction.user_name}
                    </td>
                    <td className="py-4 px-6 text-gray-600">
                      {transaction.product}
                    </td>
                    <td className="py-4 px-6 text-center font-semibold">
                      {transaction.qty}
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          transaction.mode.toLowerCase() === "online"
                            ? "bg-red-100 text-red-700"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        {transaction.mode}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-gray-600">
                      {transaction.store_name}
                    </td>
                    <td className="py-4 px-6">
                      <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-semibold">
                        {transaction.status}
                      </span>
                    </td>
                    <td className="py-4 px-6 font-semibold">
                      ₹{transaction.amount.toFixed(2)}
                    </td>
                    <td className="py-4 px-6 text-gray-600">
                      {transaction.address}
                    </td>
                    <td className="py-4 px-6 text-gray-600">
                      {transaction.phone}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="bg-white border-t border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Showing {indexOfFirstTransaction + 1} to{" "}
                {Math.min(indexOfLastTransaction, totalTransactions)} of{" "}
                {totalTransactions} transactions
              </div>

              <div className="flex items-center gap-2">
                {/* Previous Button */}
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === 1
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                      : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  Previous
                </button>

                {/* Page Numbers */}
                <div className="flex items-center gap-1">
                  {getPageNumbers().map((pageNum, idx) =>
                    pageNum === "..." ? (
                      <span
                        key={`ellipsis-${idx}`}
                        className="px-3 py-2 text-gray-500"
                      >
                        ...
                      </span>
                    ) : (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                          currentPage === pageNum
                            ? "bg-gradient-to-r from-red-600 to-orange-500 text-white"
                            : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                        }`}
                      >
                        {pageNum}
                      </button>
                    ),
                  )}
                </div>

                {/* Next Button */}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === totalPages
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                      : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
