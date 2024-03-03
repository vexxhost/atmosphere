package deploy

import (
	"context"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	"github.com/go-logr/logr"
	"github.com/vexxhost/atmosphere/internal/deploy/util"
)

type NamespaceManager struct {
	functions  *util.OnceValueMap
	logger     logr.Logger
	managerSet *ManagerSet
}

func NewNamespaceManager(managerSet *ManagerSet) *NamespaceManager {
	return &NamespaceManager{
		functions:  util.NewOnceValueMap(),
		logger:     managerSet.logger.WithName("namespace"),
		managerSet: managerSet,
	}
}

func (m *NamespaceManager) Create(ctx context.Context, name string) error {
	return m.functions.Do(name, func() error {
		logger := m.logger.WithValues("namespace", name)
		logger.Info("Reconciling namespace")

		namespace := &corev1.Namespace{
			ObjectMeta: metav1.ObjectMeta{
				Name: name,
			},
		}

		op, err := controllerutil.CreateOrUpdate(ctx, m.managerSet.Client, namespace, func() error { return nil })
		if err != nil {
			logger.Error(err, "Failed to reconcile namespace")
			return err
		}

		logger.Info("Reconciled namespace", "operation", op)
		return nil
	})
}
