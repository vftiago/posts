---
title: React Hooks, Closures, and the Lifecycle of a Render
published: false
description: A deep dive into how React's render-commit lifecycle creates closures, why function identity matters for hooks, and how useEffectEvent solves the stale closure problem.
tags: react, javascript, hooks, closures
# cover_image: https://direct_url_to_image.jpg
# Use a ratio of 100:42 for best results.
# published_at: 2026-02-22 16:00 +0000
---

React 19.2 added a hook called `useEffectEvent`. It solves a specific problem: reading the latest props and state inside a `useEffect` callback without causing the effect to re-run when those values change. That problem — stale closures vs. unwanted re-synchronization — has been one of the most persistent pain points in React hooks since their introduction.

To understand why `useEffectEvent` exists and what it actually does, it helps to start from the bottom: how React's render lifecycle works, what JavaScript closures have to do with it, and what "function identity" really means at the engine level.

## The Render-Commit Lifecycle

In class-based React, the lifecycle was explicit: `componentDidMount`, `componentDidUpdate`, `componentWillUnmount`. With function components, there are no named lifecycle methods. Instead, the component function _is_ the render — React calls it every time it needs to determine what the component should display. That call is the _render phase_, where the function receives the current props, reads the current state via hooks, and returns JSX describing what should appear on screen.

The render phase must be _pure_. The component function should produce the same output given the same props and state, with no observable side effects — no network requests, no analytics calls, no DOM mutations. React enforces this in development via Strict Mode, which deliberately double-invokes component functions and simulates unmounting and remounting components to surface impure behavior.

After the render phase, React compares the new output against the previous output and determines the minimal set of changes needed. Then it enters the _commit phase_, where it applies those changes to the real DOM. Effects registered with `useEffect` run _after_ the commit, once the browser has painted. This is the intended place for side effects: the DOM is up to date and the render is complete.

This two-phase model — pure computation followed by committed side effects — is the foundation that the rest of this article builds on.

## Every Render Creates a Closure

A component re-renders when its state changes, its parent re-renders, or a context it consumes changes. A prop change alone triggers a re-render, not a remount — the component function runs again, but `useState` returns the existing state, not the initial value. State only resets when React treats the component as an entirely new instance (because its `key` changed, its position in the tree shifted, or the component type at that position changed).

This matters because every time React calls the component function, every local variable, every inline callback, and every value derived from props or state exists within that particular invocation's scope. In JavaScript terms, each render creates a new _closure_ — a function bundled together with references to the variables in scope at the time it was created.

Consider this component:

```javascript
const Page = ({ url }) => {
  const [count, setCount] = useState(0);

  const logVisit = () => {
    console.log(url, count);
  };

  useEffect(() => {
    logVisit();
  }, [url]);

  return <button onClick={() => setCount(count + 1)}>Count: {count}</button>;
};
```

On the first render, `logVisit` is a function that closes over `url` and `count` as they exist in that render — say, `"/home"` and `0`. On the second render (after the user clicks the button), React calls `Page` again. A _new_ `logVisit` function is created, closing over `"/home"` and `1`. These two `logVisit` functions look identical in source code, but they are different objects in memory, each holding references to different values.

This is the mechanism behind stale closures in React. The effect's dependency array lists only `[url]`, so when `count` changes the effect doesn't re-run — it still holds the `logVisit` closure from a previous render, and that closure still sees the old `count`. The values don't update in place; each render produces its own snapshot.

## What "Function Identity" Means

The reason closures cause problems for hooks comes down to how JavaScript represents functions and how React compares them.

In JavaScript, functions are objects. When you write `() => {}`, the engine allocates a new object in memory. That object contains a pointer to the compiled code and a pointer to the _lexical environment_ — the closure, holding the variables the function captured. The variable you assign the function to doesn't contain the function itself; it contains a _reference_ to the function object, which is effectively a memory address managed by the engine.

This means:

```javascript
const fn1 = () => {};
const fn2 = () => {};

console.log(fn1 === fn2); // false
```

Even though `fn1` and `fn2` have identical source code, they are different objects at different memory addresses. Reference equality compares the reference itself, not source code, not behavior, not names. Two variables are only equal if they point to the exact same object in memory.

```javascript
const fn1 = () => {};
const fn2 = fn1;

console.log(fn1 === fn2); // true
```

Here, `fn2` is assigned the same reference as `fn1`. No new object is created. Both variables point to the same function object, so strict equality returns `true`.

This is what "function identity" means — whether two references point to the same object. And this is exactly what dependency arrays check. When React evaluates `[callback]` in a dependency array, it compares the current reference to the previous one using [`Object.is()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is). For objects (including functions), `Object.is()` behaves the same as `===` — it checks whether both operands are the same object in memory. If the reference changed, the effect re-runs. If it didn't, the effect is skipped.

## The Problem: New Closures Mean New Identities

Since each render creates new function objects with new references, including a function in a dependency array means the effect re-runs every render. But the tension between stale closures and unwanted re-runs isn't limited to function dependencies — it applies to any value you read inside an effect but don't want to trigger re-synchronization.

Consider this analytics tracking example:

```javascript
const Page = ({ url }) => {
  const [numberOfItems, setNumberOfItems] = useState(0);

  useEffect(() => {
    trackEvent("visit", { numberOfItems, url });
  }, [url, numberOfItems]);

  return (
    <div>
      <p>Items: {numberOfItems}</p>
      <button onClick={() => setNumberOfItems(numberOfItems + 1)}>
        Add Item
      </button>
    </div>
  );
};
```

The intent is to fire an analytics event when the `url` changes. But because the effect reads `numberOfItems`, the `exhaustive-deps` rule from `eslint-plugin-react-hooks` (correctly) insists it be in the dependency array. Now the effect fires whenever `numberOfItems` changes too — every button click sends a "visit" event. That's not a bug in the dependency array rules; it's a fundamental tension between "read the latest value" and "only run when specific things change."

You could omit `numberOfItems` from the array and suppress the lint warning, but then you're back to stale closures: the effect would capture whatever `numberOfItems` was when it last ran due to a `url` change, and that value might be wrong.

## The Ref Escape Hatch

Before React offered an official solution, the community converged on a pattern that uses refs to break out of the closure trap. The idea: keep a stable function reference that never changes identity, but have it internally delegate to the latest version of the callback.

```javascript
const useStableCallback = (callback) => {
  const callbackRef = useRef(callback);

  useLayoutEffect(() => {
    callbackRef.current = callback;
  });

  return useCallback((...args) => {
    return callbackRef.current(...args);
  }, []);
};
```

This works by exploiting the difference between a closure and a ref. The wrapper function returned by `useCallback(fn, [])` is created once and never changes — its identity is stable. But the wrapper doesn't close over any props or state directly. Instead, it reads `callbackRef.current` at call time, and that ref is updated to point to the latest callback on every render via the `useLayoutEffect`.

Think of it as indirection: the wrapper is a permanent address, and the ref is call forwarding. Each render updates where the call gets forwarded to, but the address itself never changes.

This pattern works, but it's a userland workaround with rough edges. The `useLayoutEffect` introduces a timing gap: during the render itself, the ref still points to the previous callback, because layout effects run after commit. And the pattern has no integration with React's concurrent rendering features — it works through a mutable escape hatch that React's scheduler doesn't know about.

## useEffectEvent: The Official Solution

React 19.2 added `useEffectEvent`, which solves the same problem as the ref pattern but through a fundamentally different mechanism.

```javascript
const Page = ({ url }) => {
  const [numberOfItems, setNumberOfItems] = useState(0);

  const onVisit = useEffectEvent((visitedUrl) => {
    trackEvent("visit", { numberOfItems, url: visitedUrl });
  });

  useEffect(() => {
    onVisit(url);
  }, [url]);

  return (
    <div>
      <p>Items: {numberOfItems}</p>
      <button onClick={() => setNumberOfItems(numberOfItems + 1)}>
        Add Item
      </button>
    </div>
  );
};
```

The effect depends only on `[url]`, so it runs only when the URL changes. But when it calls `onVisit`, that function sees the current `numberOfItems` — not a stale snapshot.

Unlike the ref workaround, `useEffectEvent` does _not_ return a function with a stable identity. The React docs are explicit about this — effect event functions intentionally have an unstable identity that changes on every render. That sounds like it should cause the same problem as any other inline function, but the solution works at a different level.

Where the ref pattern hides a mutable value behind a stable reference to work _around_ the dependency array, `useEffectEvent` works _with_ React's dependency model. It tells React (and the linter) that this function represents _non-reactive logic_ — logic that should read from the current render but should not cause the effect to re-synchronize. The updated `eslint-plugin-react-hooks` recognizes effect event functions and excludes them from dependency arrays entirely. You don't need to list `onVisit` in the deps because React treats it as an effect event, not a reactive dependency. The docs also guarantee that effect events always "see" the latest values from render — without the timing gap that the ref pattern's `useLayoutEffect` introduces, where the ref still points to the previous callback during render itself.

Effect events also come with intentional restrictions: they can only be called from inside effects or other effect events, and they can't be passed to child components, called during render, or used as event handlers. Because React controls the implementation internally, it can ensure correct behavior in concurrent rendering scenarios (transitions, time-slicing) without relying on mutable refs that React's scheduler doesn't know about.

## Putting It Together

The progression from naive `useEffect` usage to `useEffectEvent` follows directly from how React's lifecycle interacts with JavaScript closures:

1. **Naive** — Put everything in the dependency array. The effect runs more often than intended.
2. **Suppress the lint** — Omit dependencies. The effect runs at the right time but reads stale values.
3. **Ref workaround** — Stable identity via `useCallback` and a mutable ref. Works, but fragile and opaque.
4. **`useEffectEvent`** — Fresh values without dependency churn, integrated into React's rendering model, with clear semantic intent.

The ref pattern and `useEffectEvent` arrive at the same outcome — an effect that runs only when intended but reads current values — through opposite mechanisms. The ref pattern stabilizes the function reference so the dependency array ignores it. `useEffectEvent` lets the reference change freely but teaches React and the linter that the function isn't a reactive dependency in the first place. Both exist because of the same underlying reality: JavaScript closures capture values at creation time, function identity is determined by object reference, and React's dependency arrays compare those references across renders using `Object.is()`.
