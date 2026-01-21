import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import UserJourney from './pages/UserJourney'
import StoreKeeper from './pages/StoreKeeper'
import Admin from './pages/Admin'

export default function Pages() {
  return (
    <div className="bg-[#eee] text-gray-200 font-sans text-[1.4vw] rounded-xl shadow p-6 min-h-screen p-6 ">
      <header className="max-w-6xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-slate-800">Agentic Dashboard</h1>
          <nav className="space-x-3 text-sm">
            <Link to="/" className="text-indigo-600">Home</Link>
            <Link to="/user" className="text-slate-600">User</Link>
            <Link to="/store" className="text-slate-600">Store Keeper</Link>
            <Link to="/admin" className="text-slate-600">Admin</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/user" element={<UserJourney />} />
          <Route path="/store" element={<StoreKeeper />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
    </div>
  )
}
