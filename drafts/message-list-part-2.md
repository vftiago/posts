---
title: Live Coding a Message List Component (Part 2): Architecture Decisions
published: false
description: Before writing implementation code, we need to decide on component structure, state shape, and CSS approach. These decisions shape everything that follows.
tags: react, interview, frontend
---

With the requirements understood, the next step is deciding how to structure the code. In a timed exercise, these decisions need to be made quickly, but they're worth a moment of thought. Changing course mid-implementation is expensive.

## Component Structure

The mental model from Part 1 suggested this structure:

```
<App>
  <JumpLinks />
  <MessageList>
    <Message />
    ...
  </MessageList>
  <MessageInput />
</App>
```

For a production codebase, this separation makes sense. Each component has a single responsibility, and they're independently testable.

For a one-hour exercise, there's a trade-off. More components means more boilerplate, more props to pass, and more opportunities for wiring mistakes. The requirements don't mention reusability or testing.

A pragmatic middle ground: keep everything in a single `App` component initially. Extract components only if the file becomes unwieldy or if extraction simplifies the logic. In practice, this exercise is small enough that a single component works fine.

If the interviewer values component design, we can discuss how we'd split it up. The code structure doesn't prevent extraction later.

## State Shape

We need to track three things:

```typescript
const [messages, setMessages] = useState(initialMessages);
const [highlightedId, setHighlightedId] = useState<number | null>(null);
const [inputValue, setInputValue] = useState("");
```

**`messages`** — An array of message objects. Each message needs an `id` (for keying and highlighting) and `text` (the content). Starting with 10 hardcoded messages:

```typescript
const initialMessages = [
  { id: 1, text: "Message 1" },
  { id: 2, text: "Message 2" },
  // ... through 10
];
```

Using sequential numeric IDs is fine here. We're not reordering or deleting messages, so there's no risk of key collisions. When adding new messages, we can derive the next ID from the array length or track a counter.

**`highlightedId`** — The ID of the currently highlighted message, or `null` if none. Storing this centrally (rather than a `highlighted` boolean on each message) makes it trivial to ensure only one message is highlighted at a time.

**`inputValue`** — The controlled input value. This could be an uncontrolled input with a ref, but controlled inputs are more predictable and the performance difference is negligible for a single text field.

## The Layout Constraint

The requirement "scroll to bottom when a message is added" implies a scrollable container. A container is only scrollable when:

1. It has a constrained height (the content can exceed it)
2. It has `overflow-y: auto` or `overflow-y: scroll`

If the container's height grew to fit its content, there would be nothing to scroll to.

We could use a fixed-height parent with flexbox or grid to distribute space among children. For a timed exercise, the simplest approach is to give the message list a fixed height directly.

```css
.message-list {
  height: 300px;
  overflow-y: auto;
}
```

The rest of the layout — jump links above, input below — just stacks naturally as block elements. No flexbox needed on the container.

## CSS Approach

Options for styling in React without external libraries:

1. **Inline styles** — JavaScript objects, no separate files
2. **CSS file** — Traditional stylesheet, imported into the component
3. **CSS Modules** — Scoped class names, supported by Vite out of the box

Inline styles are tempting for a quick exercise, but they have limitations: no pseudo-classes (`:hover`), no media queries, and the syntax is verbose. A plain CSS file is simpler and sufficient for this scope.

Vite's template already includes an `App.css` file, so we'll use that. We'll also delete `index.css` entirely (and remove its import from `main.tsx`) — Vite's default styles include dark mode support and centering logic that would interfere with our layout. For a timed exercise, starting fresh is simpler than debugging style conflicts.

## Initial Scaffold

Vite's template comes with a counter example in `App.tsx`. We'll replace it entirely with our scaffold:

```tsx
import { useState } from "react";
import "./App.css";

const initialMessages = Array.from({ length: 10 }, (_, i) => ({
  id: i + 1,
  text: `Message ${i + 1}`,
}));

const App = () => {
  const [messages, setMessages] = useState(initialMessages);
  const [highlightedId, setHighlightedId] = useState<number | null>(null);
  const [inputValue, setInputValue] = useState("");

  return (
    <div className="app">
      <div className="jump-links">
        <button>Jump to 1</button>
        <button>Jump to 5</button>
        <button>Jump to 10</button>
      </div>

      <div className="message-list">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${highlightedId === message.id ? "highlighted" : ""}`}
          >
            {message.text}
          </div>
        ))}
      </div>

      <div className="input-area">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type a message..."
        />
        <button>Send</button>
      </div>
    </div>
  );
};

export default App;
```

And the corresponding CSS:

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

This renders a functional layout with all the visual elements in place. Nothing is wired up yet — the buttons don't do anything, and the Send button doesn't add messages. But the structure is there, and we can verify the scroll container works by inspecting it in the browser.

In Part 3, we'll implement the core functionality: sending messages and auto-scrolling to the bottom.

---

_Previous: [Part 1 — Requirements Analysis](/)_

_Next: [Part 3 — Sending Messages](/)_
