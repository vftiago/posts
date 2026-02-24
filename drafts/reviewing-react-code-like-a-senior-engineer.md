---
title: Reviewing React Code Like a Senior Engineer
published: false
description: A walkthrough of common bugs and questionable patterns in a hypothetical junior developer's React + TypeScript PR, with the depth of explanation that signals senior-level understanding.
tags: [react, frontend, interview]
# cover_image: https://direct_url_to_image.jpg
# Use a ratio of 100:42 for best results.
# published_at: 2026-01-25 16:44 +0000
---

Imagine a junior colleague has opened a pull request for a small to-do list app built with React and TypeScript. The code broadly works, but reveals a pattern of misunderstandings about how React's rendering model, hooks, and TypeScript's type system actually behave. This article walks through the issues you'd flag in that review, organised from correctness bugs outward to architectural and type-safety concerns — the same layered approach you'd want to demonstrate in an interview setting.

All examples assume React 19, functional components, and TypeScript with strict mode enabled.

Here's the PR. Two files — a parent `TodoApp` component and a child `TodoItem`:

```tsx
// TodoApp.tsx
import { useState, useEffect, useMemo } from "react";
import { TodoItem } from "./TodoItem";
import { fetchTodos, saveTodosToLocalStorage } from "./api";

export function TodoApp() {
  const [todos, setTodos] = useState<any[]>([]);
  const [completedCount, setCompletedCount] = useState(0);
  const [newTitle, setNewTitle] = useState("");

  useEffect(() => {
    fetchTodos().then(setTodos);
    saveTodosToLocalStorage(todos);
  }, []);

  useEffect(() => {
    setCompletedCount(todos.filter((t) => t.completed).length);
    if (todos.length > 10) {
      alert("Too many todos!");
    }
  }, [todos]);

  const memoizedTodos = useMemo(() => todos, [todos]);

  function addTodo() {
    setTodos([...todos, { id: crypto.randomUUID(), title: newTitle, completed: false }]);
    setNewTitle("");
  }

  function toggleTodo(id: string) {
    const todo = todos.find((t) => t.id === id);
    if (todo) {
      todo.completed = !todo.completed;
    }
    setTodos(todos);
  }

  function editTodo(id: string, title: string) {
    const todo = todos.find((t) => t.id === id);
    if (todo) {
      todo.title = title;
    }
    setTodos(todos);
  }

  function deleteTodo(id: string) {
    setTodos(todos.filter((t) => t.id !== id));
  }

  return (
    <div>
      <h1>
        My Todos ({completedCount}/{todos.length} completed)
      </h1>
      <input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} />
      <button onClick={addTodo}>Add</button>
      <ul>
        {memoizedTodos.map((todo, index) => (
          <TodoItem
            key={index}
            todo={todo}
            onToggle={() => toggleTodo(todo.id)}
            onEdit={(title) => editTodo(todo.id, title)}
            onDelete={() => deleteTodo(todo.id)}
          />
        ))}
      </ul>
    </div>
  );
}
```

```tsx
// TodoItem.tsx
import { useState } from "react";

type TodoItemProps = {
  todo: { id: string; title?: string; completed: boolean };
  onToggle: () => void;
  onEdit: (title: string) => void;
  onDelete: () => void;
};

export function TodoItem({ todo, onToggle, onEdit, onDelete }: TodoItemProps) {
  const [completed, setCompleted] = useState(todo.completed);

  function handleToggle() {
    setCompleted(!completed);
    onToggle();
  }

  return (
    <li>
      <input type="checkbox" checked={completed} onChange={handleToggle} />
      <input value={todo.title} onChange={(e) => onEdit(e.target.value)} />
      <div onClick={onDelete}>×</div>
    </li>
  );
}
```

There's a lot to talk about. Let's work through it.

## Immutability and Reference Identity

The first thing that jumps out is a state mutation bug that appears in both `toggleTodo` and `editTodo`:

```typescript
function toggleTodo(id: string) {
  const todo = todos.find((t) => t.id === id);
  if (todo) {
    todo.completed = !todo.completed;
  }
  setTodos(todos);
}

function editTodo(id: string, title: string) {
  const todo = todos.find((t) => t.id === id);
  if (todo) {
    todo.title = title;
  }
  setTodos(todos);
}
```

Both handlers find the todo object and mutate it in place, then pass the same `todos` array back to `setTodos`. Toggling a checkbox or editing a title appears to do nothing — or worse, works intermittently depending on whether something else triggers a re-render.

The problem is that `setTodos(todos)` passes the same array reference back to React. React uses `Object.is(prevState, nextState)` to decide whether a state update should trigger a re-render, and since the reference hasn't changed, `Object.is` returns `true` and React bails out. The mutations have happened in memory, but React never knows about them.

This is a fundamental rule: React state must be treated as immutable. The fix is to produce a new array (and a new object for the changed item) so that the reference changes:

```typescript
// toggleTodo
setTodos((prev) => prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t)));

// editTodo
setTodos((prev) => prev.map((t) => (t.id === id ? { ...t, title } : t)));
```

The _functional updater_ form (`prev => ...`) — where you pass a function to the setter instead of the next value directly — is a good habit here too. More on why in the stale closures section below.

## Component Identity and the Key Prop

Next, the list rendering in the return statement:

```tsx
{
  memoizedTodos.map((todo, index) => <TodoItem key={index} todo={todo} />);
}
```

Using array indices as keys is one of the most common mistakes in React code reviews. Keys tell React's reconciliation algorithm which component instance corresponds to which piece of data. When you use the index, the _position_ becomes the identity. Consider what happens when you delete the second item from a three-item list: React sees key=0 (unchanged), key=1 (still present, but now receiving the third item's props), and key=2 (gone — unmounted). It doesn't remount key=1; it _reuses_ that component instance and hands it new props.

If the component is purely prop-driven, this is invisible — the reused instance renders the new data and the output looks correct. But the moment a component holds local state or uncontrolled DOM state, the mismatch surfaces. In this PR, `TodoItem` keeps its own `completed` state via `useState(todo.completed)`, so after a deletion the surviving instance retains the _old_ item's local state while receiving the _new_ item's props. Checkboxes show the wrong checked state, and any uncontrolled input text stays attached to the wrong item.

The fix is straightforward: use a stable, unique identifier from the data itself:

```tsx
<TodoItem key={todo.id} todo={todo} />
```

Index keys are only safe when the list is static (no reordering, insertion, or deletion) _and_ items have no local or uncontrolled DOM state — which is rarely the case in a to-do app.

## Derived State and the Render Cycle

`TodoApp` tracks a completed count in its own piece of state, updated inside the `[todos]` effect:

```typescript
const [completedCount, setCompletedCount] = useState(0);

useEffect(() => {
  setCompletedCount(todos.filter((t) => t.completed).length);
  if (todos.length > 10) {
    alert("Too many todos!");
  }
}, [todos]);
```

The `setCompletedCount` call works, but it's doing unnecessary work. The sequence is: render with the old count, commit to the DOM, paint (the user briefly sees the stale count), run the effect, call `setCompletedCount`, which triggers a _second_ render with the corrected count. Every state change to `todos` produces two render cycles instead of one, and the stale intermediate state can cause a visible flicker.

The completed count is _derived data_ — it can be computed entirely from `todos`, which means it doesn't need its own state at all. For a cheap computation like filtering an array and reading its length, the simplest and most efficient approach is to compute it inline during render:

```typescript
const completedCount = todos.filter((t) => t.completed).length;
```

No state, no effect, no extra render cycle. The value is recalculated on every render, which is fine because array filtering is fast and React renders are cheap. Reaching for `useMemo` here would be premature optimisation — `useMemo` itself has overhead (dependency comparison, cache storage), and the React docs explicitly recommend reserving it for computations that are genuinely expensive.

Incidentally, the PR also contains that problem — memoising something that doesn't need it:

```typescript
const memoizedTodos = useMemo(() => todos, [todos]);
```

This does nothing. `useMemo` returns the memoised result when the dependencies haven't changed, but if `todos` _is_ the dependency and `todos` _is_ the value, you're just adding overhead to return the same reference you already had.

## Understanding Effects

Effects are the most commonly misused hook in React, and `TodoApp` has two of them — each mixing multiple unrelated concerns together because they share a dependency array. At least two of those concerns shouldn't be effects at all.

### Missing Dependencies

Inside the first effect, `saveTodosToLocalStorage` references `todos` — but the dependency array is empty:

```typescript
useEffect(() => {
  fetchTodos().then(setTodos);
  saveTodosToLocalStorage(todos);
}, []);
```

The intent is to persist todos to localStorage whenever they change, but the empty dependency array means this effect runs exactly once — on mount. After the initial save, subsequent changes to `todos` are never persisted.

The dependency array isn't an optimisation knob you tune; it's a declaration of which values the effect reads. If the effect references `todos`, then `todos` must be in the array. But fixing this by adding `todos` to the dependency array would cause the _entire_ effect — including the fetch — to re-run on every change to `todos`, which isn't what you want either. This is a consequence of grouping unrelated concerns into a single effect: the dependency arrays become impossible to get right for all the logic inside.

The `saveTodosToLocalStorage` call should be its own effect with the correct dependency:

```typescript
useEffect(() => {
  saveTodosToLocalStorage(todos);
}, [todos]);
```

The underlying misconception is treating `useEffect` like a lifecycle method (`componentDidMount`), where the empty array means "run on mount". Effects are synchronisation mechanisms — they keep external systems (localStorage, the DOM, a WebSocket) in sync with React state. The dependency array tells React _when_ to re-synchronise. Grouping effects by dependency array rather than by concern makes this harder to get right — each effect should do one thing, so its dependencies naturally reflect exactly what that one thing needs.

### Effects for Event-Driven Logic

The second effect also contains an alert that fires when there are too many to-dos:

```typescript
useEffect(() => {
  setCompletedCount(todos.filter((t) => t.completed).length);
  if (todos.length > 10) {
    alert("Too many todos!");
  }
}, [todos]);
```

The alert uses an effect to respond to a state change, but it's really a consequence of a user action (adding a to-do), not something that needs synchronising with an external system. The distinction matters because effects run _after_ render and paint, which means the alert fires later than the user expects, and it runs on every re-render where the condition is true — including on mount if the data is loaded from localStorage. Additionally, we're not actually preventing the user from adding more than 10 to-dos, we're just warning them after the fact.

The fix is to move the check into the event handler that adds the to-do:

```typescript
function addTodo() {
  if (todos.length >= 10) {
    alert("Too many todos!");
    return;
  }
  setTodos((prev) => [...prev, { id: crypto.randomUUID(), title: newTitle, completed: false }]);
  setNewTitle("");
}
```

This way the feedback is immediate, predictable, and directly tied to the action that caused it. A good mental model: effects are for _synchronisation with external systems_ (I/O, subscriptions, DOM manipulation). Business logic that responds to user actions belongs in event handlers.

## Stale Closures and Functional Updates

The `addTodo` handler spreads the current `todos` array directly:

```typescript
function addTodo() {
  setTodos([...todos, { id: crypto.randomUUID(), title: newTitle, completed: false }]);
  setNewTitle("");
}
```

This works most of the time, but it can silently drop updates. The issue is that `todos` is captured from the render in which `addTodo` was defined. If another state update to `todos` is queued between renders — say the fetch effect resolves while the user is clicking "Add" — `addTodo` reads a stale `todos` that doesn't include the fetched data, and the update overwrites it. The same problem applies to `deleteTodo`, which also spreads `todos` directly rather than using a functional updater.

Since React 18, all state updates are batched by default — inside event handlers, promises, and timeouts alike — which makes this kind of interleaving more likely than it was in earlier versions.

The fix is the functional updater form:

```typescript
setTodos((prev) => [...prev, { id: crypto.randomUUID(), title: newTitle, completed: false }]);
```

The `prev` parameter always reflects the most recent state, including any updates that are still queued. This makes the update self-contained — it doesn't depend on a closed-over value that might be stale.

This pattern is worth internalising as a default: any time a state update depends on the previous state, use the functional form.

## Async Effects and Race Conditions

With `saveTodosToLocalStorage` separated into its own effect, the first effect is left with the fetch:

```typescript
useEffect(() => {
  fetchTodos().then(setTodos);
}, []);
```

A quick note on the syntax: `.then(setTodos)` is _point-free_ style — it passes `setTodos` directly as the `.then` callback, which means the resolved value of the promise becomes the argument. It's equivalent to `.then((data) => setTodos(data))`.

The concern here isn't a warning — React 18 removed the "state update on an unmounted component" warning that used to fire in this scenario. The real problem is a _race condition_. If the component unmounts and remounts (which happens during development in Strict Mode, and can happen in production with fast navigation), two fetch requests are now in flight. Whichever resolves last wins, and that might not be the one you expect.

The recommended cleanup pattern uses `AbortController`, which actually cancels the in-flight HTTP request rather than just ignoring its result:

```typescript
useEffect(() => {
  const controller = new AbortController();

  fetch("/api/todos", { signal: controller.signal })
    .then((res) => res.json())
    .then(setTodos)
    .catch((err) => {
      if (err.name !== "AbortError") throw err;
    });

  return () => controller.abort();
}, []);
```

When the effect cleans up (on unmount or before re-running), `controller.abort()` cancels the request. The `fetch` promise rejects with an `AbortError`, which you catch and ignore. This approach has two advantages over the boolean-flag pattern (`let cancelled = false`): it actually frees network resources instead of just discarding the response, and it integrates with the browser's native request cancellation.

The cleanup function runs before the effect re-executes (if dependencies change) and when the component unmounts. Strict Mode's double-invocation is specifically designed to surface this class of bug — if your effect breaks when run twice, it's missing cleanup. The same principle applies to any resource that outlives a render: timers (`setTimeout`, `setInterval`), event listeners, WebSocket connections — anything your effect sets up, the cleanup function must tear down.

## TypeScript: Explicit Types at the Boundary

Two TypeScript issues span both files.

### Typing State as `any[]`

```typescript
const [todos, setTodos] = useState<any[]>([]);
```

The code compiles and runs, but `any[]` opts out of everything TypeScript is there to provide. There's no autocomplete on `todo.completed` — a typo like `todo.compleeted` won't be caught. Refactoring a field name won't produce compiler errors at the usage sites. And `any` is contagious: it flows through `.filter()`, `.map()`, and into child component props, silently disabling type checking across the component.

TypeScript infers a bare `useState([])` as `never[]`, an array that can never contain anything, turning every call to `setTodos` into a compile-time error. That's arguably better than `any[]`, which silently compiles and hides bugs at every usage site. The junior likely reached for `any[]` to make the compiler stop complaining, trading a loud failure for a quiet one.

The fix is an explicit type:

```typescript
type Todo = {
  id: string;
  title: string;
  completed: boolean;
};

const [todos, setTodos] = useState<Todo[]>([]);
```

This is a good example of a broader principle: _type the boundaries_. When TypeScript can't infer a meaningful type from the initial value alone — empty arrays, `null`, data from external sources — provide an explicit type parameter. The type flows from there through the rest of the component without needing further annotations, and the compiler catches bugs like the `title?: string` issue discussed below.

### Controlled Input Type Instability

In `TodoItem`, the title is rendered in an input:

```tsx
<input value={todo.title} onChange={(e) => onEdit(e.target.value)} />
```

Look at the `TodoItemProps` type — `title` is marked as optional (`title?: string`). When `todo.title` is `undefined`, React will warn:

> A component is changing an uncontrolled input to controlled.

This happens because an `undefined` value makes the input _uncontrolled_ (React doesn't manage its value), and when `title` later resolves to a string, it becomes _controlled_. React doesn't allow switching between the two modes.

The fix is to ensure the value is always a string:

```tsx
<input value={todo.title ?? ""} onChange={(e) => onEdit(e.target.value)} />
```

This is really a TypeScript issue in disguise — if the `Todo` type marked `title` as required (`title: string`), the problem couldn't arise. Tightening the type definition at the boundary prevents the bug at the usage site.

## Single Source of Truth

Back in `TodoItem`, the component manages its own `completed` state via `useState(todo.completed)`, while the parent also tracks completion in the `todos` array. Two sources of truth for the same data will inevitably diverge — the local state might say an item is complete while the parent's array says it isn't, or vice versa.

State should live at the _lowest common owner_ — the nearest ancestor that needs to read or modify it. In a to-do app, the parent owns the `todos` array, and `TodoItem` should receive `completed` as a prop and call an `onToggle` callback to request changes. No local duplication.

## Structuring Your Feedback

If you're presenting this kind of review in an interview, organising your feedback in layers demonstrates that you're thinking systematically rather than pointing out issues at random:

1. **Correctness** — Bugs that produce wrong behaviour: state mutation, stale closures, missing effect dependencies, async race conditions.
2. **React model** — Patterns that misuse React's APIs: effects for derived state, effects for event-driven logic, missing cleanup.
3. **Type safety** — Weak or incorrect types that undermine compile-time guarantees: untyped state, optional fields that should be required.
4. **Architecture** — Structural issues that make the code harder to maintain: duplicated state, poor state co-location.
5. **UX and accessibility** — Issues a code review should also catch: missing `<label>` elements for inputs, clickable `<div>` elements that should be `<button>` elements for keyboard and screen-reader support, absent loading and error states.

The first two layers are where you demonstrate the deepest technical understanding. The last layer shows you're thinking about the product, not just the code.

> Key talking points that signal senior-level understanding in a review discussion:
>
> - "React compares state by reference identity using `Object.is`, which is why immutable updates are required — not just a convention."
> - "Effects are for synchronising with external systems, not for responding to state changes or modelling lifecycle."
> - "Functional state updates prevent stale closure bugs because the updater always receives the latest state."
> - "Keys define component identity during reconciliation — an unstable key means React can't correctly preserve or reuse component instances."
