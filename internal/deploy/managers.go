package deploy

import (
	"github.com/go-logr/logr"
	rabbitmqv1beta1 "github.com/rabbitmq/cluster-operator/api/v1beta1"
	clientsetscheme "k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"k8s.io/utils/ptr"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// TODO: mangaer interface

type ManagerOptions struct {
	DryRun bool
	Logger logr.Logger
}

type ManagerSet struct {
	client.Client

	Options *ManagerOptions

	Helm      *HelmManager
	Image     *ImageManager
	Namespace *NamespaceManager
	Rabbitmq  *RabbitmqManager

	logger logr.Logger
}

func NewManagerSet(config *rest.Config, opts *ManagerOptions) (*ManagerSet, error) {
	logger := opts.Logger.WithName("manager")

	err := rabbitmqv1beta1.AddToScheme(clientsetscheme.Scheme)
	if err != nil {
		return nil, err
	}

	client, err := client.New(config, client.Options{
		DryRun: ptr.To(opts.DryRun),
		Scheme: clientsetscheme.Scheme,
	})
	if err != nil {
		return nil, err
	}

	if opts.DryRun {
		logger.Info("Running in dry-run mode")
	}

	managerSet := &ManagerSet{
		Client:  client,
		Options: opts,

		logger: logger.WithValues("dry-run", opts.DryRun),
	}

	managerSet.Image = NewImageManager(managerSet)
	managerSet.Namespace = NewNamespaceManager(managerSet)
	managerSet.Rabbitmq = NewRabbitmqManager(managerSet)

	return managerSet, nil
}
