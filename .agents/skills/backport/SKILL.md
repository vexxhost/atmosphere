---
name: backport
description: >
  Backport a merged PR to one or more stable branches. Handles cherry-pick
  conflict resolution and creates individual PRs per branch. Can be invoked
  with a PR number and optional list of target branches, or will auto-detect
  target branches from the PR's backport labels. Use when asked to backport
  a PR, fix a failed automated backport, or manually port changes to stable
  branches.
---

# Backport Skill

## Invocation

This skill can be triggered in two ways:

- **From a PR with backport labels**: provide a PR number and the skill will
  read the `backport stable/<X>` labels to determine target branches.
- **Explicitly**: provide a PR number and a specific list of target branches
  (e.g. "backport #3697 to stable/2024.1 and stable/2023.2").

## Workflow

### 1. Understand the change

Fetch the full diff of the original PR. Read and understand what the change
does — which files are modified, what is being added or removed, and what
component behaviour it affects. This understanding is essential for making
good judgements during conflict resolution and compatibility checks later.

### 2. Determine target branches

If target branches are not explicitly provided, read the PR's
`backport stable/<X>` labels. Then check comments from `vexxhost-bot` to
identify which branches already have an open or merged backport PR — skip
those. Sort the remaining branches **newest first** (e.g. `stable/2025.1`
before `stable/2024.2` before `stable/zed`).

### 3. Process branches one by one (cascade strategy)

Use a **cascade strategy**: cherry-pick onto the newest branch first, fix any
conflicts there, then use that fixed commit as the source for the next-older
branch. This means conflicts only need to be resolved once and the fix
propagates naturally through older branches.

For the **first branch**, cherry-pick the original merged commit from `main`:

```bash
git fetch origin <branch>
git worktree add -d .worktree/backport-<PR>-to-<slug> origin/<branch>
cd .worktree/backport-<PR>-to-<slug>
git switch --create backport-<PR>-to-<branch>
git cherry-pick -x <original-sha>
```

For each **subsequent branch**, cherry-pick from the previous branch's commit:

```bash
PREV=$(git -C .worktree/backport-<PR>-to-<prev-slug> rev-parse HEAD)
git cherry-pick -x $PREV
```

**Branch slug convention**: replace `/` with `.` in worktree directory names
(e.g. `stable/2025.1` → `.worktree/backport-<PR>-to-stable-2025.1`) but keep
`/` in the git branch name itself.

### 4. Assess compatibility before applying

Before applying (or after a conflict surfaces), compare the diff being applied
against the state of the target branch. Ask: does this change make sense for
this branch as-is? Consider things like:

- Does the branch have the required dependency or component version for this
  change to function?
- Are the files being patched present and structurally similar enough?

If the change cannot work on the target branch without a prerequisite that is
absent, **skip the branch** and clearly note why (so the user can act on it
later).

### 5. Resolve conflicts

If `git cherry-pick` fails, inspect the conflicts. Use the understanding of
the change (from step 1) and the state of the target branch to resolve them
thoughtfully. The goal is to produce a result that correctly applies the
intent of the original change to the target branch — not to mechanically
accept one side or the other.

After resolving all conflicts:

```bash
git add <resolved-files>
git cherry-pick --continue --no-edit
```

### 6. Validate

After each successful cherry-pick, run pre-commit across the range of the
cherry-picked commit:

```bash
pre-commit run --from-ref HEAD~1 --to-ref HEAD
```

Any hook failures that are unrelated to the files touched by the backport
should be ignored. Investigate and fix any failures that are caused by the
backported changes before pushing.

### 7. Push and open a PR

```bash
git push origin backport-<PR>-to-<branch>

gh pr create \
  --repo vexxhost/atmosphere \
  --base <branch> \
  --head backport-<PR>-to-<branch> \
  --title "[Backport <branch>] <original PR title>" \
  --body "# Description\nBackport of #<PR> to \`<branch>\`."
```

### 8. Clean up

After all PRs are created, remove all worktrees:

```bash
git worktree remove --force .worktree/backport-<PR>-to-<slug>
```

## Reporting

Finish with a summary table covering every branch that was labeled, including
skipped ones:

| Branch | PR | Notes |
|---|---|---|
| `stable/2025.1` | #NNNN | ✅ Created |
| `stable/2024.2` | #NNNN | ✅ Clean apply |
| `stable/zed` | — | ⏭️ Skipped — requires prerequisite #NNNN first |
