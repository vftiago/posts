---
title: Live Coding a Message List Component (Part 4): Jump & Highlight
published: false
description: Implementing the jump-to-message links with smooth scrolling and a timed highlight effect, including proper timeout cleanup.
tags: react, interview, frontend
---

The final piece of functionality: clicking "Jump to 1", "Jump to 5", or "Jump to 10" should scroll that message into view and highlight it for 1 second.

## Scrolling to a Specific Message

We need a way to reference individual message elements. Options:

1. **Refs for each message** — Store refs in an object or Map, keyed by message ID
2. **DOM query** — Use `getElementById` or similar to find the element when needed

Option 1 is more "React-like" but requires managing a collection of refs. Option 2 is simpler and works fine for this use case. We'll use data attributes and `querySelector`:

```tsx
<div
  key={message.id}
  data-message-id={message.id}
  className={`message ${highlightedId === message.id ? "highlighted" : ""}`}
>
  {message.text}
</div>
```

Then to scroll to a message:

```typescript
const jumpToMessage = (id: number) => {
  const element = document.querySelector(`[data-message-id="${id}"]`);
  element?.scrollIntoView({ behavior: "smooth" });
};
```

Wire up the buttons:

```tsx
<div className="jump-links">
  <button onClick={() => jumpToMessage(1)}>Jump to 1</button>
  <button onClick={() => jumpToMessage(5)}>Jump to 5</button>
  <button onClick={() => jumpToMessage(10)}>Jump to 10</button>
</div>
```

## Adding the Highlight

When we jump to a message, we also need to highlight it. Update `jumpToMessage`:

```typescript
const jumpToMessage = (id: number) => {
  const element = document.querySelector(`[data-message-id="${id}"]`);
  element?.scrollIntoView({ behavior: "smooth" });
  setHighlightedId(id);
};
```

The CSS from Part 2 already handles the visual:

```css
.message.highlighted {
  background: #fff3cd;
}
```

## The Timeout

The highlight should disappear after 1 second. A first attempt:

```typescript
const jumpToMessage = (id: number) => {
  const element = document.querySelector(`[data-message-id="${id}"]`);
  element?.scrollIntoView({ behavior: "smooth" });
  setHighlightedId(id);

  setTimeout(() => {
    setHighlightedId(null);
  }, 1000);
};
```

This works for a single click, but has a problem: if the user clicks "Jump to 1" and then "Jump to 5" within a second, both timeouts are running. The first timeout will clear the highlight prematurely.

We need to cancel the previous timeout when starting a new one. A ref can hold the timeout ID:

```typescript
const highlightTimeoutRef = useRef<number | null>(null);

const jumpToMessage = (id: number) => {
  const element = document.querySelector(`[data-message-id="${id}"]`);
  element?.scrollIntoView({ behavior: "smooth" });
  setHighlightedId(id);

  if (highlightTimeoutRef.current) {
    clearTimeout(highlightTimeoutRef.current);
  }

  highlightTimeoutRef.current = setTimeout(() => {
    setHighlightedId(null);
  }, 1000);
};
```

Now clicking a new jump link cancels the previous timeout, and only the latest highlight will clear after 1 second.

## Cleanup on Unmount

If the component unmounts while a timeout is pending, the callback would still fire and attempt to update state on an unmounted component. Cleaning up prevents this:

```typescript
useEffect(() => {
  return () => {
    if (highlightTimeoutRef.current) {
      clearTimeout(highlightTimeoutRef.current);
    }
  };
}, []);
```

The empty dependency array means this effect runs once on mount and cleans up on unmount.

## Final Code

Here's the complete component:

```tsx
import { useState, useRef, useEffect } from "react";
import "./App.css";

const initialMessages = Array.from({ length: 10 }, (_, i) => ({
  id: i + 1,
  text: `Message ${i + 1}`,
}));

const App = () => {
  const [messages, setMessages] = useState(initialMessages);
  const [highlightedId, setHighlightedId] = useState<number | null>(null);
  const [inputValue, setInputValue] = useState("");

  const listRef = useRef<HTMLDivElement>(null);
  const highlightTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTo({
        top: listRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  useEffect(() => {
    return () => {
      if (highlightTimeoutRef.current) {
        clearTimeout(highlightTimeoutRef.current);
      }
    };
  }, []);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const newMessage = {
      id: messages.length + 1,
      text: inputValue.trim(),
    };

    setMessages([...messages, newMessage]);
    setInputValue("");
  };

  const jumpToMessage = (id: number) => {
    const element = document.querySelector(`[data-message-id="${id}"]`);
    element?.scrollIntoView({ behavior: "smooth" });
    setHighlightedId(id);

    if (highlightTimeoutRef.current) {
      clearTimeout(highlightTimeoutRef.current);
    }

    highlightTimeoutRef.current = setTimeout(() => {
      setHighlightedId(null);
    }, 1000);
  };

  return (
    <div className="app">
      <div className="jump-links">
        <button onClick={() => jumpToMessage(1)}>Jump to 1</button>
        <button onClick={() => jumpToMessage(5)}>Jump to 5</button>
        <button onClick={() => jumpToMessage(10)}>Jump to 10</button>
      </div>

      <div className="message-list" ref={listRef}>
        {messages.map((message) => (
          <div
            key={message.id}
            data-message-id={message.id}
            className={`message ${highlightedId === message.id ? "highlighted" : ""}`}
          >
            {message.text}
          </div>
        ))}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="input-area">
        <input
          autoFocus
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type a message..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

export default App;
```

All requirements are now implemented. In Part 5, we'll review the solution, discuss what we'd improve with more time, and look at the complete code with CSS.

---

_Previous: [Part 3 — Sending Messages](/)_

_Next: [Part 5 — Polish & Retrospective](/)_
