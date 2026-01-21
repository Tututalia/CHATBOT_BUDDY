import React, { useState } from "react";
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import Pages from "./pages.jsx";
import { BrowserRouter } from 'react-router-dom'
import { AdminDataProvider } from './AdminDataContext';

export default function ChatWidget() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Floating Icon */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-3 right-3 bg-blue-600 text-white w-10 h-10 rounded-full shadow-2xl flex items-center justify-center text-3xl hover:bg-blue-700 transition-all"
      >
        🤖
      </button>

      {/* Chat Window */}
      {open && (
        <div className="fixed bottom-20 right-3 w-[100%] h-[650px] bg-[#0d0d0d] text-gray-200 font-sans text-[1.4vw] rounded-2xl shadow-2xl border border-gray-300 overflow-hidden animate-fade-in">
         
               <App />
         
        </div>
      )}
    </>
  );
}

createRoot(document.getElementById('root')).render(
   <React.StrictMode>
     <BrowserRouter>
      <AdminDataProvider>
       <Pages />
       <ChatWidget/> 
       </AdminDataProvider>
     </BrowserRouter>
   </React.StrictMode>
);
