---
title: Five JavaScript Interview Questions Answered in Depth
published: false
description: Senior-level answers to five common JavaScript interview questions about Map vs Object, == vs ===, parameter passing, closures, and garbage collection.
tags: [javascript, interview]
cover_image: https://dev-to-uploads.s3.amazonaws.com/uploads/articles/ov3kmc3c7xkfrziz833w.jpg
---

The following five questions still come up regularly in JavaScript interviews, because they test whether you understand the model underneath the language rather than just the syntax. Each one has a short answer — a sentence or two that demonstrates you know the concept — but the in-depth explanation behind that answer is what distinguishes a rehearsed response from genuine understanding.

## 1. Efficient Key-Value Lookup

Q: _I have a list of variables each with a unique key in my JavaScript code and I want to store the variables in a data structure so that I can efficiently retrieve the one that corresponds to each key. What are some data structures I can use for that?_

A: Use a plain object or a `Map`. Both can be fast in practice, but `Map` is the purpose-built keyed collection and the specification expects implementations to provide sublinear average access time.

JavaScript has two built-in options for associating values with unique keys: plain objects and `Map`.

A **plain object** is the traditional choice. You set properties with bracket or dot notation, and modern engines optimize property access heavily, but the language specification does not guarantee a particular complexity bound. The main limitation is that object keys are always strings or [Symbols](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol) — any other type is coerced to a string. This means numeric keys like `1` and string keys like `"1"` refer to the same property:

```javascript
const obj = {};
obj[1] = "one";
obj["1"] = "also one";
console.log(Object.keys(obj)); // ["1"] — only one entry
```

A **`Map`** is the purpose-built key-value collection introduced in ES2015. It accepts keys of any type — objects, functions, primitives — and uses the [SameValueZero algorithm](https://tc39.es/ecma262/#sec-samevaluezero) for key comparison, so `1` and `"1"` are distinct keys:

```javascript
const map = new Map();
map.set(1, "one");
map.set("1", "string one");
console.log(map.size); // 2 — distinct keys
```

`Map` also preserves insertion order for iteration, exposes a `size` property directly, and is iterable out of the box with `for...of`. Ordinary objects have more nuanced [own-property ordering](https://tc39.es/ecma262/#sec-ordinaryownpropertykeys): integer index keys come first in ascending numeric order, then other string keys in insertion order, then Symbols in insertion order. They also inherit prototype properties unless you deliberately create them with `Object.create(null)`. Plain objects work well for structured data with known string keys (configuration, parsed JSON, API responses), while `Map` is the better choice when keys are dynamic, non-string, or when you want keyed-collection semantics rather than object-property semantics.

## 2. Strict vs. Loose Equality

Q: _Why does JavaScript have a triple equals operator?_

A: `==` performs type coercion before comparing, which can produce unintuitive results. `===` compares both type and value without coercion, making equality checks predictable.

JavaScript's loose equality operator (`==`) follows the [Abstract Equality Comparison algorithm](https://tc39.es/ecma262/#sec-islooselyequal), which may coerce operands according to a complex set of rules before comparing them. The rules are complex enough that even experienced developers can't always predict the result:

```javascript
0 == ""; // true  — "" is coerced to 0
0 == "0"; // true  — "0" is coerced to 0
"" == "0"; // false — same type, different values
```

The first two comparisons are `true`, but the third is `false` — loose equality isn't transitive, which makes it difficult to reason about. The underlying problem is that coercion happens pairwise: each comparison can follow a different conversion path, so two `true` comparisons do not imply a third one will also be `true`.

Strict equality (`===`) is much easier to reason about: if the types differ, the result is `false`, and for most values that's the end of the story. Two number-specific cases are worth knowing, though: `NaN === NaN` is `false`, and `+0 === -0` is `true`. If those cases matter, use `Object.is()`. For all other values it agrees with `===`, but `Object.is(NaN, NaN)` is `true` and `Object.is(+0, -0)` is `false`, so it exposes JavaScript's same-value comparison directly.

## 3. Pass by Value vs. Pass by Reference

Q: _What's the difference between pass by value and pass by reference?_

A: [Function parameters in JavaScript are passed by value](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions#passing_arguments). Reassigning the parameter does not affect the caller. When the copied value happens to be an object reference, both caller and callee can still use that copied reference to access and mutate the same object.

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

When you pass `original` to a function, JavaScript copies the _reference value_, not the object itself. Both the caller's variable and the function's parameter now refer to the same object. Mutating properties through either reference affects the shared object, which is why `mutate` works. But `reassign` only overwrites the local copy of the reference — the caller's `original` variable still points to the same object it always did.

So the important rule is this: JavaScript never gives the callee the ability to rebind the caller's variable. It only gives the callee another copy of the current value, and that value may itself point to a shared object.

## 4. Closures in JavaScript

Q: _What is a closure in JavaScript?_

A: A closure is a function that retains access to variables from its enclosing lexical scope, even after that scope has finished executing.

When JavaScript creates a function, the function object stores a reference to the _lexical environment_ in which it was defined — the ECMAScript specification models this with the function's [`[[Environment]]` internal slot](https://tc39.es/ecma262/#table-internal-slots-of-ecmascript-function-objects). This means a function can resolve identifiers from the scope that existed when it was created, regardless of when or where it's eventually called.

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

`createCounter` has returned, but `increment` and `current` still have access to `count` through their closure. `count` is not exposed as a property, so those returned methods are the only ordinary programmatic way to read or update it.

An important detail is that closures capture the _binding_ itself, not a snapshot of its value at the time the closure is created. If the outer variable changes after the closure is created, the closure sees the updated value. This is the mechanism behind a classic gotcha:

```javascript
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// logs: 3, 3, 3
```

Because `var` is function-scoped, there's a single `i` binding shared across all three closures. By the time the callbacks execute, the loop has finished and `i` is 3. Replacing `var` with `let` in the loop header fixes this, not merely because `let` is block-scoped, but because [`for (let i = ...)` creates a fresh binding for `i` on each iteration](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for#lexical_declarations_in_the_initialization_block). Each closure captures a different binding, so each callback sees the value from its own iteration.

## 5. Garbage Collection and Memory Leaks

Q: _Can you please explain what a garbage collector does or is and what's meant by a memory leak in that context?_

A: A garbage collector automatically frees memory occupied by objects that are no longer reachable from the program's root references. A memory leak is memory the program no longer needs but that remains reachable, so the collector can't reclaim it.

Modern JavaScript engines (V8, SpiderMonkey, JavaScriptCore) use collectors built on the foundational [_mark-and-sweep_](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Memory_management#mark-and-sweep_algorithm) idea, layered with generational, incremental, and concurrent techniques to reduce pause times. Starting from a set of roots — such as the global object and currently active execution contexts — the collector traverses every reachable reference, following object properties, captured variables, and other links. Any object with no path from a root is considered garbage and can be reclaimed.

In JavaScript, a memory leak happens when code unintentionally keeps a reference alive, so the garbage collector correctly determines the object is still reachable and leaves it alone. The collector is working as designed; the bug is in the code holding onto references it no longer needs.

Common sources of memory leaks in JavaScript:

- **Listeners on long-lived targets** — attaching a listener to `window`, `document`, or some other long-lived object and forgetting to remove it can keep the listener closure, and everything it captures, alive indefinitely
- **Detached DOM nodes still referenced from JavaScript** — removing an element from the document does not make it collectible if some variable, array, cache, or closure still points to it
- **Closures retaining more state than expected** — a surviving closure keeps the bindings it closes over reachable. Multiple closures created by the same function invocation may share one lexical environment, so keeping one alive can keep more of that invocation's state alive than you intended
- **Uncleared timers** — `setInterval` callbacks that are never cleared continue to execute and keep their closures and referenced data alive indefinitely

The key distinction is that garbage collection is about _reachability_, not about whether your business logic is "finished" with an object. If some path from a root can still reach it, the collector must keep it alive. A memory leak is therefore usually a reference-management bug in application code, not a failure of the collector.

## Final Thoughts

Each of these questions tests a different mental model: property keys versus keyed collections, coercion rules, parameter passing, lexical scope, and reachability. In an interview, a one-line answer gets you through the prompt, but the ability to explain the mechanism is what usually convinces the interviewer that you understand JavaScript rather than merely recognizing trivia.
