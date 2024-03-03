package util

import (
	"context"
	"fmt"
	"strings"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/util/wait"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func IsCRDNotFoundError(err error) bool {
	if meta.IsNoMatchError(err) || errors.IsNotFound(err) ||
		strings.Contains(err.Error(), "failed to get API group resources") {
		return true
	}

	return false
}

func WaitForDaemonSet(ctx context.Context, c client.Client, key client.ObjectKey) error {
	ds := &appsv1.DaemonSet{}

	err := wait.PollUntilContextTimeout(ctx, 5*time.Second, 2*time.Minute, true, func(ctx context.Context) (bool, error) {
		err := c.Get(ctx, key, ds)
		if err != nil {
			return false, err
		}

		if ds.Status.ObservedGeneration == 0 {
			return false, nil
		}

		return ds.Status.DesiredNumberScheduled == ds.Status.NumberReady, nil
	})

	if err != nil {
		return fmt.Errorf("failed to wait for DaemonSet %s: %w", key.Name, err)
	}

	return nil
}
