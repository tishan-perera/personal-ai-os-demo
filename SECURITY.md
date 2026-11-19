# Security

This demo keeps secrets out of git and keeps consequential actions behind an owner decision.

## Never commit

- API keys, tokens, passwords, private keys, or a `.env` file with values
- Real mail, real payment details, account numbers, or private contact details
- Exports of a live inbox, calendar, or ledger

`.env.example` lists variable names only. Leave the values empty.

## If a secret lands in git

Rotate the credential first. Deleting the file in a later commit leaves it in old history. Purge the history, then rotate again if the secret was pushed.

## What the app will not do

- Demo mode makes no network call.
- Optional model mode runs only when `ATRIUM_LLM=on` and `ATRIUM_LLM_API_KEY` is set in the environment. The key is sent as a bearer token to the base URL you configure. It is not written to the state file or the audit log.
- The approval label `owner` is a name on a local decision. It is not a login.
- Request text is stored as data. Planners do not turn it into a shell command, a payee, or an address.
