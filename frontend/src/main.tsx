import React from "react";
import ReactDOM from "react-dom/client";

import { AppRoutes } from "./app/routes";
import { AppProviders } from "./app/providers";
import "./shared/styles/index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppProviders>
      <AppRoutes />
    </AppProviders>
  </React.StrictMode>
);
