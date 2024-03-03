package deploy

import (
	rabbitmqv1beta1 "github.com/rabbitmq/cluster-operator/api/v1beta1"
	log "github.com/sirupsen/logrus"
	clientsetscheme "k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"k8s.io/utils/ptr"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// TODO: mangaer interface

type ManagerOptions struct {
	DryRun bool
}

type ManagerSet struct {
	client.Client

	Options *ManagerOptions

	Image     *ImageManager
	Namespace *NamespaceManager
	Rabbitmq  *RabbitmqManager

	logger *log.Entry
}

func NewManagerSet(config *rest.Config, opts *ManagerOptions) (*ManagerSet, error) {
	err := rabbitmqv1beta1.AddToScheme(clientsetscheme.Scheme)
	if err != nil {
		return nil, err
	}

	client, err := client.New(config, client.Options{
		DryRun: ptr.To(opts.DryRun),
		Scheme: clientsetscheme.Scheme,
	})
	if err != nil {
		log.Fatal(err)
	}

	managerSet := &ManagerSet{
		Client:  client,
		Options: opts,

		logger: log.WithField("dry-run", opts.DryRun),
	}

	managerSet.Image = NewImageManager(managerSet)
	managerSet.Namespace = NewNamespaceManager(managerSet)
	managerSet.Rabbitmq = NewRabbitmqManager(managerSet)

	return managerSet, nil
}
