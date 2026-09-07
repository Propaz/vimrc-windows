#!/usr/bin/env python3
"""Report on, and optionally prune, Vim's undo / backup / swap directories.

Vim never cleans these up itself, so they grow for years. This is a
maintenance chore, not an editor feature, which is why it lives here and not
in _vimrc.

Nothing is deleted without --apply. Swap files that may still hold unsaved
work are never deleted unless you also pass --include-risky.

Usage:
    python vim-state-clean.py                  # report only
    python vim-state-clean.py --apply          # prune the safe categories
    python vim-state-clean.py --keep-days 180  # tighten the age cutoff
    python vim-state-clean.py --recover-cmds   # print `vim -r` for risky swaps
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass, field

# Vim replaces every path separator with '%' when it encodes a file's full
# path into a state-file name. On Windows both ':' and '\' are replaced, so
# "E:\Projects\x" becomes "E%%Projects%x".
WINDOWS = os.name == "nt"

# An orphaned file must also be this old before we trust the decode enough to
# delete it. Guards against a mis-decoded name for a file that still exists.
ORPHAN_GRACE_DAYS = 7


def decode_source_path(name: str) -> str:
    """Turn a Vim state-file name back into the path it was made from."""
    if WINDOWS:
        # First '%%' is the drive colon plus separator, the rest are separators.
        return name.replace("%%", ":" + os.sep, 1).replace("%", os.sep)
    return name.replace("%", "/")


@dataclass
class Entry:
    path: str
    source: str
    size: int
    mtime: float
    reason: str


@dataclass
class Bucket:
    title: str
    note: str
    safe: bool
    entries: list[Entry] = field(default_factory=list)

    @property
    def size(self) -> int:
        return sum(e.size for e in self.entries)


def scan_dir(directory: str, suffix: str) -> list[tuple[str, str, os.stat_result]]:
    """Yield (path, decoded source path, stat) for each file in *directory*."""
    out = []
    if not os.path.isdir(directory):
        return out
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        try:
            st = os.stat(path)
        except OSError:
            continue
        if not os.path.isfile(path):
            continue
        stem = name[: -len(suffix)] if suffix and name.endswith(suffix) else name
        out.append((path, decode_source_path(stem), st))
    return out


def classify(vim_dir: str, keep_days: int) -> dict[str, Bucket]:
    now = time.time()
    age_cutoff = now - keep_days * 86400
    orphan_cutoff = now - ORPHAN_GRACE_DAYS * 86400

    buckets = {
        "orphaned": Bucket(
            "ORPHANED   undo/backup whose source file is gone",
            "safe to delete",
            safe=True,
        ),
        "aged": Bucket(
            f"AGED       undo/backup untouched for over {keep_days} days",
            "safe to delete",
            safe=True,
        ),
        "swap_dead": Bucket(
            "SWAP dead  source gone, or file saved after the swap",
            "safe to delete",
            safe=True,
        ),
        "swap_risky": Bucket(
            "SWAP RISKY swap is NEWER than the file on disk",
            "may hold unsaved changes -- inspect with `vim -r`, do not bulk-delete",
            safe=False,
        ),
    }

    for sub, suffix in ((".undo", ""), (".backup", "~")):
        for path, source, st in scan_dir(os.path.join(vim_dir, sub), suffix):
            exists = os.path.exists(source)
            if not exists and st.st_mtime < orphan_cutoff:
                buckets["orphaned"].entries.append(
                    Entry(path, source, st.st_size, st.st_mtime, "source missing")
                )
            elif st.st_mtime < age_cutoff:
                buckets["aged"].entries.append(
                    Entry(path, source, st.st_size, st.st_mtime, "stale")
                )

    for path, source, st in scan_dir(os.path.join(vim_dir, ".swp"), ".swp"):
        if not os.path.exists(source):
            buckets["swap_dead"].entries.append(
                Entry(path, source, st.st_size, st.st_mtime, "source missing")
            )
            continue
        try:
            src_mtime = os.path.getmtime(source)
        except OSError:
            continue
        if st.st_mtime <= src_mtime:
            buckets["swap_dead"].entries.append(
                Entry(path, source, st.st_size, st.st_mtime, "file saved after swap")
            )
        else:
            buckets["swap_risky"].entries.append(
                Entry(path, source, st.st_size, st.st_mtime, "swap newer than file")
            )

    return buckets


def mb(n: int) -> str:
    return f"{n / 1048576:.1f} MB"


def report(buckets: dict[str, Bucket], show_all: bool) -> None:
    limit = None if show_all else 8
    for bucket in buckets.values():
        print(f"{bucket.title}")
        print(f"    {len(bucket.entries)} files, {mb(bucket.size)} -- {bucket.note}")
        shown = bucket.entries if limit is None else bucket.entries[:limit]
        for e in shown:
            age = (time.time() - e.mtime) / 86400
            print(f"      {age:5.0f}d  {e.source}")
        if limit is not None and len(bucket.entries) > limit:
            print(f"      ... and {len(bucket.entries) - limit} more (--all to list)")
        print()


def prune(buckets: dict[str, Bucket], include_risky: bool) -> tuple[int, int]:
    removed = freed = 0
    for key, bucket in buckets.items():
        if not bucket.safe and not (include_risky and key == "swap_risky"):
            continue
        for e in bucket.entries:
            try:
                os.remove(e.path)
            except OSError as exc:
                print(f"  could not remove {e.path}: {exc}", file=sys.stderr)
                continue
            removed += 1
            freed += e.size
    return removed, freed


def main() -> int:
    default_vim_dir = os.path.join(os.path.expanduser("~"), ".vim")

    p = argparse.ArgumentParser(
        description="Report on and prune Vim's undo/backup/swap directories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--vim-dir", default=default_vim_dir,
                   help=f"directory holding .undo/.backup/.swp (default: {default_vim_dir})")
    p.add_argument("--keep-days", type=int, default=365,
                   help="delete undo/backup files untouched for longer than this (default: 365)")
    p.add_argument("--apply", action="store_true",
                   help="actually delete; without it the script only reports")
    p.add_argument("--include-risky", action="store_true",
                   help="also delete swap files that may hold unsaved changes")
    p.add_argument("--all", action="store_true", help="list every file, not just the first few")
    p.add_argument("--recover-cmds", action="store_true",
                   help="print a `vim -r` command for each risky swap file and exit")
    args = p.parse_args()

    if not os.path.isdir(args.vim_dir):
        print(f"No such directory: {args.vim_dir}", file=sys.stderr)
        return 1

    buckets = classify(args.vim_dir, args.keep_days)

    if args.recover_cmds:
        risky = buckets["swap_risky"].entries
        if not risky:
            print("No risky swap files.")
            return 0
        print(f"# {len(risky)} swap files are newer than their file on disk.")
        print("# Inspect each, then :w if the recovered text is better, or :q! to discard.")
        for e in risky:
            print(f'vim -r "{e.source}"')
        return 0

    print(f"Vim state directory: {args.vim_dir}")
    print(f"Age cutoff: {args.keep_days} days\n")
    report(buckets, args.all)

    safe_total = sum(b.size for b in buckets.values() if b.safe)
    safe_count = sum(len(b.entries) for b in buckets.values() if b.safe)

    if not args.apply:
        print(f"Would remove {safe_count} files, freeing {mb(safe_total)}.")
        print("Nothing was deleted. Re-run with --apply to do it.")
        if buckets["swap_risky"].entries:
            print("Risky swap files are excluded; see --recover-cmds.")
        return 0

    removed, freed = prune(buckets, args.include_risky)
    print(f"Removed {removed} files, freed {mb(freed)}.")
    if buckets["swap_risky"].entries and not args.include_risky:
        print(f"Left {len(buckets['swap_risky'].entries)} risky swap files untouched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
