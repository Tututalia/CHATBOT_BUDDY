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
import StoreKeeperHub from "./pages/StoreKeeperHub";
import Admin from "./pages/Admin";
import ChatBot from "./src/components/ChatBot";
import Chatbot_Kiosk from "./src/components/Chatbot_Kiosk";

export default function Pages() {
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginType, setLoginType] = useState("customer"); // "customer", "storekeeper", "admin", or "kiosk"
  const [customerId, setCustomerId] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const location = useLocation();

  // Check if user is logged in
  const isLoggedIn = localStorage.getItem("loggedInCustomerId");

  const handleLogin = async (e) => {
    e.preventDefault();

    // Trim whitespace from customer ID
    const trimmedCustomerId = customerId.trim();

    // Simple validation - check if password is "123"
    if (!trimmedCustomerId || password !== "123") {
      alert("Invalid credentials! Please use password: 123");
      return;
    }

    try {
      // Determine role_id: 1 for customer, 2 for storekeeper, 3 for admin
      const roleId =
        loginType === "admin" ? "3" : loginType === "storekeeper" ? "2" : "1";

      // Call backend API to authenticate
      const response = await fetch(
        `http://localhost:8000/api/customer/${trimmedCustomerId}/${roleId}`,
      );
      const data = await response.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      // Store user data based on login type
      if (loginType === "admin") {
        localStorage.setItem("loggedInAdminId", trimmedCustomerId);
        localStorage.setItem("userRole", roleId);
        localStorage.setItem("adminData", JSON.stringify(data));
      } else {
        localStorage.setItem("loggedInCustomerId", trimmedCustomerId);
        localStorage.setItem("userRole", roleId);

        if (loginType === "storekeeper") {
          // Store the store keeper data for use in the StoreKeeper page
          localStorage.setItem("storeKeeperData", JSON.stringify(data));
        }
      }

      setShowLoginModal(false);
      setCustomerId("");
      setPassword("");

      // Redirect based on login type
      if (loginType === "admin") {
        navigate("/admin");
      } else if (loginType === "storekeeper") {
        navigate("/store");
      } else if (loginType === "kiosk") {
        navigate("/kiosk");
      } else {
        navigate("/user");
      }
    } catch (error) {
      console.error("Login error:", error);
      alert("An error occurred during login. Please try again.");
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

  const handleStoreKeeperLogout = () => {
    localStorage.removeItem("loggedInCustomerId");
    localStorage.removeItem("userRole");
    localStorage.removeItem("storeKeeperData");
    localStorage.removeItem("kioskStoreId");
    localStorage.removeItem("skBackup_customerId");
    localStorage.removeItem("skBackup_userRole");
    localStorage.removeItem("skBackup_storeKeeperData");
    navigate("/");
  };

  const isStorePage = location.pathname.startsWith("/store");
  const isAdminPage = location.pathname === "/admin";

  const handleAdminLogout = () => {
    localStorage.removeItem("loggedInAdminId");
    localStorage.removeItem("userRole");
    localStorage.removeItem("adminData");
    navigate("/");
  };

  const handleCustomerJourneyClick = (e) => {
    e.preventDefault();
    const loggedIn = localStorage.getItem("loggedInCustomerId");
    if (loggedIn) {
      navigate("/user");
    } else {
      setLoginType("customer");
      setShowLoginModal(true);
    }
  };

  return (
    <div className="bg-[#f5f5f5] min-h-screen">
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img
                src="/images/abfrl-icon.png"
                alt="ABFRL Logo"
                className="w-12 h-12 object-contain"
              />
              <h1 className="text-2xl font-bold text-slate-800">
                POWERED BY ABFRL
              </h1>
            </div>
            <div className="flex items-center gap-6">
              <nav className="space-x-6 text-base">
                {location.pathname !== "/user" &&
                  !isStorePage &&
                  !isAdminPage && (
                    <Link
                      to="/"
                      className="text-slate-700 hover:text-red-600 font-medium"
                    >
                      Home
                    </Link>
                  )}
                {location.pathname !== "/user" &&
                  !isStorePage &&
                  !isAdminPage && (
                    <a
                      href="#"
                      onClick={handleCustomerJourneyClick}
                      className="text-slate-700 hover:text-red-600 font-medium cursor-pointer"
                    >
                      Customer Journey
                    </a>
                  )}
                {location.pathname !== "/user" &&
                  !isStorePage &&
                  !isAdminPage && (
                    <Link
                      to="/store"
                      className="text-slate-700 hover:text-red-600 font-medium"
                    >
                      Store Keeper
                    </Link>
                  )}
                {location.pathname !== "/user" &&
                  !isStorePage &&
                  !isAdminPage && (
                    <Link
                      to="/admin"
                      className="text-slate-700 hover:text-red-600 font-medium"
                    >
                      Operations-Revenue Command Center
                    </Link>
                  )}
              </nav>
              {/* Show Login button only on home page */}
              {/* {location.pathname === "/" && (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="bg-gradient-to-r from-red-600 to-orange-600 text-white px-4 py-2 rounded-lg font-semibold hover:shadow-lg transition-all duration-200"
                >
                  Login
                </button>
              )} */}
              {/* Show Logout button on user route when logged in */}
              {location.pathname === "/user" && isLoggedIn && (
                <button
                  onClick={handleLogout}
                  className="bg-gradient-to-r from-gray-600 to-gray-700 text-white px-4 py-2 rounded-lg font-semibold hover:shadow-lg transition-all duration-200"
                >
                  Logout
                </button>
              )}
              {/* Show Logout button on store pages */}
              {isStorePage && (
                <button
                  onClick={handleStoreKeeperLogout}
                  className="bg-gradient-to-r from-gray-600 to-gray-700 text-white px-4 py-2 rounded-lg font-semibold hover:shadow-lg transition-all duration-200"
                >
                  Logout
                </button>
              )}
              {/* Show Logout button on admin page */}
              {isAdminPage && (
                <button
                  onClick={handleAdminLogout}
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
              <div
                className={`w-16 h-16 bg-gradient-to-br ${loginType === "admin" ? "from-red-800 to-red-900" : loginType === "storekeeper" ? "from-yellow-500 to-yellow-600" : "from-red-600 to-orange-600"} rounded-full flex items-center justify-center mx-auto mb-4`}
              >
                <svg
                  className="w-8 h-8 text-white"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  {loginType === "admin" ? (
                    <path
                      fillRule="evenodd"
                      d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                      clipRule="evenodd"
                    />
                  ) : loginType === "storekeeper" ? (
                    <path
                      fillRule="evenodd"
                      d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z"
                      clipRule="evenodd"
                    />
                  ) : (
                    <path
                      fillRule="evenodd"
                      d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                      clipRule="evenodd"
                    />
                  )}
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-800">
                {loginType === "admin"
                  ? "Admin Login"
                  : loginType === "storekeeper"
                    ? "Store Keeper Login"
                    : "Customer Login"}
              </h2>
              <p className="text-gray-600 mt-2">
                {loginType === "admin"
                  ? "Enter your admin ID and password"
                  : loginType === "storekeeper"
                    ? "Enter your store keeper ID and password"
                    : "Enter your customer ID and password"}
              </p>
            </div>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  {loginType === "admin"
                    ? "Admin ID"
                    : loginType === "storekeeper"
                      ? "Store Keeper ID"
                      : "Customer ID"}
                </label>
                <input
                  type="text"
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  placeholder={
                    loginType === "admin"
                      ? "e.g., ADMIN001"
                      : loginType === "storekeeper"
                        ? "e.g., SK001"
                        : "e.g., CUST001"
                  }
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

            {/* Sample IDs */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <p className="text-xs font-semibold text-gray-600 mb-2">
                {loginType === "admin"
                  ? "Sample Admin IDs:"
                  : loginType === "storekeeper"
                    ? "Sample Store Keeper IDs:"
                    : "Sample Customer IDs:"}
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
                {loginType === "admin" ? (
                  <>
                    <span>ADMIN001</span>
                    <span>ADMIN002</span>
                    <span>ADMIN003</span>
                    <span>ADMIN004</span>
                  </>
                ) : loginType === "storekeeper" ? (
                  <>
                    <span>SK001</span>
                    <span>SK002</span>
                    <span>SK003</span>
                    <span>SK004</span>
                  </>
                ) : (
                  <>
                    <span>CUST001</span>
                    <span>CUST002</span>
                    <span>CUST003</span>
                    <span>CUST004</span>
                  </>
                )}
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
            element={
              <Home
                onLoginClick={(type = "customer") => {
                  setLoginType(type);
                  setShowLoginModal(true);
                }}
              />
            }
          />
          <Route path="/user" element={<UserJourney />} />
          <Route path="/store" element={<StoreKeeperHub />} />
          <Route path="/store/admin" element={<StoreKeeper />} />
          <Route
            path="/store/kiosk"
            element={<Chatbot_Kiosk customerId={isLoggedIn || "GUEST"} />}
          />
          <Route path="/admin" element={<Admin />} />
          <Route
            path="/kiosk"
            element={<Chatbot_Kiosk customerId={isLoggedIn || "GUEST"} />}
          />
        </Routes>
      </main>

      {/* Chatbot - Available on all pages except home, kiosk views and store pages */}
      {location.pathname !== "/" &&
        location.pathname !== "/kiosk" &&
        location.pathname !== "/store/kiosk" &&
        location.pathname !== "/store" &&
        location.pathname !== "/store/admin" && (
          <ChatBot customerId={isLoggedIn || "GUEST"} />
        )}
    </div>
  );
}
