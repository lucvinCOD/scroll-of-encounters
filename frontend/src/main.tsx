import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
import { api } from "./services/api";
import { acceptAuthCallback } from "./services/authCallback";
import type { User } from "./types";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("O elemento raiz da aplicação não foi encontrado.");
}

async function start(element: HTMLElement) {
  element.textContent = "Abrindo o Scroll of Encounters…";
  const destination = await acceptAuthCallback(window.location, (url) => window.history.replaceState(null, "", url),
    (tokens) => api.request<User>("/auth/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(tokens) }));
  if (destination) window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}#${destination}`);
  createRoot(element).render(<StrictMode><App /></StrictMode>);
}
void start(rootElement);
