package deploy

import (
	"context"
	"errors"
	"fmt"
	"strings"

	"github.com/docker/go-units"
	rabbitmqv1beta1 "github.com/rabbitmq/cluster-operator/api/v1beta1"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/viper"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/utils/ptr"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	"github.com/vexxhost/atmosphere/internal/deploy/util"
)

type RabbitmqOptions struct {
	Name  string
	Image string
}

func RabbitmqOptionsFromViper(name string, config *viper.Viper) *RabbitmqOptions {
	return &RabbitmqOptions{
		Name:  name,
		Image: config.GetString("image"),
	}
}

type RabbitmqManager struct {
	functions  *util.OnceValueMap
	logger     *log.Entry
	managerSet *ManagerSet
}

func NewRabbitmqManager(managerSet *ManagerSet) *RabbitmqManager {
	return &RabbitmqManager{
		functions:  util.NewOnceValueMap(),
		logger:     managerSet.logger.WithField("manager", "rabbitmq"),
		managerSet: managerSet,
	}
}

func (m *RabbitmqManager) Manifest(opts *RabbitmqOptions) *rabbitmqv1beta1.RabbitmqCluster {
	return &rabbitmqv1beta1.RabbitmqCluster{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("rabbitmq-%s", opts.Name),
			Namespace: "openstack",
		},
	}
}

func (m *RabbitmqManager) Deploy(ctx context.Context, opts *RabbitmqOptions) error {
	if err := m.managerSet.Image.Pull(ctx, opts.Image, map[string]string{
		"openstack-control-plane": "enabled",
	}); err != nil {
		return err
	}

	logger := m.logger.WithFields(log.Fields{
		"name": opts.Name,
	})

	logger.Info("Reconciling RabbitMQ")

	rabbitmq := &rabbitmqv1beta1.RabbitmqCluster{
		ObjectMeta: metav1.ObjectMeta{
			Namespace: "openstack",
			Name:      fmt.Sprintf("rabbitmq-%s", opts.Name),
		},
	}

	op, err := controllerutil.CreateOrUpdate(ctx, m.managerSet.Client, rabbitmq, func() error {
		rabbitmq.Spec = rabbitmqv1beta1.RabbitmqClusterSpec{
			Affinity: &corev1.Affinity{
				NodeAffinity: &corev1.NodeAffinity{
					RequiredDuringSchedulingIgnoredDuringExecution: &corev1.NodeSelector{
						NodeSelectorTerms: []corev1.NodeSelectorTerm{
							{
								MatchExpressions: []corev1.NodeSelectorRequirement{
									{
										Key:      "openstack-control-plane",
										Operator: corev1.NodeSelectorOpIn,
										Values:   []string{"enabled"},
									},
								},
							},
						},
					},
				},
			},
			Image:    opts.Image,
			Override: rabbitmqv1beta1.RabbitmqClusterOverrideSpec{},
			Persistence: rabbitmqv1beta1.RabbitmqClusterPersistenceSpec{
				Storage: resource.NewQuantity(10*units.GiB, resource.BinarySI),
			},
			Rabbitmq: rabbitmqv1beta1.RabbitmqClusterConfigurationSpec{
				AdditionalConfig: fmt.Sprintf("%s\n", strings.Join([]string{
					"vm_memory_high_watermark.relative = 0.9",
				}, "\n")),
			},
			Replicas: ptr.To(int32(1)),
			Resources: &corev1.ResourceRequirements{
				Requests: corev1.ResourceList{
					corev1.ResourceCPU:    *resource.NewMilliQuantity(500, resource.DecimalSI),
					corev1.ResourceMemory: *resource.NewQuantity(1*units.GiB, resource.BinarySI),
				},
			},
			SecretBackend: rabbitmqv1beta1.SecretBackend{},
			Service: rabbitmqv1beta1.RabbitmqClusterServiceSpec{
				Type: corev1.ServiceTypeClusterIP,
			},
			TerminationGracePeriodSeconds: ptr.To(int64(15)),
			TLS:                           rabbitmqv1beta1.TLSSpec{},
		}

		return nil
	})

	if m.managerSet.Options.DryRun == false && util.IsCRDNotFoundError(err) {
		err := errors.New("crd not found, operator not installed")

		logger.Error(err)
		return err
	} else if !util.IsCRDNotFoundError(err) {
		logger.Error(err)
		return err
	}

	logger.WithField("operation", op).Info("Reconciled RabbitMQ")
	return nil
}
