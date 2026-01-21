import React, { useState, useEffect } from 'react'
import { useAdminData } from '../AdminDataContext';

export default function UserJourney() {
  const { records } = useAdminData();
  const [userProfile, setUserProfile] = useState(null);
  const [orderHistory, setOrderHistory] = useState([]);

  useEffect(() => {
    // Fetch user profile from backend
    fetch('/api/user/profile')
      .then(res => res.json())
      .then(data => setUserProfile(data))
      .catch(err => console.error('Error fetching user profile:', err));

    // Fetch order history from backend
    fetch('/api/user/orders')
      .then(res => res.json())
      .then(data => setOrderHistory(data))
      .catch(err => console.error('Error fetching order history:', err));
  }, []);

  // Fallback to context data if available
  const user = records?.users?.find(u => u.id === "u1") || userProfile;
  const products = records?.products || [];

  if (!user) {
    return (
      <div className="bg-[#f5f5f5] min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-8">
          <p className="text-gray-600">Loading user profile...</p>
        </div>
      </div>
    );
  }

  // Calculate product quantities from purchases
  const productMap = {};
  if (user.purchases) {
    user.purchases.forEach(pid => {
      productMap[pid] = (productMap[pid] || 0) + 1;
    });
  }

  // Get initials for avatar
  const getInitials = (name) => {
    return name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'A';
  };

  return (
    <div className="bg-[#f5f5f5] min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-12">
        
        {/* Customer Profile Section */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 w-14 h-14 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-600 to-orange-700">
                Customer Profile
              </h1>
              <p className="text-gray-600">View purchase history and loyalty details</p>
            </div>
          </div>

          {/* Profile Card */}
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl p-8 shadow-lg">
            <div className="grid grid-cols-3 gap-8 items-center">
              
              {/* Username */}
              <div>
                <p className="text-xs uppercase tracking-wide text-gray-500 mb-3 font-semibold">USERNAME</p>
                <div className="flex items-center gap-3">
                  <div className="bg-gradient-to-br from-orange-600 to-orange-700 w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    {getInitials(user.name)}
                  </div>
                  <span className="text-2xl font-bold text-gray-800">{user.name || 'Loading...'}</span>
                </div>
              </div>

              {/* Loyalty Points */}
              <div className="text-center">
                <p className="text-xs uppercase tracking-wide text-gray-500 mb-3 font-semibold">LOYALTY POINTS</p>
                <div className="inline-flex items-center gap-2 bg-white border-3 border-green-500 rounded-2xl px-6 py-3">
                  <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  <span className="text-3xl font-bold text-green-600">{user.loyaltyPoints || 850}</span>
                </div>
              </div>

              {/* User ID */}
              <div className="text-right">
                <p className="text-xs uppercase tracking-wide text-gray-500 mb-3 font-semibold">USER ID</p>
                <div className="inline-flex items-center gap-2 bg-white border-3 border-orange-500 rounded-2xl px-6 py-3">
                  <span className="text-2xl text-orange-600 font-bold">#</span>
                  <span className="text-2xl font-bold text-orange-600">{user.id || '00001'}</span>
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* Order History Section */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 w-14 h-14 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-600 to-orange-700">
              Order History
            </h2>
          </div>

          {/* Product Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.keys(productMap).map(pid => {
              const prod = products.find(p => p.id === pid);
              if (!prod) return null;
              
              return (
                <div key={pid} className="bg-white border-3 border-yellow-400 rounded-2xl overflow-hidden shadow-lg relative">
                  {/* Quantity Badge */}
                  <div className="absolute top-4 right-4 z-10">
                    <div className="bg-gradient-to-br from-orange-600 to-orange-700 text-white px-4 py-2 rounded-full flex items-center gap-1 font-bold shadow-lg">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                      <span>x{productMap[pid]}</span>
                    </div>
                  </div>

                  {/* Product Image */}
                  <div className="bg-gray-100 p-8 flex items-center justify-center" style={{ minHeight: '280px' }}>
                    {prod.image ? (
                      <img src={prod.image} alt={prod.name} className="max-h-64 object-contain" />
                    ) : (
                      <div className="w-full h-64 bg-gray-200 flex items-center justify-center text-gray-400">
                        No Image
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {Object.keys(productMap).length === 0 && (
            <div className="bg-white rounded-2xl p-12 text-center text-gray-500">
              <p>No orders found</p>
            </div>
          )}
        </div>

      </div>

      {/* Chat Button */}
      <div className="fixed bottom-8 right-8">
        <button className="bg-gradient-to-br from-orange-600 to-orange-700 text-white w-16 h-16 rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform">
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </div>
  )
}
