import React, { useState } from "react";
import {
  Routes,
  Route,
  Link,
  useNavigate,
  useLocation,
} from "react-router-dom";
import Home from "./pages/Home";
import UserJourney from "./pages/UserJourney";
import StoreKeeper from "./pages/StoreKeeper";
import Admin from "./pages/Admin";

export default function Pages() {
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [customerId, setCustomerId] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const location = useLocation();

  // Check if user is logged in
  const isLoggedIn = localStorage.getItem("loggedInCustomerId");

  const handleLogin = (e) => {
    e.preventDefault();

    // Simple validation - check if customer ID is provided and password is "123"
    if (customerId && password === "123") {
      // Store customer ID in localStorage for now
      localStorage.setItem("loggedInCustomerId", customerId);
      setShowLoginModal(false);
      setCustomerId("");
      setPassword("");
      // Redirect to user profile
      navigate("/user");
    } else {
      alert("Invalid credentials! Please use password: 123");
    }
  };

  const closeModal = () => {
    setShowLoginModal(false);
    setCustomerId("");
    setPassword("");
  };

  const handleLogout = () => {
    localStorage.removeItem("loggedInCustomerId");
    navigate("/");
  };

  return (
    <div className="bg-[#f5f5f5] min-h-screen">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-red-600 to-orange-500 rounded-lg"></div>
              <h1 className="text-xl font-bold text-slate-800">
                Agentic Dashboard
              </h1>
            </div>
            <div className="flex items-center gap-6">
              <nav className="space-x-6 text-base">
                <Link
                  to="/"
                  className="text-slate-700 hover:text-red-600 font-medium"
                >
                  Home
                </Link>
                <Link
                  to="/user"
                  className="text-slate-700 hover:text-red-600 font-medium"
                >
                  Customer Journey
                </Link>
                <Link
                  to="/store"
                  className="text-slate-700 hover:text-red-600 font-medium"
                >
                  Store Keeper
                </Link>
                <Link
                  to="/admin"
                  className="text-slate-700 hover:text-red-600 font-medium"
                >
                  Operations-Revenue Command Center
                </Link>
              </nav>
              {/* Show Login button only on home page */}
              {location.pathname === "/" && (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="bg-gradient-to-r from-red-600 to-orange-600 text-white px-4 py-2 rounded-lg font-semibold hover:shadow-lg transition-all duration-200"
                >
                  Login
                </button>
              )}
              {/* Show Logout button on user route when logged in */}
              {location.pathname === "/user" && isLoggedIn && (
                <button
                  onClick={handleLogout}
                  className="bg-gradient-to-r from-gray-600 to-gray-700 text-white px-4 py-2 rounded-lg font-semibold hover:shadow-lg transition-all duration-200"
                >
                  Logout
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-8 w-96 relative">
            {/* Close button */}
            <button
              onClick={closeModal}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>

            {/* Modal Header */}
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-red-600 to-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-white"
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
              <h2 className="text-2xl font-bold text-gray-800">
                Customer Login
              </h2>
              <p className="text-gray-600 mt-2">
                Enter your customer ID and password
              </p>
            </div>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Customer ID
                </label>
                <input
                  type="text"
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  placeholder="e.g., CUST001"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Hint: Password is "123" for all customers
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-red-600 to-orange-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all duration-200"
                >
                  Login
                </button>
              </div>
            </form>

            {/* Sample Customer IDs */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <p className="text-xs font-semibold text-gray-600 mb-2">
                Sample Customer IDs:
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
                <span>CUST001</span>
                <span>CUST002</span>
                <span>CUST003</span>
                <span>CUST004</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}

      <main>
        <Routes>
          <Route
            path="/"
            element={<Home onLoginClick={() => setShowLoginModal(true)} />}
          />
          <Route path="/user" element={<UserJourney />} />
          <Route path="/store" element={<StoreKeeper />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
    </div>
  );
}
