---
title: Why Does React Use a Virtual DOM?
published: false
description: A practical look at what the Virtual DOM really is, why direct DOM manipulation isn’t inherently slow, and what React is actually optimizing for.
tags: react, dom, vdom
cover_image: https://dev-to-uploads.s3.amazonaws.com/uploads/articles/wjelgova6jn3h8h8ci01.jpg
---

If you’ve spent any amount of time with React, you’ve probably heard of the Virtual DOM (or VDOM for short) as well as some version of this claim:

> React uses a Virtual DOM because direct DOM manipulation is slow.

A catchy if hand-wavy explanation. Also a bit misleading.

The DOM isn't slow in the way people usually mean — JavaScript can execute DOM mutations very quickly. What's expensive is what the browser has to do after you mutate the DOM. React's Virtual DOM exists to manage those costs, not to replace the DOM with something inherently faster.

## The DOM Is Not Just a JavaScript Object Tree

Although the DOM feels like a normal JavaScript object tree, it is not. DOM nodes are host objects, provided by the browser, usually implemented in native code.

When you change a DOM node, you’re not just mutating memory owned by the JavaScript engine. You’re interacting with the browser’s rendering engine, which maintains a lot of additional state behind the scenes: layout information, CSS resolution, paint layers, accessibility data, and event handling metadata.

So when you do something as simple as:

```javascript
element.textContent = "Hello";
```

you’re signaling to the browser that the visual output of the page may have changed. That signal is where the real cost begins.

A DOM mutation can force the browser to do some or all of the following:

- Recalculate styles
- Recompute layout (reflow)
- Repaint pixels
- Re-composite layers on the GPU

These steps are typically far more expensive than the JavaScript that triggered them, and they can _cascade_: a change in one part of the DOM may affect layout elsewhere.

The browser is smart and aggressively optimizes, but even when it knows a write only affects paint, it can't know the extent of the damage without doing the work, so it must pessimistically mark parts of the rendering pipeline as “dirty”. The cost isn’t the mutation itself — it’s the invalidation of rendering state.

## Why Many Small DOM Updates Are a Problem

The classic performance issue isn’t “touching the DOM”, it’s touching it repeatedly, in small increments, while the browser observes every change.

If you interleave DOM reads and writes (like reading an element's height, then setting it, then reading the next element's height, etc...), the browser may be forced to recalculate layout repeatedly — even though only the final state actually matters.

Experienced developers learned to work around this by batching writes, caching reads, and carefully ordering operations to avoid layout thrashing. It worked, but it was brittle and easy to get wrong.

React’s Virtual DOM formalizes this idea.

## What the Virtual DOM Actually Is

React's Virtual DOM is a tree of plain JavaScript objects. It has no connection to layout, styles, or rendering. You can create it, throw it away, and compare it freely without the browser caring at all. Only after it computes the final desired UI does it touch the real DOM.

This indirection allows React to do three important things:

1. **Batch updates** — Multiple state changes are grouped into a single DOM commit.
2. **Avoid unnecessary writes** — If a piece of UI didn't change, React doesn't touch the corresponding DOM node.
3. **Minimize observable mutations** — The browser sees only the smallest required set of changes, not every intermediate state.

The Virtual DOM isn't faster than the real DOM at mutation. It reduces total work by shielding the browser from noise.

## Why Diffing Is Usually Cheaper

Comparing plain JavaScript objects is fast. Creating them is fast. Throwing them away is fast. Triggering layout and paint is not.

React trades extra JavaScript work — diffing Virtual DOM trees — for a reduction in browser rendering work. For most applications with non-trivial UI complexity, that trade is a net win.

This also explains why React can afford to re-run component functions so often. React distinguishes between the _render phase_ (calling component functions to produce a Virtual DOM description) and the _commit phase_ (applying changes to the real DOM). The expensive browser work only happens during the commit phase, once React knows exactly what needs to change.

The DOM is not “slow” in an absolute sense. Modern browsers are extremely fast, and for small or simple applications, direct DOM manipulation can be perfectly fine — or even faster than React.

The Virtual DOM shines when:

- Updates are frequent
- State changes are complex
- You want predictable, maintainable UI updates at scale

React’s real contribution isn’t raw performance. It’s making efficient DOM usage the default, instead of something developers have to constantly think about.

A better way to phrase the original claim would be:

> The DOM can be expensive to _observe changing_.

The Virtual DOM exists to ensure the browser only sees the final, minimal set of changes that matter.
