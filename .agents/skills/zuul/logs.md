# Zuul log retrieval and artifact navigation

## Reading job logs

Each build in the buildset response has a `log_url` pointing to a
directory listing of log artifacts. The main log file is `job-output.txt`
at that URL.

The log file can be very large (multiple MB). To find the failure
efficiently, use HTTP range requests or stream the file and grep for
key patterns like `fatal`, `FAILED` (excluding `RETRYING` lines),
`PLAY RECAP`, and `failed=`. Look for the PLAY RECAP with `failed=`
greater than zero, then work backward from there to find the root cause.

## Discovering available log artifacts

Each build has a `zuul-manifest.json` at its `log_url` root. The
manifest is a recursive JSON tree of all artifacts with file sizes —
it can be hundreds of KB so never dump it into context raw.

Use the helper script to scan it efficiently:

    python3 .github/skills/zuul/scan-manifest.py <log_url>
    python3 .github/skills/zuul/scan-manifest.py <log_url> neutron

The first form shows system diagnostics, top pod logs by size, and
failed pods. The second form searches for files matching a keyword.
Use the output to decide which specific files to fetch.

Use the scan-manifest output to discover what artifacts are available
for each build rather than assuming a fixed directory layout.
