import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import SortableTransactionTable from './SortableTransactionTable';

export default function StoreKeeper() {
  const [storeKeeperData, setStoreKeeperData] = useState(null);
  const [transactionData, setTransactionData] = useState(null);
  const [timeRange, setTimeRange] = useState("monthly");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

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

  const fetchTransactionData = async (storeId, range) => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/store/${storeId}/transactions?time_range=${range}`);
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
  const sold = transactionData?.products_sold?.map(item => ({
    name: item.product_name,
    count: item.total_quantity
  })) || [];

  // Calculate payment stats from transactions
  const successCount = transactionData?.transactions?.filter(t => t.status === "Success").length || 0;
  const failedCount = transactionData?.transactions?.filter(t => t.status === "Failed").length || 0;

  const payments = [
    { name: 'Success', value: successCount },
    { name: 'Failed', value: failedCount }
  ]

  const COLORS = ['#4f46e5', '#ef4444']
  const storeId = storeKeeperData.store_id || "sk1"
  
  return (
    <div className="bg-[#f5f5f5] min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
      
      {/* Store Keeper Info Section */}
      <div className="mb-6 p-6 bg-gradient-to-r from-yellow-600 to-yellow-700 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold mb-4 text-white">Store Keeper Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div className="bg-white/20 backdrop-blur-sm p-3 rounded-lg">
            <p className="text-yellow-100 font-semibold mb-1">Store ID</p>
            <p className="text-white text-lg font-bold">{storeKeeperData.store_id}</p>
          </div>
          <div className="bg-white/20 backdrop-blur-sm p-3 rounded-lg">
            <p className="text-yellow-100 font-semibold mb-1">Store Name</p>
            <p className="text-white text-lg font-bold">{storeKeeperData.store_name}</p>
          </div>
          <div className="bg-white/20 backdrop-blur-sm p-3 rounded-lg">
            <p className="text-yellow-100 font-semibold mb-1">Manager</p>
            <p className="text-white text-lg font-bold">{storeKeeperData.manager}</p>
          </div>
          <div className="bg-white/20 backdrop-blur-sm p-3 rounded-lg">
            <p className="text-yellow-100 font-semibold mb-1">Phone</p>
            <p className="text-white text-lg font-bold">{storeKeeperData.phone}</p>
          </div>
        </div>
        <div className="mt-3 bg-white/20 backdrop-blur-sm p-3 rounded-lg">
          <p className="text-yellow-100 font-semibold mb-1">Address</p>
          <p className="text-white">{storeKeeperData.address}</p>
        </div>
        
        {/* JSON Response Display */}
        <details className="mt-4 bg-white/10 backdrop-blur-sm rounded-lg">
          <summary className="cursor-pointer p-3 text-white font-semibold hover:bg-white/20 rounded-lg transition-all">
            📋 View API Response (JSON)
          </summary>
          <pre className="p-4 text-xs overflow-x-auto text-gray-100 bg-black/50 rounded-b-lg mt-2">
            {JSON.stringify(storeKeeperData, null, 2)}
          </pre>
        </details>
      </div>

      <div className="space-y-6">
        {/* Product Performance Section */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-red-700 via-orange-600 to-orange-500 p-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 backdrop-blur-sm p-3 rounded-xl">
                  <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-white">Product Performance</h3>
                  <p className="text-orange-100 text-sm mt-1">Real-time performance metrics and insights</p>
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
                  <p className="text-orange-100 text-xs font-medium">Total Transactions</p>
                  <p className="text-white text-2xl font-bold">{transactionData?.total_transactions || 0}</p>
                </div>
              </div>
            </div>
          </div>
          <div className="p-8 bg-gradient-to-br from-gray-50 to-white">
            <div style={{ height: 450 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sold} margin={{ top: 20, right: 30, left: 20, bottom: 120 }}>
                  <defs>
                    <linearGradient id="colorBar" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity={1}/>
                      <stop offset="100%" stopColor="#fb923c" stopOpacity={0.8}/>
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="name" 
                    angle={-45} 
                    textAnchor="end" 
                    height={120}
                    interval={0}
                    tick={{ fontSize: 11, fill: '#6b7280' }}
                    stroke="#d1d5db"
                  />
                  <YAxis 
                    allowDecimals={false} 
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    stroke="#d1d5db"
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1f2937', 
                      border: 'none', 
                      borderRadius: '8px',
                      color: '#fff',
                      boxShadow: '0 10px 25px rgba(0,0,0,0.2)'
                    }}
                    cursor={{ fill: 'rgba(249, 115, 22, 0.1)' }}
                  />
                  <Bar 
                    dataKey="count" 
                    fill="url(#colorBar)" 
                    radius={[8, 8, 0, 0]}
                    maxBarSize={60}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Payments Section */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6">
            <div className="flex items-center gap-3">
              <div className="bg-white/20 backdrop-blur-sm p-3 rounded-xl">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                  <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Payment Analytics</h3>
                <p className="text-indigo-100 text-sm mt-1">Transaction success rate and status</p>
              </div>
            </div>
          </div>
          <div className="p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl border border-green-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-700 text-sm font-semibold uppercase tracking-wide">Successful</p>
                    <p className="text-4xl font-bold text-green-900 mt-2">{successCount}</p>
                  </div>
                  <div className="bg-green-500 p-4 rounded-full">
                    <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              </div>
              <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-xl border border-red-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-red-700 text-sm font-semibold uppercase tracking-wide">Failed</p>
                    <p className="text-4xl font-bold text-red-900 mt-2">{failedCount}</p>
                  </div>
                  <div className="bg-red-500 p-4 rounded-full">
                    <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 p-6 rounded-xl">
              <div style={{ height: 320 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie 
                      data={payments} 
                      dataKey="value" 
                      nameKey="name" 
                      cx="50%" 
                      cy="50%" 
                      outerRadius={100}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      labelLine={{ stroke: '#6b7280', strokeWidth: 1 }}
                    >
                      {payments.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Legend 
                      wrapperStyle={{ paddingTop: '20px' }}
                      iconType="circle"
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1f2937', 
                        border: 'none', 
                        borderRadius: '8px',
                        color: '#fff'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>

        {/* Transaction Table Section */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-gray-700 to-gray-800 p-6">
            <div className="flex items-center gap-3">
              <div className="bg-white/20 backdrop-blur-sm p-3 rounded-xl">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Transaction History</h3>
                <p className="text-gray-300 text-sm mt-1">Detailed transaction records and history</p>
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
  )
}
