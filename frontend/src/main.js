import { jsx as _jsx } from "react/jsx-runtime";
import React from "react";
import ReactDOM from "react-dom/client";
import { AppRoutes } from "./app/routes";
import { AppProviders } from "./app/providers";
import "./shared/styles/index.css";
ReactDOM.createRoot(document.getElementById("root")).render(_jsx(React.StrictMode, { children: _jsx(AppProviders, { children: _jsx(AppRoutes, {}) }) }));
