import React, { useState, useEffect } from "react";
import { json, useNavigate, useLocation } from "react-router-dom";
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
import SortableTransactionTable from "./SortableTransactionTable";

export default function StoreKeeper() {
  const [storeKeeperData, setStoreKeeperData] = useState(null);
  const [transactionData, setTransactionData] = useState(null);
  const [timeRange, setTimeRange] = useState("monthly");
  const [loading, setLoading] = useState(true);
  const [aiInsights, setAiInsights] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const [benchmark, setBenchmark] = useState(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [dailyOrdersData, setDailyOrdersData] = useState(null);
  const [dailyOrdersTimeRange, setDailyOrdersTimeRange] = useState("weekly");
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check if user is authenticated
    const loggedInId = localStorage.getItem("loggedInCustomerId");
    const userRole = localStorage.getItem("userRole");

    if (!loggedInId || userRole !== "2") {
      // Not authenticated as store keeper, redirect to home
      alert("Please login as a store keeper to access this page");
      navigate("/");
      return;
    }

    // Load store keeper data from localStorage
    const storedData = localStorage.getItem("storeKeeperData");
    if (storedData) {
      const data = JSON.parse(storedData);
      setStoreKeeperData(data);

      // Fetch transaction data from backend
      fetchTransactionData(data.store_id, timeRange);
    } else {
      alert("Store keeper data not found. Please login again.");
      navigate("/");
    }
  }, [navigate]);

  // Fetch transaction data when time range changes
  useEffect(() => {
    if (storeKeeperData) {
      fetchTransactionData(storeKeeperData.store_id, timeRange);
    }
  }, [timeRange, storeKeeperData]);

  // Fetch daily orders data when time range changes
  useEffect(() => {
    if (storeKeeperData) {
      fetchDailyOrders(storeKeeperData.store_id, dailyOrdersTimeRange);
    }
  }, [dailyOrdersTimeRange, storeKeeperData]);

  const fetchTransactionData = async (storeId, range) => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/api/store/${storeId}/transactions?time_range=${range}`,
      );
      const data = await response.json();

      if (data.error) {
        console.error("Error fetching transactions:", data.error);
      } else {
        setTransactionData(data);
      }
    } catch (error) {
      console.error("Error fetching transaction data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDailyOrders = async (storeId, range) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/store/${storeId}/daily-orders?time_range=${range}`,
      );
      const data = await response.json();

      if (data.error) {
        console.error("Error fetching daily orders:", data.error);
        setDailyOrdersData(null);
      } else {
        setDailyOrdersData(data);
      }
    } catch (error) {
      console.error("Error fetching daily orders:", error);
      setDailyOrdersData(null);
    }
  };

  const fetchStoreBenchmark = async (range) => {
    const cacheKey = `sk_store_benchmark_${range}`;
    try {
      const cached = sessionStorage.getItem(cacheKey);
      if (cached) {
        setBenchmark(JSON.parse(cached));
        return;
      }
    } catch {
      // ignore cache issues
    }

    try {
      setBenchmarkLoading(true);

      const storeIds = Array.from(
        { length: 23 },
        (_, i) => `STR${String(i + 1).padStart(3, "0")}`,
      );

      const results = await Promise.all(
        storeIds.map(async (id) => {
          try {
            const resp = await fetch(
              `http://localhost:8000/api/store/${id}/transactions?time_range=${range}`,
            );
            const data = await resp.json();
            const txs = data?.transactions || [];

            const revenue = txs.reduce((sum, t) => {
              if (!isRevenueStatus(t?.status)) return sum;
              const amount = Number(t?.amount);
              return sum + (Number.isFinite(amount) ? amount : 0);
            }, 0);

            return {
              store_id: id,
              txCount: txs.length,
              revenue,
            };
          } catch {
            return { store_id: id, txCount: 0, revenue: 0 };
          }
        }),
      );

      const activeStores = results.filter((r) => r.txCount > 0);
      const storeCount = activeStores.length || results.length;

      const avgRevenue =
        storeCount > 0
          ? activeStores.reduce((s, r) => s + r.revenue, 0) / storeCount
          : 0;
      const avgTx =
        storeCount > 0
          ? activeStores.reduce((s, r) => s + r.txCount, 0) / storeCount
          : 0;

      const revenueSorted = [...results].sort((a, b) => b.revenue - a.revenue);
      const txSorted = [...results].sort((a, b) => b.txCount - a.txCount);

      const revenueRank =
        revenueSorted.findIndex((r) => r.store_id === storeId) + 1 || null;
      const txRank =
        txSorted.findIndex((r) => r.store_id === storeId) + 1 || null;

      const summary = {
        range,
        storeCount: results.length,
        activeStoreCount: activeStores.length,
        avgRevenue,
        avgTx,
        revenueRank,
        txRank,
      };

      setBenchmark(summary);
      try {
        sessionStorage.setItem(cacheKey, JSON.stringify(summary));
      } catch {
        // ignore cache issues
      }
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const fetchAIInsights = async (storeId, range) => {
    // COMMENTED OUT TO SAVE TOKENS - AI insights API call disabled

    try {
      setInsightsLoading(true);
      console.log("calling store api");
      const response = await fetch(
        `http://localhost:8000/api/store/${storeId}/ai-insights?time_range=${range}`,
      );
      const data = await response.json();

      if (data.error) {
        console.error("Error fetching AI insights:", data.error);
        setAiInsights(null);
      } else {
        setAiInsights(data.insights);
        console.log("data", data?.insights);
      }
    } catch (error) {
      console.error("Error fetching AI insights:", error);
      setAiInsights(null);
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleViewInsights = () => {
    if (!showInsights) {
      if (!aiInsights) {
        fetchAIInsights(storeKeeperData.store_id, timeRange);
      }
      if (!benchmark || benchmark.range !== timeRange) {
        fetchStoreBenchmark(timeRange);
      }
    }
    setShowInsights(!showInsights);
  };

  if (!storeKeeperData || loading) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600 mx-auto mb-4"></div>
          <p className="text-gray-800">Loading store data...</p>
        </div>
      </div>
    );
  }

  // Prepare data for charts from API response
  const sold =
    transactionData?.products_sold?.map((item) => ({
      name: item.product_name,
      count: item.total_quantity,
    })) || [];

  // Calculate payment stats from transactions
  const successCount =
    transactionData?.transactions?.filter((t) => t.status === "Success")
      .length || 0;
  const failedCount =
    transactionData?.transactions?.filter((t) => t.status === "Failed")
      .length || 0;

  const payments = [
    { name: "Success", value: successCount },
    { name: "Failed", value: failedCount },
  ];

  const COLORS = ["#4f46e5", "#ef4444"];
  const storeId = storeKeeperData.store_id || "sk1";

  // --- AI Insights Key Metrics (computed from store_keeper_transactions via /transactions API) ---
  const transactionsList = transactionData?.transactions || [];
  const transactionVolume = transactionsList.length;

  const uniqueCustomers = new Set(
    transactionsList.map((t) => t?.customer_id).filter(Boolean),
  );
  const customerVisits = uniqueCustomers.size || transactionVolume;

  const isRevenueStatus = (status) => {
    const s = String(status || "")
      .trim()
      .toLowerCase();
    return (
      s === "success" || s === "complete" || s === "completed" || s === "paid"
    );
  };

  const totalRevenueInr = transactionsList.reduce((sum, t) => {
    if (!isRevenueStatus(t?.status)) return sum;
    const amount = Number(t?.amount);
    return sum + (Number.isFinite(amount) ? amount : 0);
  }, 0);

  const formatINR = (amount) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(Number.isFinite(Number(amount)) ? Number(amount) : 0);

  const parseTxDate = (dateStr) => {
    if (!dateStr) return null;
    const s = String(dateStr).trim();

    // Try M/D/YYYY (or MM/DD/YYYY)
    const mdyMatch = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (mdyMatch) {
      const month = Number(mdyMatch[1]);
      const day = Number(mdyMatch[2]);
      const year = Number(mdyMatch[3]);
      const d = new Date(Date.UTC(year, month - 1, day));
      return Number.isNaN(d.getTime()) ? null : d;
    }

    // Try ISO
    const d = new Date(s);
    return Number.isNaN(d.getTime()) ? null : d;
  };

  const toDayKey = (dateObj) => {
    if (!dateObj) return null;
    const y = dateObj.getUTCFullYear();
    const m = String(dateObj.getUTCMonth() + 1).padStart(2, "0");
    const d = String(dateObj.getUTCDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  };

  const completedTxCount = transactionsList.reduce(
    (count, t) => (isRevenueStatus(t?.status) ? count + 1 : count),
    0,
  );
  const avgTransactionValueInr =
    completedTxCount > 0 ? totalRevenueInr / completedTxCount : 0;

  // Build a simple day-series to infer transaction + revenue trends.
  const dayBuckets = new Map();
  for (const t of transactionsList) {
    const dt = parseTxDate(t?.date);
    const key = toDayKey(dt);
    if (!key) continue;

    if (!dayBuckets.has(key)) {
      dayBuckets.set(key, { txCount: 0, revenue: 0 });
    }
    const b = dayBuckets.get(key);
    b.txCount += 1;
    if (isRevenueStatus(t?.status)) {
      const amt = Number(t?.amount);
      if (Number.isFinite(amt)) b.revenue += amt;
    }
  }

  const series = Array.from(dayBuckets.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([day, v]) => ({ day, ...v }));

  const splitIndex = Math.max(1, Math.floor(series.length / 2));
  const firstHalf = series.slice(0, splitIndex);
  const secondHalf = series.slice(splitIndex);

  const sum = (arr, key) => arr.reduce((s, x) => s + (x[key] || 0), 0);
  const txFirst = sum(firstHalf, "txCount");
  const txSecond = sum(secondHalf, "txCount");
  const revFirst = sum(firstHalf, "revenue");
  const revSecond = sum(secondHalf, "revenue");

  const trendLabel = (first, second) => {
    if (series.length < 2) return "stable";
    const delta = second - first;
    const denom = Math.max(1, Math.abs(first));
    const pct = (delta / denom) * 100;
    if (pct > 10) return "increasing";
    if (pct < -10) return "decreasing";
    return "stable";
  };

  const transactionTrend = trendLabel(txFirst, txSecond);
  const revenueTrend = trendLabel(revFirst, revSecond);

  const zoneComparisonText = benchmark
    ? ` Compared with ${benchmark.activeStoreCount || benchmark.storeCount} other stores in the zone, this store ranks ${benchmark.revenueRank}/${benchmark.storeCount} by revenue and ${benchmark.txRank}/${benchmark.storeCount} by transaction volume. Zone averages are ${formatINR(benchmark.avgRevenue)} revenue and ${Math.round(benchmark.avgTx)} transactions per store.`
    : benchmarkLoading
      ? " Benchmarking performance against other stores..."
      : "";

  const performanceOverview =
    transactionVolume > 0
      ? `Over the selected period, the store recorded ${transactionVolume} transactions from ${customerVisits} customer visits. Total revenue is ${formatINR(totalRevenueInr)} with an average transaction value of ${formatINR(avgTransactionValueInr)}. Transaction activity is ${transactionTrend}, and the revenue trend is ${revenueTrend} across the period.${zoneComparisonText}`
      : aiInsights?.performance_overview ||
        "No transactions found for the selected period.";

  const defaultKeyMetrics = [
    {
      metric: "Customer Visits",
      value: `${customerVisits}`,
      insight: "Total customer visits in the selected period.",
    },
    {
      metric: "Revenue",
      value: formatINR(totalRevenueInr),
      insight: "Total revenue from completed transactions.",
    },
    {
      metric: "Transaction Volume",
      value: `${transactionVolume}`,
      insight: "Total transactions recorded for this store.",
    },
  ];

  const keyMetrics = aiInsights?.key_metrics?.length
    ? aiInsights.key_metrics.map((m) => {
        const metricName = String(m?.metric || "").toLowerCase();

        if (metricName.includes("success")) {
          return {
            ...m,
            metric: "Customer Visits",
            value: `${customerVisits}`,
            insight: "Total customer visits in the selected period.",
          };
        }

        if (metricName.includes("revenue")) {
          return {
            ...m,
            value: formatINR(totalRevenueInr),
            insight: "Total revenue from completed transactions.",
          };
        }

        if (metricName.includes("transaction")) {
          return {
            ...m,
            value: `${transactionVolume}`,
          };
        }

        return m;
      })
    : defaultKeyMetrics;

  return (
    <div className="bg-[#f5f5f5] min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Store Keeper Info Section */}
        <div className="mb-6 p-6 bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 rounded-lg shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-white">
              Store Keeper Dashboard
            </h2>
            {location.pathname === "/store/admin" && (
              <button
                onClick={() => navigate("/store")}
                className="flex items-center gap-2 px-4 py-2 bg-white/20 backdrop-blur-sm text-white rounded-lg font-semibold hover:bg-white/30 transition-all duration-200 text-sm"
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
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
                Back to Store
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div className="bg-white p-3 rounded-lg shadow-sm">
              <p className="text-gray-600 font-semibold mb-1">Store ID</p>
              <p className="text-gray-900 text-lg font-bold">
                {storeKeeperData.store_id}
              </p>
            </div>
            <div className="bg-white p-3 rounded-lg shadow-sm">
              <p className="text-gray-600 font-semibold mb-1">Store Name</p>
              <p className="text-gray-900 text-lg font-bold">
                {storeKeeperData.store_name}
              </p>
            </div>
            <div className="bg-white p-3 rounded-lg shadow-sm">
              <p className="text-gray-600 font-semibold mb-1">Manager</p>
              <p className="text-gray-900 text-lg font-bold">
                {storeKeeperData.manager}
              </p>
            </div>
            <div className="bg-white p-3 rounded-lg shadow-sm">
              <p className="text-gray-600 font-semibold mb-1">Phone</p>
              <p className="text-gray-900 text-lg font-bold">
                {storeKeeperData.phone}
              </p>
            </div>
          </div>
          <div className="mt-3 bg-white p-3 rounded-lg shadow-sm">
            <p className="text-gray-600 font-semibold mb-1">Address</p>
            <p className="text-gray-900">{storeKeeperData.address}</p>
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
                        <h3 className="text-xl font-bold text-gray-800 mb-2">
                          📊 Performance Overview
                        </h3>
                        <p className="text-gray-700 leading-relaxed">
                          {performanceOverview}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Key Metrics */}
                  {keyMetrics && (
                    <div>
                      <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <span className="text-2xl">📈</span> Key Metrics
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {keyMetrics.map((metric, index) => (
                          <div
                            key={index}
                            className="bg-white p-5 rounded-xl shadow-lg border border-gray-200 hover:shadow-xl transition-shadow"
                          >
                            <p className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
                              {metric.metric}
                            </p>
                            <p className="text-3xl font-bold text-indigo-600 my-2">
                              {metric.value}
                            </p>
                            <p className="text-sm text-gray-600">
                              {metric.insight}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Top Performing Products */}
                  {aiInsights.top_products &&
                    aiInsights.top_products.length > 0 && (
                      <div>
                        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                          <span className="text-2xl">🏆</span> Top Performing
                          Products
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {aiInsights.top_products.map((product, index) => (
                            <div
                              key={index}
                              className="bg-gradient-to-br from-green-50 to-emerald-50 p-5 rounded-xl border border-green-200 shadow-md"
                            >
                              <div className="flex items-start justify-between mb-3">
                                <h4 className="font-bold text-gray-800 text-lg">
                                  {product.product}
                                </h4>
                                <span className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                                  {product.quantity} sold
                                </span>
                              </div>
                              <p className="text-gray-700 text-sm">
                                {product.recommendation}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Underperforming Products */}
                  {aiInsights.underperforming_products &&
                    aiInsights.underperforming_products.length > 0 && (
                      <div>
                        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                          <span className="text-2xl">⚠️</span> Products Needing
                          Attention
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {aiInsights.underperforming_products.map(
                            (product, index) => (
                              <div
                                key={index}
                                className="bg-gradient-to-br from-orange-50 to-amber-50 p-5 rounded-xl border border-orange-200 shadow-md"
                              >
                                <div className="flex items-start justify-between mb-3">
                                  <h4 className="font-bold text-gray-800 text-lg">
                                    {product.product}
                                  </h4>
                                  <span className="bg-orange-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                                    {product.quantity} sold
                                  </span>
                                </div>
                                <p className="text-gray-700 text-sm">
                                  {product.recommendation}
                                </p>
                              </div>
                            ),
                          )}
                        </div>
                      </div>
                    )}

                  {/* Strategic Recommendations */}
                  {aiInsights.strategic_recommendations &&
                    aiInsights.strategic_recommendations.length > 0 && (
                      <div>
                        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                          <span className="text-2xl">🎯</span> Strategic
                          Recommendations
                        </h3>
                        <div className="space-y-4">
                          {aiInsights.strategic_recommendations.map(
                            (rec, index) => (
                              <div
                                key={index}
                                className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-purple-500"
                              >
                                <div className="flex items-start justify-between mb-2">
                                  <h4 className="font-bold text-gray-800 text-lg">
                                    {rec.title}
                                  </h4>
                                  <span
                                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                      rec.priority === "High"
                                        ? "bg-red-100 text-red-700"
                                        : rec.priority === "Medium"
                                          ? "bg-yellow-100 text-yellow-700"
                                          : "bg-blue-100 text-blue-700"
                                    }`}
                                  >
                                    {rec.priority} Priority
                                  </span>
                                </div>
                                <p className="text-gray-700">
                                  {rec.description}
                                </p>
                              </div>
                            ),
                          )}
                        </div>
                      </div>
                    )}

                  {/* Customer Attraction Strategies */}
                  {aiInsights.customer_attraction_strategies &&
                    aiInsights.customer_attraction_strategies.length > 0 && (
                      <div>
                        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                          <span className="text-2xl">🎪</span> Customer
                          Attraction Strategies
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {aiInsights.customer_attraction_strategies.map(
                            (strategy, index) => (
                              <div
                                key={index}
                                className="bg-gradient-to-br from-pink-50 to-rose-50 p-5 rounded-xl border border-pink-200 shadow-md"
                              >
                                <h4 className="font-bold text-gray-800 text-lg mb-2">
                                  {strategy.strategy}
                                </h4>
                                <p className="text-gray-700 text-sm mb-3">
                                  {strategy.description}
                                </p>
                                <div className="bg-pink-100 p-3 rounded-lg">
                                  <p className="text-xs font-semibold text-pink-800 uppercase">
                                    Expected Impact
                                  </p>
                                  <p className="text-sm text-pink-900 mt-1">
                                    {strategy.expected_impact}
                                  </p>
                                </div>
                              </div>
                            ),
                          )}
                        </div>
                      </div>
                    )}

                  {/* Loss Minimization */}
                  {aiInsights.loss_minimization &&
                    aiInsights.loss_minimization.length > 0 && (
                      <div>
                        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                          <span className="text-2xl">💰</span> Loss Minimization
                          Strategies
                        </h3>
                        <div className="space-y-4">
                          {aiInsights.loss_minimization.map((loss, index) => (
                            <div
                              key={index}
                              className="bg-gradient-to-r from-teal-50 to-cyan-50 p-5 rounded-xl border border-teal-200 shadow-md"
                            >
                              <h4 className="font-bold text-gray-800 text-lg mb-2">
                                {loss.area}
                              </h4>
                              <p className="text-gray-700 mb-3">
                                {loss.suggestion}
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
                                  {loss.potential_savings}
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
                      onClick={() =>
                        fetchAIInsights(storeKeeperData.store_id, timeRange)
                      }
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

        <div className="space-y-6">
          {/* Product Performance Section */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 p-6">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="bg-white/20 backdrop-blur-sm p-3 rounded-xl">
                    <svg
                      className="w-8 h-8 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-white">
                      Product Performance
                    </h3>
                    <p className="text-red-100 text-sm mt-1">
                      Real-time performance metrics and insights
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="flex gap-2 flex-wrap">
                    <button
                      onClick={() => setTimeRange("daily")}
                      className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 ${
                        timeRange === "daily"
                          ? "bg-yellow-500 text-white shadow-lg scale-105"
                          : "bg-white/20 backdrop-blur-sm text-white hover:bg-white/30"
                      }`}
                    >
                      Daily
                    </button>
                    <button
                      onClick={() => setTimeRange("weekly")}
                      className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 ${
                        timeRange === "weekly"
                          ? "bg-yellow-500 text-white shadow-lg scale-105"
                          : "bg-white/20 backdrop-blur-sm text-white hover:bg-white/30"
                      }`}
                    >
                      Weekly
                    </button>
                    <button
                      onClick={() => setTimeRange("monthly")}
                      className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 ${
                        timeRange === "monthly"
                          ? "bg-yellow-500 text-white shadow-lg scale-105"
                          : "bg-white/20 backdrop-blur-sm text-white hover:bg-white/30"
                      }`}
                    >
                      Monthly
                    </button>
                    <button
                      onClick={() => setTimeRange("all")}
                      className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 ${
                        timeRange === "all"
                          ? "bg-yellow-500 text-white shadow-lg scale-105"
                          : "bg-white/20 backdrop-blur-sm text-white hover:bg-white/30"
                      }`}
                    >
                      All Time
                    </button>
                  </div>
                  <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-lg">
                    <p className="text-red-100 text-xs font-medium">
                      Total Transactions
                    </p>
                    <p className="text-white text-2xl font-bold">
                      {transactionData?.total_transactions || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="p-4 bg-gradient-to-br from-gray-50 to-white">
              <div style={{ height: 700 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={sold}
                    margin={{ top: 40, right: 50, left: 50, bottom: 160 }}
                  >
                    <defs>
                      <linearGradient id="colorBar" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f59e0b" stopOpacity={1} />
                        <stop
                          offset="100%"
                          stopColor="#fb923c"
                          stopOpacity={0.8}
                        />
                      </linearGradient>
                    </defs>
                    <XAxis
                      dataKey="name"
                      angle={-45}
                      textAnchor="end"
                      height={140}
                      interval={0}
                      tick={{
                        fontSize: 13,
                        fill: "#4b5563",
                        fontWeight: 500,
                        dy: 5,
                      }}
                      stroke="#d1d5db"
                      tickMargin={12}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 13, fill: "#4b5563", fontWeight: 500 }}
                      stroke="#d1d5db"
                      tickMargin={8}
                      label={{
                        value: "Quantity Sold",
                        angle: -90,
                        position: "insideLeft",
                        style: { fill: "#6b7280", fontWeight: 600 },
                      }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "none",
                        borderRadius: "12px",
                        color: "#fff",
                        boxShadow: "0 10px 25px rgba(0,0,0,0.2)",
                        padding: "12px 16px",
                        fontSize: "14px",
                      }}
                      cursor={{ fill: "rgba(249, 115, 22, 0.1)" }}
                    />
                    <Bar
                      dataKey="count"
                      fill="url(#colorBar)"
                      radius={[10, 10, 0, 0]}
                      maxBarSize={70}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Last 7 Days Orders Section */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 p-6">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="bg-white/20 backdrop-blur-sm p-3 rounded-xl">
                    <svg
                      className="w-8 h-8 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">
                      {dailyOrdersData?.title || "Last 7 Days Orders"}
                    </h3>
                    <p className="text-red-100 text-sm mt-1">
                      Daily order trends and patterns
                    </p>
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => setDailyOrdersTimeRange("daily")}
                    className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 ${
                      dailyOrdersTimeRange === "daily"
                        ? "bg-yellow-500 text-white shadow-lg scale-105"
                        : "bg-white/20 backdrop-blur-sm text-white hover:bg-white/30"
                    }`}
                  >
                    Daily
                  </button>
                  <button
                    onClick={() => setDailyOrdersTimeRange("weekly")}
                    className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 ${
                      dailyOrdersTimeRange === "weekly"
                        ? "bg-yellow-500 text-white shadow-lg scale-105"
                        : "bg-white/20 backdrop-blur-sm text-white hover:bg-white/30"
                    }`}
                  >
                    Weekly
                  </button>
                  <button
                    onClick={() => setDailyOrdersTimeRange("monthly")}
                    className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 ${
                      dailyOrdersTimeRange === "monthly"
                        ? "bg-yellow-500 text-white shadow-lg scale-105"
                        : "bg-white/20 backdrop-blur-sm text-white hover:bg-white/30"
                    }`}
                  >
                    Past Month
                  </button>
                </div>
              </div>
            </div>
            <div className="p-8">
              {dailyOrdersData &&
              dailyOrdersData.daily_orders &&
              dailyOrdersData.daily_orders.length > 0 ? (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
                    {/* Total Orders Card */}
                    <div className="bg-gradient-to-br from-gray-50 to-white p-6 rounded-xl border border-gray-200">
                      <div className="flex flex-col items-center justify-center h-full text-center">
                        <div className="bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 p-4 rounded-full mb-4">
                          <svg
                            className="w-8 h-8 text-white"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
                          </svg>
                        </div>
                        <p className="text-gray-600 text-sm font-semibold uppercase tracking-wide mb-2">
                          Total Orders
                        </p>
                        <p className="text-5xl font-bold text-gray-900">
                          {dailyOrdersData.total_orders}
                        </p>
                      </div>
                    </div>

                    {/* Pie Chart */}
                    <div className="lg:col-span-3 bg-gradient-to-br from-gray-50 to-white p-6 rounded-xl border border-gray-200">
                      <div style={{ height: 350 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={dailyOrdersData.daily_orders}
                              dataKey="count"
                              nameKey="date"
                              cx="50%"
                              cy="50%"
                              outerRadius={140}
                              innerRadius={80}
                              label={({ date, count, percentage }) =>
                                `${new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}: ${count} (${percentage}%)`
                              }
                              labelLine={{ stroke: "#6b7280", strokeWidth: 2 }}
                            >
                              {dailyOrdersData.daily_orders.map(
                                (entry, index) => {
                                  const colors = [
                                    "#991b1b",
                                    "#b91c1c",
                                    "#dc2626",
                                    "#f97316",
                                    "#fb923c",
                                    "#fbbf24",
                                    "#fde047",
                                  ];
                                  return (
                                    <Cell
                                      key={`cell-${index}`}
                                      fill={colors[index % colors.length]}
                                    />
                                  );
                                },
                              )}
                            </Pie>
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "#1f2937",
                                border: "none",
                                borderRadius: "12px",
                                color: "#fff",
                                padding: "12px 16px",
                                boxShadow: "0 10px 25px rgba(0,0,0,0.2)",
                              }}
                              formatter={(value, name, props) => [
                                `${value} orders (${props.payload.percentage}%)`,
                                new Date(name).toLocaleDateString("en-US", {
                                  weekday: "long",
                                  month: "short",
                                  day: "numeric",
                                }),
                              ]}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  {/* Daily Breakdown Cards */}
                  <div className="mb-6">
                    <h4 className="text-lg font-bold text-gray-800 mb-4">
                      Daily Breakdown
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                      {dailyOrdersData.daily_orders.map((day, index) => {
                        const colors = [
                          "#991b1b",
                          "#b91c1c",
                          "#dc2626",
                          "#f97316",
                          "#fb923c",
                          "#fbbf24",
                          "#fde047",
                        ];
                        const date = new Date(day.date);
                        return (
                          <div
                            key={day.date}
                            className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <div
                                className="w-3 h-3 rounded-full"
                                style={{
                                  backgroundColor:
                                    colors[index % colors.length],
                                }}
                              />
                              <p className="text-xs font-semibold text-gray-600 uppercase">
                                {date.toLocaleDateString("en-US", {
                                  weekday: "short",
                                })}
                              </p>
                            </div>
                            <p className="text-2xl font-bold text-gray-900 mb-1">
                              {day.count}
                            </p>
                            <p className="text-xs text-gray-500">
                              {date.toLocaleDateString("en-US", {
                                month: "short",
                                day: "numeric",
                              })}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Summary Statistics */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-red-50 to-orange-50 p-5 rounded-xl border border-red-200">
                      <div className="flex items-center gap-3">
                        <div className="bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 p-3 rounded-lg">
                          <svg
                            className="w-6 h-6 text-white"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                        <div>
                          <p className="text-xs text-red-700 font-semibold uppercase tracking-wide">
                            Peak Day
                          </p>
                          <p className="text-lg font-bold text-red-900">
                            {dailyOrdersData.peak_day
                              ? `${new Date(dailyOrdersData.peak_day.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })} (${dailyOrdersData.peak_day.count})`
                              : "N/A"}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-gradient-to-br from-orange-50 to-yellow-50 p-5 rounded-xl border border-orange-200">
                      <div className="flex items-center gap-3">
                        <div className="bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 p-3 rounded-lg">
                          <svg
                            className="w-6 h-6 text-white"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-xs text-orange-700 font-semibold uppercase tracking-wide">
                            Avg Daily
                          </p>
                          <p className="text-lg font-bold text-orange-900">
                            {dailyOrdersData.avg_daily} orders
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-gradient-to-br from-yellow-50 to-amber-50 p-5 rounded-xl border border-yellow-200">
                      <div className="flex items-center gap-3">
                        <div className="bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 p-3 rounded-lg">
                          <svg
                            className="w-6 h-6 text-white"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                        <div>
                          <p className="text-xs text-yellow-700 font-semibold uppercase tracking-wide">
                            Growth
                          </p>
                          <p className="text-lg font-bold text-yellow-900">
                            {dailyOrdersData.growth || "N/A"}
                          </p>
                        </div>
                      </div>
                    </div>
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
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <p className="text-gray-600 font-medium">No orders found</p>
                  <p className="text-gray-400 text-sm mt-2">
                    No orders in the selected time range
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Transaction Table Section */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 p-6">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 backdrop-blur-sm p-3 rounded-xl">
                  <svg
                    className="w-8 h-8 text-white"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white">
                    Transaction History
                  </h3>
                  <p className="text-red-100 text-sm mt-1">
                    Detailed transaction records and history
                  </p>
                </div>
              </div>
            </div>
            <div className="p-6">
              <SortableTransactionTable storeId={storeId} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
