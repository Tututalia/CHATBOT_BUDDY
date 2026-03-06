import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function StoreKeeperHub() {
  const [storeKeeperData, setStoreKeeperData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCustomerLogin, setShowCustomerLogin] = useState(false);
  const [custId, setCustId] = useState("");
  const [custPassword, setCustPassword] = useState("");
  const navigate = useNavigate();

  const handleCustomerKioskLogin = async (e) => {
    e.preventDefault();
    const trimmedId = custId.trim();
    if (!trimmedId || custPassword !== "123") {
      alert("Invalid credentials! Please use password: 123");
      return;
    }
    try {
      const response = await fetch(
        `http://localhost:8000/api/customer/${trimmedId}/1`,
      );
      const data = await response.json();
      if (data.error) {
        alert(data.error);
        return;
      }
      // Preserve store keeper session so we can restore it when exiting kiosk
      localStorage.setItem(
        "skBackup_customerId",
        localStorage.getItem("loggedInCustomerId") || "",
      );
      localStorage.setItem(
        "skBackup_userRole",
        localStorage.getItem("userRole") || "",
      );
      localStorage.setItem(
        "skBackup_storeKeeperData",
        localStorage.getItem("storeKeeperData") || "",
      );

      localStorage.setItem("loggedInCustomerId", trimmedId);
      localStorage.setItem("userRole", "1");
      // Save the store keeper's store_id for the kiosk to use
      if (storeKeeperData?.store_id) {
        localStorage.setItem("kioskStoreId", storeKeeperData.store_id);
      }
      setShowCustomerLogin(false);
      setCustId("");
      setCustPassword("");
      navigate("/store/kiosk");
    } catch (error) {
      console.error("Login error:", error);
      alert("An error occurred during login. Please try again.");
    }
  };

  useEffect(() => {
    const loggedInId = localStorage.getItem("loggedInCustomerId");
    const userRole = localStorage.getItem("userRole");

    if (!loggedInId || userRole !== "2") {
      alert("Please login as a store keeper to access this page");
      navigate("/");
      return;
    }

    const storedData = localStorage.getItem("storeKeeperData");
    if (storedData) {
      setStoreKeeperData(JSON.parse(storedData));
      setLoading(false);
    } else {
      alert("Store keeper data not found. Please login again.");
      navigate("/");
    }
  }, [navigate]);

  if (loading || !storeKeeperData) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600 mx-auto mb-4"></div>
          <p className="text-gray-800">Loading store data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#f5f5f5] min-h-screen flex flex-col">
      {/* ── Panel 1: Store Details + Navigation Buttons ── */}
      <div className="w-full px-6 pt-6 pb-4">
        <div className="max-w-7xl mx-auto">
          <div className="bg-gradient-to-r from-red-900 via-red-700 to-yellow-600 rounded-xl shadow-lg p-6">
            {/* Title row */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-5">
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <svg
                  className="w-7 h-7 text-white"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z"
                    clipRule="evenodd"
                  />
                </svg>
                Store Dashboard
              </h2>

              {/* Navigation Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => navigate("/store/admin")}
                  className="flex items-center gap-2 px-6 py-2.5 bg-white text-red-800 font-semibold rounded-lg shadow hover:shadow-lg hover:scale-[1.03] transition-all duration-200"
                >
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M3 3a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V3zm0 6a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V9zm1 5a1 1 0 00-1 1v2a1 1 0 001 1h12a1 1 0 001-1v-2a1 1 0 00-1-1H4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Store Admin
                </button>
                <button
                  onClick={() => setShowCustomerLogin(true)}
                  className="flex items-center gap-2 px-6 py-2.5 bg-yellow-400 text-red-900 font-semibold rounded-lg shadow hover:shadow-lg hover:scale-[1.03] transition-all duration-200"
                >
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm14 1a1 1 0 00-1-1H5a1 1 0 00-1 1v4a1 1 0 001 1h10a1 1 0 001-1V6zM2 15.5a.5.5 0 01.5-.5h15a.5.5 0 010 1h-15a.5.5 0 01-.5-.5z" />
                  </svg>
                  Customer Kiosk
                </button>
              </div>
            </div>

            {/* Store detail cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              <div className="bg-white p-3 rounded-lg shadow-sm">
                <p className="text-gray-600 font-semibold mb-1">Store ID</p>
                <p className="text-gray-900 text-lg font-bold">
                  {storeKeeperData.store_id}
                </p>
              </div>
              <div className="bg-white p-3 rounded-lg shadow-sm">
                <p className="text-gray-600 font-semibold mb-1">Store Name</p>
                <p className="text-gray-900 text-lg font-bold">
                  {storeKeeperData.store_name}
                </p>
              </div>
              <div className="bg-white p-3 rounded-lg shadow-sm">
                <p className="text-gray-600 font-semibold mb-1">Manager</p>
                <p className="text-gray-900 text-lg font-bold">
                  {storeKeeperData.manager}
                </p>
              </div>
              <div className="bg-white p-3 rounded-lg shadow-sm">
                <p className="text-gray-600 font-semibold mb-1">Phone</p>
                <p className="text-gray-900 text-lg font-bold">
                  {storeKeeperData.phone}
                </p>
              </div>
            </div>
            <div className="mt-3 bg-white p-3 rounded-lg shadow-sm">
              <p className="text-gray-600 font-semibold mb-1">Address</p>
              <p className="text-gray-900">{storeKeeperData.address}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Panel 2: Promotional Video (looped, muted) ── */}
      <div className="flex-1 px-6 pb-6">
        <div className="max-w-7xl mx-auto h-full">
          <div
            className="relative w-full rounded-xl overflow-hidden shadow-lg bg-black"
            style={{ minHeight: "460px" }}
          >
            <video
              className="w-full h-full object-cover rounded-xl"
              style={{ minHeight: "460px" }}
              src="/videos/Pantaloons_OnLoop_JP_Nagar_Bengaluru_1080P.mp4"
              autoPlay
              loop
              muted
              playsInline
            />
          </div>
        </div>
      </div>

      {/* ── Customer Login Modal ── */}
      {showCustomerLogin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-8 w-96 relative">
            {/* Close button */}
            <button
              onClick={() => {
                setShowCustomerLogin(false);
                setCustId("");
                setCustPassword("");
              }}
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

            {/* Header */}
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-yellow-500 rounded-full flex items-center justify-center mx-auto mb-4">
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
                Customer Kiosk Login
              </h2>
              <p className="text-gray-600 mt-2">
                Enter customer ID and password to start kiosk session
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleCustomerKioskLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Customer ID
                </label>
                <input
                  type="text"
                  value={custId}
                  onChange={(e) => setCustId(e.target.value)}
                  placeholder="e.g., CUST001"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={custPassword}
                  onChange={(e) => setCustPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Hint: Password is "123" for all customers
                </p>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCustomerLogin(false);
                    setCustId("");
                    setCustPassword("");
                  }}
                  className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-orange-500 to-yellow-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all duration-200"
                >
                  Login
                </button>
              </div>
            </form>

            {/* Sample IDs */}
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
    </div>
  );
}
