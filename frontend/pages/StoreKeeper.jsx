import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAdminData } from '../AdminDataContext';
import data from '../data/admin.json'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import SortableTransactionTable from './SortableTransactionTable'; // Import the new component

export default function StoreKeeper() {
  const [storeKeeperData, setStoreKeeperData] = useState(null);
  const navigate = useNavigate();
  
  var { records } = useAdminData();

  var data = records

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
      setStoreKeeperData(JSON.parse(storedData));
    } else {
      alert("Store keeper data not found. Please login again.");
      navigate("/");
    }
  }, [navigate]);

  if (!storeKeeperData) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600 mx-auto mb-4"></div>
          <p className="text-gray-800">Loading store keeper data...</p>
        </div>
      </div>
    );
  }
  
  const sold = data.storeStats.productsSold.map(item => {
    const product = data.products.find(p => p.id === item.productId)
    return { name: product ? product.name : `Product ${item.productId}`, count: item.count }
  })

  const payments = [
    { name: 'Success', value: data.storeStats.paymentsSuccess },
    { name: 'Failed', value: data.storeStats.paymentsFailed }
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

      <h2 className="text-xl font-semibold mb-4 text-gray-800">Store Analytics</h2>
      <div className="grid grid-cols-1 lg:grid-cols-1 gap-6">
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h3 className="font-medium mb-4 text-gray-800 text-lg">Products Sold</h3>
          <div style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sold}>
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#4f46e5" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h3 className="font-medium mb-4 text-gray-800 text-lg">Payments: Success vs Failed</h3>
          <div style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={payments} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {payments.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 text-sm text-gray-700">
            Failed payments: <span className="font-semibold text-red-600">{data.storeStats.paymentsFailed}</span>
          </div>

          <div>
            
            <SortableTransactionTable storeId={storeId} />

          </div>
        </div>
      </div>
      </div>
    </div>
  )
}
