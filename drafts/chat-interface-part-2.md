---
title: Frontend Coding Challenge — Chat-Like Interface (Part 2)
published: false
description: Walking through a hypothetical frontend live coding challenge step-by-step.
tags: react, interview, frontend
---

_This is Part 2 of a two-part series. [Part 1](/) covered requirements analysis, architecture decisions, and sending messages._

The remaining functionality is the jump links: clicking "Jump to First" or "Jump to Last" should scroll that message into view and highlight it for 1 second.

## Scrolling to a Specific Message

We need a way to reference individual message elements. There are two reasonable approaches:

1. **Refs** — Store refs and attach them during render
2. **DOM query** — Use `querySelector` to find the element when needed

Option 1 is more idiomatic in React. Option 2 requires less setup (no ref management) and works fine for this use case. We'll use data attributes and `querySelector`:

```tsx
<div
  key={message.id}
  data-message-id={message.id}
  className={highlightedId === message.id ? "message highlighted" : "message"}
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

Wire up the buttons. Since we're using 0-based IDs (matching array indices), the first message has ID `0` and the last has ID `messages.length - 1`:

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
  const element = document.querySelector(`[data-message-id="${id}"]`);
  element?.scrollIntoView({ behavior: "smooth" });
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
  const element = document.querySelector(`[data-message-id="${id}"]`);
  element?.scrollIntoView({ behavior: "smooth" });
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
  const element = document.querySelector(`[data-message-id="${id}"]`);
  element?.scrollIntoView({ behavior: "smooth" });
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

If the component unmounts while a timeout is pending, the callback would still fire and attempt to do unnecessary work. A cleanup effect prevents this:

```typescript
useEffect(() => {
  return () => {
    if (highlightTimeoutRef.current !== null) {
      clearTimeout(highlightTimeoutRef.current);
    }
  };
}, []);
```

The empty dependency array means the effect body runs once on mount, and the returned cleanup function runs on unmount.

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

## Trade-offs

Several decisions prioritized simplicity over ideal design:

**Single component** — Everything lives in `App`. For a production codebase, we'd extract `MessageList`, `Message`, `JumpLinks`, and `MessageInput` as separate components with clear props interfaces. This improves testability and reusability.

**DOM query for scrolling** — Using `querySelector` with data attributes bypasses React's ref system. A more React-idiomatic approach would store refs in a Map:

```tsx
const messageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

{
  messages.map((message) => (
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
  ));
}

// Then to scroll:
messageRefs.current.get(id)?.scrollIntoView({ behavior: "smooth" });
```

The `if (el)` check handles a React behavior: ref callbacks are called with the DOM element on mount and with `null` on unmount, allowing the Map to stay in sync with the DOM.

Since our requirements only call for jumping to first and last, we could use two dedicated refs instead of a Map. But the Map approach is no more complex than managing two refs and would scale naturally if requirements expanded to include additional jump targets — the same reasoning we applied to `highlightedId` in Part 1.

**No TypeScript interface for messages** — We rely on type inference for the message shape. Defining an explicit type makes the contract clearer:

```typescript
type Message = {
  id: number;
  text: string;
};
```

## What We'd Improve

Given more time, these changes would make the code production-ready:

**Extract components** — Separate concerns into focused components with clear props.

**Use refs instead of DOM queries** — The Map-based ref pattern shown above is more type-safe and doesn't rely on the DOM structure matching our expectations.

**Handle empty state** — If this component were extended to support message deletion, we'd want to show an empty state and disable the jump buttons when there are no messages. The Map-based ref pattern shown above would also handle this cleanly, removing refs as messages are deleted.

**Accessibility** — Add ARIA labels to the jump links, ensure proper focus management after scrolling, and announce new messages to screen readers.

**CSS transitions** — The highlight appears and disappears instantly. A fade-out transition would be smoother:

```css
.message {
  transition: background-color 0.3s ease;
}
```

**Scroll behavior edge case** — If the user is reading older messages and a new message arrives, auto-scrolling to the bottom might be disruptive. A production chat would detect if the user has scrolled up and show a "New messages" indicator instead.

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

  const listRef = useRef<HTMLDivElement>(null);
  const highlightTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
      if (highlightTimeoutRef.current !== null) {
        clearTimeout(highlightTimeoutRef.current);
      }
    };
  }, []);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const newMessage = {
      id: messages.length,
      text: inputValue.trim(),
    };

    setMessages([...messages, newMessage]);
    setInputValue("");
  };

  const jumpToMessage = (id: number) => {
    const element = document.querySelector(`[data-message-id="${id}"]`);
    element?.scrollIntoView({ behavior: "smooth" });
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

      <div className="message-list" ref={listRef}>
        {messages.map((message) => (
          <div
            key={message.id}
            data-message-id={message.id}
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

_Previous: [Part 1 — Understanding the Requirements and Basic Structure](/)_
