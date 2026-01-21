
import React, { useState, useMemo } from 'react';
import data from '../data/admin.json'
import { useAdminData } from '../AdminDataContext';

import SortableTransactionTable from './SortableTransactionTable'; // Import the new component

// Import necessary Recharts components
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'

export default function Admin() {
   var { records } = useAdminData();

   var data =records
  
  // --- Data Processing for existing components ---
  const totals = {
    users: data.users.length,
    products: data.products.length,
    storeKeepers: data.storeKeepers.length
  }
  const userPurchaseCounts = data.users.map(u => ({
    name: u.name,
    purchases: u.purchases.length
  }))

  // --- 1. Data Processing for Online | Offline Pie Chart ---
  const purchaseModeData = Object.entries(
    data.transactions.reduce((acc, trans) => {
      acc[trans.mode] = (acc[trans.mode] || 0) + 1
      return acc
    }, {})
  ).map(([name, value]) => ({ name, value }))

  const COLORS = ['#0088FE', '#00C49F'] // Blue for Online, Green for Offline

  // --- 2. Data Processing for On Store Tables ---
     

  const storePurchases = Object.entries(
    data.transactions
      .filter(t => t.mode === 'Offline' && t.storeId)
      .reduce((acc, trans) => {
        acc[trans.storeId] = (acc[trans.storeId] || 0) + 1
        return acc
      }, {})
  ).map(([storeId, count]) => ({ storeId, count }))

  // --- 3. Data Processing for Transactions: Month wise ---
  const monthlyTransactions = data.transactions.reduce((acc, trans) => {
    if (!acc[trans.month]) {
      acc[trans.month] = { name: trans.month, Online: 0, Offline: 0 }
    }
    acc[trans.month][trans.mode] += 1 // Count transactions, not amount
    return acc
  }, {})



  const monthlyData = Object.values(monthlyTransactions).sort((a, b) => new Date(`1 ${a.name} 2023`) - new Date(`1 ${b.name} 2023`))
  const storeId=""

  
  const getStoreNameById = (id) => {
  const store = data.storeKeepers.find((item) => item.id == id);
  return store ? store.store_name : 'Unknown Store';
};

  return (
    <div className="bg-[#0d0d0d] text-gray-200 font-sans text-[1.4vw] rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Admin Dashboard</h2>

      {/* Totals Grid (Existing) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 border rounded">
          <div className="text-sm text-gray-500">Users</div>
          <div className="text-2xl font-bold">{totals.users}</div>
        </div>
        <div className="p-4 border rounded">
          <div className="text-sm text-gray-500">Products</div>
          <div className="text-2xl font-bold">{totals.products}</div>
        </div>
        <div className="p-4 border rounded">
          <div className="text-sm text-gray-500">Store Keepers</div>
          <div className="text-2xl font-bold">{totals.storeKeepers}</div>
        </div>
      </div>

      {/* New Row for Pie Chart and Store Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        
        {/* 1. Total Purchased Online | Offline Pie Chart */}
        <div className="p-4 border rounded">
          <h3 className="font-medium mb-3">Purchases: Online vs Offline</h3>
          <div style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={purchaseModeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {purchaseModeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 2. On Store Tables */}
        <div className="p-4 border rounded">
          <h3 className="font-medium mb-3">Offline Purchases per Store</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-600">
                <th className="pb-2">Store Name</th>
                <th className="pb-2">Purchases Count</th>
              </tr>
            </thead>
            <tbody>
              {storePurchases.map((store, i) => (
                <tr key={i} className="border-t">
                  <td className="py-2">{getStoreNameById(store.storeId)}</td>
                  <td className="py-2">{store.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* New Row for Monthly Transactions Chart */}
      <div className="grid grid-cols-1 gap-6 mb-6">
        {/* 3. Transactions : Month wise | Mode online or instore kyiosk */}
        <div className="p-4 border rounded">
          <h3 className="font-medium mb-3">Monthly Transaction Modes</h3>
          <div style={{ height: 350 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar dataKey="Online" stackId="a" fill="#0088FE" />
                <Bar dataKey="Offline" stackId="a" fill="#00C49F" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Original Existing Components */}
      <div className="grid grid-cols-1 lg:grid-cols-1 gap-6">
        <div className="p-4 border rounded">
          <h3 className="font-medium mb-3">Transactions</h3>
          {/* ... existing table code ... */}
           <div className="mt-8">
            <SortableTransactionTable storeId={storeId} />
          </div>
        </div>

    
      </div>
    </div>
  )
}