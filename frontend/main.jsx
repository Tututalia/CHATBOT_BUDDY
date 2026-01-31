import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import Pages from "./pages.jsx";
import { BrowserRouter } from "react-router-dom";
import { AdminDataProvider } from "./AdminDataContext";
import ChatBot from "./src/components/ChatBot.jsx";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AdminDataProvider>
        <Pages />
        <ChatBot />
      </AdminDataProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
