---
title: Why Does React Use a Virtual DOM?
published: false
description: A practical look at what the Virtual DOM really is, why direct DOM manipulation isn't inherently slow, what React is actually optimizing for, and how other frameworks solve the same problem differently.
tags: react, dom, vdom, signals
cover_image: https://dev-to-uploads.s3.amazonaws.com/uploads/articles/wjelgova6jn3h8h8ci01.jpg
---

If you've spent any amount of time with React, you've probably heard of the Virtual DOM (or VDOM for short) as well as some version of this claim:

> React uses a Virtual DOM because direct DOM manipulation is slow.

A catchy if hand-wavy explanation. Also a bit misleading.

The DOM isn't slow in the way people usually mean — JavaScript can execute DOM mutations very quickly. What's expensive is what the browser has to do after you mutate the DOM. React's Virtual DOM exists to manage those costs.

## The DOM Is Not Just a JavaScript Object Tree

Although the DOM feels like a normal JavaScript object tree, it is not. DOM nodes are host objects, provided by the browser, implemented in native code (C++ in most browser engines).

When you change a DOM node, you're not just mutating memory owned by the JavaScript engine. You're interacting with the browser's rendering engine, which maintains a lot of additional state behind the scenes: layout information, CSS resolution, paint layers, accessibility data, and event handling metadata.

So when you do something as simple as:

```javascript
element.textContent = "Hello";
```

you're signaling to the browser that the visual output of the page may have changed. That signal is where the real cost begins.

A DOM mutation can force the browser to do some or all of the following:

- Recalculate styles
- Recompute layout (reflow)
- Repaint pixels
- Re-composite layers on the GPU

These steps are typically far more expensive than the JavaScript that triggered them, and they can _cascade_: a change in one part of the DOM may affect layout elsewhere.

The browser is smart and uses heuristics to limit the scope of invalidation, but determining what's affected still requires work. The cost isn't the mutation itself — it's the invalidation and recalculation of rendering state.

## Why Many Small DOM Updates Are a Problem

The classic performance issue isn't "touching the DOM", it's _how_ you touch it — specifically, interleaving reads and writes.

Browsers naturally batch rendering work: they wait until JavaScript execution completes before running the rendering pipeline. But if you read a layout property (like `offsetHeight`) after modifying the DOM, the browser must calculate layout _immediately_ to return an accurate value. This is called _forced synchronous layout_.

If you do this repeatedly — read, write, read, write — the browser is forced to recalculate layout on each read, even though only the final state matters. This pattern is known as _layout thrashing_.

Experienced developers learned to work around this by batching writes, caching reads, and carefully ordering operations to avoid layout thrashing. It worked, but it was brittle and easy to get wrong.

React's Virtual DOM formalizes this idea.

## What the Virtual DOM Actually Is

React's Virtual DOM is a tree of plain JavaScript objects. It has no connection to layout, styles, or rendering. You can create it, throw it away, and compare it freely without triggering any browser rendering work. Only after it computes the final desired UI does it touch the real DOM.

This indirection allows React to do three important things:

1. **Batch updates** — Multiple state changes are grouped into a single DOM commit.
2. **Avoid unnecessary writes** — If a piece of UI didn't change, React doesn't touch the corresponding DOM node.
3. **Minimize observable mutations** — The browser sees only the smallest required set of changes, not every intermediate state.

In other words, the Virtual DOM reduces total work by _shielding the browser from noise_.

## Why Diffing Is Usually Cheaper

All the Virtual DOM operations (creating trees, comparing them, throwing them away) are plain JavaScript work. The expensive part is what happens when changes reach the browser's rendering pipeline.

React trades extra JavaScript work for a reduction in browser rendering work. For most applications with non-trivial UI complexity, that trade is a net win.

This also explains why React can afford to re-run component functions so often. React distinguishes between the _render phase_ (calling component functions to produce a Virtual DOM description) and the _commit phase_ (applying changes to the real DOM). The expensive browser work only happens during the commit phase, once React knows exactly what needs to change.

The DOM is not "slow" in an absolute sense. Modern browsers are extremely fast, and for small or simple applications, direct DOM manipulation can be perfectly fine, or even faster than React.

The Virtual DOM shines when:

- Updates are frequent
- State changes are complex
- You want predictable, maintainable UI updates at scale

React's real contribution isn't raw performance. It's making efficient DOM usage the default, instead of something developers have to constantly think about.

A more precise way to phrase the original claim would be:

> React uses a Virtual DOM because committing only the necessary changes to the real DOM keeps expensive browser rendering work to a minimum.

The Virtual DOM exists to ensure the browser only sees the final, minimal set of changes that matter.

## Beyond the Virtual DOM

The Virtual DOM was React's answer to a real problem, and it worked well enough to shape how a generation of developers thinks about UI. But it's not the only answer.

The core insight — that you need to minimize unnecessary DOM mutations — can be achieved through different mechanisms. While React builds a tree, diffs it, and patches the real DOM, other frameworks skip the intermediate tree entirely by tracking exactly which pieces of state affect which parts of the UI.

This alternative approach is often called _fine-grained reactivity_, and its most common implementation uses _signals_.

## What Are Signals?

A signal is a reactive primitive: a container for a value that notifies subscribers when it changes. The key insight is that if the framework knows precisely which DOM nodes depend on which pieces of state, it can update only those nodes directly when state changes — without diffing an entire tree representation of the UI.

Consider a counter. In a signal-based system, when the count value changes, the framework doesn't re-run the entire component or diff a tree. It updates only the specific text node displaying the count, because it tracked that dependency when the UI was first created.

This inverts the React model. In React, a state change re-renders the component and its entire subtree by default, then diffs the result to find what changed. Signal-based frameworks track dependencies upfront and update only what's affected, without re-running component functions.

## Tradeoffs

Neither approach is inherently superior. The Virtual DOM and fine-grained reactivity represent different points in a design space, optimizing for different concerns.

Virtual DOM diffing offers a simple mental model: describe what the UI should look like given the current state, and let the framework figure out the DOM updates. This makes reasoning about your application straightforward. The cost is the overhead of re-running component functions and comparing trees on every state change — work that happens even when the output is identical. For most applications this overhead is negligible, and React provides mechanisms to skip re-rendering subtrees when their inputs haven't changed.

Fine-grained reactivity avoids the overhead of diffing a full tree representation on every update. For simple value changes, updates go directly to the affected DOM nodes. List updates still require some form of reconciliation, but the work is scoped to the list itself rather than the entire component subtree. The tradeoff is a different mental model: instead of writing render functions that re-run on every state change, you're wiring up reactive primitives that persist and update in place.

Both approaches produce applications that are fast enough for the vast majority of use cases. The differences tend to matter at the margins — very large component trees, very frequent updates, or very constrained devices.

## Choosing an Approach

The existence of VDOM-less frameworks doesn't invalidate React's approach. React's ecosystem, tooling, and community remain substantial advantages. The Virtual DOM model is well-understood, well-documented, and works well for a wide range of applications.

What these alternative approaches demonstrate is that the Virtual DOM is a _solution_, not _the_ solution. Understanding that distinction — knowing why React chose its approach and what the alternatives optimize for — makes you a more informed developer, regardless of which framework you use.
