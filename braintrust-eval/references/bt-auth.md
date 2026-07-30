# Braintrust auth (org-scoped keys)

Braintrust API keys are **scoped to one org**, so which key you use *is* which org
the run lands in. This skill runs across two orgs, so `.env` holds two keys.

## The canonical `.env`

One file, fixed location: `/Users/jess/Documents/Coding Projects/Braintrust/.env`.
Sub-projects have their own `.env`s with a generic `BRAINTRUST_API_KEY` — **ignore
those and never sweep them for keys** (credential-scanning guards will block it,
and the org they belong to is unknown anyway).

```dotenv
# /Users/jess/Documents/Coding Projects/Braintrust/.env
BRAINTRUST_API_KEY_PERSONAL=sk-...      # personal org (Jess Wang)
BRAINTRUST_API_KEY_BRAINTRUST=sk-...    # Braintrust org
# optional, self-hosted only:
# BRAINTRUST_API_URL=https://api.braintrust.dev
```

If the file or the needed variable is missing: create/append the stub line, ask
the user to fill it in the file (never in chat), then verify with the org-list
call below and confirm the org name matches what the user picked.

## Verifying a key's org

`GET /v1/organization` can return an **empty list** even for a valid key (org-member
permissions), so don't use it to verify. List projects instead — a valid key sees
its org's projects, and the roster makes it obvious which org you're in:

```bash
curl -s "https://api.braintrust.dev/v1/project?limit=100" \
  -H "Authorization: Bearer $KEY"   # -> objects[].name; empty/401 means bad key
```

Phase 1 asks which org, then selects the matching key:
- **Personal** → `BRAINTRUST_API_KEY_PERSONAL`
- **Braintrust** → `BRAINTRUST_API_KEY_BRAINTRUST`

**Governance default:** if the eval touches sensitive / customer / proprietary
data, default to the Personal org unless the user says otherwise.

## Rules

- **Never ask the user to paste a key into the chat**, and never print one. Keys
  are read from the environment only. If the chosen key is missing, point the user
  at `.env.example` and stop.
- Get a key from the Braintrust app → **Settings → API Keys**. Each org has its
  own; copy the one for the org you're targeting.

## Making model calls through Braintrust

The **gateway** gives you one OpenAI-compatible endpoint for many providers,
authed with your Braintrust key — handy for judges and for the task model.
(The older `/v1/proxy` AI proxy is deprecated; the gateway is a drop-in
replacement — same key, same OpenAI-compatible shape, just a new base URL.)

```
POST https://gateway.braintrust.dev/chat/completions
Authorization: Bearer <the org's key>
```

## Resolving a project

```bash
curl "$BRAINTRUST_API_URL/v1/project?project_name=My%20Project" \
  -H "Authorization: Bearer $KEY"   # -> objects[0].id, objects[0].org_id
```

> Duplicated into each Braintrust skill for self-containment — keep copies in sync.
