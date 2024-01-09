package tls

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	cmv1 "github.com/cert-manager/cert-manager/pkg/apis/certmanager/v1"
	cmmeta "github.com/cert-manager/cert-manager/pkg/apis/meta/v1"
	cmclient "github.com/cert-manager/cert-manager/pkg/client/clientset/versioned/typed/certmanager/v1"
	log "github.com/sirupsen/logrus"
	"github.com/vexxhost/atmosphere/internal/net"
	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/fields"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/apimachinery/pkg/watch"
	kubernetes "k8s.io/client-go/kubernetes/typed/core/v1"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/cache"
)

type LibvirtCertificateType string

const (
	LibvirtCertificateTypeAPI LibvirtCertificateType = "api"
	LibvirtCertificateTypeVNC LibvirtCertificateType = "vnc"
)

const (
	EnvVarPodUID       = "POD_UID"
	EnvVarPodName      = "POD_NAME"
	EnvVarPodNamespace = "POD_NAMESPACE"
	EnvVarPodIP        = "POD_IP"
)

type LibvirtCertificateSpec struct {
	Type      LibvirtCertificateType
	IssuerRef cmmeta.ObjectReference
}

type LibvirtManager struct {
	logger            *log.Entry
	spec              *LibvirtCertificateSpec
	certificate       *cmv1.Certificate
	certificateName   string
	certificateClient cmclient.CertificateInterface
	secretClient      kubernetes.SecretInterface
}

func NewLibvirtManager(config *rest.Config, spec *LibvirtCertificateSpec) (*LibvirtManager, error) {
	required := []string{
		EnvVarPodName,
		EnvVarPodNamespace,
		EnvVarPodUID,
		EnvVarPodIP,
	}

	for _, env := range required {
		if os.Getenv(env) == "" {
			return nil, fmt.Errorf("missing required environment variable: %s", env)
		}
	}

	mgr := &LibvirtManager{}

	hostname, err := net.Hostname()
	if err != nil {
		return nil, err
	}

	fqdn, err := net.FQDN()
	if err != nil {
		return nil, err
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	cmClient, err := cmclient.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	podUID := types.UID(os.Getenv(EnvVarPodUID))
	podNamespace := os.Getenv(EnvVarPodNamespace)
	podName := os.Getenv(EnvVarPodName)
	podIP := os.Getenv(EnvVarPodIP)

	mgr.spec = spec
	mgr.secretClient = clientset.Secrets(podNamespace)
	mgr.certificateClient = cmClient.Certificates(podNamespace)
	mgr.certificateName = fmt.Sprintf("%s-%s", podName, spec.Type)

	mgr.logger = log.WithFields(log.Fields{
		"certificateName": mgr.certificateName,
		"podName":         podName,
		"podNamespace":    podNamespace,
		"podUID":          podUID,
		"podIP":           podIP,
		"hostname":        hostname,
		"fqdn":            fqdn,
		"issuerKind":      spec.IssuerRef.Kind,
		"issuerName":      spec.IssuerRef.Name,
	})

	mgr.certificate = &cmv1.Certificate{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mgr.certificateName,
			Namespace: podNamespace,
			OwnerReferences: []metav1.OwnerReference{
				{
					APIVersion: "v1",
					Kind:       "Pod",
					Name:       podName,
					UID:        podUID,
				},
			},
		},
		Spec: cmv1.CertificateSpec{
			SecretName: mgr.certificateName,
			CommonName: podIP,
			Usages: []cmv1.KeyUsage{
				cmv1.UsageClientAuth,
				cmv1.UsageServerAuth,
			},
			DNSNames:    []string{hostname, fqdn},
			IPAddresses: []string{podIP},
			IssuerRef:   spec.IssuerRef,
		},
	}

	return mgr, nil
}

func (m *LibvirtManager) Create(ctx context.Context) error {
	// Create certificate
	_, err := m.certificateClient.Create(ctx, m.certificate, metav1.CreateOptions{})
	if err != nil && !errors.IsAlreadyExists(err) {
		return err
	}

	m.logger.Info("certificate created")

	// Wait for certificate to become ready
	err = wait.PollUntilContextTimeout(ctx, 5*time.Second, 300*time.Second, true, func(ctx context.Context) (bool, error) {
		certificate, err := m.certificateClient.Get(ctx, m.certificateName, metav1.GetOptions{})
		if err != nil {
			return false, err
		}

		for _, condition := range certificate.Status.Conditions {
			if condition.Type == cmv1.CertificateConditionReady {
				if condition.Status == cmmeta.ConditionTrue {
					return true, nil
				}

				m.logger.WithFields(log.Fields{
					"reason":  condition.Reason,
					"message": condition.Message,
				}).Info("certificate not ready")
			}
		}

		return false, nil
	})
	if err != nil {
		return err
	}

	m.logger.Info("certificate ready")

	// Create patch with ownerReference so the secret is garbage collected
	patch := []map[string]interface{}{
		{
			"op":    "add",
			"path":  "/metadata/ownerReferences",
			"value": m.certificate.OwnerReferences,
		},
	}
	patchBytes, err := json.Marshal(patch)
	if err != nil {
		return err
	}

	m.logger.Info("patching secret")

	// Patch secret with ownerReference
	_, err = m.secretClient.Patch(ctx, m.certificateName, types.JSONPatchType, patchBytes, metav1.PatchOptions{})
	return err
}

func (m *LibvirtManager) Watch(ctx context.Context) {
	for {
		m.watch(ctx)
		m.logger.Info("watch closed or disconnected, retrying in 5 seconds")

		time.Sleep(5 * time.Second)
	}
}

func (m *LibvirtManager) watch(ctx context.Context) {
	fieldSelector := fields.OneTermEqualSelector("metadata.name", m.certificateName).String()

	listWatcher := &cache.ListWatch{
		ListFunc: func(options metav1.ListOptions) (runtime.Object, error) {
			options.FieldSelector = fieldSelector
			return m.secretClient.List(ctx, options)
		},
		WatchFunc: func(options metav1.ListOptions) (watch.Interface, error) {
			options.FieldSelector = fieldSelector
			return m.secretClient.Watch(ctx, options)
		},
	}

	_, controller := cache.NewInformer(
		listWatcher,
		&v1.Secret{},
		time.Minute,
		cache.ResourceEventHandlerFuncs{
			AddFunc: func(obj interface{}) {
				secret := obj.(*v1.Secret)
				m.write(secret)
			},
			UpdateFunc: func(oldObj, newObj interface{}) {
				secret := newObj.(*v1.Secret)
				m.write(secret)
			},
			DeleteFunc: func(obj interface{}) {
				m.logger.Fatal("secret deleted")
			},
		},
	)

	stop := make(chan struct{})
	defer close(stop)
	controller.Run(stop)
}

func (m *LibvirtManager) write(secret *v1.Secret) {
	switch m.spec.Type {
	case LibvirtCertificateTypeAPI:
		m.createDirectory("/etc/pki/libvirt/private")
		m.writeFile("/etc/pki/CA/cacert.pem", secret.Data["ca.crt"])
		m.writeFile("/etc/pki/libvirt/servercert.pem", secret.Data["tls.crt"])
		m.writeFile("/etc/pki/libvirt/private/serverkey.pem", secret.Data["tls.key"])
		m.writeFile("/etc/pki/libvirt/clientcert.pem", secret.Data["tls.crt"])
		m.writeFile("/etc/pki/libvirt/private/clientkey.pem", secret.Data["ca.key"])
		m.createDirectory("/etc/pki/qemu")
		m.writeFile("/etc/pki/qemu/ca-cert.pem", secret.Data["ca.crt"])
		m.writeFile("/etc/pki/qemu/server-cert.pem", secret.Data["tls.crt"])
		m.writeFile("/etc/pki/qemu/server-key.pem", secret.Data["tls.key"])
		m.writeFile("/etc/pki/qemu/client-cert.pem", secret.Data["tls.crt"])
		m.writeFile("/etc/pki/qemu/client-key.pem", secret.Data["tls.key"])
	case LibvirtCertificateTypeVNC:
		m.createDirectory("/etc/pki/libvirt-vnc")
		m.writeFile("/etc/pki/libvirt-vnc/ca-cert.pem", secret.Data["ca.crt"])
		m.writeFile("/etc/pki/libvirt-vnc/server-cert.pem", secret.Data["tls.crt"])
		m.writeFile("/etc/pki/libvirt-vnc/server-key.pem", secret.Data["tls.key"])
	}
}

func (m *LibvirtManager) createDirectory(path string) {
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		return
	}

	m.logger.WithFields(log.Fields{
		"path": path,
	}).Info("creating directory")

	err := os.MkdirAll(path, 0755)
	if err != nil {
		m.logger.Fatal(err)
	}
}

func (m *LibvirtManager) writeFile(path string, data []byte) {
	log := m.logger.WithFields(log.Fields{
		"path": path,
	})

	existingData, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			log.Info("file does not exist, creating file")

			err = os.WriteFile(path, data, 0644)
			if err != nil {
				log.Fatal(err)
			}

			return
		}

		m.logger.Fatal(err)
	}

	if bytes.Equal(existingData, data) {
		return
	}

	log.Info("file contents changed, updating file")

	err = os.WriteFile(path, data, 0644)
	if err != nil {
		log.Fatal(err)
	}
}
