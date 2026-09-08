# Reusable prompts

Prompts that produced good results on this repo, kept so the next session does
not have to rediscover the framing. Substitute the bracketed parts.

They all lean on the same two ideas: **verify against what is installed, not
from memory**, and **state the invariant the change must not break**. Read
`docs/CONVENTIONS.md` before using any of them.

---

## Audit a config

> Audit `[vim/_vimrc]` for dead and redundant configuration. For every option,
> plugin variable and mapping, check it against what is actually installed
> (`~/vimfiles/plugged` for Vim plugins, IdeaVim 2.46.2's `Options.kt` /
> extension registry / action ids for `.ideavimrc`) — not from memory. Report:
>
> 1. variables no plugin reads,
> 2. options that are no-ops in this context (GUI vs terminal, or overridden
>    later),
> 3. values that are silently wrong (Vim-regex vs glob, `:set` parsing, doubled
>    Visual ranges),
> 4. leader mappings that are a prefix of another mapping,
> 5. anything that can abort the file on a machine where a dependency is
>    missing.
>
> For each finding give the concrete failure — what breaks, when — not a style
> opinion. Do not change anything yet.

## Add a mapping

> Add `[description]` on `[key]` in both `vim/_vimrc` and `.ideavimrc`.
>
> Constraints: the leader-prefix invariant in
> `docs/CONVENTIONS.md#1-never-break-the-leader-prefix-invariant` must hold —
> check `:map ,` first and tell me if the key is already a prefix or a leaf.
> If the two editors cannot express the same behaviour, say so and propose the
> closest IDE `<Action>` instead of forcing it. Update the key-map table in
> `README.md` in the same change.

## Add a plugin

> Add `[plugin]` to `vim/_vimrc`.
>
> Decide eager vs lazy explicitly and justify it: if it registers commands,
> hijacks an event at startup, or is needed before the first keypress, it
> cannot be lazy. Check the plugin's own docs for the option names you set and
> confirm each one is actually read in `~/vimfiles/plugged/[plugin]`. Guard
> anything that needs an external binary with `executable()`. Note the reason
> in `docs/RATIONALE.md#plugin-loading`.

## Verify one suspicious option

> Is `[g:some_option]` actually read by `[plugin]`? Grep the installed source
> in `~/vimfiles/plugged/`, quote the line that reads it, and if nothing reads
> it, tell me what the real option is and where the plugin defines it.

## Check startup cost

> Profile gVim startup and per-keystroke cost for this config:
>
> ```
> gvim.exe --startuptime startup.log -f -u <repo>\vim\_vimrc -c 'qa!'
> ```
>
> Report the slowest entries, then check whether anything runs on
> `TextChanged`, `CursorHold`, `InsertCharPre` or a linter's default timing.
> Measure the tools themselves (`ruff`, `mypy`) on a small file, warm and cold,
> before recommending a timing change.

## Slim the comments

> Reduce the comments in `[file]` to: section headers, short "do not change
> this / this is deliberate" notes, and lookup tables needed at the keyboard.
> Move every root-cause explanation, measurement and account of what an earlier
> version got wrong into `docs/RATIONALE.md` under a linkable heading, and
> reference it by anchor from the config.
>
> Change no functional line. Prove it: compare code-only lines before and after
> as a set (`grep -v '^\s*"' | grep -v '^\s*$' | sort`, then `diff`) and account
> for every difference.

## Load-test before committing

> Load-test `vim/_vimrc` in both branches and report any `E...` line that comes
> from the config itself — the console/fallback branch with `vim.exe -es`, and
> the GUI branch with `gvim.exe -f`, since `has('gui_running')` skips the GUI
> block in the first. Use `-S probe.vim` rather than many `-c` flags (Vim
> allows at most 10). Then dump the resulting values of the options the change
> touched and confirm each one landed.

## Cut a release

> Cut `[v0.2.0]`. Summarise what changed since `[v0.1.0]` from the actual diff,
> not the commit subjects. Call out separately: fixes a user will feel, keys
> whose meaning changed, and anything requiring manual action after upgrading
> (re-run an installer, `:PlugInstall`, install a new binary). Then tag, push
> and create the GitHub release with `gh`.
