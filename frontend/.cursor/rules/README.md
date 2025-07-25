# Rules Directory for HTTPayer Frontend

This directory contains project-specific rules for the HTTPayer frontend,
designed to guide both human developers and AI collaborators (e.g., Cursor) in
maintaining consistency, quality, and adherence to the project's architectural
principles.

## Purpose

The rules in this directory encode domain-specific knowledge, workflows, and
standards for the HTTPayer frontend. They ensure that all contributors—human or
AI—follow the same guidelines when working on the codebase. These rules are
scoped to the frontend and are version-controlled to evolve alongside the
project.

## How Rules Work

Cursor uses these rules to provide persistent, reusable context during code
generation, inline edits, and chat-based assistance. Each rule file is written
in MDC format (`.mdc`) and can be applied in different ways:

- **Always:** Included in every context.
- **Auto Attached:** Applied when files matching specific patterns are
  referenced.
- **Agent Requested:** Available to the AI, which decides whether to include
  them.
- **Manual:** Only applied when explicitly invoked.

## Rules Overview

### General Rules

- **File:** `general.md`
- **Purpose:** High-level project principles, including adherence to Next.js
  conventions, TypeScript enforcement, and the "Blockchain Abstraction"
  philosophy of HTTPayer.

### State Management Rules

- **File:** `state-management.md`
- **Purpose:** Defines strict separation of state concerns:
  - `wagmi` for wallet/blockchain state.
  - TanStack Query for server/API state.
  - `useState` for local UI state.

### Styling Rules

- **File:** `styling.md`
- **Purpose:** Mandates the use of Tailwind CSS for all styling. Prohibits
  inline styles and custom CSS, and promotes the use of `clsx` for conditional
  classes.

### Component Structure Rules

- **File:** `component-structure.md`
- **Purpose:** Governs the organization and nature of React components,
  including the default preference for React Server Components (RSCs) and
  criteria for Client Components (`"use client";`).

### API Interaction Rules

- **File:** `api-interaction.md`
- **Purpose:** Defines interaction patterns with backend services, emphasizing
  adherence to the Backend Interaction Specifications in `ARCHITECTURE.md`.

### Code Generation Rules

- **File:** `code-generation.md`
- **Purpose:** Provides specific directives for AI when generating new code,
  including TypeScript typing, default component types, and patterns for mocked
  data.

### Wallet Interaction Rules

- **File:** `wallet-interaction.md`
- **Purpose:** Details patterns for using `wagmi` and `viem`, including wallet
  connection, managing connection states, and passing blockchain signatures to
  the backend.

### Backend Contract Rules

- **File:** `backend-contract.md`
- **Purpose:** Reinforces adherence to the backend API contract, ensuring
  generated code aligns with
  `ARCHITECTURE.md#6-backend-interaction-specifications`.

## How to Use These Rules

1. **Automatic Application:** Most rules are set to `alwaysApply` or
   `autoAttach` and will automatically guide AI behavior when working on
   relevant files.
2. **Manual Invocation:** Some rules can be manually invoked using Cursor's
   context picker or by referencing them explicitly in chat.
3. **Updating Rules:** Rules should be updated as the project evolves. Ensure
   changes are version-controlled and documented.

## Best Practices for Rules

- **Keep Rules Focused:** Each rule should address a specific aspect of the
  project.
- **Provide Examples:** Include concrete examples or references to files when
  helpful.
- **Avoid Vagueness:** Write rules as clear, actionable instructions.
- **Split Large Concepts:** Break down complex ideas into smaller, composable
  rules.

## Contributing to Rules

To add or update rules:

1. Create a new `.mdc` file in this directory or edit an existing one.
2. Follow the MDC format, including metadata (`description`, `globs`, etc.).
3. Test the rule by invoking it in Cursor and ensuring it behaves as expected.
4. Commit the changes to version control.

---

By maintaining these rules, we ensure that HTTPayer's frontend remains
consistent, scalable, and easy to collaborate on—whether you're a human
developer or an AI assistant.
