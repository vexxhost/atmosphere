import RFB from "./core/rfb.js";

const params = new URLSearchParams(window.location.search);
const path = params.get("path") || "";
const parentOriginParam = params.get("parentOrigin");

function trustedParentOrigin(value) {
  if (!value) return null;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:"
      ? parsed.origin
      : null;
  } catch {
    return null;
  }
}

const parentOrigin = trustedParentOrigin(parentOriginParam);
const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const port = window.location.port ? `:${window.location.port}` : "";
const webSocketUrl = `${protocol}://${window.location.hostname}${port}/${path}`;
const status = document.getElementById("status");

function setStatus(message, hidden = false) {
  status.textContent = message;
  status.classList.toggle("hidden", hidden);
}

let rfb;
try {
  rfb = new RFB(document.getElementById("screen"), webSocketUrl);
  rfb.viewOnly = false;
  rfb.scaleViewport = true;
  rfb.resizeSession = true;
  rfb.background = "#000";
  rfb.showDotCursor = true;
} catch (error) {
  setStatus(`Failed to initialize: ${error.message}`);
  throw error;
}

rfb.addEventListener("connect", () => setStatus("Connected", true));
rfb.addEventListener("disconnect", (event) =>
  setStatus(event.detail.clean ? "Disconnected" : "Connection lost"),
);
rfb.addEventListener("credentialsrequired", () => setStatus("Credentials required"));
rfb.addEventListener("securityfailure", (event) =>
  setStatus(`Authentication failed: ${event.detail.reason || ""}`),
);

window.addEventListener("message", (event) => {
  if (!parentOrigin || event.origin !== parentOrigin || event.source !== window.parent) {
    return;
  }

  const { type, payload } = event.data || {};
  if (!rfb || typeof type !== "string") return;

  switch (type) {
    case "sunrise:ctrlAltDel":
      rfb.sendCtrlAltDel();
      break;
    case "sunrise:sendKey":
      rfb.sendKey(payload?.keysym, payload?.code, payload?.down);
      break;
    case "sunrise:disconnect":
      rfb.disconnect();
      break;
    case "sunrise:focus":
      rfb.focus();
      break;
    case "sunrise:ping":
      event.source?.postMessage({ type: "sunrise:pong" }, parentOrigin);
      break;
  }
});

if (parentOrigin && window.parent !== window) {
  window.parent.postMessage({ type: "sunrise:ready" }, parentOrigin);
}
