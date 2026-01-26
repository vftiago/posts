---
title: Live Coding a Message List Component (Part 5): Polish & Retrospective
published: false
description: Reviewing the completed solution, discussing trade-offs made under time pressure, and identifying improvements for a production codebase.
tags: react, interview, frontend
---

The component is functional. All requirements are met, including the nice-to-haves. Now let's step back and evaluate what we built.

## Requirements Checklist

- ✓ Display 10 hardcoded messages on load
- ✓ Send messages via button click
- ✓ Empty messages cannot be sent
- ✓ List scrolls to bottom on new message
- ✓ Jump links scroll to message 1, 5, or 10
- ✓ Jumped-to message is highlighted
- ✓ Highlight disappears after 1 second
- ✓ Only one message highlighted at a time
- ✓ Auto-focus input on load (nice-to-have)
- ✓ Send with Enter key (nice-to-have)

## Trade-offs Made for Speed

Several decisions prioritized speed over ideal design:

**Single component** — Everything lives in `App`. For a production codebase, we'd extract `MessageList`, `Message`, `JumpLinks`, and `MessageInput` as separate components. This improves testability and reusability, but adds overhead in a timed exercise.

**DOM query for scrolling** — Using `querySelector` with data attributes is pragmatic but bypasses React's ref system. A more React-idiomatic approach would use a ref callback or a Map of refs. The DOM query works, but it's less type-safe and relies on the DOM structure matching our expectations.

**Inline handlers** — The `onSubmit` handler is defined inline in JSX. Extracting it to a named function would be cleaner, especially if we needed to test it or reuse it.

**No TypeScript interface for messages** — We rely on type inference for the message shape. Defining an explicit `Message` interface makes the contract clearer:

```typescript
type Message = {
  id: number;
  text: string;
};
```

## What We'd Improve

Given more time, these changes would make the code production-ready:

**Extract components** — Separate concerns into focused components with clear props.

**Use refs instead of DOM queries** — A ref callback pattern to collect message refs:

```tsx
const messageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

// When rendering each message, use a ref callback:
{messages.map((message) => (
  <div
    key={message.id}
    ref={(el) => {
      if (el) {
        messageRefs.current.set(message.id, el);
      } else {
        messageRefs.current.delete(message.id);
      }
    }}
  >
    {message.text}
  </div>
))}

// Then to scroll:
messageRefs.current.get(5)?.scrollIntoView({ behavior: "smooth" });
```

The `if (el)` check handles a React behavior: when you pass a function to `ref`, React calls it twice during the element's lifecycle. First with the DOM element when it mounts, then with `null` when it unmounts. This lets us clean up the Map when messages are removed.

**Handle edge cases** — With the current requirements, the jump targets always exist (we start with 10 messages and can only add). But if this component were extended to support message deletion, we'd want to disable buttons for non-existent messages or show feedback.

**Accessibility** — Add ARIA labels to the jump links, ensure proper focus management after scrolling, and announce new messages to screen readers.

**CSS transitions** — The highlight appears and disappears instantly. A fade-out transition would be smoother:

```css
.message {
  transition: background-color 0.3s ease;
}
```

**Scroll behavior edge case** — If the user is reading older messages and a new message arrives, auto-scrolling to the bottom might be disruptive. A production chat would detect if the user has scrolled up and show a "New messages" indicator instead.

## Final Code

**App.tsx**

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

This exercise demonstrates a common pattern in timed coding challenges: balancing correctness with pragmatism. Every shortcut we took was deliberate, and we can articulate why we'd do things differently given more time.

The key is knowing the difference between "good enough for a demo" and "production-ready" — and being able to explain both.

---

_Previous: [Part 4 — Jump & Highlight](/)_
