// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package deploy

import (
	"reflect"
	"testing"
)

func TestNeutronInstallDoesNotDependOnNova(t *testing.T) {
	neutron, ok := FindComponent("neutron")
	if !ok {
		t.Fatal("neutron component not found")
	}

	value := reflect.ValueOf(neutron)
	preRole := value.FieldByName("PreRoleName")
	if preRole.IsValid() && preRole.Kind() == reflect.String && preRole.String() != "" {
		preRoleDependsOn := value.FieldByName("PreRoleDependsOn")
		if !preRoleDependsOn.IsValid() {
			t.Fatal("neutron has a pre-role but no pre-role dependencies")
		}
		for i := 0; i < preRoleDependsOn.Len(); i++ {
			if preRoleDependsOn.Index(i).String() == "nova" {
				t.Fatal("neutron pre-role must not depend on nova")
			}
		}
		return
	}

	for _, dep := range neutron.DependsOn {
		if dep == "nova" {
			t.Fatal("neutron must not depend on nova")
		}
	}
}
