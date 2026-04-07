# SPDX-License-Identifier: Apache-2.0

import argparse
import pathlib
from datetime import datetime


def update_dockerfile(dockerfile, timestamp):
    rebuild_line = f"# Atmosphere-Rebuild-Time: {timestamp}"

    lines = dockerfile.read_text().splitlines()
    new_lines = []
    rebuild_line_found = False

    for line in lines:
        if line.startswith("# Atmosphere-Rebuild-Time: "):
            new_lines.append(rebuild_line)
            rebuild_line_found = True
        else:
            new_lines.append(line)

    if not rebuild_line_found:
        new_lines.insert(1, rebuild_line)  # Insert after SPDX line

    dockerfile.write_text("\n".join(new_lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument(
        "dockerfiles", type=pathlib.Path, nargs="+", help="List of Dockerfiles"
    )
    args = parser.parse_args()

    if args.rebuild:
        now_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        for dockerfile in args.dockerfiles:
            update_dockerfile(dockerfile, now_utc)


if __name__ == "__main__":
    main()
