# Installed-public conformance cell

This isolated cell is intentionally blocked, unlocked, and unexecuted.

Do not add distributions, generate `uv.lock`, or run its tests until
`index_preflight.py --mode approved-public-index` has explicit reviewer approval
and succeeds. At that point the reviewer must record exact public distribution
versions and lock/file hashes for the public exports below before observation:

- `deepagents.create_deep_agent`
- `deepagents.RubricMiddleware`
- `deepagents.SubAgent`
- `deepagents.SubAgentMiddleware`

Only public package-index distributions are permitted. Source checkouts, path or
editable dependencies, copied wheels, and other worktree environments are
forbidden. The conformance cell must use a deterministic fake chat model and no
provider network. Until those pins exist, every cell remains
`blocked-package-index-evidence`.
