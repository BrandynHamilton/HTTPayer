# Contributing to HTTPayer

Thank you for your interest in contributing! Please follow these guidelines for
a smooth experience.

## Local Development Setup

### Frontend

```bash
cd frontend
pnpm install
cp .env.local.example .env.local # Fill in required env vars
pnpm dev
```

### Backend (Node.js)

```bash
cd backend
npm install
npm run dev
```

### Backend (Python Treasury/Facilitator)

```bash
cd backend
uv venv
uv sync
uv run python treasury/main.py
```

### SDKs

- Python: See `packages/python/README.md`
- TypeScript: See `packages/typescript/httpayer-ts/README.md`

## Environment Variables

- `NEXT_PUBLIC_HTTPAYER_API_URL` — HTTPayer Orchestration Service (safe to
  expose)
- `NEXT_PUBLIC_TREASURY_API_URL` — Treasury Service (safe to expose)
- `HTTPAYER_API_KEY` — API key for backend authentication (**set this in your
  `.env.local`, never commit or share it, and only use it in server-side code.
  Do NOT use the `NEXT_PUBLIC_` prefix for secrets.**)

> ⚠️ **Security Note:** Only use un-prefixed environment variables (like
> `HTTPAYER_API_KEY`) for secrets, and access them in server-side code only. Any
> variable prefixed with `NEXT_PUBLIC_` will be exposed to the browser. See
> [Next.js docs](https://nextjs.org/docs/app/guides/environment-variables) for
> details.

## Testing

- Frontend: `pnpm test` (if available)
- Backend: `npm test` (Node.js), `pytest` (Python)
- SDKs: See respective README files for testing instructions

## Coding Standards & Architecture

- All API types are defined in `src/types/` and validated at runtime with Zod
  schemas in `src/schemas/`.
- Linting: Run `pnpm lint` (frontend), `npm run lint` (backend), or `black`
  (Python)
- Coding standards and patterns are enforced via rules in
  [frontend/.cursor/rules/](frontend/.cursor/rules/).
- The architecture, data flow, and API contract are described in
  [`frontend/ARCHITECTURE.md`](frontend/ARCHITECTURE.md).

## Contribution Workflow

1. Fork the repo and create a feature branch
2. Make your changes (with tests if possible)
3. Run linting/formatting tools
4. Open a pull request and describe your changes
5. Participate in code review

## See Also

- [frontend/ARCHITECTURE.md](frontend/ARCHITECTURE.md) — Full architecture, data
  flow, and API contract
- [frontend/.cursor/rules/](frontend/.cursor/rules/) — Coding standards and best
  practices
- [TODO.md](./TODO.md) — Development roadmap and open tasks
