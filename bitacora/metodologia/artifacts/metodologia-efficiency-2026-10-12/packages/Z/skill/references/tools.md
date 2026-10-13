# Tools & infrastructure

Each project has `TOOLS.md` in its bitácora folder; infrastructure shared by several projects lives in the root
`~/bitacora/TOOLS.md`. Together they say how to reach everything the project runs on: servers (SSH), hosting
(Vercel, Netlify, AWS…), CLIs, storage, databases, external services. The SessionStart context lists the names.

## Optional RTK output reduction

For long shell output, read the RTK section of [communication-and-context.md](communication-and-context.md).
Check availability and the installed command's help before using it. Prefer supported filters for noisy read-only
inspection and planned checks; use native commands when RTK is absent or exact content is needed. Preserve the
exit code and recover saved raw diagnostics before considering another execution. This guidance installs no
binary, hook or proxy and grants no new permission to run the wrapped command.

## Using them

When the user asks things like "revisa el deploy en el VPS", "conéctate a Vercel y mira los logs", "haz el deploy en
Netlify", "baja el backup del bucket":

1. Read the project's `TOOLS.md` (and the shared one). Use exactly the access it documents: the SSH host alias or
   key path, the CLI and its linked project, the env var names.
2. Act. Prefer the documented commands; read the output; report in Spanish what you found or did, with evidence.
3. Noisy read-only checks (long logs, many containers) can go to the `runner` subagent with the exact access
   from TOOLS.md, so you get only what matters.
4. Log it in today's session section (what, where, result). A deploy or infra change is also worth a line in
   SUMMARY.md's current state.

**Autonomy line:**
- **Read-only** (status, logs, listing deployments, inspecting files/containers, querying with SELECT, `df`, `top`)
  → do it freely, whenever it helps — also unprompted while debugging.
- **Changes** (deploy, restart, migrations, editing server files, env vars, DNS, deleting anything, scaling,
  anything that costs money) → do it when the user asked for that action (their request *is* the authorization),
  otherwise ask first — batched, per `execution.md` §2. Executor sessions launched with full permissions follow
  the same line.
- Before a risky change on a server (migration, config edit), take the cheap safety step first: backup/dump, copy
  the file, note the current version to roll back to.

## Keeping it current

- When you discover or set up access to something new (a server, a CLI project link, a bucket), add a `###` block to
  the right TOOLS.md, following the commented example in the file: type, access, what runs there, status/log
  commands, deploy command, notes.
- When access or commands change, edit the block in place. Infrastructure decisions (moving hosts, new provider)
  also go to DECISIONS.md.
- If the user mentions access you don't have documented, ask once for the alias/path/CLI and record it.

## Secrets — never in the bitácora

The bitácora is a git repository. Never write passwords, tokens, private keys or connection strings with
credentials into TOOLS.md, logs, specs, artifacts or commit messages. Reference them: `~/.ssh/config` host alias,
key file path, env var name, password-manager entry, "CLI already logged in". Never print a secret's value in
the conversation either; if a command would echo one, mask it.
