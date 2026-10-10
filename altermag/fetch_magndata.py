#!/usr/bin/env python3
"""
Download commensurate MAGNDATA magnetic structures (.mcif) for a trusted
altermagnet validation set.

MAGNDATA (Bilbao Crystallographic Server) serves each entry's magnetic CIF at
    https://cryst.ehu.es/magndata/tmp/<index>_<compound>.mcif
where the tmp file is generated when the entry page index.php?index=<index> is
visited. So per entry we GET the page, scrape the exact mcif href, then fetch
the file. Only commensurate entries (index 0.N) are pulled -- amcheck needs a
commensurate magnetic cell.

Be polite: this hits an academic server. Default delay is 0.7 s between entries.

Usage:
    python fetch_magndata.py --start 1 --end 150 --outdir mcif
"""

import argparse
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://cryst.ehu.es/magndata"
_HREF = re.compile(r'tmp/([0-9.]+_[A-Za-z0-9]+\.mcif)', re.I)


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "altermag-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_entry(index, outdir):
    """Return saved Path for entry 0.<index>, or None if no commensurate mcif."""
    page = _get(f"{BASE}/index.php?index=0.{index}").decode("utf-8", "replace")
    m = _HREF.search(page)
    if not m:
        return None
    relname = m.group(1)                     # e.g. 0.110_Cr2O3.mcif
    data = _get(f"{BASE}/tmp/{relname}")
    if not data.lstrip().startswith(b"#\\#CIF"):
        return None
    path = outdir / relname
    path.write_bytes(data)
    return path


def main():
    ap = argparse.ArgumentParser(description="Download MAGNDATA mcif entries")
    ap.add_argument("--start", type=int, default=1, help="first entry number")
    ap.add_argument("--end", type=int, default=150, help="last entry number (incl)")
    ap.add_argument("--outdir", default="mcif")
    ap.add_argument("--delay", type=float, default=0.7,
                    help="seconds between entries (be polite)")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    got = miss = err = 0
    for i in range(args.start, args.end + 1):
        try:
            path = fetch_entry(i, outdir)
            if path is None:
                miss += 1
            else:
                got += 1
                print(f"  [0.{i}] {path.name}")
        except Exception as e:  # noqa: BLE001
            err += 1
            sys.stderr.write(f"[err] 0.{i}: {e}\n")
        time.sleep(args.delay)

    print(f"\nDownloaded {got} mcif files "
          f"({miss} no-commensurate-mcif, {err} errors) into {outdir}")


if __name__ == "__main__":
    main()
