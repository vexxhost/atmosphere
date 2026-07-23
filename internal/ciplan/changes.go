// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package ciplan

import (
	"bufio"
	"bytes"
	"context"
	"fmt"
	"io"
	"os/exec"
	"strings"
)

// ParseChanges accepts either one path per line or git diff --name-status
// output. Rename and copy records preserve both the old and new paths.
func ParseChanges(reader io.Reader) ([]Change, error) {
	var changes []Change
	scanner := bufio.NewScanner(reader)
	lineNumber := 0
	for scanner.Scan() {
		lineNumber++
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		fields := strings.Split(line, "\t")
		switch len(fields) {
		case 1:
			changes = append(changes, Change{Status: "M", Path: fields[0]})
		case 2:
			if fields[0] == "" || fields[1] == "" {
				return nil, fmt.Errorf("invalid changed-file record on line %d", lineNumber)
			}
			changes = append(changes, Change{Status: fields[0], Path: fields[1]})
		case 3:
			if !strings.HasPrefix(fields[0], "R") && !strings.HasPrefix(fields[0], "C") {
				return nil, fmt.Errorf(
					"three-column changed-file record on line %d must be a rename or copy",
					lineNumber,
				)
			}
			changes = append(changes, Change{
				Status:       fields[0],
				PreviousPath: fields[1],
				Path:         fields[2],
			})
		default:
			return nil, fmt.Errorf("invalid changed-file record on line %d", lineNumber)
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("reading changed files: %w", err)
	}
	return changes, nil
}

// GitChanges obtains name-status records for a three-dot Git diff.
func GitChanges(ctx context.Context, base, head string) ([]Change, error) {
	if strings.TrimSpace(base) == "" || strings.TrimSpace(head) == "" {
		return nil, fmt.Errorf("both base and head revisions are required")
	}

	command := exec.CommandContext(
		ctx,
		"git",
		"diff",
		"--name-status",
		"--find-renames",
		base+"..."+head,
	)
	output, err := command.Output()
	if err != nil {
		return nil, fmt.Errorf("collecting changed files from Git: %w", err)
	}
	return ParseChanges(bytes.NewReader(output))
}
