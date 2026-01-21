import React from 'react'
import { useNavigate } from 'react-router-dom'

export default function Home() {
  const nav = useNavigate()
  return (
    <div className="bg-[#0d0d0d] text-gray-200 font-sans text-[1.4vw] rounded-xl shadow p-6 shadow">
      <h2 className="text-lg font-semibold mb-4">Dashboard</h2>
      <p className="text-sm text-gray-600 mb-6">Choose a journey to explore data.</p>

      <div className="flex gap-4">
        <button onClick={() => nav('/user')} className="px-6 py-3 rounded-lg bg-indigo-600 text-white">User Journey</button>
        <button onClick={() => nav('/store')} className="px-6 py-3 rounded-lg bg-green-600 text-white">Store Keeper Journey</button>
        <button onClick={() => nav('/admin')} className="px-6 py-3 rounded-lg bg-slate-700 text-white">Admin Journey</button>
      </div>
    </div>
  )
}
