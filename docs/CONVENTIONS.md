# Working conventions

Rules for changing anything in this repo — for a human or an agent picking it
up later. `docs/RATIONALE.md` explains *why the current values are what they
are*; this file is about *how to change them without breaking something*.

---

## Repo layout

```
dotfiles/
  vim/_vimrc            gVim config          -> symlinked to %USERPROFILE%\_vimrc
  .ideavimrc            IdeaVim config       -> symlinked to %USERPROFILE%\.ideavimrc
  install-vim.bat       symlink _vimrc      (Windows, needs admin or Dev Mode)
  install.bat           symlink .ideavimrc  (Windows)
  install.sh            symlink .ideavimrc  (macOS / Linux)
  vim-state-clean.py    prune ~/.vim/.undo, .backup, .swp
  vim-state-clean.bat   wrapper for the above
  README.md             what this is, install, key map
  docs/RATIONALE.md     why every non-obvious value is what it is
  docs/CONVENTIONS.md   this file
  docs/PROMPTS.md       reusable prompts for future sessions
```

Plugins live in `~/vimfiles/plugged` (vim-plug); editor state lives in
`~/.vim/.undo`, `.backup`, `.swp`. Neither is part of this repo.

---

## The eight rules

### 1. Never break the leader-prefix invariant

**No leader mapping may be a prefix of another.** `,x` plus `,xy` means every
use of `,x` waits out `timeoutlen` (600 ms), and it is always the short,
frequent key that pays. Five collisions have already been fixed here; see the
table in `docs/RATIONALE.md#the-leader-prefix-invariant`.

Current groups — these are the *only* keys allowed a second character:

```
,c*  clipboard    ,g*  git       ,t*  toggles
,=*  format       ,h*  history   ,v*  this config
,r*  run/refactor (.ideavimrc only, nmap-only)
```

Everything else is a leaf. Before adding `,xy`, check that `,x` is free:

```vim
:verbose map ,x
:map ,                " the whole leader tree at once
```

Uppercase is a different key, so `,u`/`,U` and `,t`/`,T` are fine.

### 2. Keep the shared keys in sync — in three places

A key in the shared scheme means the same thing in gVim and in the JetBrains
IDEs. Changing one side without the other is the main way this repo rots.
A shared-key change touches:

1. `vim/_vimrc`
2. `.ideavimrc`
3. the key-map table in `README.md`

If a key genuinely cannot port, put it under **gVim-only** or **IDE-only** in
the README table and say why in `docs/RATIONALE.md`.

### 3. Verify against the installed source, not from memory

Every option name, plugin variable and action id in these files was checked
against what is actually installed. Plugin globals that no plugin reads are the
most common form of dead config — `g:NERDTreeAutoClose`, `g:fzf_ag_command` and
`g:fzf_history_file` were all in here, all inert.

```bash
# does the plugin read this variable at all?
grep -rn "fzf_ag_command" ~/vimfiles/plugged/

# what options does ALE actually define?
grep -rn "ale_python_auto" ~/vimfiles/plugged/ale/autoload/

# IdeaVim: option names, plugin names, action ids
#   set trackactionids   -> every IDE action reports its id in a notification
```

For IdeaVim, an unknown option is not silent: it raises **E518** on every
start. Vim is worse — a bad *value* often fails silently.

### 4. Degrade gracefully, never abort the file

An error partway through a vimrc leaves everything below it unapplied. So:

| Situation | Guard |
|---|---|
| external binary | `if executable('rg')` |
| Vim feature | `if has('directx')`, `has('clipboard_working')` |
| event exists | `if exists('##TextYankPost')` |
| option value may be unsupported | `silent! set wildoptions=pum` |
| colorscheme may be missing | `silent! colorscheme gruvbox` |
| whole plugin manager missing | `if filereadable(expand('~/vimfiles/autoload/plug.vim'))` … `else` fallback |

A fresh clone with no vim-plug must still open a usable editor.

### 5. Buffer-local by default in autocommands

Anything an autocommand sets should be `setlocal` / `b:`. A global `set` from an
autocommand is never restored and leaks into every other buffer for the rest of
the session — that is exactly how large-file mode used to kill syntax
highlighting session-wide.

### 6. Comments in the config are terse; reasoning goes in docs

The config keeps only:

- section headers,
- short "**do not** change this / this looks wrong but is deliberate" notes,
- lookup tables you need *at the keyboard* (the renmode table).

Everything else — root causes, measurements, what an earlier version got wrong
— belongs in `docs/RATIONALE.md`, linked by anchor. Do not reintroduce
changelog-style comments (`" the previous version did X`); the git history and
that file cover it.

### 7. Cost anything that runs while you type

Linters, autocommands and `updatetime` work fire constantly. mypy was measured
at ~133 ms warm / ~565 ms cold on a four-line file, which is why
`ale_lint_on_text_changed` is `'never'`. Measure before enabling anything on
`TextChanged`, `CursorHold` or `InsertCharPre`.

### 8. Both configs are symlinked — mind `backupcopy`

`%USERPROFILE%\_vimrc` and `%USERPROFILE%\.ideavimrc` are symlinks into this
repo, so editing them **is** editing the repo. `set backupcopy=yes` keeps Vim
from replacing the symlink with a regular file on write. Do not change it.

---

## Testing a change

Load-test both branches of `_vimrc` before committing. The GUI branch
(`has('gui_running')`) is skipped by the console test, so run both.

**Console / fallback branch:**

```bash
vim.exe -es -u "C:\Users\Propaz\dotfiles\vim\_vimrc" \
  -c 'redir! > loadtest.txt' -c 'silent messages' -c 'redir END' -c 'qa!' < /dev/null
cat loadtest.txt
```

**GUI branch** (`-f` keeps gVim in the foreground so the shell waits; a window
flashes):

```bash
gvim.exe -f -u "C:\Users\Propaz\dotfiles\vim\_vimrc" \
  -c 'redir! > gvimtest.txt' -c 'silent messages' \
  -c 'echo "renderoptions=".&renderoptions' -c 'echo "guifont=".&guifont' \
  -c 'redir END' -c 'qa!'
cat gvimtest.txt
```

Expect no `E...` lines from `_vimrc` itself. One known, pre-existing E254 from
lightline appears in the console test only — see
`docs/RATIONALE.md#termguicolors-and-the-console-fallback`.

**Prove no functional line was lost** when reflowing comments — compare
code-only lines against the previous commit as a set:

```bash
git show HEAD:vim/_vimrc | grep -v '^\s*"' | grep -v '^\s*$' | sort > /tmp/old.txt
grep -v '^\s*"' vim/_vimrc  | grep -v '^\s*$' | sort > /tmp/new.txt
diff /tmp/old.txt /tmp/new.txt      # every line here must be intentional
```

**Check a mapping actually landed:**

```vim
:verbose map ,u          " what it maps to, and which line defined it
:PythonToolInfo          " which venv, LSP and linters this buffer picked
```

`.ideavimrc` has no offline test: reload it in the IDE with `,vs` and watch for
`E518` in the IdeaVim notification.

---

## Releasing

Tags are lightweight-to-annotated and releases are cut with `gh`:

```bash
git add -A && git commit -m "..."
git push
git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --title "..." --notes-file <file>
```

Keep the notes factual: what changed, what was fixed, what a user of the
previous version must re-do (e.g. re-run `install-vim.bat`, run `:PlugInstall`).
