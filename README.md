# md2gdoc

> Convert local Markdown files into properly-formatted Google Docs from the command line.

```bash
md2gdoc draft.md
# https://docs.google.com/document/d/1ABc.../edit
```

That's it. Markdown in, shareable Google Doc URL out. Headings, lists, tables, code blocks, links — all rendered as real Google Docs formatting, not literal `##` characters.

## Why this exists

Large language models are exceptionally good at producing Markdown. Drafts, briefs, proposals, memos, reports, meeting notes — give an LLM a halfway-coherent prompt and it'll hand you a beautifully structured `.md` file.

The problem: **Markdown is a developer format, not a sharing format.** You can't email a `.md` file to your CEO. You can't drop it in a board deck. Pasting Markdown source into a Google Doc gives you literal `##` and `**` characters, because the clipboard path doesn't run Google's Markdown importer. Even "Paste as plain text" doesn't help.

The good news: Google Docs *does* have a real Markdown importer — it's the one that runs when you do **File → Open** on a `.md` file inside Google Drive. The result is a perfectly formatted Doc with proper headings, lists, tables, and code blocks. The bad news: doing that by hand for every draft is friction enough that most people just give up and ship the Markdown.

`md2gdoc` removes the friction. It's a single-file Python CLI that uploads your `.md` file via the Google Drive API with the target mimeType set to `application/vnd.google-apps.document` — which triggers the *exact same* Markdown importer as the File → Open path. One command, no UI clicking, instantly shareable URL.

## What makes this different

| Approach | Result |
|---|---|
| Paste Markdown into a Google Doc | Literal `##` and `*` characters. Awful. |
| Paste as plain text | Same, minus the bold. Still awful. |
| Manually upload via Drive UI, then "Open with Google Docs" | Works, but tedious — 4+ clicks per file. |
| Apps Script web app | Works, but requires hosting and maintenance. |
| Docs API `batchUpdate` | This *is* the clipboard-paste path under the hood. Bad. |
| **md2gdoc** | One command. Native Drive Markdown importer. Done. |

## How it works

The whole trick is two lines of metadata in the upload request:

```python
metadata = {
    "name": "My Document",
    "mimeType": "application/vnd.google-apps.document",  # ← the magic
}
media = MediaFileUpload("draft.md", mimetype="text/markdown")
service.files().create(body=metadata, media_body=media).execute()
```

When Drive sees a `text/markdown` upload with a target mimeType of `application/vnd.google-apps.document`, it routes the file through its native Markdown-to-Docs importer (the same one Google added to Docs in 2024). You get a real Doc, not a wrapped text file.

## Features

- Single-file Python script — no package install required
- Multi-account support: switch between personal, work, client accounts via `--account NAME`
- Optional Drive folder placement (`--folder FOLDER_ID`)
- Custom doc titles (`--name "..."`)
- Minimal OAuth scope (`drive.file`) — this app can only see files it created, not your existing Drive contents
- Optional Claude Code slash command (`/to-gdoc`) for use with [Claude Code](https://claude.com/claude-code)

## Installation

### Option A: with `uv` (recommended)

If you have [`uv`](https://github.com/astral-sh/uv) installed, the script is fully self-contained — `uv` reads its [PEP 723](https://peps.python.org/pep-0723/) inline dependency metadata and handles everything.

```bash
curl -O https://raw.githubusercontent.com/YOUR_USER/md2gdoc/main/md2gdoc.py
chmod +x md2gdoc.py
sudo mv md2gdoc.py /usr/local/bin/md2gdoc
```

First run will be slightly slower while `uv` builds the ephemeral env; subsequent runs are instant.

### Option B: with the bundled `install.sh` (no uv required)

Clones the repo, creates a dedicated venv at `~/.local/share/md2gdoc/venv`, installs deps, and symlinks the script to `/usr/local/bin/md2gdoc`.

```bash
git clone https://github.com/YOUR_USER/md2gdoc.git
cd md2gdoc
./install.sh
```

You can override locations with environment variables:

```bash
INSTALL_DIR=~/foo BIN_DIR=~/.local/bin ./install.sh
```

## One-time Google Cloud setup

`md2gdoc` talks to your Google Drive on your behalf, which means it needs OAuth credentials. You only do this once, and the same credentials work for every Google account you sign in with later.

1. Open <https://console.cloud.google.com/>
2. Create a new project (or pick an existing one)
3. **APIs & Services → Library** → search for "Google Drive API" → **Enable**
4. **APIs & Services → OAuth consent screen**
   - User type: **External**
   - App name: `md2gdoc` (or whatever you want)
   - Add yourself **and any other Google accounts you'll use** (e.g. your work Workspace account) as **test users**. If you skip the second account here, it'll hit a "this app isn't verified" wall when you try to bind it.
5. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Name: `md2gdoc`
6. Click the download icon to grab the JSON, then move it into place:
   ```bash
   mkdir -p ~/.config/md2gdoc
   mv ~/Downloads/client_secret_*.json ~/.config/md2gdoc/client_secrets.json
   ```

That's it. The first time you run `md2gdoc`, a browser window will pop up asking you to sign in and grant `drive.file` permission. After that, the token is cached and you won't see the browser again.

## Usage

### Basics

```bash
md2gdoc draft.md
# Uploads to your default account, returns the Doc URL.

md2gdoc draft.md --name "Q2 Strategy Memo"
# Override the doc title (default is the filename without .md).

md2gdoc draft.md --folder 1AbCdEfGhIjKlMnOpQrStUvWxYz
# Drop the doc into a specific Drive folder. The folder ID is the chunk after
# /folders/ in the folder's URL.
```

### Multi-account workflow

The `--account` (`-a`) flag lets you bind any number of named profiles to different Google accounts. Each profile gets its own cached token at `~/.config/md2gdoc/token-<name>.json`.

```bash
md2gdoc draft.md -a personal     # → your personal Gmail
md2gdoc draft.md -a work         # → your Workspace account
md2gdoc draft.md -a client-acme  # → a separate client account
```

The first time you use a name, a browser opens and you sign in with whichever account you want bound to that label. Subsequent uses are silent. You can use any names you like — `personal`/`work` is just a convention.

To change the default profile (used when you omit `-a`), set an env var:

```bash
export MD2GDOC_DEFAULT_ACCOUNT=work
```

### All flags

```
md2gdoc <file> [--account NAME] [--name TITLE] [--folder FOLDER_ID]

  -a, --account NAME       Account profile (default: 'personal' or $MD2GDOC_DEFAULT_ACCOUNT)
  -n, --name TITLE         Document title (default: filename without extension)
  -f, --folder FOLDER_ID   Drive folder ID to place the doc in
```

## Claude Code integration

If you use [Claude Code](https://claude.com/claude-code), there's a slash command in `claude-code/to-gdoc.md` that exposes `md2gdoc` as `/to-gdoc`. To install it:

```bash
mkdir -p ~/.claude/commands
cp claude-code/to-gdoc.md ~/.claude/commands/to-gdoc.md
```

Now in any Claude Code session you can do:

```
/to-gdoc ~/Documents/proposal.md
/to-gdoc ~/Documents/proposal.md -a work
/to-gdoc ~/Documents/proposal.md -a work --name "Acme Q2 Proposal"
```

Claude will run `md2gdoc` with your arguments and report the resulting Doc URL.

This is especially useful when Claude has just *generated* a Markdown file for you — you can convert and share it without leaving the terminal.

## Security & privacy

- The OAuth scope is `drive.file`, the most restrictive option Google offers. It grants this app access only to files **it has created** — `md2gdoc` cannot read, list, or modify any of your existing Drive contents. If you uninstall, nothing it touched leaves Drive; the docs it created remain yours.
- OAuth tokens are stored in plaintext at `~/.config/md2gdoc/token-<name>.json`. They're scoped to your user account and protected by filesystem permissions only. If your laptop is at risk of physical compromise, treat them like any other local credential.
- Your `client_secrets.json` is *not* a secret in the API-key sense — it identifies your Google Cloud project to Google. The actual authorization happens at sign-in time. But there's no reason to share it either.

## Troubleshooting

**"Missing OAuth client secrets..."**
You haven't completed the one-time Google Cloud setup yet. See above.

**Browser opens but says "This app isn't verified"**
You're trying to sign in with a Google account that isn't listed as a test user on your OAuth consent screen. Go back to step 4 of the setup and add it.

**"Drive API error: ... insufficient authentication scopes"**
Your cached token was created with an older scope. Delete it and re-auth:
```bash
rm ~/.config/md2gdoc/token-<account>.json
md2gdoc draft.md -a <account>
```

**Token refresh keeps failing silently**
Same fix as above — delete the cached token and let the script reissue it.

**Doc has weird formatting / missing things**
Google's Markdown importer is good but not perfect. Things that work well: headings, paragraphs, bold/italic, ordered/unordered lists, links, tables, fenced code blocks, blockquotes. Things that may not survive: HTML embedded in Markdown, exotic flavors (footnotes, definition lists), nested code fences. If something specific breaks, try simplifying that section.

## License

MIT. See [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome. Please keep the script single-file and dependency-light — the goal is "one curl away from working."
