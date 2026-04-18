---
title: Why Does React Use a Virtual DOM?
published: true
description: A practical look at what the Virtual DOM really is, why direct DOM manipulation isn't inherently slow, and what React is actually optimizing for.
tags: react, dom, vdom, javascript
cover_image: https://dev-to-uploads.s3.amazonaws.com/uploads/articles/aop2r76m1f5z4i1l5fya.jpg
---

If you've spent any amount of time with React, you've probably heard of the Virtual DOM (or VDOM for short) as well as some version of this claim:

> React uses a Virtual DOM because direct DOM manipulation is slow.

A catchy if hand-wavy explanation. Also a bit misleading.

The DOM isn't slow in the way people usually mean — JavaScript can execute DOM mutations very quickly. What's expensive is what the browser has to do after you mutate the DOM. React's Virtual DOM exists to manage those costs.

## The DOM Is Not Just a JavaScript Object Tree

Although the [DOM](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model) feels like a normal JavaScript object tree, it is not. DOM nodes are browser-provided host objects, not ordinary JavaScript objects you fully control.

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

The browser is smart and uses heuristics to limit the scope of invalidation, but determining what's affected still requires work. The cost isn't the mutation itself — it's the invalidation and recalculation of rendering state as part of the browser's [rendering pipeline](https://developer.mozilla.org/en-US/docs/Web/Performance/How_browsers_work).

## Why Many Small DOM Updates Are a Problem

Browsers naturally batch rendering work: they typically defer style, layout, and paint until the current JavaScript task yields. But "batched" doesn't mean "free" — the more mutations the browser has to process, the more rendering work it has to do.

Consider a naive approach to declarative UI: every time state changes, tear down a chunk of the DOM and rebuild it from scratch. The browser would recalculate styles, recompute layout, and repaint for an entire subtree, even if only a single text node actually changed. The mutations themselves are cheap, but the rendering work they trigger scales with the number of nodes affected.

The problem gets worse when DOM reads enter the picture. If you read a layout property (like [`offsetHeight`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/offsetHeight)) after layout-affecting DOM changes, the browser may need to calculate layout _immediately_ to return an accurate value instead of deferring that work until later. This is called _forced synchronous layout_. Do this repeatedly — write, read, write, read — and the browser is forced to recalculate layout on every read, even though only the final state matters. This pattern is known as _layout thrashing_.

Experienced developers learned to work around both problems: reuse DOM nodes instead of replacing them, batch writes together, cache reads, and carefully order operations. It worked, but it was brittle and easy to get wrong.

React's Virtual DOM formalizes this discipline.

## What the Virtual DOM Actually Is

React's Virtual DOM is best thought of as a tree of [lightweight UI descriptions](https://react.dev/reference/react/createElement#what-is-a-react-element-exactly). JSX ultimately becomes React element objects describing `type`, `props`, and `children`. Conceptually, a piece of UI can look like this:

```javascript
// simplified
{
  type: "button",
  props: {
    className: "primary",
    children: "Save"
  }
}
```

A full render produces a tree of these descriptions. They are not DOM nodes, and they have no direct connection to layout, styles, or rendering. You can create them, throw them away, and compare them freely without triggering browser rendering work. Only after React computes the final desired UI does it touch the real DOM.

This indirection allows React to do three important things:

1. **Batch related updates** — Multiple state changes are often collapsed into fewer DOM commits.
2. **Avoid unnecessary writes** — If a piece of UI didn't change, React doesn't touch the corresponding DOM node.
3. **Minimize observable mutations** — The browser sees only the smallest required set of changes, not every intermediate state.

In other words, the Virtual DOM reduces total work by _shielding the browser from noise_.

## Why Diffing Is Usually Cheaper

All the Virtual DOM operations (creating trees, comparing them, throwing them away) are plain JavaScript work. The expensive part is what happens when changes reach the browser's rendering pipeline.

React trades extra JavaScript work for a reduction in browser rendering work. For most applications with non-trivial UI complexity, that trade is a net win.

This also explains why React can afford to re-run component functions so often. React distinguishes between the [_render phase_ and _commit phase_](https://react.dev/learn/render-and-commit) — calling component functions to produce a Virtual DOM description, then applying changes to the real DOM. The expensive browser work only happens during the commit phase, once React knows exactly what needs to change.

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

Other frameworks reduce or avoid general-purpose tree diffing for many updates by using [_signals_](https://angular.dev/guide/signals#what-are-signals), [_fine-grained reactivity_](https://docs.solidjs.com/advanced-concepts/fine-grained-reactivity), or compiler-generated update code such as Svelte 5's [runes](https://svelte.dev/docs/svelte/what-are-runes). That doesn't invalidate React's approach; it just means the Virtual DOM is a _solution_, not _the_ solution.

The useful question is not "Which camp is right?" It's "What work is the framework doing on each update, and where does it pay that cost?" For React, the core idea is straightforward: build a JavaScript-side description of the UI, compare it with the previous one, and commit only the necessary changes to the real DOM.
