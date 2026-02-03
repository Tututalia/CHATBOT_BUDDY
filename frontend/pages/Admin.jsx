
import React, { useState, useEffect } from 'react';

// Import necessary Recharts components
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'

export default function Admin() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('overview');
  const [timeRange, setTimeRange] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const transactionsPerPage = 10;

  // Fetch dashboard data from API
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/api/admin/dashboard?time_range=${timeRange}`);
        const data = await response.json();
        setDashboardData(data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
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
          <div className="text-xl text-red-500">Error loading dashboard data</div>
        </div>
      </div>
    );
  }
  
  // --- Data Processing for existing components ---
  const totals = {
    customers: dashboardData.summary.total_customers,
    productsSold: dashboardData.summary.total_products_sold,
    retailStores: dashboardData.summary.total_retail_stores
  }

  // --- 1. Data Processing for Online vs Offline Pie Chart ---
  const onlineVsOfflineData = [
    { 
      name: 'Online', 
      value: dashboardData.transactions_overview.online.count 
    },
    { 
      name: 'Offline', 
      value: dashboardData.transactions_overview.offline.count 
    }
  ];

  const ONLINE_OFFLINE_COLORS = ['#A52A2A', '#FFA500']; // Maroon for Online, Orange for Offline

  // --- Calculate Top Customers for Online ---
  const onlineCustomerPurchases = {};
  
  dashboardData.transactions
    .filter(t => t.mode.toLowerCase() === 'online')
    .forEach(trans => {
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
      count: data.count
    }));

  // --- Calculate Top Customers for Offline ---
  const offlineCustomerPurchases = {};
  
  dashboardData.transactions
    .filter(t => t.mode.toLowerCase() === 'offline')
    .forEach(trans => {
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
      count: data.count
    }));

  // --- Calculate Offline Sales by Store ---
  const offlineStoreSales = {};
  
  dashboardData.transactions
    .filter(t => t.mode.toLowerCase() === 'offline')
    .forEach(trans => {
      const storeName = trans.store_name || 'Unknown Store';
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
      count: data.count
    }));

  // Generate distinct colors for pie chart (orange/yellow shades for stores)
  const STORE_COLORS = [
    '#FFA500', '#FFB84D', '#FF8C00', '#FFD700', '#F4A460',
    '#DAA520', '#CD853F', '#D2691E', '#B8860B', '#8B4513',
    '#A0522D', '#D2B48C', '#DEB887', '#F5DEB3'
  ];

  const CUSTOMER_COLORS = [
    '#8B1A1A', '#A52A2A', '#C44536', '#D2691E', '#E07B39',
    '#FF8C42', '#FFA500', '#FFB84D', '#CD853F', '#D2B48C'
  ];

  // Determine which data to show based on active view
  const getPieChartData = () => {
    if (activeView === 'online') return topOnlineCustomers;
    if (activeView === 'offline') return offlineSalesByStore;
    return onlineVsOfflineData;
  };

  const getPieChartColors = () => {
    if (activeView === 'overview') return ONLINE_OFFLINE_COLORS;
    if (activeView === 'offline') return STORE_COLORS;
    return CUSTOMER_COLORS;
  };

  const pieChartData = getPieChartData();
  const pieChartColors = getPieChartColors();

  // --- 2. Data Processing for Offline Purchases per Store ---
  const storePurchases = dashboardData.offline_purchases_per_store || [];

  // --- 3. Data Processing for Transactions: Month wise ---
  const monthlyData = dashboardData.monthly_trends.map(trend => ({
    name: trend.month,
    Online: trend.online,
    Offline: trend.offline
  }));

  const storeId = "";

  // Pagination logic
  const totalTransactions = dashboardData.transactions.length;
  const totalPages = Math.ceil(totalTransactions / transactionsPerPage);
  const indexOfLastTransaction = currentPage * transactionsPerPage;
  const indexOfFirstTransaction = indexOfLastTransaction - transactionsPerPage;
  const currentTransactions = dashboardData.transactions.slice(indexOfFirstTransaction, indexOfLastTransaction);

  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
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
        pageNumbers.push('...');
        pageNumbers.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pageNumbers.push(1);
        pageNumbers.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) pageNumbers.push(i);
      } else {
        pageNumbers.push(1);
        pageNumbers.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pageNumbers.push(i);
        pageNumbers.push('...');
        pageNumbers.push(totalPages);
      }
    }
    
    return pageNumbers;
  };

  return (
    <div className="bg-gray-50 min-h-screen p-6">
      {/* Header */}
      <div className="flex items-center mb-6">
        <div className="w-12 h-12 bg-gradient-to-br from-red-800 to-orange-600 rounded-lg flex items-center justify-center mr-4">
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
          </svg>
        </div>
        <div>
          <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-700 to-orange-600">
            Operations-Revenue Dashboard
          </h2>
          <p className="text-gray-600 text-sm">Complete analytics and performance metrics</p>
        </div>
      </div>

      {/* Top Stats Grid - 3 Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="text-sm text-gray-500 mb-2">No of Customer</div>
          <div className="text-4xl font-bold text-red-700">{totals.customers.toLocaleString()}</div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="text-sm text-gray-500 mb-2">No of Product Sold</div>
          <div className="text-4xl font-bold text-orange-600">{totals.productsSold.toLocaleString()}</div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="text-sm text-gray-500 mb-2">No of Retail Stores</div>
          <div className="text-4xl font-bold text-orange-600">{totals.retailStores}</div>
        </div>
      </div>

      {/* New Row for Pie Chart and Store Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        
        {/* 1. Total Transactions: Online vs Offline */}
        <div className="rounded-xl shadow-lg overflow-hidden">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-red-800 to-orange-600 p-6">
            <h3 className="text-xl font-semibold mb-3 text-white">
              {activeView === 'overview' && 'Total Transactions: Online vs Offline(Past 1 Month)'}
              {activeView === 'online' && 'Online Sales by Top Customers'}
              {activeView === 'offline' && 'Offline Sales by Store'}
            </h3>
            {/* Tab-like buttons */}
            <div className="flex gap-2 bg-orange-200/30 p-1 rounded-lg">
              <button 
                onClick={() => setActiveView('overview')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeView === 'overview' 
                    ? 'bg-white text-red-900' 
                    : 'bg-transparent text-white hover:bg-white/20'
                }`}
              >
                Overview
              </button>
              <button 
                onClick={() => setActiveView('online')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeView === 'online' 
                    ? 'bg-white text-red-900' 
                    : 'bg-transparent text-white hover:bg-white/20'
                }`}
              >
                Online
              </button>
              <button 
                onClick={() => setActiveView('offline')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeView === 'offline' 
                    ? 'bg-white text-red-900' 
                    : 'bg-transparent text-white hover:bg-white/20'
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
                      <Cell key={`cell-${index}`} fill={pieChartColors[index % pieChartColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value, name, props) => {
                      if (activeView === 'overview') {
                        return [value, name];
                      }
                      return [`₹${value.toLocaleString('en-IN')}`, `${props.payload.name} (${props.payload.count} items)`];
                    }}
                  />
                  {activeView === 'overview' && <Legend />}
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            {/* Total Revenue Section */}
            <div className="mt-6 border-2 border-yellow-400 rounded-xl p-4 bg-orange-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-orange-600 to-orange-700 rounded-xl flex items-center justify-center">
                    <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 uppercase tracking-wide font-semibold">Total Revenue</div>
                    <div className="text-3xl font-bold text-orange-700">
                      ₹{(
                        activeView === 'overview' ? dashboardData.summary.total_revenue :
                        activeView === 'online' ? dashboardData.transactions_overview.online.revenue :
                        dashboardData.transactions_overview.offline.revenue
                      ).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="bg-white px-4 py-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">Transactions</div>
                    <div className="text-xl font-bold text-red-700">
                      {(
                        activeView === 'overview' ? dashboardData.summary.total_transactions :
                        activeView === 'online' ? dashboardData.transactions_overview.online.count :
                        dashboardData.transactions_overview.offline.count
                      ).toLocaleString('en-IN')}
                    </div>
                  </div>
                  <div className="bg-white px-4 py-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">Avg Value</div>
                    <div className="text-xl font-bold text-orange-600">
                      ₹{(
                        activeView === 'overview' ? dashboardData.summary.avg_transaction_value :
                        activeView === 'online' ? (dashboardData.transactions_overview.online.count > 0 
                          ? dashboardData.transactions_overview.online.revenue / dashboardData.transactions_overview.online.count 
                          : 0) :
                        (dashboardData.transactions_overview.offline.count > 0 
                          ? dashboardData.transactions_overview.offline.revenue / dashboardData.transactions_overview.offline.count 
                          : 0)
                      ).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
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
            <h3 className="text-xl font-semibold text-white">Offline Purchases per Store</h3>
          </div>
          {/* Table area with white background and scroll */}
          <div className="bg-white max-h-[500px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 sticky top-0">
                <tr className="text-left text-gray-700">
                  <th className="py-3 px-6 font-semibold">Store Name</th>
                  <th className="py-3 px-6 font-semibold text-right">Purchases Count</th>
                </tr>
              </thead>
              <tbody className="text-gray-800">
                {storePurchases.map((store, i) => (
                  <tr key={i} className="border-t border-gray-200 hover:bg-gray-50 transition-colors">
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

      {/* New Row for Monthly Transactions Chart */}
      <div className="grid grid-cols-1 gap-6 mb-6">
        {/* 3. Monthly Transaction Trends */}
        <div className="rounded-xl shadow-lg overflow-hidden">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-red-800 to-orange-600 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white">Monthly Transaction Trends</h3>
                <p className="text-sm text-orange-100">Online vs Offline sales comparison</p>
              </div>
            </div>
          </div>
          
          {/* Chart area with white background */}
          <div className="bg-white p-6">
            <div style={{ height: 350 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <XAxis dataKey="name" stroke="#6B7280" />
                  <YAxis allowDecimals={false} stroke="#6B7280" label={{ value: 'Number of Transactions', angle: -90, position: 'insideLeft' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: '8px' }}
                    labelStyle={{ color: '#1F2937' }}
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
                  <div className="text-xs text-gray-600 uppercase tracking-wide font-semibold">Online Transactions</div>
                </div>
                <div className="text-4xl font-bold text-red-800">
                  {dashboardData.transactions_overview.online.count.toLocaleString('en-IN')}
                </div>
              </div>
              <div className="bg-orange-50 border-2 border-orange-200 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                  <div className="text-xs text-gray-600 uppercase tracking-wide font-semibold">Offline Transactions</div>
                </div>
                <div className="text-4xl font-bold text-orange-600">
                  {dashboardData.transactions_overview.offline.count.toLocaleString('en-IN')}
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
                <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                  <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white">Transaction History of ABFRL Stores across the Zone</h3>
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
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
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
                  <tr key={transaction.id || index} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="py-4 px-6 font-semibold text-red-700">{transaction.id}</td>
                    <td className="py-4 px-6 text-gray-600">{transaction.date}</td>
                    <td className="py-4 px-6 font-medium">{transaction.user_name}</td>
                    <td className="py-4 px-6 text-gray-600">{transaction.product}</td>
                    <td className="py-4 px-6 text-center font-semibold">{transaction.qty}</td>
                    <td className="py-4 px-6">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        transaction.mode.toLowerCase() === 'online' 
                          ? 'bg-red-100 text-red-700' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {transaction.mode}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-gray-600">{transaction.store_name}</td>
                    <td className="py-4 px-6">
                      <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-semibold">
                        {transaction.status}
                      </span>
                    </td>
                    <td className="py-4 px-6 font-semibold">₹{transaction.amount.toFixed(2)}</td>
                    <td className="py-4 px-6 text-gray-600">{transaction.address}</td>
                    <td className="py-4 px-6 text-gray-600">{transaction.phone}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          <div className="bg-white border-t border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Showing {indexOfFirstTransaction + 1} to {Math.min(indexOfLastTransaction, totalTransactions)} of {totalTransactions} transactions
              </div>
              
              <div className="flex items-center gap-2">
                {/* Previous Button */}
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === 1
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Previous
                </button>
                
                {/* Page Numbers */}
                <div className="flex items-center gap-1">
                  {getPageNumbers().map((pageNum, idx) => (
                    pageNum === '...' ? (
                      <span key={`ellipsis-${idx}`} className="px-3 py-2 text-gray-500">...</span>
                    ) : (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                          currentPage === pageNum
                            ? 'bg-gradient-to-r from-red-600 to-orange-500 text-white'
                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    )
                  ))}
                </div>
                
                {/* Next Button */}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === totalPages
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
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
  )
}