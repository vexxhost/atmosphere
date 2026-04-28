// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

//go:build linux

package deploy

import (
	"bufio"
	"context"
	"io"
	"os/exec"
	"sync"
	"testing"
	"time"
)

// TestConfigureSubprocess_ReapsGrandchildrenOnCancel verifies that when the
// context is cancelled, descendants of the direct subprocess are killed and
// the parent's pipe-reading goroutines unblock — even if those grandchildren
// inherit stdout/stderr and would otherwise hold the pipes open. This is the
// exact failure mode that caused the molecule-aio-ovn job to hang for over an
// hour after magnum's main role failed mid-deploy.
func TestConfigureSubprocess_ReapsGrandchildrenOnCancel(t *testing.T) {
	if _, err := exec.LookPath("sh"); err != nil {
		t.Skipf("sh not available: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Spawn a shell that detaches a child with `setsid sleep 60` inheriting
	// our stdout. When the parent shell exits, the grandchild stays alive
	// holding the pipe — mirroring how ansible-playbook leaves ssh helpers
	// behind. Without configureSubprocess, scanner.Scan() below would block
	// for the full 60 s.
	cmd := exec.CommandContext(ctx, "sh", "-c", "sleep 60 & wait")
	configureSubprocess(cmd)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		t.Fatalf("stdout pipe: %v", err)
	}

	if err := cmd.Start(); err != nil {
		t.Fatalf("start: %v", err)
	}

	scannerDone := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		scanner := bufio.NewScanner(stdout)
		for scanner.Scan() {
		}
		close(scannerDone)
	}()

	// Give the subprocess a moment to start, then cancel.
	time.Sleep(100 * time.Millisecond)
	cancel()

	waitDone := make(chan error, 1)
	go func() { waitDone <- cmd.Wait() }()

	// configureSubprocess sets WaitDelay = subprocessCancelGracePeriod.
	// Allow a comfortable margin on top of that for goroutine scheduling.
	deadline := subprocessCancelGracePeriod + 5*time.Second

	select {
	case <-waitDone:
	case <-time.After(deadline):
		t.Fatalf("cmd.Wait did not return within %v after ctx cancel", deadline)
	}

	select {
	case <-scannerDone:
	case <-time.After(deadline):
		t.Fatalf("stdout scanner did not unblock within %v after ctx cancel", deadline)
	}

	wg.Wait()
}

// readAllUntilEOF is a tiny helper kept around for clarity in error messages.
var _ = io.Discard
