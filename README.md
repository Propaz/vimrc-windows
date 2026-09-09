# dotfiles — gVim + IdeaVim on Windows

Two editor configs that share one key map, so muscle memory carries from gVim
into the JetBrains IDEs and back.

| File | Editor | Installed as |
|---|---|---|
| [`vim/_vimrc`](vim/_vimrc) | gvim.exe 9.2 x64 (scoop), GUI-first | `%USERPROFILE%\_vimrc` |
| [`.ideavimrc`](.ideavimrc) | IdeaVim 2.46.2 (IntelliJ IDEA, Rider) | `%USERPROFILE%\.ideavimrc` |

Both are installed as **symlinks**, so editing the file in your editor edits
this repo.

- **[docs/RATIONALE.md](docs/RATIONALE.md)** — why every non-obvious value is
  what it is
- **[docs/CONVENTIONS.md](docs/CONVENTIONS.md)** — rules for changing anything
  here, and how to test it
- **[docs/PROMPTS.md](docs/PROMPTS.md)** — reusable prompts for future work

---

## Install

### Windows

`mklink` needs **Administrator rights or Developer Mode**. Both scripts back up
an existing regular file before replacing it.

```bat
git clone git@github.com:Propaz/vimrc-windows.git dotfiles
cd dotfiles
install-vim.bat     :: %USERPROFILE%\_vimrc     -> vim\_vimrc
install.bat         :: %USERPROFILE%\.ideavimrc -> .ideavimrc
```

Then in gVim: `:PlugInstall`. vim-plug itself must be present at
`~/vimfiles/autoload/plug.vim` — without it the config still loads, just with
plugins disabled and a message saying so.

### macOS / Linux

Only `.ideavimrc` is portable (`_vimrc` is Windows-specific):

```sh
./install.sh        # ~/.ideavimrc -> .ideavimrc
```

---

## Requirements

Everything optional is guarded, so a missing binary degrades one feature
instead of breaking startup.

| Tool | Used for | Required |
|---|---|---|
| gVim 9.2 x64, `+directx` | the config's target | yes |
| Consolas | the only font pinned (ships with Windows) | yes |
| [vim-plug](https://github.com/junegunn/vim-plug) | plugins | yes, for plugins |
| `rg` (ripgrep) | `:grep`, `,f`, `,u`, file completion | strongly |
| `fzf.exe` | `,b` `,F` `,l` `,U` and friends | strongly |
| `bat` | fzf preview window | no |
| `jq` | `,=j` / `,=c` | no |
| `ag` | the `:Ag` command | no |
| `ruff`, `mypy` | Python linting and fixing | per project |
| `pylsp` / `jedi-language-server` / `pyright` | Python completion + autoimport | no |
| `uv` | runs Python tools from the locked env | no |
| Go toolchain | `vim-go` (`:GoUpdateBinaries`) | no |

```powershell
scoop install vim ripgrep fzf bat jq
```

Python tooling is resolved **per project**: ALE prefers
`<venv>\Scripts\<tool>.exe` over `%PATH%`, and runs tools as `uv run <tool>`
when a `uv.lock` sits above the buffer. Open a Python file and run
`:PythonToolInfo` to see which venv, LSP and linters that buffer picked. If
something is missing you get one warning per environment, with the `uv add
--dev …` line to fix it.

---

## Key map

Leader is `,`. Groups (`,c*` `,g*` `,t*` `,=*` `,h*` `,v*` and `,r*` in the IDE)
are the only keys allowed a second character — everything else is a single
keystroke after the leader, so nothing waits out `timeoutlen`. See
[the invariant](docs/CONVENTIONS.md#1-never-break-the-leader-prefix-invariant)
before adding a mapping.

### Shared — same meaning in gVim and in the IDE

| Key | Action | gVim | IDE |
|---|---|---|---|
| `,w` | save | `:w` | Save All |
| `,d` | close buffer / editor | `:bp\|bd #` | Close Editor |
| `,n` / `,p` | next / previous | buffer | tab |
| `,b` | switcher | `:Buffers` | Switcher |
| `,e` | project tree | NERDTree | Project tool window |
| `,1`…`,9` | go to tab N | `gt` | `gt` |
| `,rg` | find text in project | `:Rg` | Find in Path |
| `,ff` | find file by name | `:Files` | Go to File |
| `,u` | usages of word under cursor | `:Rg <cword>` | Find Usages |
| `,l` | jump inside current file | `:BLines` | File Structure |
| `,a` | select all | `ggVG` | Select All |
| `,/` | toggle comment (also visual) | commentary | Comment by Line |
| `,o` / `,O` | blank line below / above | | |
| `,<space>` | clear search highlight | | |
| `,j` / `,k` | move line down / up (also `<A-j>`/`<A-k>`, incl. Insert) | | |
| `,T` | terminal | `:terminal` | Terminal window |
| `,hh` | recent files | `:History` | Recent Files |
| `,gl` | file history / log | `:Gclog -10 -- %` | File History |
| `,gb` | blame | `:Git blame` | Annotate |
| `,gd` | diff against repo version | `:Ghdiffsplit` | Compare with Same Version |
| `,gs` | status / local changes | `:Git` | Local Changes |
| `,gp` | pull | `:Git pull` | Git Pull |
| `,cf` | copy file name | | Copy File Name |
| `,cp` | copy full path | | Copy Absolute Path |
| `,=f` | reformat / reindent buffer | `gg=G` | Reformat Code |
| `,=r` | strip stray CR | | |
| `,tr` | toggle relative numbers | | |
| `,th` | toggle search highlight | | |
| `,vm` / `,vs` | edit / reload this config | | |
| `,r` | replace selection in file (Visual) | | |
| `[g` / `]g` | previous / next problem | ALE | Goto Error |
| `<F5>` | history of this file | undotree | Local History |
| `gd` | go to declaration | Vim built-in | IdeaVim built-in |
| `<C-w>v` / `<C-w>s` | split vertically / horizontally | | |
| `*` / `#` | search the selection, literally (Visual) | | |

### gVim only

| Key | Action |
|---|---|
| `,U` | open the file *named* after the word under the cursor (`:FZF -q <cword>`) |
| `,cd` | `lcd` to the current file's directory |
| `,cm` | copy `:messages` to the clipboard |
| `,=j` / `,=c` | jq pretty-print / compact (buffer or selection) |
| `,tp` / `<F2>` | toggle `paste` |
| `,<CR>` | blank line below (alias of `,o`) |
| `<C-f>` | `:Files` (alias of `,F`) |
| `<C-t>` | new tab (also in Insert mode) |
| `<C-q>` | close window |
| `<F9>` / `<F10>` | rebuild render target / cycle renmode — see below |
| `<PageUp>` / `<PageDown>` | half-page scroll, re-centred |
| `<A-v>` | paste the clipboard into a terminal buffer |
| `<C-x><C-f>` / `<C-x><C-l>` | fzf-complete a path from the project root / a line |

`,U` has no IDE twin on purpose: there that job is `gd`, which is exact rather
than fuzzy and is bound on both sides.

### IDE only

| Key | Action |
|---|---|
| `,rr` / `,rd` / `,rs` | Run / Debug / Stop |
| `,rn` / `,rf` | Rename element / Refactor this |
| `,hc` | Recent Changes |
| `<C-S-c>` / `<C-S-v>` | copy / paste via the system clipboard, explicitly |

### Commands

| Command | Effect |
|---|---|
| `:PythonToolInfo` | which venv, LSP and linters the current buffer picked |
| `:RenderCycle` (`<F10>`) | cycle DirectWrite renmode |
| `:RenderReset` (`<F9>`) | rebuild the DirectWrite render target |
| `:RenderGDI` | drop to plain GDI rendering |
| `:RenderDX` | re-apply the pinned DirectWrite settings |
| `:Ag` | fzf + the silver searcher, with preview |

If text ever starts to **drift or staircase across the line**, that is the
DirectWrite glyph-advance bug: press `<F9>`, and if it persists `<F10>` to
cycle modes or `:RenderGDI` to opt out of DirectWrite entirely. Full
explanation: [RATIONALE](docs/RATIONALE.md#directwrite-glyph-drift).

---

## Plugins

lightline · gruvbox · VimCompletesMe · vim-cursorword · fzf + fzf.vim ·
undotree · vim-fugitive · vim-commentary · vim-surround · NERDTree · ALE ·
[karate-linter](https://github.com/Propaz/karate-linter) · vim-go

Loading is eager or lazy per plugin for concrete reasons — fugitive's `:Gclog`
and NERDTree's netrw hijacking both break when deferred. See
[RATIONALE](docs/RATIONALE.md#plugin-loading).

---

## Maintenance

Vim never prunes its undo, backup and swap directories, so they grow for years
(this repo's own had reached 39 MB / 317 files). That is housekeeping, not an
editor feature, so it lives outside the config:

```bat
vim-state-clean.bat                 :: report only
vim-state-clean.bat --apply         :: prune the safe categories
vim-state-clean.bat --recover-cmds  :: print `vim -r` commands for risky swaps
```

Editor state lives in `~/.vim/.undo`, `~/.vim/.backup`, `~/.vim/.swp`; plugins
live in `~/vimfiles/plugged`. Neither is part of this repo. Backups use
`writebackup` only — a crash-safety window during the write, not permanent
history, which git and `undofile` already provide.

---

## Known limitations

- **Console gVim fallback.** The config is GUI-first. In a console without the
  `+vtp` feature, lightline raises `E254: Invalid color name guibg=` because
  its gruvbox colorscheme is defined in gui colours only. Harmless for the
  target; the one-line fix is
  [in the rationale](docs/RATIONALE.md#termguicolors-and-the-console-fallback).
- **IdeaVim `*` / `#` / `,r`** do not escape `/` or newlines in the selection —
  IdeaVim has no expression register on the search line and no `substitute()`.
  Everything else is literal and safe.
- **`.ideavimrc` has no offline test.** Reload with `,vs` in the IDE and watch
  the notification for `E518`.
