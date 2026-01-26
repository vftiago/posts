---
title: Live Coding a Message List Component (Part 1): Requirements Analysis
published: false
description: The first step in any timed coding challenge is understanding what you're actually being asked to build. Here's how to read requirements critically.
tags: react, interview, frontend
---

This is the first in a series where I walk through a frontend coding challenge step-by-step, focusing on the decisions that matter under time pressure. Not just the code, but the reasoning that leads to it.

## The Challenge

Here's what we're given:

**Constraints**

- Use React
- No external libraries
- No AI tools
- Time limit: 1 hour

**Requirements**

- Display 10 hardcoded messages on load
- User can type a message and click "Send" to append it to the list
- Empty messages cannot be sent
- The list scrolls to the bottom when a new message is added
- Links above the list allow jumping to message 1, 5, or 10
- Clicking a link scrolls that message into view and highlights it
- Highlighted messages have a distinct background color
- The highlight disappears after 1 second
- Only one message can be highlighted at a time

**Nice-to-have**

- Auto-focus the input on page load
- Send messages with Enter key

A reference GIF shows the expected behavior. The component is a chat-like interface: a scrollable message list, an input field, a send button, and three "jump to" links.

## Reading the Requirements

Before writing any code, it's better to carefully read each requirement and check whether its implementation is obvious. Some of these have hidden implications.

**"Display 10 hardcoded messages on load"**

Straightforward. We need initial data. The messages can be simple strings or objects with IDs. Since we'll need to reference "message 1, 5, or 10" later, giving each message a stable identifier makes sense.

**"The list scrolls to the bottom when a new message is added"**

This tells us something about the UI structure. For a container to be scrollable, it needs a constrained height and `overflow-y: auto`. If the container grew to fit all content, there would be nothing to scroll.

This means we're building a fixed-height (or flex-constrained) scrollable area, not a page that grows infinitely. The layout decision is implied by this requirement.

**"Links allow jumping to message 1, 5, or 10"**

The reference shows 10 hardcoded messages with text like "Message 1", "Message 5", etc. The jump links target the 1st, 5th, and 10th messages in the list. Since we start with 10 messages and can only add (not remove), these targets will always exist. We'll need a way to scroll a specific message into view, which means either storing refs for each message or using DOM queries.

**"The highlight disappears after 1 second"**

This requires a timeout. Timeouts in React components need cleanup on unmount to avoid memory leaks and state updates on unmounted components. We'll need `useEffect` with a cleanup function, or a ref to track and cancel the timeout.

**"Only one message can be highlighted at a time"**

If we click "Jump to 5" while message 1 is still highlighted, message 1's highlight should disappear immediately. This means highlighted state should be tracked centrally (not per-message), and we should cancel any existing timeout when a new highlight starts.

## Ambiguities

Some things are left to interpretation:

**Message structure** — Are messages just strings, or do they have metadata (timestamp, author)? The reference shows simple text. We'll use objects with `id` and `text` to keep things extensible without overcomplicating.

**Styling specifics** — No pixel-perfect mockup is provided. The reference gives us the general layout. Match the structure and behavior; exact colors and spacing are secondary.

**Scroll behavior** — The reference shows smooth scrolling. `scrollIntoView` supports this via `{ behavior: "smooth" }`.

## Mental Model

Before writing code, here's how the component tree and state will likely look:

```
<App>
  <JumpLinks />          // "Jump to 1 | 5 | 10"
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

We'll need refs for scrolling:

- A ref to the message list container (to scroll to bottom)
- A way to reference individual messages (to scroll a specific one into view)

## Environment Setup

The constraints allow any tooling and environment. For a quick React setup with minimal configuration, Vite is a good choice:

```bash
pnpm create vite message-list --template react-ts
```

This gives us a working React + TypeScript project in seconds. TypeScript is optional per the requirements, but the autocompletion and type checking are worth it, and Vite's template requires no additional setup.

With the requirements analyzed and the environment ready, we can start writing code. In Part 2, we'll make the architectural decisions concrete and write the initial scaffold.

---

_Next: [Part 2 — Architecture Decisions](/)_
