---
title: "VDOM-less Approaches to Reactive UI"
published: true
description: React uses a Virtual DOM. Svelte and SolidJS use fine-grained signals. How do these approaches differ, and when does each make sense?
tags: react, svelte, solidjs, javascript
---

React, Svelte, and SolidJS solve the same fundamental problem: keeping the DOM in sync with application state. However, they take remarkably different approaches.

_(NOTE: This comparison reflects React 19, Svelte 5, and SolidJS 1.x as of early 2026.)_

- **React** — Diffs Virtual DOM trees at runtime
- **Svelte** — Hybrid compile-time + signals approach (Svelte 5 adopted fine-grained reactivity)
- **SolidJS** — Tracks fine-grained dependencies at runtime

Each approach has tradeoffs. Understanding them helps you choose the right tool, or at least clarify why your current tool works the way it does.

## The Problem They All Solve

[DOM mutations aren’t slow](https://dev.to/vftiago/why-does-react-use-a-virtual-dom-1305). What’s slow is the browser work that follows: recalculating styles, recomputing layout, repainting pixels. Every mutation indicates to the browser that something might have changed.

Naive approaches — updating the DOM directly on every state change — can trigger excessive browser work. The goal is to minimize unnecessary DOM operations while keeping the UI in sync with state.

## React: Virtual DOM Diffing

React’s core model: describe what the UI should look like, and let React figure out the minimal DOM updates needed.

```jsx
const Counter = () => {
  const [count, setCount] = useState(0);

  return <button onClick={() => setCount(count + 1)}>Clicked {count} times</button>;
};
```

When `count` changes:

1. React calls the component function again
2. A new Virtual DOM tree is created
3. React diffs the new tree against the previous one
4. Only the changed parts are applied to the real DOM

This model is predictable: UI is a function of state. The tradeoff is that React must re-run the component and diff the result — even when the output is identical. React Compiler can reduce unnecessary re-renders, but the fundamental model remains: re-run, diff, patch.

**Benefits:**

- Large ecosystem and community
- Predictable mental model (UI as function of state)
- Mature tooling (DevTools, testing libraries, meta-frameworks)

**Drawbacks:**

- Overhead from diffing, even with optimizations (negligible for most applications)
- Runtime includes the reconciler and scheduler

## Svelte: Compile-Time + Fine-Grained Reactivity

Svelte’s approach has evolved significantly. Before version 5, Svelte was purely compile-time: the compiler analyzed your code and generated vanilla JavaScript that updated the DOM directly. Svelte 5 adopts a hybrid approach, combining compile-time optimizations with SolidJS-style fine-grained signals called "[runes](https://svelte.dev/docs/svelte/v5-migration-guide#Reactivity-syntax-changes)":

```svelte
<script>
  let count = $state(0);
</script>

<button onclick={() => count++}>
  Clicked {count} times
</button>
```

The `$state` rune creates a signal under the hood. When `count` changes, only the specific DOM nodes that depend on it update — no diffing needed. This combines the ergonomics of Svelte’s original approach with the performance characteristics of fine-grained reactivity.

**Benefits:**

- Fine-grained updates with minimal overhead
- Less boilerplate than React
- Better scaling with component count than pre-Svelte 5

**Drawbacks:**

- Uses `.svelte` files with custom syntax
- Smaller ecosystem than React

## SolidJS: Fine-Grained Signals

SolidJS looks like React but works fundamentally differently. Components run once, not on every update.

```jsx
const Counter = () => {
  const [count, setCount] = createSignal(0);

  return <button onClick={() => setCount(count() + 1)}>Clicked {count()} times</button>;
};
```

The key difference: `count` is a function (a _signal_), not a value. When you call `count()` inside JSX, SolidJS tracks that this expression depends on this signal. When the signal updates, only the subscribers (the DOM nodes that depend on it) update — not the whole component.

Components are setup functions, not render functions. They establish reactive relationships once, and those relationships handle future updates directly.

**Benefits:**

- React-like syntax
- Automatic dependency tracking (also true of Svelte 5)
- Fine-grained control over what updates

**Drawbacks:**

- Signals are functions — easy to forget the `()`
- Destructuring props breaks reactivity
- Conditional rendering needs specific patterns (`<Show>`, `<For>`)
- Smaller ecosystem than React

## Runtime Size

The architectural differences show up in bundle size. React ships both the reconciler and scheduler. Svelte 5's runtime grew compared to earlier versions due to its signals system, but individual components compile smaller, improving scaling for larger applications. SolidJS ships a reactivity system but no diffing algorithm.

For small widgets or performance-critical applications, runtime size might matter. For typical SPAs, it's often negligible compared to application code.

## Performance Characteristics

In benchmarks, SolidJS and Svelte consistently outperform React in raw update speed. But benchmarks measure synthetic scenarios — clicking a button thousands of times, rendering enormous lists.

Real-world performance depends on:

- How often state changes
- How complex the component tree is
- How much work happens in component functions
- Network latency and bundle loading

For most applications, all three frameworks are fast enough. The differences matter at the margins — highly interactive UIs, low-powered devices, or very large applications.

## The Bigger Picture

The Virtual DOM was React’s answer to a real problem: making UI updates predictable without manual DOM optimization. It worked well enough that it shaped how a generation of developers thinks about UI. Svelte and SolidJS demonstrate that the Virtual DOM isn’t the only answer. The right choice depends on what you’re optimizing for.

All three frameworks produce working applications. The differences are in developer experience, performance characteristics, and ecosystem maturity. Choose based on your actual constraints, not benchmark results.
