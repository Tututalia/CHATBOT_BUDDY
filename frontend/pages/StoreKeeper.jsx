import React from 'react'
import { useAdminData } from '../AdminDataContext';
import data from '../data/admin.json'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import SortableTransactionTable from './SortableTransactionTable'; // Import the new component

export default function StoreKeeper() {
  
  var { records } = useAdminData();

  var data =records
  
  const sold = data.storeStats.productsSold.map(item => {
    const product = data.products.find(p => p.id === item.productId)
    return { name: product ? product.name : `Product ${item.productId}`, count: item.count }
  })

  const payments = [
    { name: 'Success', value: data.storeStats.paymentsSuccess },
    { name: 'Failed', value: data.storeStats.paymentsFailed }
  ]

  const COLORS = ['#4f46e5', '#ef4444']
  const storeId="sk1"
  return (
    <div className="bg-[#0d0d0d] text-gray-200 font-sans text-[1.4vw] rounded-xl shadow p-6 shadow">
      <h2 className="text-lg font-semibold mb-4">Store Keeper Journey</h2>
      <div className="grid grid-cols-1 lg:grid-cols-1 gap-6">
        <div className="p-4 border rounded">
          <h3 className="font-medium mb-2">Products Sold</h3>
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

        <div className="p-4 border rounded">
          <h3 className="font-medium mb-2">Payments: Success vs Failed</h3>
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
          <div className="mt-3 text-sm text-gray-600">
            Failed payments: <span className="font-semibold">{data.storeStats.paymentsFailed}</span>
          </div>

          <div>
            
            <SortableTransactionTable storeId={storeId} />

          </div>
        </div>
      </div>
    </div>
  )
}
