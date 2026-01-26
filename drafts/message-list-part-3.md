---
title: Live Coding a Message List Component (Part 3): Sending Messages
published: false
description: Implementing the send functionality, including input handling, validation, and auto-scrolling to the latest message.
tags: react, interview, frontend
---

With the scaffold in place, we can start wiring up functionality. This part covers sending messages and auto-scrolling, which together form the core interaction.

## The Send Handler

When the user clicks "Send", we need to:

1. Ignore empty input
2. Create a new message object
3. Append it to the messages array
4. Clear the input
5. Scroll to the bottom

```typescript
const handleSend = () => {
  if (!inputValue.trim()) return;

  const newMessage = {
    id: messages.length + 1,
    text: inputValue.trim(),
  };

  setMessages([...messages, newMessage]);
  setInputValue("");
};
```

The `trim()` call handles inputs that are only whitespace. Using `messages.length + 1` for the ID works because we never delete messages — IDs will always be unique and sequential.

Wire this to the button:

```tsx
<button onClick={handleSend}>Send</button>
```

## Enter Key Support

The nice-to-have list mentions sending with Enter. This is a small addition:

```tsx
<input
  type="text"
  value={inputValue}
  onChange={(e) => setInputValue(e.target.value)}
  onKeyDown={(e) => e.key === "Enter" && handleSend()}
  placeholder="Type a message..."
/>
```

Using `onKeyDown` rather than `onKeyPress` since `onKeyPress` is deprecated.

## Auto-Scroll to Bottom

After adding a message, the list should scroll to show it. We need a ref to the scrollable container:

```typescript
const listRef = useRef<HTMLDivElement>(null);
```

Attach it to the message list:

```tsx
<div className="message-list" ref={listRef}>
```

Now we need to scroll after messages update. The direct approach — calling `scrollTo` right after `setMessages` — won't work because state updates are asynchronous. The DOM won't reflect the new message yet.

We need `useEffect` to run after the render:

```typescript
useEffect(() => {
  if (listRef.current) {
    listRef.current.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }
}, [messages]);
```

This runs whenever `messages` changes. `scrollHeight` is the total height of the content, so scrolling to it puts us at the bottom.

One subtlety: this effect also runs on initial render with the 10 hardcoded messages. That's fine — starting scrolled to the bottom is reasonable for a chat-like interface.

## Auto-Focus Input

Another nice-to-have: focusing the input on page load. A ref and effect handle this:

```typescript
const inputRef = useRef<HTMLInputElement>(null);

useEffect(() => {
  inputRef.current?.focus();
}, []);
```

The empty dependency array means this runs once on mount. Attach the ref:

```tsx
<input
  ref={inputRef}
  type="text"
  value={inputValue}
  onChange={(e) => setInputValue(e.target.value)}
  onKeyDown={(e) => e.key === "Enter" && handleSend()}
  placeholder="Type a message..."
/>
```

## Simplifying with a Form

Looking at what we've built, there's a simpler approach. Using a `<form>` element gives us Enter key submission for free, and the `autoFocus` attribute removes the need for a ref and effect:

```tsx
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
```

This eliminates `inputRef`, the focus effect, and the `onKeyDown` handler. It's also more semantic — we're submitting a form, not just clicking a button.

## Current State

Here's the full component with sending and scrolling implemented, using the form approach:

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

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTo({
        top: listRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const newMessage = {
      id: messages.length + 1,
      text: inputValue.trim(),
    };

    setMessages([...messages, newMessage]);
    setInputValue("");
  };

  return (
    <div className="app">
      <div className="jump-links">
        <button>Jump to 1</button>
        <button>Jump to 5</button>
        <button>Jump to 10</button>
      </div>

      <div className="message-list" ref={listRef}>
        {messages.map((message) => (
          <div
            key={message.id}
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

The jump links still don't work, and `highlightedId` isn't being set anywhere. That's next.

---

_Previous: [Part 2 — Architecture Decisions](/)_

_Next: [Part 4 — Jump & Highlight](/)_
