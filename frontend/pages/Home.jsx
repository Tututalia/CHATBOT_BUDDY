import React from "react";
import { useNavigate } from "react-router-dom";

export default function Home({ onLoginClick }) {
  const nav = useNavigate();
  return (
    <div className="bg-[#f5f5f5] py-8">
      {/* Logo and Welcome Section */}
      <div className="text-center mb-12">
        <div className="mb-6">
          <div className="inline-block bg-gradient-to-br from-red-600 to-orange-500 px-8 py-3 rounded-lg">
            <div className="text-white text-lg font-bold tracking-wide">
              FASHION & RETAIL
            </div>
          </div>
        </div>

        <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-600 to-orange-600 mb-3">
          Welcome to ABFRL Agentic Dashboard
        </h1>

        <p className="text-lg text-gray-600 max-w-4xl mx-auto">
          Navigate through different Agentic journeys for different
          persona-based user groups
        </p>
      </div>

      {/* Three Cards Section */}
      <div className="max-w-7xl mx-auto px-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Customer Journey Card */}
          <div className="rounded-2xl overflow-hidden shadow-lg">
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 p-6 text-white">
              <div className="bg-white/20 w-14 h-14 rounded-xl flex items-center justify-center mb-3">
                <svg
                  className="w-7 h-7"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold mb-1">Customer Journey</h2>
              <div className="w-12 h-0.5 bg-white/50"></div>
            </div>

            <div className="bg-white p-6">
              <p className="text-gray-600 text-sm mb-6 min-h-[90px]">
                Different AI agents to interact with customers in real time to
                fulfill purchase orders from product selection through
                post-purchase support
              </p>

              <div className="flex gap-2">
                <button
                  onClick={onLoginClick}
                  className="flex-1 px-4 py-2.5 border-2 border-red-600 text-red-600 rounded-lg font-semibold hover:bg-red-50 transition-colors flex items-center justify-center gap-1 text-sm"
                >
                  Online
                  <svg
                    className="w-3 h-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
                <button
                  onClick={onLoginClick}
                  className="flex-1 px-4 py-2.5 border-2 border-red-600 text-red-600 rounded-lg font-semibold hover:bg-red-50 transition-colors flex items-center justify-center gap-1 text-sm"
                >
                  In-Store Kiosk
                  <span>🏪</span>
                </button>
              </div>
            </div>
          </div>

          {/* Store Keeper Card */}
          <div className="rounded-2xl overflow-hidden shadow-lg">
            <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 p-6 text-white">
              <div className="bg-white/20 w-14 h-14 rounded-xl flex items-center justify-center mb-3">
                <svg
                  className="w-7 h-7"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold mb-1">Store Keeper</h2>
              <div className="w-12 h-0.5 bg-white/50"></div>
            </div>

            <div className="bg-white p-6">
              <p className="text-gray-600 text-sm mb-6 min-h-[90px]">
                Manage inventory levels, track orders, monitor store operations,
                and analyze performance metrics efficiently
              </p>

              <button
                onClick={() => nav("/store")}
                className="w-full px-4 py-2.5 border-2 border-red-600 text-red-600 rounded-lg font-semibold hover:bg-red-50 transition-colors flex items-center justify-center gap-1 text-sm"
              >
                Manage Store
                <svg
                  className="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Operations-Revenue Command Center Card */}
          <div className="rounded-2xl overflow-hidden shadow-lg">
            <div className="bg-gradient-to-br from-red-800 to-red-900 p-6 text-white">
              <div className="bg-white/20 w-14 h-14 rounded-xl flex items-center justify-center mb-3">
                <svg
                  className="w-7 h-7"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold mb-1">
                Operations-Revenue Command Center
              </h2>
              <div className="w-12 h-0.5 bg-white/50"></div>
            </div>

            <div className="bg-white p-6">
              <p className="text-gray-600 text-sm mb-6 min-h-[90px]">
                To be used by regional or zonal leaders to monitor performance
                and revenue across retail stores through agentic insights
              </p>

              <button
                onClick={() => nav("/admin")}
                className="w-full px-4 py-2.5 border-2 border-red-600 text-red-600 rounded-lg font-semibold hover:bg-red-50 transition-colors flex items-center justify-center gap-1 text-sm"
              >
                Open Command Center
                <svg
                  className="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
