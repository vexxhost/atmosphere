package testutils

import (
	"testing"

	"github.com/stretchr/testify/assert"

	"github.com/vexxhost/atmosphere/internal/openstack_helm"
)

func TestDatabaseConf(t *testing.T, config *openstack_helm.DatabaseConf) {
	assert.Equal(t, 600, config.ConnectionRecycleTime)
	assert.Equal(t, 5, config.MaxPoolSize)
	assert.Equal(t, -1, config.MaxRetries)
}
