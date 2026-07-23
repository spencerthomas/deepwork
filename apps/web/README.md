# Deep Work web

The `/` route is the first-task browser flow: create a task, follow the named
SSE events, submit an approval or rejection, inspect the terminal result, and
reopen any task from the list during the same browser session.

Run the real API-backed app:

```sh
pnpm dev:web
```

The API defaults to `http://127.0.0.1:8000`. Set
`NEXT_PUBLIC_API_BASE_URL` to use another API origin.

For a credential-free local demonstration, run one command from the repository
root:

```sh
pnpm demo:web
```

That command explicitly sets `NEXT_PUBLIC_DEMO_MODE=fixture`. The page keeps a
visible fixture-mode banner and uses the same typed client interface as the API
transport; the default mode never falls back to fixture success.
