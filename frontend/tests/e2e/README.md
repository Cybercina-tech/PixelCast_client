# End-to-end tests (Playwright)

1. Copy [`../../.env.e2e.example`](../../.env.e2e.example) to `frontend/.env.e2e` and set `E2E_USERNAME` and `E2E_PASSWORD` to a valid account on your dev stack.
2. Start the app (e.g. Docker Compose with frontend on port 5173).
3. Run: `npm run e2e` from the `frontend` directory.

`playwright.config.js` loads `frontend/.env.e2e` if present. You can override `E2E_BASE_URL` when the UI is not on `http://localhost:5173`.
