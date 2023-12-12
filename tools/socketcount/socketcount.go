package main

import (
	"bytes"
	"context"
	"fmt"
	"path/filepath"
	"strconv"
	"strings"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/pflag"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/tools/remotecommand"
	"k8s.io/client-go/util/homedir"
)

var (
	kubeconfig string
)

func init() {
	homedir := homedir.HomeDir()
	pflag.StringVar(
		&kubeconfig,
		"kubeconfig",
		filepath.Join(homedir, ".kube", "config"),
		"absolute path to the kubeconfig file",
	)
}

func main() {
	pflag.Parse()

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		log.Fatal(err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatal(err)
	}

	pods, err := clientset.CoreV1().Pods("kube-system").List(context.TODO(), metav1.ListOptions{
		LabelSelector: "k8s-app=kube-proxy",
	})
	if err != nil {
		log.Fatal(err)
	}

	totalSockets := 0
	for _, pod := range pods.Items {
		req := clientset.CoreV1().RESTClient().
			Post().
			Resource("pods").
			Namespace(pod.Namespace).
			Name(pod.Name).
			SubResource("exec").
			VersionedParams(&v1.PodExecOptions{
				Command: []string{"/bin/sh", "-c", "cat /proc/cpuinfo | grep '^physical id' | sort | uniq | wc -l"},
				Stdin:   false,
				Stdout:  true,
				Stderr:  true,
				TTY:     false,
			}, scheme.ParameterCodec)

		exec, err := remotecommand.NewSPDYExecutor(config, "POST", req.URL())
		if err != nil {
			log.Fatal(err)
		}

		var stdout, stderr bytes.Buffer
		err = exec.StreamWithContext(context.TODO(), remotecommand.StreamOptions{
			Stdout: &stdout,
			Stderr: &stderr,
		})
		if err != nil {
			log.Fatal(err)
		}

		sockets, err := strconv.ParseInt(strings.Trim(stdout.String(), "\n"), 10, 64)
		if err != nil {
			log.Fatal(err)
		}

		totalSockets += int(sockets)

		fmt.Printf(
			"- %s: %d sockets\n",
			pod.Spec.NodeName,
			sockets,
		)
	}

	fmt.Printf("Total sockets: %d\n", totalSockets)
}
