#!/bin/bash
# md2gdoc installer — creates an isolated venv and installs the CLI on PATH.
#
# Use this if you don't have `uv` installed. If you do have uv, you don't need
# this — just chmod +x md2gdoc.py and symlink it onto your PATH; uv will handle
# dependencies automatically via the PEP 723 inline metadata.
#
# Environment overrides:
#   INSTALL_DIR — where to put the venv (default: ~/.local/share/md2gdoc)
#   BIN_DIR     — where to put the symlink (default: /usr/local/bin)

set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-${HOME}/.local/share/md2gdoc}"
BIN_DIR="${BIN_DIR:-/usr/local/bin}"
CONFIG_DIR="${HOME}/.config/md2gdoc"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SCRIPT="${SCRIPT_DIR}/md2gdoc.py"

if [ ! -f "$SOURCE_SCRIPT" ]; then
  echo "error: cannot find md2gdoc.py next to install.sh (looked at $SOURCE_SCRIPT)" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required but not found on PATH" >&2
  exit 1
fi

echo "==> Creating venv at $INSTALL_DIR/venv"
mkdir -p "$INSTALL_DIR"
python3 -m venv "$INSTALL_DIR/venv"

echo "==> Installing dependencies"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet \
  google-api-python-client \
  google-auth-oauthlib \
  google-auth-httplib2

echo "==> Installing script to $INSTALL_DIR/md2gdoc.py"
cp "$SOURCE_SCRIPT" "$INSTALL_DIR/md2gdoc.py"
# Rewrite the shebang to point at the venv's python so the script is directly
# executable without uv.
sed -i.bak "1s|.*|#!${INSTALL_DIR}/venv/bin/python|" "$INSTALL_DIR/md2gdoc.py"
rm "$INSTALL_DIR/md2gdoc.py.bak"
chmod +x "$INSTALL_DIR/md2gdoc.py"

echo "==> Linking $BIN_DIR/md2gdoc -> $INSTALL_DIR/md2gdoc.py"
if [ -w "$BIN_DIR" ]; then
  ln -sf "$INSTALL_DIR/md2gdoc.py" "$BIN_DIR/md2gdoc"
else
  echo "    $BIN_DIR is not writable; using sudo..."
  sudo ln -sf "$INSTALL_DIR/md2gdoc.py" "$BIN_DIR/md2gdoc"
fi

echo "==> Creating config dir at $CONFIG_DIR"
mkdir -p "$CONFIG_DIR"

echo
echo "Installed."
echo "  binary:      $BIN_DIR/md2gdoc"
echo "  venv:        $INSTALL_DIR/venv"
echo "  config dir:  $CONFIG_DIR"
echo
echo "Next step: complete the one-time Google Cloud setup, then drop your"
echo "client_secrets.json into $CONFIG_DIR/client_secrets.json."
echo "See README.md for the walkthrough."
