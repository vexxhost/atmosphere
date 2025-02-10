package testutils

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"

	"github.com/vexxhost/atmosphere/internal/openstack_helm"
)

func TestDatabaseConf(t *testing.T, config *openstack_helm.DatabaseConf) {
	assert.Equal(t, 600, config.ConnectionRecycleTime)
	assert.Equal(t, 5, config.MaxPoolSize)
	assert.Equal(t, -1, config.MaxRetries)
}

func podNameForClass(pod string) string {
	// There are a few pods which are built/created inside "helm-toolkit" so
	// we cannot refer to them by their full name or the code will get real
	// messy.
	if strings.HasSuffix(pod, "db_init") {
		return "db_init"
	} else if strings.HasSuffix(pod, "db_sync") {
		return "db_sync"
	} else if strings.HasSuffix(pod, "_bootstrap") {
		return "bootstrap"
	}

	return pod
}

func TestAllPodsHaveRuntimeClass(t *testing.T, vals *openstack_helm.HelmValues) {
	for pod := range vals.Pod.Mounts {
		podName := podNameForClass(pod)
		assert.Contains(t, vals.Pod.RuntimeClass, podName)
	}
}

func TestAllPodsHavePriorityClass(t *testing.T, vals *openstack_helm.HelmValues) {
	for pod := range vals.Pod.Mounts {
		podName := podNameForClass(pod)
		assert.Contains(t, vals.Pod.PriorityClass, podName)
	}
}
