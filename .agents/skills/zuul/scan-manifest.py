#!/usr/bin/env python3
"""Scan a Zuul build's zuul-manifest.json and print useful summaries.

Usage:
    python3 scan-manifest.py <log_url> [keyword]

Examples:
    python3 scan-manifest.py https://logs.oss.vexxhost.dev/abc/oss/def/
    python3 scan-manifest.py https://logs.oss.vexxhost.dev/abc/oss/def/ neutron
"""

import json
import subprocess
import sys


def flatten(nodes, prefix=""):
    for n in nodes:
        path = prefix + "/" + n["name"]
        if "children" in n:
            yield from flatten(n["children"], path)
        else:
            yield (path, n.get("size", 0))


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    log_url = sys.argv[1].rstrip("/")
    keyword = sys.argv[2].lower() if len(sys.argv) > 2 else None

    manifest = json.loads(
        subprocess.check_output(
            ["curl", "-s", log_url + "/zuul-manifest.json"],
            timeout=30,
        )
    )
    files = list(flatten(manifest["tree"]))
    print(f"Total files: {len(files)}")

    if keyword:
        matches = [(p, s) for p, s in files if keyword in p.lower()]
        print(f'\nFiles matching "{keyword}": {len(matches)}')
        for p, s in matches:
            print(f"  {s:>10}  {p}")
        return

    # Default: show system diagnostics + top pod logs + failed pods
    print("\n=== System diagnostics ===")
    for p, s in files:
        if "/system/" in p:
            print(f"  {s:>10}  {p}")

    print("\n=== Pod logs (top 20 by size) ===")
    pod_logs = [(p, s) for p, s in files if "/pod-logs/" in p]
    for p, s in sorted(pod_logs, key=lambda x: -x[1])[:20]:
        print(f"  {s:>10}  {p}")

    failed = [(p, s) for p, s in files if "/failed-pods/" in p and s > 0]
    if failed:
        print("\n=== Failed pod logs (non-empty) ===")
        for p, s in failed:
            print(f"  {s:>10}  {p}")


if __name__ == "__main__":
    main()
