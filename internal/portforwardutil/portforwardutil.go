package portforwardutil

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"os"

	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/cli-runtime/pkg/genericclioptions"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/portforward"
	"k8s.io/client-go/transport/spdy"
)

func NewForService(config *rest.Config, service *v1.Service, port int) (*portforward.PortForwarder, error) {
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	ep, err := clientset.CoreV1().Endpoints(service.Namespace).Get(
		context.TODO(),
		service.Name,
		metav1.GetOptions{},
	)
	if err != nil {
		return nil, err
	}

	if len(ep.Subsets) == 0 {
		return nil, fmt.Errorf("no subsets found")
	}

	pod := &v1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      ep.Subsets[0].Addresses[0].TargetRef.Name,
			Namespace: service.Namespace,
		},
	}

	return NewForPod(config, pod, port)
}

func NewForPod(config *rest.Config, pod *v1.Pod, port int) (*portforward.PortForwarder, error) {
	streams := genericclioptions.IOStreams{
		In:     os.Stdin,
		Out:    os.Stdout,
		ErrOut: os.Stderr,
	}

	parsedUrl, err := url.Parse(config.Host)
	if err != nil {
		return nil, err
	}

	parsedUrl.Path = fmt.Sprintf(
		"/api/v1/namespaces/%s/pods/%s/portforward",
		pod.Namespace, pod.Name,
	)

	transport, upgrader, err := spdy.RoundTripperFor(config)
	if err != nil {
		return nil, err
	}

	dialer := spdy.NewDialer(
		upgrader,
		&http.Client{Transport: transport},
		http.MethodPost,
		parsedUrl,
	)

	return portforward.New(
		dialer,
		[]string{fmt.Sprintf("%d:%d", 3306, port)},
		make(chan struct{}),
		make(chan struct{}),
		streams.Out,
		streams.ErrOut,
	)
}
