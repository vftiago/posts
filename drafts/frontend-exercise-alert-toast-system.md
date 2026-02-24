---
title: Frontend Coding Challenge — Alert Toast System
published: false
description: Walking through a hypothetical frontend live coding challenge step-by-step — building a toast notification system with routing persistence.
tags: react, interview, frontend
# cover_image: https://direct_url_to_image.jpg
# Use a ratio of 100:42 for best results.
# published_at: 2026-02-23 16:00 +0000
---

This post walks through a hypothetical frontend live coding challenge from the perspective of the interviewee, focusing on the reasoning behind each decision.

## The Challenge

Build a toast notification system in React.

**Constraints**

- Use Vite with the `react-ts` template. No other constraints.

**Requirements**

- Three alert types: success, warning, and error
- Each alert has a title and a message
- Alerts auto-dismiss after 5 seconds, or the user can dismiss them manually
- Multiple alerts can be visible at the same time
- Alerts stack vertically, with the oldest at the bottom
- Alerts remain visible across route navigation — create two dummy pages to demonstrate this

## Going through the Requirements

**"Three alert types: success, warning, and error"**

Each type will need distinct visual styling — color, icon, or both. A union type (`"success" | "warning" | "error"`) constrains the values at the type level.

**"Each alert has a title and a message"**

This defines the data shape. Combined with the type, each alert is an object with at least `type`, `title`, and `message`. We'll also need an `id` for keying and removal.

**"Alerts auto-dismiss after 5 seconds, or the user can dismiss them manually"**

Two removal paths for the same alert. The timeout needs to be cleaned up if the user dismisses manually — otherwise the callback fires on an ID for an alert that's already been removed, which is harmless but wasteful. The removal logic handles this naturally — filtering out a non-existent ID is a no-op.

**"Multiple alerts can be visible at the same time"**

This means the state is an array, not a single value. Each alert manages its own timeout independently.

**"Alerts stack vertically, with the oldest at the bottom"**

If alerts render in array order (first to last, top to bottom in the DOM), then "oldest at the bottom" means new alerts are _prepended_ to the array, or we render from bottom to top using CSS. The more natural approach is to append new alerts to the array and use `flex-direction: column-reverse` on the container, or simply render in order and position the container at the bottom of the viewport with newest on top. We'll think about this when we get to the layout.

Actually, let's be precise: "oldest at the bottom" with a stack growing upward means the newest alert appears at the top of the stack. If we position the toast container at the bottom-right of the viewport (a common pattern), new toasts appear above existing ones. The simplest approach is to append to the array and render them in order inside a container that's anchored to the bottom — each new item pushes the stack up naturally.

**"Alerts remain visible across route navigation"**

This is the most architecturally significant requirement. If alert state lives inside a page component, navigating away destroys it. The state needs to live _above_ the router — in a React context provider that wraps the entire application. This is the key insight: the toast system is application-level state, not page-level state.

## Architecture Decisions

### Routing

We need React Router for client-side navigation. Two minimal pages are sufficient — what they display doesn't matter, as long as each page has buttons to trigger alerts and links to navigate between them.

### State Management

The alert state must survive route changes, so it lives in a context provider that wraps the router. The provider exposes two things: the current list of alerts, and a function to add new ones. Removal is handled internally (via timeout or dismiss button), though exposing a `removeAlert` function keeps the API flexible.

```
<AlertProvider>        // owns the alert state
  <BrowserRouter>
    <Nav />            // navigation links
    <Routes>
      <Route ... />    // page components call addAlert
      <Route ... />
    </Routes>
    <AlertContainer /> // renders the toast stack
  </BrowserRouter>
</AlertProvider>
```

`AlertContainer` is rendered outside the routes, at a fixed position on the screen, so it's unaffected by route changes.

### Component Structure

For a live coding exercise, we want to minimize the number of files without losing clarity. We'll use three files:

- **App.tsx** — Routes, navigation, page components, and the root layout
- **AlertContext.tsx** — The context, provider, and `useAlerts` hook
- **App.css** — All styles

The page components are trivial, so extracting them into separate files would just add import wiring for no real benefit.

### Data Shape

```typescript
type AlertType = "success" | "warning" | "error";

type Alert = {
  id: number;
  type: AlertType;
  title: string;
  message: string;
};
```

A numeric auto-incrementing ID is sufficient. We never reorder or reuse IDs — each alert gets the next number in the sequence.

## Environment Setup

```bash
npm create vite@latest alert-system -- --template react-ts
cd alert-system
npm install react-router-dom
```

React Router is the only dependency beyond Vite's template. Note that React Router v6.4 introduced `createBrowserRouter` and `RouterProvider` as the recommended data-routing API, and v7 took this further by merging with Remix to offer a framework mode with file-based routing. The classic `BrowserRouter` component still works in v7's library mode and is simpler to set up — a pragmatic choice for a timed exercise.

## Building the Alert Context

The context needs to provide two things to consumers: a way to add alerts, and a way to remove them. The alert list itself is only needed by the `AlertContainer`, but since the container also lives in the component tree, it consumes the same context.

```tsx
import { createContext, useContext, useState, useCallback, useRef } from "react";

type AlertType = "success" | "warning" | "error";

type Alert = {
  id: number;
  type: AlertType;
  title: string;
  message: string;
};

type AlertContextValue = {
  alerts: Alert[];
  addAlert: (type: AlertType, title: string, message: string) => void;
  removeAlert: (id: number) => void;
};

const AlertContext = createContext<AlertContextValue | null>(null);
```

We initialize the context with `null` rather than a dummy default object. This way, if `useAlerts` is called outside a provider, we get an explicit error instead of silent misbehavior:

```typescript
function useAlerts() {
  const context = useContext(AlertContext);

  if (context === null) {
    throw new Error("useAlerts must be used within an AlertProvider");
  }

  return context;
}
```

### The Provider

```tsx
function AlertProvider({ children }: { children: React.ReactNode }) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const nextId = useRef(0);

  const removeAlert = useCallback((id: number) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== id));
  }, []);

  const addAlert = useCallback(
    (type: AlertType, title: string, message: string) => {
      const id = nextId.current++;

      setAlerts((prev) => [...prev, { id, type, title, message }]);

      setTimeout(() => {
        removeAlert(id);
      }, 5000);
    },
    [removeAlert],
  );

  return <AlertContext.Provider value={{ alerts, addAlert, removeAlert }}>{children}</AlertContext.Provider>;
}
```

A few things to note:

**ID generation** — `nextId` is a ref, not state, because changing it shouldn't trigger a re-render. Each call to `addAlert` grabs the current value and increments it. This is safe because the read and increment happen synchronously within a single function call, and JavaScript executes on a single thread — there's no concurrent access to worry about.

**Auto-dismiss timeout** — The `setTimeout` is set up at add time, capturing the `id` in its closure. When it fires, it calls `removeAlert`, which filters the array. If the user already dismissed the alert manually, the filter still runs — `prev.filter(...)` returns an array without the already-removed ID, which is the same content but a new array reference. Since `filter` always returns a new array reference, React will re-render the provider and any consumers that read `alerts` from context, even though nothing visually changed. React's reconciliation will determine that no DOM mutations are needed, so nothing happens on screen — but the component tree still goes through a render cycle. This is technically wasteful, but the cost is negligible and adding a guard (e.g., checking whether the ID exists before calling `setAlerts`) would complicate the code for no user-visible benefit.

**`useCallback`** — Both `addAlert` and `removeAlert` are wrapped in `useCallback` to maintain stable references. This prevents unnecessary re-renders of consumers that depend on these functions. `removeAlert` has no dependencies (it only uses `setAlerts` with a functional update), and `addAlert` depends on `removeAlert`. Since `removeAlert`'s reference is stable thanks to `useCallback` with an empty dependency array, `addAlert`'s reference is also stable.

### Why Not Clean Up Timeouts?

A common pattern for components with timeouts is to store timeout IDs in a ref and clear them on unmount. We don't do that here, and the reasoning is straightforward: the `AlertProvider` wraps the entire application — it mounts once and never unmounts during the app's lifetime. There's no unmount to clean up for. If we were building this as a library where the provider might be conditionally rendered, we'd store timeout IDs in a Map and clear them in a cleanup effect. For this exercise, the added complexity isn't justified.

## The Page Components

Two minimal pages, each with buttons to trigger different alert types:

```tsx
function Home() {
  const { addAlert } = useAlerts();

  return (
    <div className="page">
      <h2>Home</h2>
      <p>Trigger alerts and navigate to Settings — they'll persist.</p>
      <div className="alert-buttons">
        <button onClick={() => addAlert("success", "Upload Complete", "Your file has been uploaded successfully.")}>
          Success Alert
        </button>
        <button
          onClick={() => addAlert("warning", "Storage Almost Full", "You've used 90% of your available storage.")}
        >
          Warning Alert
        </button>
        <button
          onClick={() => addAlert("error", "Connection Lost", "Unable to reach the server. Retrying in 30 seconds.")}
        >
          Error Alert
        </button>
      </div>
    </div>
  );
}

function Settings() {
  const { addAlert } = useAlerts();

  return (
    <div className="page">
      <h2>Settings</h2>
      <p>Alerts triggered on Home are still visible here.</p>
      <div className="alert-buttons">
        <button onClick={() => addAlert("success", "Settings Saved", "Your preferences have been updated.")}>
          Success Alert
        </button>
        <button onClick={() => addAlert("warning", "Weak Password", "Consider using a stronger password.")}>
          Warning Alert
        </button>
        <button onClick={() => addAlert("error", "Delete Failed", "Could not delete your account. Please try again.")}>
          Error Alert
        </button>
      </div>
    </div>
  );
}
```

These are intentionally simple. The content doesn't matter — the point is that each page can add alerts, and alerts created on one page remain visible after navigating to the other.

## The Alert Container

This component reads the alert list from context and renders them in a fixed-position container:

```tsx
function AlertContainer() {
  const { alerts, removeAlert } = useAlerts();

  return (
    <div className="alert-container">
      {alerts.map((alert) => (
        <div key={alert.id} className={`alert alert-${alert.type}`}>
          <div className="alert-content">
            <strong className="alert-title">{alert.title}</strong>
            <p className="alert-message">{alert.message}</p>
          </div>
          <button className="alert-dismiss" onClick={() => removeAlert(alert.id)} aria-label="Dismiss alert">
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
```

The `alert-${alert.type}` class gives us per-type styling without conditional logic in the component. The dismiss button calls `removeAlert` directly — the timeout for that alert is still scheduled, but as discussed, it will be a no-op when it fires.

### Stacking Order

The container is anchored to the bottom-right of the viewport with `position: fixed`. Alerts render in array order, and since new alerts are appended to the end of the array, they appear after existing ones in the DOM — which with normal flex column layout would place them visually below. But the requirement says the oldest should be at the bottom — meaning new alerts should appear _above_ existing ones.

`flex-direction: column-reverse` solves this. It reverses the visual order so the last item in the array (newest) appears at the top, and the first (oldest) at the bottom. The container grows upward from its anchored bottom position.

One tradeoff to be aware of: `column-reverse` creates a mismatch between visual order and DOM order. Screen readers and keyboard tab order follow the DOM (oldest first), while sighted users see newest first. For a toast system where the only interactive element per toast is a dismiss button, this is a minor concern — but in a production system, you might instead prepend new alerts to the array and use regular `column` direction, so DOM order matches visual order.

```css
.alert-container {
  position: fixed;
  bottom: 16px;
  right: 16px;
  display: flex;
  flex-direction: column-reverse;
  gap: 8px;
  z-index: 1000;
}
```

## Wiring Up the App

```tsx
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import "./App.css";

function App() {
  return (
    <AlertProvider>
      <BrowserRouter>
        <nav className="nav">
          <Link to="/">Home</Link>
          <Link to="/settings">Settings</Link>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        <AlertContainer />
      </BrowserRouter>
    </AlertProvider>
  );
}

export default App;
```

`AlertProvider` wraps everything, so both page components and the `AlertContainer` share the same context. The `AlertContainer` sits outside `<Routes>`, so it's always rendered regardless of which route is active.

## Requirements Checklist

- ✓ Three alert types: success, warning, and error
- ✓ Each alert has a title and a message
- ✓ Alerts auto-dismiss after 5 seconds
- ✓ User can dismiss alerts manually
- ✓ Multiple alerts can be visible simultaneously
- ✓ Alerts stack vertically, oldest at the bottom
- ✓ Alerts persist across route navigation

## What We'd Improve

**Animations** — Alerts appear and disappear abruptly. Entry animations are straightforward (a CSS animation triggered on mount), but exit animations are harder — React removes the DOM node immediately on unmount, so there's no opportunity to play a transition. You'd either use a library like `framer-motion` or manage a "leaving" state that triggers a CSS exit animation before actually removing the element from the DOM.

**Accessibility** — The alert container should use `aria-live="polite"` so screen readers announce new alerts. The dismiss button already has an `aria-label`, but keyboard navigation through the alert stack could be improved.

**Pause on hover** — A common pattern is to pause the auto-dismiss timer when the user hovers over an alert. This would require storing timeout IDs (likely in a Map keyed by alert ID) and using `clearTimeout`/`setTimeout` in `mouseenter`/`mouseleave` handlers, along with tracking how much time has elapsed.

**Deduplication** — If the same alert is triggered rapidly (e.g., a network error retrying every second), the stack fills up with identical messages. A production system might deduplicate by content, or cap the maximum number of visible alerts.

---

## Final Code

**AlertContext.tsx**

```tsx
import { createContext, useContext, useState, useCallback, useRef } from "react";

type AlertType = "success" | "warning" | "error";

type Alert = {
  id: number;
  type: AlertType;
  title: string;
  message: string;
};

type AlertContextValue = {
  alerts: Alert[];
  addAlert: (type: AlertType, title: string, message: string) => void;
  removeAlert: (id: number) => void;
};

const AlertContext = createContext<AlertContextValue | null>(null);

export function useAlerts() {
  const context = useContext(AlertContext);

  if (context === null) {
    throw new Error("useAlerts must be used within an AlertProvider");
  }

  return context;
}

export function AlertProvider({ children }: { children: React.ReactNode }) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const nextId = useRef(0);

  const removeAlert = useCallback((id: number) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== id));
  }, []);

  const addAlert = useCallback(
    (type: AlertType, title: string, message: string) => {
      const id = nextId.current++;

      setAlerts((prev) => [...prev, { id, type, title, message }]);

      setTimeout(() => {
        removeAlert(id);
      }, 5000);
    },
    [removeAlert],
  );

  return <AlertContext.Provider value={{ alerts, addAlert, removeAlert }}>{children}</AlertContext.Provider>;
}
```

**App.tsx**

```tsx
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { AlertProvider, useAlerts } from "./AlertContext";
import "./App.css";

function Home() {
  const { addAlert } = useAlerts();

  return (
    <div className="page">
      <h2>Home</h2>
      <p>Trigger alerts and navigate to Settings — they'll persist.</p>
      <div className="alert-buttons">
        <button onClick={() => addAlert("success", "Upload Complete", "Your file has been uploaded successfully.")}>
          Success Alert
        </button>
        <button
          onClick={() => addAlert("warning", "Storage Almost Full", "You've used 90% of your available storage.")}
        >
          Warning Alert
        </button>
        <button
          onClick={() => addAlert("error", "Connection Lost", "Unable to reach the server. Retrying in 30 seconds.")}
        >
          Error Alert
        </button>
      </div>
    </div>
  );
}

function Settings() {
  const { addAlert } = useAlerts();

  return (
    <div className="page">
      <h2>Settings</h2>
      <p>Alerts triggered on Home are still visible here.</p>
      <div className="alert-buttons">
        <button onClick={() => addAlert("success", "Settings Saved", "Your preferences have been updated.")}>
          Success Alert
        </button>
        <button onClick={() => addAlert("warning", "Weak Password", "Consider using a stronger password.")}>
          Warning Alert
        </button>
        <button onClick={() => addAlert("error", "Delete Failed", "Could not delete your account. Please try again.")}>
          Error Alert
        </button>
      </div>
    </div>
  );
}

function AlertContainer() {
  const { alerts, removeAlert } = useAlerts();

  return (
    <div className="alert-container">
      {alerts.map((alert) => (
        <div key={alert.id} className={`alert alert-${alert.type}`}>
          <div className="alert-content">
            <strong className="alert-title">{alert.title}</strong>
            <p className="alert-message">{alert.message}</p>
          </div>
          <button className="alert-dismiss" onClick={() => removeAlert(alert.id)} aria-label="Dismiss alert">
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

function App() {
  return (
    <AlertProvider>
      <BrowserRouter>
        <nav className="nav">
          <Link to="/">Home</Link>
          <Link to="/settings">Settings</Link>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        <AlertContainer />
      </BrowserRouter>
    </AlertProvider>
  );
}

export default App;
```

**App.css**

```css
.nav {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #ccc;
}

.nav a {
  text-decoration: none;
  color: #333;
  font-weight: 500;
}

.nav a:hover {
  color: #0066cc;
}

.page {
  padding: 16px;
}

.alert-buttons {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.alert-container {
  position: fixed;
  bottom: 16px;
  right: 16px;
  display: flex;
  flex-direction: column-reverse;
  gap: 8px;
  z-index: 1000;
  max-width: 360px;
}

.alert {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 6px;
  border-left: 4px solid;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.alert-success {
  border-left-color: #16a34a;
}

.alert-warning {
  border-left-color: #ca8a04;
}

.alert-error {
  border-left-color: #dc2626;
}

.alert-content {
  flex: 1;
}

.alert-title {
  display: block;
  margin-bottom: 4px;
}

.alert-message {
  margin: 0;
  font-size: 0.875rem;
  color: #555;
}

.alert-dismiss {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #999;
  padding: 0;
  line-height: 1;
}

.alert-dismiss:hover {
  color: #333;
}
```

## Wrapping Up

The key architectural decision in this exercise is recognizing that toast notifications are application-level state. The moment the requirements mention "persists across navigation", that rules out local component state and points toward a context provider wrapping the router. Everything else — the stacking, the auto-dismiss, the dismiss button — follows naturally once that structure is in place.
