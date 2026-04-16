package wait

import (
	"context"
	"testing"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/watch"
	"k8s.io/client-go/kubernetes/fake"
	k8stesting "k8s.io/client-go/testing"
)

func int32Ptr(i int32) *int32 { return &i }

func TestForDeployment_AlreadyReady(t *testing.T) {
	deploy := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{Name: "keystone-api", Namespace: "openstack"},
		Status: appsv1.DeploymentStatus{
			Conditions: []appsv1.DeploymentCondition{
				{Type: appsv1.DeploymentAvailable, Status: corev1.ConditionTrue},
			},
		},
	}

	cs := fake.NewSimpleClientset(deploy)
	err := ForDeployment(context.Background(), cs, "openstack", "keystone-api", "Available", "True", 5*time.Second)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
}

func TestForDeployment_BecomesReady(t *testing.T) {
	deploy := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{Name: "keystone-api", Namespace: "openstack"},
		Status:     appsv1.DeploymentStatus{},
	}

	cs := fake.NewSimpleClientset(deploy)
	fakeWatcher := watch.NewFake()
	cs.PrependWatchReactor("deployments", k8stesting.DefaultWatchReactor(fakeWatcher, nil))

	go func() {
		time.Sleep(50 * time.Millisecond)
		fakeWatcher.Modify(&appsv1.Deployment{
			ObjectMeta: metav1.ObjectMeta{Name: "keystone-api", Namespace: "openstack"},
			Status: appsv1.DeploymentStatus{
				Conditions: []appsv1.DeploymentCondition{
					{Type: appsv1.DeploymentAvailable, Status: corev1.ConditionTrue},
				},
			},
		})
	}()

	err := ForDeployment(context.Background(), cs, "openstack", "keystone-api", "Available", "True", 5*time.Second)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
}

func TestForDeployment_Timeout(t *testing.T) {
	deploy := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{Name: "keystone-api", Namespace: "openstack"},
		Status:     appsv1.DeploymentStatus{},
	}

	cs := fake.NewSimpleClientset(deploy)
	fakeWatcher := watch.NewFake()
	cs.PrependWatchReactor("deployments", k8stesting.DefaultWatchReactor(fakeWatcher, nil))

	err := ForDeployment(context.Background(), cs, "openstack", "keystone-api", "Available", "True", 100*time.Millisecond)
	if err == nil {
		t.Fatal("expected timeout error, got nil")
	}
}

func TestForStatefulSetReady_AlreadyReady(t *testing.T) {
	sts := &appsv1.StatefulSet{
		ObjectMeta: metav1.ObjectMeta{Name: "percona-xtradb-pxc", Namespace: "openstack"},
		Spec:       appsv1.StatefulSetSpec{Replicas: int32Ptr(3)},
		Status:     appsv1.StatefulSetStatus{ReadyReplicas: 3, Replicas: 3},
	}

	cs := fake.NewSimpleClientset(sts)
	err := ForStatefulSetReady(context.Background(), cs, "openstack", "percona-xtradb-pxc", 5*time.Second)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
}

func TestForStatefulSetReady_BecomesReady(t *testing.T) {
	sts := &appsv1.StatefulSet{
		ObjectMeta: metav1.ObjectMeta{Name: "percona-xtradb-pxc", Namespace: "openstack"},
		Spec:       appsv1.StatefulSetSpec{Replicas: int32Ptr(3)},
		Status:     appsv1.StatefulSetStatus{ReadyReplicas: 1, Replicas: 3},
	}

	cs := fake.NewSimpleClientset(sts)
	fakeWatcher := watch.NewFake()
	cs.PrependWatchReactor("statefulsets", k8stesting.DefaultWatchReactor(fakeWatcher, nil))

	go func() {
		time.Sleep(50 * time.Millisecond)
		fakeWatcher.Modify(&appsv1.StatefulSet{
			ObjectMeta: metav1.ObjectMeta{Name: "percona-xtradb-pxc", Namespace: "openstack"},
			Spec:       appsv1.StatefulSetSpec{Replicas: int32Ptr(3)},
			Status:     appsv1.StatefulSetStatus{ReadyReplicas: 3, Replicas: 3},
		})
	}()

	err := ForStatefulSetReady(context.Background(), cs, "openstack", "percona-xtradb-pxc", 5*time.Second)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
}

func TestForSecret_AlreadyExists(t *testing.T) {
	secret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{Name: "cluster-issuer-ca", Namespace: "cert-manager"},
	}

	cs := fake.NewSimpleClientset(secret)
	err := ForSecret(context.Background(), cs, "cert-manager", "cluster-issuer-ca", 5*time.Second)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
}

func TestForSecret_Created(t *testing.T) {
	cs := fake.NewSimpleClientset()
	fakeWatcher := watch.NewFake()
	cs.PrependWatchReactor("secrets", k8stesting.DefaultWatchReactor(fakeWatcher, nil))

	go func() {
		time.Sleep(50 * time.Millisecond)
		fakeWatcher.Add(&corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{Name: "cluster-issuer-ca", Namespace: "cert-manager"},
		})
	}()

	err := ForSecret(context.Background(), cs, "cert-manager", "cluster-issuer-ca", 5*time.Second)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
}
