// Copyright (c) 2024 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package main

import (
	"context"
	"fmt"

	"github.com/kelseyhightower/envconfig"
	log "github.com/sirupsen/logrus"
	"k8s.io/client-go/rest"

	"github.com/vexxhost/pod-tls-sidecar/pkg/template"
	"github.com/vexxhost/pod-tls-sidecar/pkg/tls"
)

type IssuerInfo struct {
	Kind string `envconfig:"ISSUER_KIND" required:"true"`
	Name string `envconfig:"ISSUER_NAME" required:"true"`
}

func main() {
	var apiIssuer IssuerInfo
	if err := envconfig.Process("API", &apiIssuer); err != nil {
		log.Fatal(err)
	}

	var vncIssuer IssuerInfo
	if err := envconfig.Process("VNC", &vncIssuer); err != nil {
		log.Fatal(err)
	}

	config, err := rest.InClusterConfig()
	if err != nil {
		log.Fatal(err)
	}

	ctx := context.Background()

	go createCertificateSpec(ctx, config, "api", &apiIssuer, &tls.WritePathConfig{
		CertificateAuthorityPaths: []string{"/etc/pki/CA/cacert.pem", "/etc/pki/qemu/ca-cert.pem"},
		CertificatePaths:          []string{"/etc/pki/libvirt/servercert.pem", "/etc/pki/libvirt/clientcert.pem", "/etc/pki/qemu/server-cert.pem", "/etc/pki/qemu/client-cert.pem"},
		CertificateKeyPaths:       []string{"/etc/pki/libvirt/private/serverkey.pem", "/etc/pki/libvirt/private/clientkey.pem", "/etc/pki/qemu/server-key.pem", "/etc/pki/qemu/client-key.pem"},
	})
	go createCertificateSpec(ctx, config, "vnc", &vncIssuer, &tls.WritePathConfig{
		CertificateAuthorityPaths: []string{"/etc/pki/libvirt-vnc/ca-cert.pem"},
		CertificatePaths:          []string{"/etc/pki/libvirt-vnc/server-cert.pem"},
		CertificateKeyPaths:       []string{"/etc/pki/libvirt-vnc/server-key.pem"},
	})

	<-ctx.Done()
}

func createCertificateSpec(ctx context.Context, config *rest.Config, name string, issuer *IssuerInfo, writePathConfig *tls.WritePathConfig) {
	tmpl, err := template.New(fmt.Sprintf(`
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
	name: {{ .PodInfo.Name }}-%s
	namespace: {{ .PodInfo.Namespace }}
spec:
	commonName: "{{ .FQDN }}"
	dnsNames:
		- "{{ .Hostname }}"
		- "{{ .FQDN }}"
	ipAddresses:
		- "{{ .PodInfo.IP }}"
	usages:
		- client auth
		- server auth
	issuerRef:
		kind: %s
		name: %s
	secretName: {{ .PodInfo.Name }}-%s
`, name, issuer.Kind, issuer.Name, name))
	if err != nil {
		log.Fatal(err)
	}

	manager, err := tls.NewManager(config, tmpl, writePathConfig)
	if err != nil {
		log.Fatal(err)
	}

	err = manager.Create(ctx)
	if err != nil {
		log.Fatal(err)
	}

	manager.Watch(ctx)
}
