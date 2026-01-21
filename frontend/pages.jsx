import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import UserJourney from './pages/UserJourney'
import StoreKeeper from './pages/StoreKeeper'
import Admin from './pages/Admin'

export default function Pages() {
  return (
    <div className="bg-[#f5f5f5] min-h-screen">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-red-600 to-orange-500 rounded-lg"></div>
              <h1 className="text-xl font-bold text-slate-800">Agentic Dashboard</h1>
            </div>
            <nav className="space-x-6 text-base">
              <Link to="/" className="text-slate-700 hover:text-red-600 font-medium">Home</Link>
              <Link to="/user" className="text-slate-700 hover:text-red-600 font-medium">Customer Journey</Link>
              <Link to="/store" className="text-slate-700 hover:text-red-600 font-medium">Store Keeper</Link>
              <Link to="/admin" className="text-slate-700 hover:text-red-600 font-medium">Operations-Revenue Command Center</Link>
            </nav>
          </div>
        </div>
      </header>

      <main>
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
