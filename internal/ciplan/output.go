// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package ciplan

import (
	"fmt"
	"io"
	"strings"
)

// WriteText writes an explainable summary suitable for a Zuul console log.
func WriteText(writer io.Writer, plan Plan) error {
	if _, err := fmt.Fprintf(writer, "CI plan mode: %s\n", plan.Mode); err != nil {
		return err
	}

	if len(plan.Changes) > 0 {
		if _, err := fmt.Fprintln(writer, "Changed files:"); err != nil {
			return err
		}
		for _, change := range plan.Changes {
			if change.PreviousPath == "" {
				if _, err := fmt.Fprintf(writer, "  %s\t%s\n", change.Status, change.Path); err != nil {
					return err
				}
			} else if _, err := fmt.Fprintf(
				writer,
				"  %s\t%s -> %s\n",
				change.Status,
				change.PreviousPath,
				change.Path,
			); err != nil {
				return err
			}
		}
	}

	if len(plan.Matches) > 0 {
		if _, err := fmt.Fprintln(writer, "Matches:"); err != nil {
			return err
		}
		for _, match := range plan.Matches {
			targets := ""
			if len(match.Targets) > 0 {
				targets = " -> " + strings.Join(match.Targets, ",")
			}
			if _, err := fmt.Fprintf(
				writer,
				"  %s: %s (%s)%s\n",
				match.Path,
				match.Rule,
				match.Action,
				targets,
			); err != nil {
				return err
			}
		}
	}

	if len(plan.Targets) > 0 {
		if _, err := fmt.Fprintf(writer, "Direct targets: %s\n", strings.Join(plan.Targets, ", ")); err != nil {
			return err
		}
	}
	if len(plan.DeploymentRoots) > 0 {
		if _, err := fmt.Fprintf(
			writer,
			"Deployment roots: %s\n",
			strings.Join(plan.DeploymentRoots, ", "),
		); err != nil {
			return err
		}
	}
	if len(plan.VerificationProfiles) > 0 {
		if _, err := fmt.Fprintf(
			writer,
			"Verification profiles: %s\n",
			strings.Join(plan.VerificationProfiles, ", "),
		); err != nil {
			return err
		}
	}

	for _, variant := range plan.Variants {
		if _, err := fmt.Fprintf(
			writer,
			"Variant %s (%d components): %s\n",
			variant.NetworkBackend,
			len(variant.Components),
			strings.Join(variant.Components, ", "),
		); err != nil {
			return err
		}
	}

	if len(plan.Jobs) > 0 {
		if _, err := fmt.Fprintln(writer, "Molecule jobs:"); err != nil {
			return err
		}
		for _, job := range plan.Jobs {
			action := "skip"
			if job.Run {
				action = "run"
			}
			components := ""
			if len(job.Components) > 0 {
				components = fmt.Sprintf(" (%d components)", len(job.Components))
			}
			if _, err := fmt.Fprintf(
				writer,
				"  %s: %s%s - %s\n",
				job.Name,
				action,
				components,
				job.Reason,
			); err != nil {
				return err
			}
		}
	}

	if len(plan.Reasons) > 0 {
		if _, err := fmt.Fprintln(writer, "Reasons:"); err != nil {
			return err
		}
		for _, reason := range plan.Reasons {
			if _, err := fmt.Fprintf(writer, "  - %s\n", reason); err != nil {
				return err
			}
		}
	}
	return nil
}
