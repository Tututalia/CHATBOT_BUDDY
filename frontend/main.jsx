import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import Pages from "./pages.jsx";
import { BrowserRouter } from "react-router-dom";
import { AdminDataProvider } from "./AdminDataContext";

createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <AdminDataProvider>
      <Pages />
    </AdminDataProvider>
  </BrowserRouter>,
);
