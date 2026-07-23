// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/vexxhost/atmosphere/internal/ciplan"
)

func newCICmd() *cobra.Command {
	command := &cobra.Command{
		Use:   "ci",
		Short: "Plan selective CI deployments and verification",
	}
	command.AddCommand(newCIPlanCmd())
	command.AddCommand(newCIValidateCmd())
	return command
}

func newCIValidateCmd() *cobra.Command {
	var configPath string
	command := &cobra.Command{
		Use:   "validate",
		Short: "Validate the selective CI policy and dependency graph",
		RunE: func(command *cobra.Command, args []string) error {
			config, err := ciplan.LoadConfig(configPath)
			if err != nil {
				return err
			}
			if _, err := ciplan.New(config); err != nil {
				return err
			}
			_, err = fmt.Fprintf(command.OutOrStdout(), "CI plan policy %s is valid\n", configPath)
			return err
		},
	}
	command.Flags().StringVar(
		&configPath,
		"config",
		"ci/molecule-plan.yaml",
		"Path to the CI planning policy",
	)
	return command
}

func newCIPlanCmd() *cobra.Command {
	var (
		configPath   string
		changedFiles []string
		filesFrom    string
		base         string
		head         string
		format       string
		outputPath   string
	)

	command := &cobra.Command{
		Use:   "plan",
		Short: "Map changed files to Molecule deployment variants",
		RunE: func(command *cobra.Command, args []string) error {
			changes, err := collectChanges(
				command,
				changedFiles,
				filesFrom,
				base,
				head,
			)
			if err != nil {
				return err
			}

			config, err := ciplan.LoadConfig(configPath)
			if err != nil {
				return err
			}
			planner, err := ciplan.New(config)
			if err != nil {
				return err
			}
			plan, err := planner.Plan(changes)
			if err != nil {
				return err
			}

			output, closeOutput, err := planOutput(command.OutOrStdout(), outputPath)
			if err != nil {
				return err
			}
			defer closeOutput()

			switch format {
			case "json":
				encoder := json.NewEncoder(output)
				encoder.SetIndent("", "  ")
				return encoder.Encode(plan)
			case "text":
				return ciplan.WriteText(output, plan)
			default:
				return fmt.Errorf("unsupported output format %q", format)
			}
		},
	}

	command.Flags().StringVar(
		&configPath,
		"config",
		"ci/molecule-plan.yaml",
		"Path to the CI planning policy",
	)
	command.Flags().StringSliceVar(
		&changedFiles,
		"changed-file",
		nil,
		"Changed repository path; may be provided more than once",
	)
	command.Flags().StringVar(
		&filesFrom,
		"files-from",
		"",
		"Read paths or git name-status records from a file, or - for stdin",
	)
	command.Flags().StringVar(&base, "base", "", "Base Git revision for a three-dot diff")
	command.Flags().StringVar(&head, "head", "", "Head Git revision for a three-dot diff")
	command.Flags().StringVar(&format, "format", "text", "Output format: text or json")
	command.Flags().StringVar(&outputPath, "output", "-", "Write the plan to this file, or - for stdout")
	return command
}

func collectChanges(
	command *cobra.Command,
	changedFiles []string,
	filesFrom string,
	base string,
	head string,
) ([]ciplan.Change, error) {
	usingChangedFiles := len(changedFiles) > 0
	usingFilesFrom := strings.TrimSpace(filesFrom) != ""
	usingGit := strings.TrimSpace(base) != "" || strings.TrimSpace(head) != ""

	sources := 0
	for _, used := range []bool{usingChangedFiles, usingFilesFrom, usingGit} {
		if used {
			sources++
		}
	}
	if sources != 1 {
		return nil, fmt.Errorf(
			"provide exactly one change source: --changed-file, --files-from, or --base with --head",
		)
	}

	if usingChangedFiles {
		changes := make([]ciplan.Change, 0, len(changedFiles))
		for _, changedFile := range changedFiles {
			changes = append(changes, ciplan.Change{Status: "M", Path: changedFile})
		}
		return changes, nil
	}

	if usingFilesFrom {
		var (
			reader io.Reader
			file   *os.File
			err    error
		)
		if filesFrom == "-" {
			reader = command.InOrStdin()
		} else {
			file, err = os.Open(filesFrom)
			if err != nil {
				return nil, fmt.Errorf("opening changed-file input: %w", err)
			}
			defer file.Close()
			reader = file
		}
		return ciplan.ParseChanges(reader)
	}

	if strings.TrimSpace(base) == "" || strings.TrimSpace(head) == "" {
		return nil, fmt.Errorf("--base and --head must be provided together")
	}
	return ciplan.GitChanges(command.Context(), base, head)
}

func planOutput(stdout io.Writer, outputPath string) (io.Writer, func(), error) {
	if outputPath == "" || outputPath == "-" {
		return stdout, func() {}, nil
	}
	file, err := os.Create(outputPath)
	if err != nil {
		return nil, nil, fmt.Errorf("creating plan output: %w", err)
	}
	return file, func() { _ = file.Close() }, nil
}
