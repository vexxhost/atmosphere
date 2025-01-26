#!/bin/bash -xe

VERSION=$1

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version> <latest_version>"
  exit 1
fi

# Update the version
sed -i s/^version:.*/version:\ $VERSION/ galaxy.yml
sed -i s/^atmosphere_version:.*/atmosphere_version:\ $VERSION/ roles/defaults/defaults/main.yml

# Create release commit
git add galaxy.yml roles/defaults/defaults/main.yml
git commit -m "Release $VERSION"

# Create a local tag
git tag v$VERSION

# Push the release commit
git push gerrit refs/heads/$(git rev-parse --abbrev-ref HEAD)
git push --tags gerrit refs/heads/$(git rev-parse --abbrev-ref HEAD)
