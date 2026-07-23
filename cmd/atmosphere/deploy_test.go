// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package main

import "testing"

func TestParseDependencyOptions(t *testing.T) {
	options, err := parseDependencyOptions([]string{
		"csi_driver=local-path-provisioner",
		"network_backend=ovn",
	})
	if err != nil {
		t.Fatalf("parseDependencyOptions returned an error: %v", err)
	}
	if options["csi_driver"] != "local-path-provisioner" {
		t.Errorf("unexpected CSI driver: %q", options["csi_driver"])
	}
	if options["network_backend"] != "ovn" {
		t.Errorf("unexpected network backend: %q", options["network_backend"])
	}
}

func TestParseDependencyOptionsRejectsInvalidValues(t *testing.T) {
	tests := []struct {
		name   string
		values []string
	}{
		{name: "missing separator", values: []string{"csi_driver"}},
		{name: "missing key", values: []string{"=rbd"}},
		{name: "missing value", values: []string{"csi_driver="}},
		{name: "duplicate key", values: []string{"csi_driver=rbd", "csi_driver=local-path-provisioner"}},
		{name: "unknown key", values: []string{"csi_drivr=rbd"}},
		{name: "unknown network backend", values: []string{"network_backend=linuxbridge"}},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if _, err := parseDependencyOptions(test.values); err == nil {
				t.Fatalf("expected an error for %v", test.values)
			}
		})
	}
}
