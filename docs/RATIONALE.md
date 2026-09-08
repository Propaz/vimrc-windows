# Rationale

Why the configs look the way they do. The configs themselves carry only short
"do not touch this" notes; the reasoning lives here.

Every claim below was verified against the installed plugin sources
(`~/vimfiles/plugged`), IdeaVim 2.46.2, and `:help`, not from memory.

---

## Targets

| File | Runs in | Assumes |
|---|---|---|
| `vim/_vimrc` | gvim.exe 9.2 x64 (scoop), GUI | DirectWrite, UTF-8, `%PATH%` has rg/fzf |
| `.ideavimrc` | IdeaVim 2.46.2 in IntelliJ IDEA / Rider | the IDE owns indentation, status bar, file lifecycle |

`_vimrc` is written GUI-first. The few genuinely terminal-only options are
guarded with `!has('gui_running')` so a console fallback still behaves.

---

## `_vimrc`

### Option order

`encoding` is set first: it must be settled before anything touches text, and
`:help renderoptions` requires `encoding=utf-8` before DirectWrite is enabled.

`mapleader` is set before plugins load. Any `<Leader>` mapping a plugin defines
at load time binds to whatever the leader was at that moment, so setting it
later leaves plugin mappings on the old leader (`\`).

`background=dark` must precede `:colorscheme`, or gruvbox picks its light
variants.

### Windows shell

Vim adopts `$SHELL` when it is set, and MSYS2 / Git-Bash set it to a POSIX
shell — which silently breaks `:!`, `:grep` and fzf under gVim. The whole
cmd.exe family is pinned so the values stay internally consistent.

`shellpipe` is the subtle one. A bare `set shellpipe=|` sets it to an **empty
string**: in `:set`, `|` is parsed as a command separator, so `:grep` captured
nothing at all. It must be `>%s\ 2>&1`.

### `termguicolors` and the console fallback

24-bit colour is a **terminal** feature — `:help termguicolors` says it applies
gui colours *"in the terminal"*. The GUI always uses `guifg`/`guibg` directly,
so setting it under gVim is a no-op. It is kept only for the console fallback.

On the Win32 console it additionally needs the `+vtp` virtual-terminal feature.
Without that check `set termguicolors` throws **E954**, and lightline then
cascades into **E254: Invalid color name guibg=** because it has no gui colours
to work with.

> **Known limitation.** The `has('vcon')` guard fixes E954, but when `vcon` is
> absent (`vim -es`, or a console without VT) lightline still raises E254,
> because the gruvbox lightline colorscheme is defined in gui colours only.
> Harmless for the GUI-first target. If the console fallback ever matters, set
> `let g:lightline.colorscheme = '16color'` when `!&termguicolors`.

### Clipboard: yanks only

`clipboard=unnamed` would route **deletes and changes** to the system clipboard
too, clobbering whatever was copied from another app. Instead a `TextYankPost`
autocommand mirrors to `+` only when the operator was `y` and no register was
named. Deletes stay in Vim's own registers; `"+p` pastes from the OS.

This is the one place `_vimrc` and `.ideavimrc` deliberately differ — see
[IdeaVim clipboard](#ideavim-clipboard).

### Options deliberately NOT set

| Option | Why not |
|---|---|
| `lazyredraw` | Suppresses redraws mid-macro; under gVim + DirectWrite that is a known source of stale/torn glyphs. The macro speedup is irrelevant in a GUI on modern hardware. |
| `showmatch` | It physically jumps the cursor to the match. The bundled matchparen plugin already highlights the pair in place. |

`ruler` **is** set even though lightline replaces the status line, where it is
inert: it still does its job in the no-plugin fallback path.

### DirectWrite glyph drift

The symptom: text drifts and staircases across the line, worse the further
right you look. `:help renderoptions` admits *"some fonts and options
combination causes trouble on drawing glyphs."*

Root cause: a bare `set renderoptions=type:directx` leaves `renmode` and
`taamode` at DEFAULT, which lets DirectWrite lay glyphs out with **fractional
advance widths**. Vim paints text onto a fixed character grid, so those
sub-pixel fractions accumulate along a line and the text visibly walks out of
its cells. Pinning an **integer-advance** rendering mode is the fix.

| renmode | Name | Behaviour |
|---|---|---|
| 3 | GDI_NATURAL | ClearType smoothing + integer advances — **the default here** |
| 2 | GDI_CLASSIC | Snaps hardest to the grid; most conservative |
| 5 | NATURAL_SYMMETRIC | Prettiest, but fractional → drift-prone |
| 0 | DEFAULT | DirectWrite decides; this is what drifted |

Recovery, if it ever reappears:

| Key / command | Effect |
|---|---|
| `<F10>` / `:RenderCycle` | Cycle renmode live to A/B the fix |
| `<F9>` / `:RenderReset` | Rebuild the render target |
| `:RenderGDI` | Drop to plain GDI — no sub-pixel positioning, cannot drift |
| `:RenderDX` | Re-apply the pinned DirectWrite settings |

`<F9>` exists because plain `<C-l>` only repaints the grid; it does not
re-create the DirectWrite render target, so an already-corrupted glyph layout
survives a normal redraw.

### Font

`guifont=Consolas:h14`, with **no `:cANSI` suffix**. That charset spec forces
the ANSI codepage, so gVim selects a *fallback* font for anything outside it —
including Cyrillic. Two fonts with different advance widths on one screen is
itself a cause of misaligned glyphs. Consolas ships Cyrillic, so UTF-8 uses it
directly. `linespace=0` keeps the line height deterministic.

### State directories and backup policy

Undo/backup/swap live under `~/.vim`, plugins under `~/vimfiles`. The split is
cosmetic, and `~/.vim` already holds 300+ real undo files — moving them would
orphan working undo history for no functional gain.

`backup` kept a **permanent** copy of every file on every save and pruned
nothing: `~/.vim/.backup` had reached 39 MB / 317 files, 37 of them for files
that no longer exist. `writebackup` keeps the crash-safety window during the
write itself (backup written → original replaced → backup removed) without
accumulating history that git and `undofile` already provide.

`backupcopy=yes` forces copy-not-rename, which preserves symlinks — and
`~/_vimrc` is one.

Vim never prunes these directories, so they grow for years. That is
housekeeping, not an editor feature, so it lives outside the config in
`vim-state-clean.py` / `vim-state-clean.bat`.

### Plugin loading

The whole `plug#begin`/`plug#end` block sits behind a `filereadable()` check on
`plug.vim`, so a fresh clone of this repo with no vim-plug yet does not take
the rest of the file down with it — the `else` branch enables `filetype plugin
indent on` and `syntax enable` and carries on.

| Plugin | Loading | Why |
|---|---|---|
| `vim-fugitive` | eager | Lazy-loading on `['G','Git']` missed `:Gclog` / `:Ghdiffsplit` |
| `nerdtree` | eager | `NERDTreeHijackNetrw` only works if NERDTree is loaded *when a directory is opened*, so it cannot sit behind the toggle command |
| `undotree` | `on: UndotreeToggle` | Nothing needs it before the first toggle |
| `vim-go` | `for: go` | Heavy, and pulls in its own tooling |
| `karate-linter` | `for: cucumber, karate` | Filetype-specific by nature |
| `fzf` | no `do: fzf#install()` | `fzf.exe` comes from scoop and is on `%PATH%`; this clone only supplies the Vim plugin half |

`silent! colorscheme gruvbox` matters: on a machine where gruvbox is not
installed yet (before the first `:PlugInstall`) a bare `:colorscheme` throws
E185 and **aborts the rest of the vimrc**, leaving a half-configured editor.

### netrw and NERDTree

netrw is intentionally left **enabled**. Disabling it (`g:loaded_netrw = 1`)
also kills `gx` (open URL under cursor) and fugitive's `:GBrowse`, and it
contradicts `NERDTreeHijackNetrw`. Hijacking is the supported way to have
NERDTree handle directories while netrw keeps providing its other services.

`g:NERDTreeQuitOnOpen` is the option that closes the tree after opening a file.
`g:NERDTreeAutoClose`, used previously, **does not exist in NERDTree at all**.

`g:NERDTreeIgnore` takes **Vim regexes, not globs**. `'\venv'` used to be
listed there: in a Vim regex `\v` means "very magic", so that pattern collapsed
to plain `env` and hid *every* path containing the substring — `environment.py`,
`env.example`, `test_environment/`. The entries are now `'^venv$'` and
`'\.venv'`.

### fzf

`g:fzf_layout = { 'down': '~40%' }` — a bottom split avoids the
floating-window rendering issues in gVim.

`:Ag` takes its flags from the **command definition**, not from a global.
`g:fzf_ag_command` and `g:fzf_history_file` are not read by fzf.vim anywhere
(verified against the plugin source), so the command is overridden instead.

There is deliberately **no `,ag` mapping**: `,a` (select all) would become a
prefix of it and wait out `timeoutlen` on every use, and `:Ag <cword>` is what
`,u` already does through rg. The `:Ag` command itself remains.

`FindProjectRoot()` is a **global** function, not `s:`-local, because it is
called from an `<expr>` mapping, which is not evaluated in this script's
context.

### ALE

`g:ale_linters` sets `'go': []` on purpose — vim-go already provides Go
diagnostics, and running both means two toolchains linting the same buffer.

Both ruff entries in `g:ale_fixers` are needed and they are not duplicates:
`ruff` as a *fixer* runs `ruff check --fix` (lint autofixes) and does **not**
reformat; `ruff_format` is the formatter half. Format first, then apply lint
fixes.

Lint timing: mypy costs ~133 ms warm and ~565 ms cold even on a four-line file,
and with ALE's default (`'normal'`) it re-runs 200 ms after every pause in
typing. On a real project that is seconds of wasted background work per minute.
`lint_on_text_changed = 'never'` plus lint on save and on leaving Insert mode
keeps ruff's feedback fast enough.

Trailing whitespace is significant in markdown, diffs and commit messages, so
`b:ale_fix_on_save = 0` for those filetypes keeps the `'*'` fixer from
rewriting them.

### Python toolchain

ruff and mypy need no help finding the project venv: ALE resolves them through
`ale#python#FindExecutable()`, which walks up from the buffer and prefers
`<venv>\Scripts\<tool>.exe` over anything on `%PATH%`.

`g:ale_python_auto_uv` runs tools as `uv run <tool>` whenever a `uv.lock` sits
above the buffer, so the locked environment is used even if the venv was never
activated.

`g:ale_python_auto_virtualenv` is read **only** by the LSP linters (jedils,
pylsp, pyright) — verified in `ale_linters/python/`. It has no effect on ruff or
mypy.

ALE's completion and autoimport are **LSP-only** features. ruff and mypy are
plain linters that expose no completion at all, so `g:ale_completion_enabled`
stays inert until one of `g:python_lsp_preference` is present; first match wins.

The autoload pitfall in `s:PythonDetect()`: do **not** guard the call with
`exists('*ale#python#FindVirtualenv')`. For an autoload function that has not
been sourced yet, `exists()` returns 0, which would silently disable detection
on every first call. Calling it inside `try`/`catch` triggers the autoload and
still survives ALE being absent (E117).

Warnings are keyed per venv (`s:python_warned`), not per buffer, so a fully
provisioned environment stays silent and a broken one complains once.
`:PythonToolInfo` reports what detection actually picked.

### The leader-prefix invariant

**No leader mapping may be a prefix of another.** If `,x` and `,xy` both exist,
every use of `,x` waits out `timeoutlen` (600 ms) before Vim can tell them
apart — and it is always the short, frequent key that pays.

Collisions found and fixed, in order:

| Was | Problem | Now |
|---|---|---|
| `,n` + `,nr` | `,n` (next buffer) blocked | `,tr` toggles relativenumber |
| `,f` + `,ff`/`,fj`/`,fcj`/`,fcr` | the most-used key was the slowest | flattened into `,f` `,F` `,u` `,U` `,l` |
| `,cf` + `,cfp` | `,cf` (copy filename) blocked | `,cp` copies the full path |
| `,w` + `,wf` | **save**, the single most-used mapping, waited 600 ms | `,wf` → `,U` |
| `,a` + `,ag` | select-all blocked whenever `ag` was on `%PATH%` | `,ag` mapping removed |

`,wf` had to keep a key of its own rather than being dropped: `,u` greps the
word in file **contents** and `,F` opens an **empty** file prompt, so neither
does what `,wf` did — open the file *named* after the word under the cursor.
It is now `,U`, and it has no IDE twin on purpose: in the IDE that job is `gd`
(Go to Declaration), which is exact rather than fuzzy and is bound on both
sides.

Uppercase is a different key, so `,u`/`,U` and `,t`/`,T` are not collisions.

### Mapping details worth keeping

**Visual-mode ranges double.** In a Visual-mode mapping, `:` **already**
inserts `'<,'>`. The jq mappings used to read `:'<,'>!jq`, so the range was
doubled and the mapping died with
`E492: Not an editor command: '<,'>'<,'>!jq` — it never worked. The Visual
variants must spell only `:!jq`.

**`,=r`** strips stray CR with `:keeppatterns %s/\r//ge`. The `e` flag avoids
E486 when the buffer is already clean; `keeppatterns` means the search register
is never touched, so no `:nohlsearch` is needed afterwards. (`.ideavimrc` does
need it — IdeaVim has no `:keeppatterns`.)

**`,=f`** wraps `gg=G` in `mz` / `` `z `` so the cursor returns instead of being
dumped on the last line by `G`.

**Line moves are Alt-based.** The old `inoremap <leader>j/k` made every comma
typed in prose hang on `timeoutlen` mid-word. `<A-j>`/`<A-k>` work in Insert
mode without that; the `,j`/`,k` aliases are kept for muscle memory in Normal
and Visual mode only.

**`s:VSetSearch()`** makes `*`, `#` and Visual `,r` work on a selection:

- It yanks into register `z`, not the unnamed register. That leaves `""` intact
  **and** keeps the `YankToClipboard` autocommand from firing (it only mirrors
  yanks whose `regname` is empty), so hitting `*` never touches the system
  clipboard. Yanking into `"z` also repoints the unnamed register at it, so
  both registers are saved and restored.
- `\V` (very nomagic) makes the selection literal, so selecting text containing
  `.`, `*` or `[` searches for those characters instead of a broken regex.
- A linewise selection carries a trailing newline; unstripped, the pattern
  would only match occurrences sitting at end-of-line.
- Visual `,r` is deliberately **not** `<silent>`: the command line has to stay
  on screen waiting for the replacement text.

### Large-file mode

Everything in `s:LargeFileMode()` is **buffer-local by design**. The previous
version used global `set eventignore+=FileType`, `filetype off` and
`filetype plugin indent off` and never restored them, so opening one big log
silently killed syntax highlighting and every ftplugin for the **whole session**
until restart.

`setlocal syntax=0` was also a no-op — the value that disables syntax is `OFF`.

---

## `.ideavimrc`

### IdeaVim option subset

IdeaVim implements roughly 60 of Vim's options. Anything the IDE owns outright
is not an option at all, and an unknown one raises **E518** on every start —
IdeaVim does not abort the file, but it flags the config as broken. These were
therefore removed rather than kept "for symmetry" with `_vimrc`:

| Removed | Owned by |
|---|---|
| `autoindent`, `copyindent`, `shiftround`, `expandtab`, `tabstop`, `shiftwidth` | the IDE's code style |
| `ruler`, `laststatus` | the IDE's status bar |
| `lazyredraw` | nothing — there is no redraw loop to suppress |
| `paste` | nothing — there is nothing to protect a paste from |
| `showmatch` | the IDE's brace highlighter, which does it in place |
| `hidden`, `autoread`, `backup`, `undofile`, `swapfile` | the IDE's file lifecycle and Local History |

`autoindent` in particular was in this file and raised E518 on every start.

`ideamarks` and `ideawrite` were also set here and are redundant: both are
global toggles that already default to on / `"all"`, so A–Z marks already sync
with IDE bookmarks and `:w` already behaves like `:wa`.

### IdeaVim clipboard

`set clipboard^=unnamedplus` — `^=` **prepends**. This matters: IdeaVim
overrides the default of `clipboard` to `"ideaput,autoselect"`, and a plain
`set clipboard=unnamed,unnamedplus` (what this file used to do) **threw both
away**. Losing `ideaput` means losing the IDE's paste handlers — auto-import of
pasted code, reindentation, the Java-to-Kotlin conversion prompt — for every
`p` in the editor.

On Windows `*` and `+` are the same clipboard, so `unnamedplus` alone is enough;
`unnamed` would be redundant.

Unlike `_vimrc`, deletes **do** reach the clipboard here: IdeaVim has no
`TextYankPost` event — its autocommand list is `Buf*`/`Win*`/`Insert*`/`Focus*`/
`FileType` — so the yank-only trick does not port. Mappings that must not touch
the clipboard name a register explicitly (`"zy`); an explicit register always
bypasses `clipboard`.

### IdeaVim bundled plugins

Enabled: `surround`, `commentary`, `highlightedyank`, `ReplaceWithRegister`,
`argtextobj`, `textobj-entire`, `matchit`.

Also bundled in 2.46.2 and left off. Enable with `set <name>`:

| Plugin | Keys | Note |
|---|---|---|
| `exchange` | `cxx` / `cx{motion}` | swap two regions |
| `textobj-indent` | `ii` / `ai` | an indentation block |
| `functextobj` | `if` / `af` | a function body |
| `classtextobj` | `ic` / `ac` | a class |
| `camelcasemotion` | `,w` / `,b` | **would collide with `<leader>`** |
| `indentwise` | `[-` `[+` `]-` `]+` | move by indent level |
| `vim-paragraph-motion` | `{` `}` | also stop on whitespace-only lines |
| `multiple-cursors` | `<A-n>` / `<A-x>` | IDE multi-caret, Vim-style |
| `abolish` | `:S` | case-preserving substitute |
| `NERDTree` | — | NERDTree keys in the Project view |
| `yankring` | `<C-p>` / `<C-n>` | new in 2.46: cycle the ring after a paste |
| `sneak` | `s{char}{char}` | **shadows Vim's `s`** (substitute char) |
| `targets` | — | superset of a/i text objects, but it also defines `ia`/`aa` for arguments, so it **conflicts with `argtextobj`** — pick one |

### `sethandler`

Without it the IDE swallows the key before IdeaVim ever sees it. `a:vim` means
all modes are handled by Vim. Needed for `<C-S-c>` (Copy Reference), `<C-S-v>`
(Paste from History), `<A-j>`/`<A-k>` (Add Selection for Next Occurrence) and
`<F5>` (Copy, refactoring).

### Mapping choices

`map` (recursive) is fine for `<Action>` mappings — there is no Vim command
underneath to recurse into — and it covers Normal/Visual/Operator-pending in one
line. `nnoremap`/`xnoremap` are used wherever the right-hand side is actual Vim.

The `,r*` group is `nmap`-only so it never shadows the Visual-mode `,r`
(replace selection) at the bottom of the file.

`:split`, not `:edit`, for `,vm`. In IdeaVim 2.46.2 `:source`, `:read` and
`:split` all run their argument through path expansion (so `~` and `$VAR`
resolve), but `:edit` does **not** — it hands the raw string to the IDE, and
`:e ~/.ideavimrc` simply fails to find a file. Close the split with `<C-w>c`.

`MoveLineDown`/`MoveLineUp` is the plain line move, i.e. the same thing
`_vimrc`'s `:m` mappings do. The syntax-aware one is
`MoveStatementDown`/`MoveStatementUp`, which moves whole statements and methods
— not bound here.

### Deleted outright

- `set which-key` and ~50 `g:WhichKeyDesc_*` lines. which-key is **not** part of
  IdeaVim — it is the separate *IdeaVim-Which-Key* marketplace plugin, and it is
  not installed, so `set which-key` raised E518 and every label was inert. If it
  gets installed, the labels can come back.
- `vnoremap <leader>p "_dP` — redundant with `ReplaceWithRegister`'s `gr`, which
  is enabled above and does exactly this, and it shadowed `,p`.
- `map <leader>gd <Action>(GotoDeclaration)` — a third spelling of a key that
  already worked (`gd`/`gD` are built into IdeaVim), and it stole `,gd` from the
  git group.
- `,fa` → Search Everywhere is Shift+Shift in every JetBrains keymap and needs
  no mapping. `,wv`/`,ws` → `<C-w>v`/`<C-w>s`, native in both editors.

### Not ported from `_vimrc`

`s:VSetSearch()`'s `escape()`/`substitute()` call, which also handles `/` and
multi-line selections. On the **search** command line IdeaVim's `<C-R>` only
inserts a register — unlike Insert mode, it has no `=` expression-register
branch — so `escape()` cannot be applied there, and its Vimscript has no
`substitute()` at all. A selection containing `/` or a newline therefore still
needs a manual fix-up in the search line. Everything else, which is the
overwhelming majority, is literal and safe.
