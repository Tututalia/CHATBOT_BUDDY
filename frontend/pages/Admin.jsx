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
      } else {
        setAiInsights(data.insights);
      }
    } catch (error) {
      console.error("Error fetching AI insights:", error);
      setAiInsights(null);
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
                    Analyzing admin dashboard data
                  </p>
                </div>
              </div>
            ) : aiInsights ? (
              <>
                {/* Performance Overview */}
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

                {/* Key Insights */}
                {aiInsights.key_insights &&
                  aiInsights.key_insights.length > 0 && (
                    <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl border-l-4 border-green-500 shadow-md">
                      <div className="flex items-start gap-3 mb-4">
                        <div className="bg-green-500 p-2 rounded-lg mt-1">
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
                              d="M13 10V3L4 14h7v7l9-11h-7z"
                            />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-green-900">
                            Key Insights
                          </h3>
                          <p className="text-green-700 text-sm">
                            Critical findings from your data
                          </p>
                        </div>
                      </div>
                      <div className="space-y-3 ml-11">
                        {aiInsights.key_insights.map((insight, idx) => (
                          <div
                            key={idx}
                            className="bg-white p-4 rounded-lg shadow-sm border border-green-200"
                          >
                            <div className="flex items-start gap-3">
                              <div className="bg-green-100 p-1.5 rounded-full mt-0.5">
                                <svg
                                  className="w-4 h-4 text-green-600"
                                  fill="currentColor"
                                  viewBox="0 0 20 20"
                                >
                                  <path
                                    fillRule="evenodd"
                                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                              </div>
                              <p className="text-gray-700 text-sm flex-1">
                                {insight}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                {/* Recommendations */}
                {aiInsights.recommendations &&
                  aiInsights.recommendations.length > 0 && (
                    <div className="bg-gradient-to-r from-amber-50 to-yellow-50 p-6 rounded-xl border-l-4 border-amber-500 shadow-md">
                      <div className="flex items-start gap-3 mb-4">
                        <div className="bg-amber-500 p-2 rounded-lg mt-1">
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
                              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                            />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-amber-900">
                            Recommendations
                          </h3>
                          <p className="text-amber-700 text-sm">
                            Actions to optimize performance
                          </p>
                        </div>
                      </div>
                      <div className="space-y-3 ml-11">
                        {aiInsights.recommendations.map((rec, idx) => (
                          <div
                            key={idx}
                            className="bg-white p-4 rounded-lg shadow-sm border border-amber-200"
                          >
                            <div className="flex items-start gap-3">
                              <div className="bg-amber-100 p-1.5 rounded-full mt-0.5">
                                <svg
                                  className="w-4 h-4 text-amber-600"
                                  fill="currentColor"
                                  viewBox="0 0 20 20"
                                >
                                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                                  <path
                                    fillRule="evenodd"
                                    d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                              </div>
                              <p className="text-gray-700 text-sm flex-1">
                                {rec}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                {/* Opportunities */}
                {aiInsights.opportunities &&
                  aiInsights.opportunities.length > 0 && (
                    <div className="bg-gradient-to-r from-teal-50 to-cyan-50 p-6 rounded-xl border-l-4 border-teal-500 shadow-md">
                      <div className="flex items-start gap-3 mb-4">
                        <div className="bg-teal-500 p-2 rounded-lg mt-1">
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
                        <div>
                          <h3 className="text-lg font-bold text-teal-900">
                            Growth Opportunities
                          </h3>
                          <p className="text-teal-700 text-sm">
                            Areas with potential for improvement
                          </p>
                        </div>
                      </div>
                      <div className="space-y-3 ml-11">
                        {aiInsights.opportunities.map((opp, idx) => (
                          <div
                            key={idx}
                            className="bg-white p-4 rounded-lg shadow-sm border border-teal-200"
                          >
                            <h4 className="font-semibold text-teal-900 mb-2">
                              {opp.area}
                            </h4>
                            <p className="text-gray-700 text-sm mb-3">
                              {opp.suggestion}
                            </p>
                            <div className="flex items-center gap-2 text-teal-700">
                              <svg
                                className="w-5 h-5"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                  clipRule="evenodd"
                                />
                              </svg>
                              <span className="font-semibold text-sm">
                                {opp.potential_savings}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

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
