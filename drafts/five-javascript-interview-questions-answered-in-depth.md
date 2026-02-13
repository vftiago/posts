---
title: Five JavaScript Interview Questions Answered in Depth
published: false
description: Short answers and deep dives into key-value data structures, type coercion, pass by value, closures, and garbage collection in JavaScript.
tags: [javascript, interview, frontend]
---

These five questions come up regularly in frontend interviews, usually early on as a way to gauge foundational JavaScript understanding. Each one has a short answer — a sentence or two that demonstrates you know the concept — but the depth behind that answer is what distinguishes a rehearsed response from genuine understanding.

## Efficient Key-Value Lookup

_I have a list of variables each with a unique key in my JavaScript code and I want to store the variables in a data structure so that I can efficiently retrieve the one that corresponds to each key, what are some data structures I can use for that?_

> Use a plain object or a `Map`. Both provide constant-time lookup by key on average.

JavaScript has two built-in options for associating values with unique keys: plain objects and `Map`.

A **plain object** is the traditional choice. You set properties with bracket or dot notation, and retrieval is O(1) on average. The main limitation is that object keys are always strings or Symbols — any other type is coerced to a string. This means numeric keys like `1` and string keys like `"1"` refer to the same property:

```javascript
const obj = {};
obj[1] = "one";
obj["1"] = "also one";
console.log(Object.keys(obj)); // ["1"] — only one entry
```

A **`Map`** is the purpose-built key-value collection introduced in ES2015. It accepts keys of any type — objects, functions, primitives — and uses the SameValueZero algorithm for key comparison, so `1` and `"1"` are distinct keys:

```javascript
const map = new Map();
map.set(1, "one");
map.set("1", "string one");
console.log(map.size); // 2 — distinct keys
```

`Map` also maintains guaranteed insertion order, exposes a `size` property directly, and is iterable out of the box with `for...of`. Plain objects work well for structured data with known string keys (configuration, API responses), while `Map` is the better choice when keys are dynamic, non-string, or when the collection changes frequently.

## Strict vs. Loose Equality

_Why does JavaScript have a triple equals operator?_

> `==` performs type coercion before comparing, which can produce unintuitive results. `===` compares both type and value without coercion, making equality checks predictable.

JavaScript's loose equality operator (`==`) follows the Abstract Equality Comparison algorithm, which converts operands to a common type before comparing them. The rules are complex enough that even experienced developers can't always predict the result:

```javascript
0 == ""; // true  — "" is coerced to 0
0 == "0"; // true  — "0" is coerced to 0
"" == "0"; // false — same type, different values
```

The first two comparisons are `true`, but the third is `false` — loose equality isn't transitive, which makes it difficult to reason about.

Strict equality (`===`) is straightforward: if the types differ, return `false`. No conversion, no surprises. The only edge case worth knowing is that `NaN === NaN` evaluates to `false` — `NaN` is the only JavaScript value that isn't strictly equal to itself. Use `Number.isNaN()` to test for it.

For completeness, `Object.is()` provides a third comparison that behaves like `===` except in two cases: `Object.is(NaN, NaN)` returns `true`, and `Object.is(+0, -0)` returns `false`. It's rarely needed in day-to-day code, but it's the most precise value identity check JavaScript offers.

## Pass by Value vs. Pass by Reference

_What's the difference between pass by value and pass by reference?_

> Pass by value means the function receives a copy of the data, so changes to the copy don't affect the original. Pass by reference means the function receives the original variable itself, so reassigning it changes the caller's variable too. JavaScript is always pass by value, but for objects the "value" being passed is a reference to the object in memory.

This distinction trips people up because JavaScript's behavior with objects _looks_ like pass by reference but isn't. The key test: in a language with true pass by reference (C++ with `&`, C# with `ref`), you can write a `swap(a, b)` function that exchanges the values of two variables in the caller's scope. You can't do that in JavaScript.

Here's what actually happens:

```javascript
function reassign(obj) {
  obj = { name: "new" };
}

function mutate(obj) {
  obj.name = "mutated";
}

const original = { name: "original" };

reassign(original);
console.log(original.name); // "original" — unchanged

mutate(original);
console.log(original.name); // "mutated" — changed
```

When you pass `original` to a function, JavaScript copies the _reference_ (the memory address), not the object itself. Both the caller's variable and the function's parameter now point to the same object in memory. Mutating properties through either reference affects the shared object, which is why `mutate` works. But `reassign` only overwrites the local copy of the reference — the caller's `original` variable still points to the same object it always did.

This behavior is sometimes called "call by sharing," a term first described by Barbara Liskov for the CLU language in 1974: you can mutate the shared object, but you can't rebind the caller's variable.

## Closures in JavaScript

_What is a closure in JavaScript?_

> A closure is a function that retains access to variables from its enclosing lexical scope, even after that scope has finished executing.

When JavaScript creates a function, it attaches a reference to the _lexical environment_ in which the function was defined — the ECMAScript specification calls this the function's `[[Environment]]` internal slot. This means a function can always access the variables that were in scope when it was created, regardless of when or where it's eventually called.

A common use of closures is creating private state:

```javascript
function createCounter(start) {
  let count = start;
  return {
    increment() {
      return ++count;
    },
    current() {
      return count;
    },
  };
}

const counter = createCounter(0);
counter.increment(); // 1
counter.increment(); // 2
counter.current(); // 2
```

`createCounter` has returned, but `increment` and `current` still have access to `count` through their closure. There's no other way to reach `count` — it's effectively private.

An important detail is that closures capture variables _by reference_, not by value. If the outer variable changes after the closure is created, the closure sees the updated value. This is the mechanism behind a classic gotcha:

```javascript
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// logs: 3, 3, 3
```

Because `var` is function-scoped, there's a single `i` variable shared across all three closures. By the time the callbacks execute, the loop has finished and `i` is 3. Replacing `var` with `let` fixes this because `let` is block-scoped — each iteration creates a new binding, and each closure captures its own independent copy.

## Garbage Collection and Memory Leaks

_Can you please explain what a garbage collector does or is and what's meant by a memory leak in that context?_

> A garbage collector automatically frees memory occupied by values that are no longer reachable from the program's root references. A memory leak is memory the program no longer needs but that remains reachable, so the collector can't reclaim it.

Modern JavaScript engines (V8, SpiderMonkey, JavaScriptCore) use a _mark-and-sweep_ algorithm. Starting from a set of roots — the global object and the current call stack — the collector traverses every reachable reference, following object properties, closure environments, and other pointers. Any object not reachable from a root is considered garbage, and its memory is freed.

Earlier approaches used _reference counting_, where each object tracked how many incoming references it had. When the count hit zero, the memory was released. The fatal flaw was circular references: two objects referencing each other never reach a count of zero, even if nothing else in the program references either of them. Mark-and-sweep doesn't have this problem because it traces reachability from roots rather than tracking individual counts.

A memory leak in a garbage-collected language looks different from one in a language with manual memory management like C. In C, a leak means allocated memory whose pointer has been lost — the memory is truly orphaned. In JavaScript, a leak means you're unintentionally keeping a reference alive, so the garbage collector correctly determines the object is still reachable and leaves it alone. The collector is working as designed; the bug is in the code holding onto references it no longer needs.

Common sources of memory leaks in JavaScript:

- **Forgotten event listeners** — attaching a listener to a DOM element and never removing it, especially when the listener's closure holds references to large data structures
- **Detached DOM nodes** — removing an element from the document but retaining a JavaScript reference to it, preventing the element and its subtree from being collected
- **Closures capturing more than intended** — a closure referencing one variable from an outer scope may keep the entire scope alive, depending on engine optimizations
- **Uncleared timers** — `setInterval` callbacks that are never cleared continue to execute and keep their closures and all referenced data alive indefinitely
