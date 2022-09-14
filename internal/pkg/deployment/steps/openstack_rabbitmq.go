package steps

import (
	"context"
	"fmt"
	"reflect"
	"strings"
	"sync"

	log "github.com/sirupsen/logrus"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	rabbitmqv1beta1 "github.com/rabbitmq/cluster-operator/api/v1beta1"

	"sigs.k8s.io/controller-runtime/pkg/client"
)

type OpenstackRabbitmqStep struct {
	Client client.Client
	Name   string
}

func (s *OpenstackRabbitmqStep) Logger() *log.Entry {
	return log.WithField("name", s.Name)
}

func (s *OpenstackRabbitmqStep) Generate() *rabbitmqv1beta1.RabbitmqCluster {
	extraConfig := []string{
		"vm_memory_high_watermark.relative = 0.9",
	}

	return &rabbitmqv1beta1.RabbitmqCluster{
		ObjectMeta: metav1.ObjectMeta{
			Namespace: "openstack",
			Name:      fmt.Sprintf("rabbitmq-%s", s.Name),
		},
		Spec: rabbitmqv1beta1.RabbitmqClusterSpec{
			Resources: &corev1.ResourceRequirements{
				Limits: corev1.ResourceList{
					corev1.ResourceCPU:    resource.MustParse("1"),
					corev1.ResourceMemory: resource.MustParse("2Gi"),
				},
				Requests: corev1.ResourceList{
					corev1.ResourceCPU:    resource.MustParse("500m"),
					corev1.ResourceMemory: resource.MustParse("1Gi"),
				},
			},
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
			Rabbitmq: rabbitmqv1beta1.RabbitmqClusterConfigurationSpec{
				AdditionalConfig: strings.Join(extraConfig, "\n"),
			},
		},
	}
}

func (s *OpenstackRabbitmqStep) Get(ctx context.Context) (*rabbitmqv1beta1.RabbitmqCluster, error) {
	rabbitmq := s.Generate()
	deployedRabbitmq := &rabbitmqv1beta1.RabbitmqCluster{}

	err := s.Client.Get(ctx, client.ObjectKeyFromObject(rabbitmq), deployedRabbitmq)
	return deployedRabbitmq, err
}

func (s *OpenstackRabbitmqStep) Execute(ctx context.Context, wg *sync.WaitGroup) error {
	defer wg.Done()

	validation, err := s.Validate(ctx)
	if err != nil {
		return err
	}

	rabbitmq := s.Generate()

	if !validation.Installed {
		if err := s.Client.Create(ctx, rabbitmq); err != nil {
			return err
		}

		s.Logger().Info("🚀 RabbitMQ cluster created")
	} else if !validation.Updated {
		deployedRabbitmq, err := s.Get(ctx)
		if err != nil {
			return err
		}

		deployedRabbitmq.Spec = rabbitmq.Spec
		if err := s.Client.Update(ctx, deployedRabbitmq); err != nil {
			return err
		}
		s.Logger().Info("🚀 RabbitMQ cluster updated")
	}

	return nil
}

func (s *OpenstackRabbitmqStep) Validate(ctx context.Context) (*ValidationResult, error) {
	deployedRabbitmq, err := s.Get(ctx)
	if client.IgnoreNotFound(err) != nil {
		return nil, err
	}

	if errors.IsNotFound(err) {
		s.Logger().Info("⏳ RabbitMQ cluster missing from Kubernetes")
		return &ValidationResult{
			Installed: false,
			Updated:   false,
			Tested:    false,
		}, nil
	}

	rabbitmq := s.Generate()
	if !reflect.DeepEqual(deployedRabbitmq.Spec, rabbitmq.Spec) {
		s.Logger().Info("⏳ RabbitMQ configuration needs to be updated")
		return &ValidationResult{
			Installed: true,
			Updated:   false,
			Tested:    false,
		}, nil
	}

	s.Logger().Info("🚀 RabbitMQ cluster is up to date")
	return &ValidationResult{
		Installed: true,
		Updated:   true,
		Tested:    true,
	}, nil
}
