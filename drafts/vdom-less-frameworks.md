---
title: "VDOM-less Approaches to Reactive UI"
published: false
description: React uses a Virtual DOM. Svelte compiles reactivity away. SolidJS uses fine-grained signals. How do these approaches differ, and when does each make sense?
tags: react, svelte, solidjs, javascript
---

React, Svelte, and SolidJS solve the same fundamental problem: keeping the DOM in sync with application state. However, they take remarkably different approaches.

- **React** — Diffs Virtual DOM trees at runtime
- **Svelte** — Compiles reactive updates at build time
- **SolidJS** — Tracks fine-grained dependencies at runtime

Each approach has tradeoffs. Understanding them helps you choose the right tool, or at least clarify why your current tool works the way it does.

## The Problem They All Solve

DOM mutations aren’t slow. What’s slow is the browser work that follows: recalculating styles, recomputing layout, repainting pixels. Every mutation indicates to the browser that something might have changed.

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

This model is predictable: UI is a function of state. The tradeoff is that React must re-run the component and diff the result — even when the output is identical. React Compiler (introduced in React 19) can reduce unnecessary re-renders, but the fundamental model remains: re-run, diff, patch.

**Benefits:**

- Large ecosystem and community
- Predictable mental model (UI as function of state)
- Mature tooling (DevTools, testing libraries, meta-frameworks)

**Drawbacks:**

- Overhead from diffing, even with optimizations (negligible for most applications)
- Runtime includes the reconciler and scheduler

## Svelte: Compile-Time Reactivity

Svelte shifts work from runtime to build time. The compiler analyzes your code and generates vanilla JavaScript that updates the DOM directly (the example below uses Svelte 5 syntax):

```svelte
<script>
  let count = $state(0);
</script>

<button onclick={() => count++}>
  Clicked {count} times
</button>
```

The compiler sees that `count` is used in the button text and generates code that updates only that text node when `count` changes. There’s no diffing because there’s nothing to diff — the compiler knows at build time exactly which DOM nodes depend on which variables.

**Benefits:**

- Smallest runtime footprint
- No diffing overhead
- Less boilerplate than React

**Drawbacks:**

- Uses `.svelte` files with custom syntax
- Reactive dependencies must be statically analyzable
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

- Near-Svelte performance with React-like syntax
- No diffing overhead
- Fine-grained control over what updates

**Drawbacks:**

- Signals are functions — easy to forget the `()`
- Destructuring props breaks reactivity
- Conditional rendering needs specific patterns (`<Show>`, `<For>`)
- Smaller ecosystem than React

## Runtime Size

The architectural differences show up in bundle size (minified + gzipped as of early 2026):

| Framework        | Runtime Size |
| ---------------- | ------------ |
| React + ReactDOM | ~45kb        |
| Svelte           | ~3kb         |
| SolidJS          | ~7kb         |

Svelte’s minimal runtime is possible because most work happens at compile time — the compiled output includes only the code your app actually uses. SolidJS ships a reactivity system but no diffing algorithm. React ships both the reconciler and scheduler.

For small widgets or performance-critical applications, runtime size might matter. For typical SPAs, it’s often negligible compared to application code.

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
