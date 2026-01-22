import React, { useState, useEffect } from "react";
import { useAdminData } from "../AdminDataContext";

export default function UserJourney() {
  const { records } = useAdminData();
  const [userProfile, setUserProfile] = useState(null);
  const [orderHistory, setOrderHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Get the logged-in customer ID from localStorage
    const loggedInCustomerId = localStorage.getItem("loggedInCustomerId");

    if (!loggedInCustomerId) {
      setError("No customer logged in");
      setLoading(false);
      return;
    }

    // Fetch customer profile from backend
    fetch(`http://localhost:8000/api/customer/${loggedInCustomerId}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
        } else {
          setUserProfile(data);
        }
      })
      .catch((err) => {
        console.error("Error fetching customer profile:", err);
        setError("Failed to load customer profile");
      });

    // Fetch customer orders from backend
    fetch(`http://localhost:8000/api/customer/${loggedInCustomerId}/orders`)
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
        } else {
          setOrderHistory(data.order_history || []);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching order history:", err);
        setError("Failed to load order history");
        setLoading(false);
      });
  }, []);

  // Fallback to context data if backend fails
  const user = userProfile || records?.users?.find((u) => u.id === "u1");
  const products =
    orderHistory.length > 0 ? orderHistory : records?.products || [];

  if (loading) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading customer profile...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                <p className="font-semibold">Error</p>
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-8">
          <p className="text-gray-600">No customer data available...</p>
        </div>
      </div>
    );
  }

  // Calculate product quantities from purchases (for order history)
  const productMap = {};
  if (orderHistory && orderHistory.length > 0) {
    orderHistory.forEach((product) => {
      const pid = product.product_id;
      productMap[pid] = (productMap[pid] || 0) + 1;
    });
  }

  // Get initials for avatar
  const getInitials = (name) => {
    return (
      name
        ?.split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase() || "A"
    );
  };

  return (
    <div className="bg-[#f5f5f5] min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-12">
        {/* Customer Profile Section */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 w-14 h-14 rounded-2xl flex items-center justify-center">
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
            <div>
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-600 to-orange-700">
                Customer Profile
              </h1>
              <p className="text-gray-600">
                View purchase history and loyalty details
              </p>
            </div>
          </div>

          {/* Profile Card */}
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl p-8 shadow-lg">
            <div className="grid grid-cols-2 gap-8">
              {/* Left Column - Customer Info */}
              <div>
                <p className="text-xs uppercase tracking-wide text-gray-500 mb-3 font-semibold">
                  CUSTOMER INFORMATION
                </p>
                <div className="flex items-start gap-3 mb-4">
                  <div className="bg-gradient-to-br from-orange-600 to-orange-700 w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                    {getInitials(user.customer_name || user.name)}
                  </div>
                  <div className="flex-1">
                    <span className="text-2xl font-bold text-gray-800 block mb-2">
                      {user.customer_name || user.name || "Loading..."}
                    </span>
                    {/* Phone Number */}
                    {user.phone && (
                      <div className="flex items-center gap-2 text-gray-600 mb-2">
                        <svg
                          className="w-4 h-4 text-orange-600"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
                        </svg>
                        <span className="text-sm font-medium">
                          {user.phone}
                        </span>
                      </div>
                    )}
                    {/* Address */}
                    {user.address && (
                      <div className="flex items-start gap-2 text-gray-600">
                        <svg
                          className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span className="text-sm font-medium">
                          {user.address}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column - Loyalty Points and Customer ID */}
              <div className="grid grid-cols-2 gap-6">
                {/* Loyalty Points */}
                <div className="text-center">
                  <p className="text-xs uppercase tracking-wide text-gray-500 mb-3 font-semibold">
                    LOYALTY POINTS
                  </p>
                  <div className="inline-flex items-center gap-2 bg-white border-3 border-green-500 rounded-2xl px-6 py-3">
                    <svg
                      className="w-6 h-6 text-green-600"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    <span className="text-3xl font-bold text-green-600">
                      {user.loyalty_points || user.loyaltyPoints || 0}
                    </span>
                  </div>
                </div>

                {/* User ID */}
                <div className="text-center">
                  <p className="text-xs uppercase tracking-wide text-gray-500 mb-3 font-semibold">
                    CUSTOMER ID
                  </p>
                  <div className="inline-flex items-center gap-2 bg-white border-3 border-orange-500 rounded-2xl px-6 py-3">
                    <span className="text-2xl text-orange-600 font-bold">
                      #
                    </span>
                    <span className="text-2xl font-bold text-orange-600">
                      {user.customer_id || user.id || "00001"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Order History Section */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 w-14 h-14 rounded-2xl flex items-center justify-center">
              <svg
                className="w-8 h-8 text-white"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-600 to-orange-700">
              Order History
            </h2>
          </div>

          {/* Product Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {orderHistory && orderHistory.length > 0 ? (
              Object.keys(productMap).map((pid) => {
                const prod = orderHistory.find((p) => p.product_id === pid);
                if (!prod) return null;

                return (
                  <div
                    key={pid}
                    className="bg-white border-3 border-yellow-400 rounded-2xl overflow-hidden shadow-lg relative"
                  >
                    {/* Quantity Badge */}
                    <div className="absolute top-4 right-4 z-10">
                      <div className="bg-gradient-to-br from-orange-600 to-orange-700 text-white px-4 py-2 rounded-full flex items-center gap-1 font-bold shadow-lg">
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                          />
                        </svg>
                        <span>x{productMap[pid]}</span>
                      </div>
                    </div>

                    {/* Product Image */}
                    <div
                      className="bg-gray-100 p-8 flex items-center justify-center"
                      style={{ minHeight: "280px" }}
                    >
                      {prod.image_reference ? (
                        <img
                          src={prod.image_reference}
                          alt={prod.product_name}
                          className="max-h-64 object-contain"
                        />
                      ) : (
                        <div className="w-full h-64 bg-gray-200 flex items-center justify-center text-gray-400 rounded-lg">
                          <div className="text-center">
                            <svg
                              className="w-16 h-16 mx-auto mb-4 text-gray-300"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                                clipRule="evenodd"
                              />
                            </svg>
                            <p className="text-sm">{prod.product_name}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Product Details */}
                    <div className="p-6">
                      <h3 className="text-lg font-bold text-gray-800 mb-2">
                        {prod.product_name}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2">
                        Category: {prod.category}
                      </p>
                      <p className="text-xl font-bold text-green-600 mb-3">
                        ₹{prod.price}
                      </p>
                      {/* Purchase Date */}
                      {prod.purchase_date && (
                        <div className="mb-3 flex items-center gap-2 text-sm text-gray-600">
                          <svg
                            className="w-4 h-4 text-orange-600"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="font-medium">
                            Purchased: {prod.purchase_date}
                          </span>
                        </div>
                      )}
                      <div className="mt-3">
                        <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                          {prod.season}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="col-span-full bg-white rounded-2xl p-12 text-center text-gray-500">
                <svg
                  className="w-16 h-16 mx-auto mb-4 text-gray-300"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
                </svg>
                <p className="text-lg font-semibold mb-2">No orders found</p>
                <p>This customer hasn't made any purchases yet.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chat Button */}
      <div className="fixed bottom-8 right-8">
        <button className="bg-gradient-to-br from-orange-600 to-orange-700 text-white w-16 h-16 rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform">
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
