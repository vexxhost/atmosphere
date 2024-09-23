# SPDX-License-Identifier: Apache-2.0

import argparse
import pathlib
import re
from datetime import datetime

import requests

OPENDEV_GIT_PATTERN = re.compile(
    r"ADD (?:--keep-git-dir=true )?https://opendev.org/(?P<namespace>[^/]+)/(?P<repo>[^/]+)\.git#\$\{(?P<ref>[^}]+)\} /src/(?P<dir>[^ ]+)?"  # noqa
)


def update_rebuild_time(dockerfile, timestamp):
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


def bump_image(dockerfile, branch) -> bool:
    content = dockerfile.read_text()

    opendev_match = OPENDEV_GIT_PATTERN.search(content)
    if opendev_match:
        namespace = opendev_match.group("namespace")
        repo = opendev_match.group("repo")
        ref = opendev_match.group("ref")
        print(f"Bumping {repo} ({ref}) in {dockerfile}")

        url = f"https://opendev.org/api/v1/repos/{namespace}/{repo}/branches/{branch}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Update the Dockerfile with the latest commit
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith(f"ARG {ref}="):
                new_lines.append(f"ARG {ref}={data['commit']['id']}")
            else:
                new_lines.append(line)

        dockerfile.write_text("\n".join(new_lines) + "\n")
        return True

    # TODO: add support for other types of images

    print(f"Skipping {dockerfile}: No way to bump image")
    return False


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    force_rebuild_parser = subparsers.add_parser("force-rebuild")
    force_rebuild_parser.add_argument(
        "dockerfiles", type=pathlib.Path, nargs="+", help="List of Dockerfiles"
    )

    bump_parser = subparsers.add_parser("bump")
    bump_parser.add_argument(
        "--branch",
        help="Branch to bump the image to",
    )
    bump_parser.add_argument(
        "dockerfiles", type=pathlib.Path, nargs="+", help="List of Dockerfiles"
    )

    args = parser.parse_args()
    now_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    for dockerfile in args.dockerfiles:
        if args.command == "bump":
            if bump_image(dockerfile, args.branch):
                update_rebuild_time(dockerfile, now_utc)
        elif args.command == "force-rebuild":
            update_rebuild_time(dockerfile, now_utc)


if __name__ == "__main__":
    main()
