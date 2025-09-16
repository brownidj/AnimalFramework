#!/usr/bin/env zsh
# Secret & history scrub (zsh edition)
# - Prefers git-filter-repo; falls back to BFG
# - Removes .env from history and scrubs OpenAI key patterns
# - Pushes to 'clean-main' if 'main' is protected or force-push is blocked

set -e
set -u
set -o pipefail

# -------- config --------
DEFAULT_REMOTE="origin"
DEFAULT_BRANCH="main"        # current protected branch name
CLEAN_BRANCH="clean-main"    # new branch if protections block force-push
REPLACEMENTS_FILE="replacements.txt"
# Add/adjust patterns as needed:
REPLACEMENTS_CONTENT=$'# OpenAI general\nregex:sk-[A-Za-z0-9_\\-]{20,}==>***REDACTED***\n# OpenAI project-scoped\nregex:sk-proj-[A-Za-z0-9_\\-]{20,}==>***REDACTED***\n'

# -------- helpers --------
say() { print -- "[scrub] $*"; }
die() { print -- "[scrub][ERR] $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

ensure_repo_root() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a Git repository."
}

ensure_clean_worktree() {
  if [[ -n "$(git status --porcelain)" ]]; then
    die "Worktree not clean. Commit or stash first."
  fi
}

ensure_branch_vars() {
  REMOTE="${REMOTE:-$DEFAULT_REMOTE}"
  BRANCH="${BRANCH:-$DEFAULT_BRANCH}"
}

ensure_ignore_env() {
  # stop tracking .env if it was ever added
  git rm --cached .env 2>/dev/null || true
  # ensure ignore entries exist (idempotent)
  grep -qxF "/.env" .gitignore 2>/dev/null || print "/.env" >> .gitignore
  grep -qxF "/.env.*" .gitignore 2>/dev/null || print "/.env.*" >> .gitignore
  grep -qxF "*.env" .gitignore 2>/dev/null || print "*.env" >> .gitignore
  git add .gitignore
  if ! git diff --cached --quiet; then
    git commit -m "chore(security): ensure .env files are ignored"
  fi
}

scan_snapshot_for_keys() {
  say "Scanning current snapshot for 'sk-'…"
  if git grep -nE "sk-|sk-proj-" -- :/ >/dev/null 2>&1; then
    die "Secret-like strings found in current snapshot. Remove/redact them and re-run."
  fi
  say "OK: no keys in working snapshot."
}

write_replacements_file() {
  print -- "$REPLACEMENTS_CONTENT" > "$REPLACEMENTS_FILE"
  say "Wrote $REPLACEMENTS_FILE with redact patterns."
}

# ---------- git-filter-repo path ----------
scrub_with_filter_repo() {
  say "Using git-filter-repo…"
  # Remove .env files entirely from history
  git filter-repo --force --path .env --invert-paths
  # Replace key-like strings anywhere
  git filter-repo --force --replace-text "$REPLACEMENTS_FILE"
  say "History rewritten with git-filter-repo."
}

# ---------- BFG path (mirror clone) ----------
scrub_with_bfg() {
  have bfg || die "BFG not installed (brew install bfg)."
  say "Using BFG via mirror clone…"
  local TMPDIR
  TMPDIR=$(mktemp -d)
  local MIRROR="$TMPDIR/$(basename "$(pwd)").git"

  local REMOTE_URL
  REMOTE_URL=$(git remote get-url "$REMOTE")

  say "Mirror cloning $REMOTE_URL → $MIRROR"
  git clone --mirror "$REMOTE_URL" "$MIRROR"
  pushd "$MIRROR" >/dev/null

  say "BFG delete .env files from history…"
  bfg --delete-files .env

  say "BFG redact key patterns via $REPLACEMENTS_FILE…"
  cp "$(pwd:h:h)/$REPLACEMENTS_FILE" .
  bfg --replace-text "$REPLACEMENTS_FILE"

  say "GC + expire…"
  git reflog expire --expire=now --all
  git gc --prune=now --aggressive

  say "Attempting force-push to $REMOTE $BRANCH…"
  if git push --force "$REMOTE" "refs/heads/$BRANCH:refs/heads/$BRANCH"; then
    say "Force-pushed cleaned history to $BRANCH."
  else
    say "Force-push blocked. Pushing to $CLEAN_BRANCH instead…"
    git push --force "$REMOTE" "refs/heads/$BRANCH:refs/heads/$CLEAN_BRANCH" || die "Push to $CLEAN_BRANCH failed."
    say "Created $CLEAN_BRANCH on remote. Make it the default branch in your host UI, then protect it."
  fi

  popd >/dev/null
  rm -rf "$TMPDIR"
  say "BFG path completed."
}

final_verify_and_reclone_hint() {
  say "Remote updated. Re-clone fresh to drop stale objects:"
  say "  cd .. && rm -rf \"$(basename "$(pwd)")\" && git clone $(git remote get-url "$REMOTE")"
  say "Verifying history for keys (rough check)…"
  if git rev-list --objects --all | cut -d' ' -f1 | \
     xargs -n1 git cat-file -p 2>/dev/null | \
     grep -nE "sk-|sk-proj-" >/dev/null; then
    die "Detected key-like strings in history after scrub. Re-check patterns and rerun."
  fi
  say "OK: no key-like strings detected in history."
}

install_precommit_detect_secrets() {
  say "Adding pre-commit secret scanning (Yelp/detect-secrets)…"
  if ! have pre-commit; then
    if have pipx; then
      pipx install pre-commit
    else
      say "pipx not found; installing pre-commit with pip (user)…"
      python3 -m pip install --user pre-commit
    fi
  fi

  if [[ ! -f .pre-commit-config.yaml ]]; then
    cat > .pre-commit-config.yaml <<'YAML'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
YAML
    git add .pre-commit-config.yaml
    git commit -m "chore(security): add pre-commit secret scanning (detect-secrets)" || true
  fi

  pre-commit install || true
  say "Pre-commit hook installed."
}

# -------- main --------
ensure_repo_root
ensure_branch_vars
ensure_clean_worktree
ensure_ignore_env
scan_snapshot_for_keys
write_replacements_file

if have git-filter-repo; then
  scrub_with_filter_repo
  say "Attempting to push cleaned history to $BRANCH…"
  if git push --force "$REMOTE" "HEAD:refs/heads/$BRANCH"; then
    say "Force-pushed to $BRANCH."
  else
    say "Force-push blocked. Pushing to $CLEAN_BRANCH instead…"
    git push --force "$REMOTE" "HEAD:refs/heads/$CLEAN_BRANCH" || die "Push to $CLEAN_BRANCH failed."
    say "Created $CLEAN_BRANCH on remote. Make it default in the host UI, then protect it."
  fi
else
  say "git-filter-repo not found. Trying BFG path…"
  scrub_with_bfg
fi

final_verify_and_reclone_hint
install_precommit_detect_secrets

say "All done. Rotate any exposed keys (delete old), set $CLEAN_BRANCH default if created, and re-clone locally."
