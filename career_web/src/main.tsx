import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";
import "./components/profile-longevity.css";

const resumePath = new URLSearchParams(window.location.search).get("resume");
if (resumePath?.startsWith("/career-game/") && !resumePath.includes("//")) {
  window.history.replaceState({}, "", resumePath);
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
