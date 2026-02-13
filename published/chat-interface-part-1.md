---
title: Frontend Coding Challenge — Chat-Like Interface (Part 1)
published: false
description: Walking through a hypothetical frontend live coding challenge step-by-step.
tags: react, interview, frontend
cover_image:
---

This is the first of two posts where I walk through a hypothetical frontend live coding challenge from the perspective of the interviewee, focusing on not just the code, but the reasoning that leads to it.

## The Challenge

Build a chat-like interface with a scrollable message list, an input field, a send button, and two "jump to message" links.

**Constraints**

- The only constraint is that we must use React.

**Requirements**

- Display 9 hardcoded messages on load
- User can type a message and click "Send" to append it to the list
- Empty messages cannot be sent
- The list scrolls to the bottom when a new message is added
- Links above the list allow jumping to the first and last messages
- Clicking a link scrolls that message into view and highlights it
- The highlight disappears after 1 second
- Only one message can be highlighted at a time

**Nice-to-have**

- Auto-focus the input on page load
- Send messages with Enter key

## Going through the Requirements

Before writing any code, it's worth carefully reading each requirement and checking whether its implementation is obvious. Some of these have hidden implications.

**"Display 9 hardcoded messages on load"**

Straightforward. We need initial data, which can be simple strings or objects with IDs. Since we'll need to highlight specific messages later, giving each message a stable identifier makes sense.

**"The list scrolls to the bottom when a new message is added"**

This tells us something about the UI structure. For a container to scroll vertically, its computed height must be less than the height of its content, and it needs to have `overflow-y: auto` or `overflow-y: scroll`. If the container grew to fit its content, there would be nothing to scroll to. This means we're building a fixed-height scrollable area — a layout decision implied by this requirement.

**"Links allow jumping to the first and last messages"**

The jump links target the first and last messages in the list. We'll need a way to scroll a specific message into view, which means either storing refs or using DOM queries.

**"The highlight disappears after 1 second"**

This requires a timeout. Timeouts in React components need cleanup on unmount to avoid unnecessary work. We'll need `useEffect` with a cleanup function, or a ref to track and cancel the timeout.

**"Only one message can be highlighted at a time"**

If we click "Jump to Last" while the first message is still highlighted, the first message's highlight should disappear immediately. This means highlighted state should be tracked centrally (not per-message), and we should cancel any existing timeout when a new highlight starts.

## Ambiguities

Some things are left to interpretation:

**Message structure** — Are messages just strings, or do they have metadata like timestamps or authors? The requirements don't specify. We'll use objects with `id` and `text` to keep things extensible without overcomplicating.

**Styling specifics** — No mockup is provided, so exact colors, spacing, and layout are open to interpretation.

**Scroll behavior** — Should scrolling be instant or smooth? Smooth scrolling provides visual continuity, helping the user track which message was jumped to. `scrollIntoView` supports this via `{ behavior: "smooth" }`.

## Mental Model

Before writing code, here's how the component tree and state will likely look:

```
<App>
  <JumpLinks />          // "Jump to First | Last"
  <MessageList>          // scrollable container
    <Message />          // repeated for each message
    <Message />
    ...
  </MessageList>
  <MessageInput />       // input + send button
</App>
```

State lives in `App`:

- `messages` — array of message objects
- `highlightedId` — which message is highlighted (or `null`)
- `inputValue` — controlled input state

## Environment Setup

We're free to use whatever we want. For a quick React setup, Vite requires minimal configuration and gives us a working React + TypeScript project with fast hot module replacement in seconds:

```bash
npm create vite@latest chat-interface -- --template react-ts
```

TypeScript is optional, but the autocompletion and type checking help catch errors early, and Vite's template requires no additional setup.

## Architecture Decisions

With the requirements understood, the next step is deciding how to structure the code.

### Component Structure

The mental model suggested extracting `JumpLinks`, `MessageList`, `Message`, and `MessageInput` as separate components. For a production codebase, this separation makes sense — each component has a single responsibility, and they're independently testable.

For a live coding exercise, there's a trade-off. More components means more boilerplate, more props to pass, and more opportunities for wiring mistakes. A pragmatic approach is to keep everything in a single `App` component initially, and extract components only if the file becomes unwieldy or if extraction simplifies the logic.

### State Shape

We need to track three things:

```typescript
const [messages, setMessages] = useState(initialMessages);
const [highlightedId, setHighlightedId] = useState<number | null>(null);
const [inputValue, setInputValue] = useState("");
```

**`messages`** — An array of message objects. Each message needs an `id` (for keying and highlighting) and `text` (the content). Starting with 9 hardcoded messages:

```typescript
const initialMessages = Array.from({ length: 9 }, (_, i) => ({
  id: i,
  text: `Message ${i + 1}`,
}));
```

Using the array index as the ID is fine here. We're not reordering or deleting messages, so there's no risk of key collisions. When adding new messages, the next ID is simply the array length (i.e., the next available index).

**`highlightedId`** — The ID of the currently highlighted message, or `null` if none. Storing this centrally (rather than a `highlighted` boolean on each message) makes it trivial to ensure only one message is highlighted at a time. We could track this as `"first" | "last" | null` since those are our only jump targets, but using the actual message ID is no more complex and would scale naturally if requirements expanded to include additional jump targets.

**`inputValue`** — The controlled input value. This could be an uncontrolled input with a ref, but with a controlled input the value always reflects React state, making validation and transformation straightforward. The performance difference is negligible for a single text field.

### The Layout Constraint

As noted earlier, the scroll requirement implies we need a fixed-height scrollable container. For simplicity, we can give the message list a fixed height directly:

```css
.message-list {
  height: 300px;
  overflow-y: auto;
}
```

The rest of the layout — jump links above, input below — stacks naturally as block elements.

### CSS Approach

Options for styling in React without external libraries:

1. **Inline styles** — JavaScript objects, no separate files
2. **CSS file** — Traditional stylesheet, imported into the component
3. **CSS Modules** — Scoped class names, supported by Vite out of the box

Vite's template includes an `App.css` file, so we'll use that. We can also delete `index.css` and remove its import from `main.tsx` — Vite's default styles may interfere with our layout, and starting with a blank slate is simpler than debugging style conflicts.

### Initial Scaffold

We'll replace Vite's boilerplate with our scaffold:

```tsx
import { useState } from "react";
import "./App.css";

const initialMessages = Array.from({ length: 9 }, (_, i) => ({
  id: i,
  text: `Message ${i + 1}`,
}));

function App() {
  const [messages, setMessages] = useState(initialMessages);
  const [highlightedId, setHighlightedId] = useState<number | null>(null);
  const [inputValue, setInputValue] = useState("");

  return (
    <div className="app">
      <div className="jump-links">
        <button>Jump to First</button>
        <button>Jump to Last</button>
      </div>

      <div className="message-list">
        {messages.map((message) => (
          <div key={message.id} className={highlightedId === message.id ? "message highlighted" : "message"}>
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
}

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

This renders a functional layout with all the visual elements in place. Nothing is wired up yet — the buttons don't do anything, and the Send button doesn't add messages — but the structure is there, and we can verify the scroll container works by inspecting it in the browser.

## Sending Messages

With the scaffold in place, we can start wiring up functionality.

### The Send Handler

When the user clicks "Send", we need to:

1. Ignore empty input
2. Create a new message object
3. Append it to the messages array
4. Clear the input
5. Scroll to the bottom

```typescript
const handleSend = () => {
  const trimmed = inputValue.trim();

  if (!trimmed) {
    return;
  }

  setMessages((prev) => [...prev, { id: prev.length, text: trimmed }]);
  setInputValue("");
};
```

The `trim()` call handles inputs that are only whitespace. Using `prev.length` for the ID works because IDs are 0-indexed (matching array indices) and we never delete messages — IDs will always be unique and sequential.

Note the functional update form `setMessages((prev) => ...)`. This pattern derives the next state from the previous state, rather than from the `messages` variable captured in the closure. In this specific case it doesn't matter — user-initiated clicks can't race — but it's a good habit. If `handleSend` were called programmatically in quick succession, the closure-based version could produce duplicate IDs because each call would read the same stale `messages` value.

### Auto-Scroll to Bottom

After adding a message, the list should scroll to show it. We also need refs to scroll specific messages into view for the jump links. A single data structure handles both: a Map storing refs to each message element by ID.

```typescript
const messageRefs = useRef<Map<number, HTMLDivElement>>(new Map());
```

To populate the Map, we use callback refs. When you pass a function to `ref` instead of a ref object, React calls it with the DOM element when the element mounts and with `null` when it unmounts. With inline functions, React detects that the function identity changes on each render; when this happens, it calls the _old_ callback with `null`, then the _new_ callback with the element. This sounds problematic, but it's safe here because `message.id` is stable for each element — even if the old callback runs its delete logic, it deletes the correct key, and the new callback immediately re-adds it:

```tsx
{
  messages.map((message) => (
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
  ));
}
```

Now we can scroll any message into view by its ID. For auto-scroll, we want to scroll to the last message whenever the list changes. Calling `scrollIntoView` right after `setMessages` won't work because React batches state updates and commits them to the DOM after the render cycle completes — the new message won't be in the DOM yet.

We need `useEffect` to run after the render:

```typescript
useEffect(() => {
  const lastId = messages.length - 1;
  messageRefs.current.get(lastId)?.scrollIntoView({ behavior: "smooth" });
}, [messages]);
```

This runs whenever `messages` changes. Since IDs are 0-indexed and sequential, `messages.length - 1` gives us the last message's ID.

One subtlety: this effect also runs on initial render with the 9 hardcoded messages. With `behavior: "smooth"`, users see an animated scroll on page load. Whether that's desirable is a UX judgment call — some would prefer `behavior: "instant"` for the initial render, or skipping the scroll entirely. For a timed exercise, the current behavior is acceptable and doesn't contradict the requirements.

### Simplifying with a Form

The nice-to-have list mentions auto-focusing the input and sending with Enter. There's a simple approach that addresses both: using a `<form>` element gives us Enter key submission for free, and the `autoFocus` attribute removes the need for a ref and effect:

```tsx
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
```

This is also more semantic — we're submitting a form, not just clicking a button.

### Current State

Here's the full component with sending and scrolling implemented:

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

  useEffect(() => {
    const lastId = messages.length - 1;
    messageRefs.current.get(lastId)?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const trimmed = inputValue.trim();

    if (!trimmed) {
      return;
    }

    setMessages((prev) => [...prev, { id: prev.length, text: trimmed }]);
    setInputValue("");
  };

  return (
    <div className="app">
      <div className="jump-links">
        <button>Jump to First</button>
        <button>Jump to Last</button>
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

The jump links still don't work, and `highlightedId` isn't being set anywhere — but the `messageRefs` Map is ready to support them.

That's next.

---

_Next: [Part 2 — Jump, Highlight & Final Code](https://dev.to/vftiago/frontend-coding-challenge-chat-like-interface-part-2-1phe)_
