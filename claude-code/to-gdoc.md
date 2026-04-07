---
description: Upload a local Markdown file as a properly-formatted Google Doc
argument-hint: <path-to-md-file> [--account NAME] [--name "Title"] [--folder DRIVE_FOLDER_ID]
---

The user wants to convert a local Markdown file into a Google Doc using the
`md2gdoc` CLI, which uploads via Drive's native markdown-import path (the same
code path as File > Open in Google Docs — NOT the bad clipboard-paste path).

Run the command exactly as the user provided arguments:

```bash
md2gdoc $ARGUMENTS
```

Notes for interpreting the result:
- On success, the script prints a single Google Docs URL on stdout. Show that
  URL prominently to the user.
- The `--account` flag picks which Google account to use. The script supports
  any number of named profiles (e.g. `personal`, `work`, `client-acme`). If
  the user didn't pass `--account`, the script defaults to `personal` (or
  whatever `$MD2GDOC_DEFAULT_ACCOUNT` is set to).
- First-time use of an account name will pop a browser window for OAuth
  sign-in. The user should sign in with the Google account they want bound to
  that profile name. Subsequent uses are silent.
- If the script exits with "Missing OAuth client secrets...", the one-time
  Google Cloud setup hasn't been done yet. Show the script's setup
  instructions and stop.
- If the user passes a path that doesn't end in `.md`/`.markdown`/`.txt`,
  the script warns but proceeds — that's fine.
- If the path the user gave has spaces, make sure it's quoted in the shell
  command.
