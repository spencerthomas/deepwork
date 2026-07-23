# Deep Work web

The `/` route is the first-task browser flow: create a task, follow the named
SSE events, submit an approval or rejection, inspect the terminal result, and
reopen any task from the list during the same browser session.

After bootstrapping the API and installing the web dependencies, run the
credential-free API, embedded deterministic executor, and web app with one
command from the repository root:

```sh
./dev
```

The launcher resolves Node.js from `PATH`. Set `DEEPWORK_NODE` to an explicit
Node.js executable when it is installed elsewhere. External providers remain
unavailable in this mode.

For web-only development against an already running API:

```sh
pnpm dev:web
```

The API defaults to `http://127.0.0.1:8000`. Set
`NEXT_PUBLIC_API_BASE_URL` to use another API origin.

`pnpm demo:web` is a browser-only fixture harness. It keeps a visible
fixture-mode banner and uses the same typed client interface as the API
transport, but it is not integrated Outcome 1 evidence. The default mode never
falls back to fixture success.
