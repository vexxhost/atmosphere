package phases

import (
	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// NewHelmReleasesWithCrdPhase returns a list of steps that install Helm
// releases with CRDs.  We make sure to install those before any other Helm
// releases to make sure that we don't get any "missing API" errors.
func NewCrdHelmReleasePhase(client client.Client) Phase {
	return Phase{
		Steps: []steps.Step{},
	}
}
