#!/bin/bash

# SPDX-License-Identifier: Apache-2.0

# Check if the correct number of arguments are provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <issue_number>"
    exit 1
fi

# Variables
REPO="vexxhost/atmosphere"
ISSUE_NUMBER=$1
LOCAL_REPO_PATH=$(mktemp -d -t repo-XXXXXXXXXX)

# Function to clean up the local repository path
cleanup() {
    echo "Cleaning up..."
    rm -rf "$LOCAL_REPO_PATH"
}
trap cleanup EXIT

# Clone the repo into a dynamically generated path
git clone "https://github.com/$REPO.git" "$LOCAL_REPO_PATH"

cd "$LOCAL_REPO_PATH" || exit

# Fetch the latest changes
git fetch origin

# Get the issue details
ISSUE_DETAILS=$(gh issue view $ISSUE_NUMBER --json title,body --jq '{title: .title, body: .body}')
ISSUE_TITLE=$(echo "$ISSUE_DETAILS" | jq -r .title)
ISSUE_BODY=$(echo "$ISSUE_DETAILS" | jq -r .body)

# Extract the target branch from the issue title
TARGET_BRANCH=$(echo "$ISSUE_TITLE" | grep -oP '(?<=\[).+?(?=\])')

if [ -z "$TARGET_BRANCH" ]; then
    echo "Failed to extract the target branch from the issue title."
    exit 1
fi

# Extract the PR number from the issue body
PR_NUMBER=$(echo "$ISSUE_BODY" | grep -oP '(?<=#)\d+')

if [ -z "$PR_NUMBER" ]; then
    echo "Failed to extract the PR number from the issue body."
    exit 1
fi

echo "Extracted PR number: $PR_NUMBER"
echo "Extracted target branch: $TARGET_BRANCH"

# Get the merged commit ID
MERGED_COMMIT_ID=$(gh pr view $PR_NUMBER --json mergeCommit --jq .mergeCommit.oid)

# Check if the commit ID was retrieved
if [ -z "$MERGED_COMMIT_ID" ]; then
    echo "Failed to get the merged commit ID."
    exit 1
fi

# Checkout the target branch
git checkout $TARGET_BRANCH
git pull origin $TARGET_BRANCH

# Cherry-pick the merged commit
if ! git cherry-pick $MERGED_COMMIT_ID; then
    echo "Error during cherry-pick"
    exit 1
fi

# Create a new branch
NEW_BRANCH_NAME="cherry-pick-$MERGED_COMMIT_ID-$TARGET_BRANCH"
git checkout -b $NEW_BRANCH_NAME
git push origin $NEW_BRANCH_NAME

# Get the original PR title and body
PR_TITLE=$(gh pr view $PR_NUMBER --json title --jq .title)
PR_BODY=$(gh pr view $PR_NUMBER --json body --jq .body)

# Create a new PR with the same title, prefixed with the target branch name
NEW_PR_TITLE="[$TARGET_BRANCH] $PR_TITLE"
NEW_PR_BODY="${PR_BODY}\n\nCloses #$ISSUE_NUMBER"
gh pr create --title "$NEW_PR_TITLE" --body "$NEW_PR_BODY" --head "$NEW_BRANCH_NAME" --base "$TARGET_BRANCH"

echo "New pull request created."
