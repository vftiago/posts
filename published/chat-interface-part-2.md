---
title: Frontend Coding Challenge — Chat-Like Interface (Part 2)
published: false
description: Walking through a hypothetical frontend live coding challenge step-by-step.
tags: react, interview, frontend
cover_image:
---

_This is Part 2 of a two-part series. [Part 1](https://dev.to/vftiago/frontend-coding-challenge-chat-like-interface-part-1-262g) covered requirements analysis, architecture decisions, and sending messages._

Now we need to wire up the jump links: clicking "Jump to First" or "Jump to Last" should scroll that message into view and highlight it for 1 second.

## Scrolling to a Specific Message

We already implemented `messageRefs`, a Map storing refs to each message element. The same Map that powers auto-scroll also enables jumping to any message:

```typescript
const jumpToMessage = (id: number) => {
  messageRefs.current.get(id)?.scrollIntoView({ behavior: "smooth" });
};
```

Since we're using 0-based IDs (matching array indices), the first message has ID `0` and the last has ID `messages.length - 1`:

```tsx
<div className="jump-links">
  <button onClick={() => jumpToMessage(0)}>Jump to First</button>
  <button onClick={() => jumpToMessage(messages.length - 1)}>Jump to Last</button>
</div>
```

## Adding the Highlight

When we jump to a message, we also need to highlight it:

```typescript
const jumpToMessage = (id: number) => {
  messageRefs.current.get(id)?.scrollIntoView({ behavior: "smooth" });
  setHighlightedId(id);
};
```

The CSS from Part 1 already handles the visual:

```css
.message.highlighted {
  background: #fff3cd;
}
```

## The Timeout

The highlight should disappear after 1 second. A first attempt:

```typescript
const jumpToMessage = (id: number) => {
  messageRefs.current.get(id)?.scrollIntoView({ behavior: "smooth" });
  setHighlightedId(id);

  setTimeout(() => {
    setHighlightedId(null);
  }, 1000);
};
```

This works for a single click, but has a problem: if the user clicks "Jump to First" and then "Jump to Last" within a second, both timeouts are scheduled. The first timeout will clear the highlight prematurely.

We need to cancel the previous timeout when starting a new one. A ref can hold the timeout ID:

```typescript
const highlightTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

const jumpToMessage = (id: number) => {
  messageRefs.current.get(id)?.scrollIntoView({ behavior: "smooth" });
  setHighlightedId(id);

  if (highlightTimeoutRef.current !== null) {
    clearTimeout(highlightTimeoutRef.current);
  }

  highlightTimeoutRef.current = setTimeout(() => {
    setHighlightedId(null);
  }, 1000);
};
```

Now clicking a new jump link cancels the previous timeout, and only the latest highlight will clear after 1 second.

## Cleanup on Unmount

If the component unmounts while a timeout is pending, the callback would still fire and call `setHighlightedId(null)` on an unmounted component. In React 18+ this is silently ignored, but it's still a wasted call — and in older React versions it produced a warning. A cleanup effect prevents this:

```typescript
useEffect(() => {
  return () => {
    if (highlightTimeoutRef.current !== null) {
      clearTimeout(highlightTimeoutRef.current);
    }
  };
}, []);
```

The empty dependency array means the effect body runs once after the initial render, and the returned cleanup function runs on unmount.

---

## Requirements Checklist

All requirements are now implemented:

- ✓ Display 9 hardcoded messages on load
- ✓ Send messages via button click
- ✓ Empty messages cannot be sent
- ✓ List scrolls to bottom on new message
- ✓ Jump links scroll to first or last message
- ✓ Jumped-to message is highlighted
- ✓ Highlight disappears after 1 second
- ✓ Only one message highlighted at a time
- ✓ Auto-focus input on load (nice-to-have)
- ✓ Send with Enter key (nice-to-have)

## What We'd Improve

We could consider the following improvement points in order to deliver more robust, production-ready code:

**Extract components** — Separate concerns into focused components with clear props.

**Handle empty state** — If this component were extended to support message deletion, we'd want to show an empty state and disable the jump buttons when there are no messages. The `messageRefs` Map already handles deletion cleanly via the callback ref's `null` branch.

**Accessibility** — Move focus to the target message after jumping, and use an `aria-live` region to announce new messages to screen readers.

---

## Final Code

**App.tsx**

```tsx
import { useState, useRef, useEffect } from "react";
import "./App.css";

const initialMessages = Array.from({ length: 9 }, (_, i) => ({
  id: i,
  text: `Message ${i + 1}`,
}));

function App() {
  const [messages, setMessages] = useState(initialMessages);
  const [highlightedId, setHighlightedId] = useState<number | null>(null);
  const [inputValue, setInputValue] = useState("");

  const messageRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const highlightTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const lastId = messages.length - 1;
    messageRefs.current.get(lastId)?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    return () => {
      if (highlightTimeoutRef.current !== null) {
        clearTimeout(highlightTimeoutRef.current);
      }
    };
  }, []);

  const handleSend = () => {
    const trimmed = inputValue.trim();

    if (!trimmed) {
      return;
    }

    setMessages((prev) => [...prev, { id: prev.length, text: trimmed }]);
    setInputValue("");
  };

  const jumpToMessage = (id: number) => {
    messageRefs.current.get(id)?.scrollIntoView({ behavior: "smooth" });
    setHighlightedId(id);

    if (highlightTimeoutRef.current !== null) {
      clearTimeout(highlightTimeoutRef.current);
    }

    highlightTimeoutRef.current = setTimeout(() => {
      setHighlightedId(null);
    }, 1000);
  };

  return (
    <div className="app">
      <div className="jump-links">
        <button onClick={() => jumpToMessage(0)}>Jump to First</button>
        <button onClick={() => jumpToMessage(messages.length - 1)}>Jump to Last</button>
      </div>

      <div className="message-list">
        {messages.map((message) => (
          <div
            key={message.id}
            ref={(node) => {
              if (node) {
                messageRefs.current.set(message.id, node);
              } else {
                messageRefs.current.delete(message.id);
              }
            }}
            className={highlightedId === message.id ? "message highlighted" : "message"}
          >
            {message.text}
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="input-area"
      >
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
}

export default App;
```

**App.css**

```css
.app {
  max-width: 400px;
  margin: 0 auto;
  padding: 16px;
}

.jump-links {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.message-list {
  height: 300px;
  overflow-y: auto;
  border: 1px solid #ccc;
  padding: 8px;
}

.message {
  padding: 8px;
  margin-bottom: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.message.highlighted {
  background: #fff3cd;
}

.input-area {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.input-area input {
  flex: 1;
  padding: 8px;
}
```

## Wrapping Up

This exercise demonstrates a common pattern in live coding challenges: balancing correctness with pragmatism. The shortcuts we took were deliberate, and we can articulate why we'd do things differently given more time. The key is knowing the difference between "good enough for a demo" and "production-ready" — and being able to explain both.

---

_Previous: [Part 1 — Understanding the Requirements and Basic Structure](https://dev.to/vftiago/frontend-coding-challenge-chat-like-interface-part-1-262g)_
