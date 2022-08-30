#!/bin/bash

gh api \
  --header "Accept: application/vnd.github+json" \
  --jq '.actions_caches[].id' \
  --paginate \
  /repos/vexxhost/atmosphere-images/actions/caches |
    xargs -P10 -I {} /bin/bash -xec "gh api --method DELETE /repos/vexxhost/atmosphere-images/actions/caches/{} 2>&1 >/dev/null"
