package wait

import (
	"context"
	"fmt"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/fields"
	"k8s.io/apimachinery/pkg/watch"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
)

// NewClientset creates a Kubernetes clientset from standard kubeconfig resolution.
func NewClientset(kubeconfig string) (kubernetes.Interface, error) {
	rules := clientcmd.NewDefaultClientConfigLoadingRules()
	if kubeconfig != "" {
		rules.ExplicitPath = kubeconfig
	}

	config, err := clientcmd.NewNonInteractiveDeferredLoadingClientConfig(
		rules, &clientcmd.ConfigOverrides{},
	).ClientConfig()
	if err != nil {
		return nil, fmt.Errorf("building kubeconfig: %w", err)
	}

	cs, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("creating clientset: %w", err)
	}
	return cs, nil
}

// ForDeployment watches a Deployment until the given condition reaches the
// specified status, or the timeout expires. Uses the K8s Watch API for instant
// notification instead of polling.
func ForDeployment(ctx context.Context, cs kubernetes.Interface, namespace, name, conditionType, conditionStatus string, timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	deploy, err := cs.AppsV1().Deployments(namespace).Get(ctx, name, metav1.GetOptions{})
	if err == nil && deploymentConditionMet(deploy, conditionType, conditionStatus) {
		return nil
	}

	watcher, err := cs.AppsV1().Deployments(namespace).Watch(ctx, metav1.ListOptions{
		FieldSelector: fields.OneTermEqualSelector("metadata.name", name).String(),
	})
	if err != nil {
		return fmt.Errorf("watching deployment %s/%s: %w", namespace, name, err)
	}
	defer watcher.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("timed out waiting for deployment %s/%s condition %s=%s", namespace, name, conditionType, conditionStatus)
		case event, ok := <-watcher.ResultChan():
			if !ok {
				return fmt.Errorf("watch channel closed for deployment %s/%s", namespace, name)
			}
			if event.Type == watch.Error {
				return fmt.Errorf("watch error for deployment %s/%s: %v", namespace, name, event.Object)
			}
			if event.Type != watch.Added && event.Type != watch.Modified {
				continue
			}
			deploy, ok := event.Object.(*appsv1.Deployment)
			if !ok {
				continue
			}
			if deploymentConditionMet(deploy, conditionType, conditionStatus) {
				return nil
			}
		}
	}
}

// ForStatefulSetReady watches a StatefulSet until readyReplicas equals the
// desired replicas count, or the timeout expires.
func ForStatefulSetReady(ctx context.Context, cs kubernetes.Interface, namespace, name string, timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	sts, err := cs.AppsV1().StatefulSets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err == nil && statefulSetReady(sts) {
		return nil
	}

	watcher, err := cs.AppsV1().StatefulSets(namespace).Watch(ctx, metav1.ListOptions{
		FieldSelector: fields.OneTermEqualSelector("metadata.name", name).String(),
	})
	if err != nil {
		return fmt.Errorf("watching statefulset %s/%s: %w", namespace, name, err)
	}
	defer watcher.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("timed out waiting for statefulset %s/%s to be ready", namespace, name)
		case event, ok := <-watcher.ResultChan():
			if !ok {
				return fmt.Errorf("watch channel closed for statefulset %s/%s", namespace, name)
			}
			if event.Type == watch.Error {
				return fmt.Errorf("watch error for statefulset %s/%s: %v", namespace, name, event.Object)
			}
			if event.Type != watch.Added && event.Type != watch.Modified {
				continue
			}
			sts, ok := event.Object.(*appsv1.StatefulSet)
			if !ok {
				continue
			}
			if statefulSetReady(sts) {
				return nil
			}
		}
	}
}

// ForSecret watches until a Secret with the given name exists in the namespace,
// or the timeout expires.
func ForSecret(ctx context.Context, cs kubernetes.Interface, namespace, name string, timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	_, err := cs.CoreV1().Secrets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err == nil {
		return nil
	}

	watcher, err := cs.CoreV1().Secrets(namespace).Watch(ctx, metav1.ListOptions{
		FieldSelector: fields.OneTermEqualSelector("metadata.name", name).String(),
	})
	if err != nil {
		return fmt.Errorf("watching secret %s/%s: %w", namespace, name, err)
	}
	defer watcher.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("timed out waiting for secret %s/%s to exist", namespace, name)
		case event, ok := <-watcher.ResultChan():
			if !ok {
				return fmt.Errorf("watch channel closed for secret %s/%s", namespace, name)
			}
			if event.Type == watch.Error {
				return fmt.Errorf("watch error for secret %s/%s: %v", namespace, name, event.Object)
			}
			if event.Type == watch.Added || event.Type == watch.Modified {
				if _, ok := event.Object.(*corev1.Secret); ok {
					return nil
				}
			}
		}
	}
}

func deploymentConditionMet(deploy *appsv1.Deployment, condType, condStatus string) bool {
	for _, c := range deploy.Status.Conditions {
		if string(c.Type) == condType && string(c.Status) == condStatus {
			return true
		}
	}
	return false
}

func statefulSetReady(sts *appsv1.StatefulSet) bool {
	if sts.Spec.Replicas == nil {
		return sts.Status.ReadyReplicas > 0
	}
	return sts.Status.ReadyReplicas == *sts.Spec.Replicas && *sts.Spec.Replicas > 0
}
