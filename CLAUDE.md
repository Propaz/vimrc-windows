# CLAUDE.md

Editor configs for gVim on Windows (`vim/_vimrc`) and IdeaVim in the JetBrains
IDEs (`.ideavimrc`). Both are symlinked into `%USERPROFILE%`, so editing them
edits this repo.

**Read [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) before changing either
config.** The rules that are easiest to break by accident:

1. **No leader mapping may be a prefix of another** — `,x` plus `,xy` makes
   every use of `,x` wait 600 ms. Check `:map ,` first.
2. **The shared key map lives in three places** — `vim/_vimrc`, `.ideavimrc`
   and the table in `README.md`. Change all three or none.
3. **Verify option and variable names against what is installed**
   (`~/vimfiles/plugged`, IdeaVim 2.46.2), never from memory. Config that no
   plugin reads is the most common defect here.
4. **Never let a missing dependency abort the file** — guard with
   `executable()`, `has()`, `exists()`, `silent!`.
5. **Comments stay terse.** Root causes and measurements go in
   [`docs/RATIONALE.md`](docs/RATIONALE.md), referenced by anchor.

Load-test both branches of `_vimrc` before committing — the console branch with
`vim.exe -es` and the GUI branch with `gvim.exe -f`, since `has('gui_running')`
skips the GUI block in the first. Exact commands are in
[`docs/CONVENTIONS.md#testing-a-change`](docs/CONVENTIONS.md#testing-a-change).

Reusable prompts for audits, additions and releases:
[`docs/PROMPTS.md`](docs/PROMPTS.md).
