#!/bin/bash -xe

VERSION=$1
LATEST_VERSION=$2

if [ -z "$VERSION" ] || [ -z "$LATEST_VERSION" ]; then
  echo "Usage: $0 <version> <latest_version>"
  exit 1
fi

# Update the version
sed -i s/^version:.*/version:\ $VERSION/ galaxy.yml
sed -i s/^atmosphere_version:.*/atmosphere_version:\ $VERSION/ roles/defaults/defaults/main.yml

# Create release commit
git add galaxy.yml roles/defaults/defaults/main.yml
git commit -m "Release $VERSION"

# Push the release commit
git push

# Create GitHub release with gh CLI
gh release create v$VERSION --target $(git rev-parse HEAD) --generate-notes --latest=$LATEST_VERSION
