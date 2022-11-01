# Testing

## GitHub Actions

### Integration tests

#### Troubleshooting

If you're seeing problems with integration tests, you can add the following step
before the Molecule step in order to be able to troubleshoot:

```yaml
- uses: mxschmitt/action-tmate@v3
  with:
    limit-access-to-actor: true
```

Once you push the job, it will stop at the `tmate` action and you will need to
run the following command to continue:

```bash
sudo touch /continue
```

Once that's done, the job will continue to run and you'll be able to watch the
system output and potentially use `molecule` to SSH to any of the target boxes.
