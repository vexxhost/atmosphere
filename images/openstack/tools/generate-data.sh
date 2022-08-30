#!/bin/bash -xe

for RELEASE in $(ls -1 releases); do
  BRANCH=$(cat releases/${RELEASE}/branch)

  for PROJECT in $(ls projects); do
    mkdir -p projects/${PROJECT}/${RELEASE}
    curl -s https://opendev.org/api/v1/repos/openstack/${PROJECT}/branches/${BRANCH} | jq -r '.commit.id' > projects/${PROJECT}/${RELEASE}/ref
  done
done
