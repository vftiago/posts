# Message List Article Series - Plan

Initial planning outline for the five-part article series.

## Part 1: Requirements Analysis

- The challenge format and time constraints
- Reading the requirements carefully
- Identifying ambiguities (what is "message 1"? what if message 5 doesn't exist?)
- Deciding what questions to ask vs what to assume
- Initial mental model of what we're building

## Part 2: Architecture Decisions

- State shape (messages, highlightedId, inputValue)
- Component structure (single vs multiple components, time trade-off)
- The height constraint realization (scrolling implies constrained container)
- CSS strategy choice
- Basic scaffold with hardcoded messages

## Part 3: Sending Messages

- Controlled input and state
- Send button and empty validation
- Appending to the message list
- Auto-scroll to bottom (introducing refs)
- Enter key support (nice-to-have, but trivial here)

## Part 4: Jump & Highlight

- Jump links and scrollIntoView
- Refs strategy (ref callback vs DOM query)
- Highlight state and CSS
- The timeout cleanup problem
- Ensuring only one highlight at a time

## Part 5: Polish & Retrospective

- Autofocus (nice-to-have)
- Edge case review
- Complete final code
- Trade-offs we made for speed
- What we'd refactor with more time
