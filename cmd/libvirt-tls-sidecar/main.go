// Copyright (c) 2023 VEXXHOST, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

package main

import (
	"context"
	"fmt"
	"os"

	cmmeta "github.com/cert-manager/cert-manager/pkg/apis/meta/v1"
	log "github.com/sirupsen/logrus"
	"k8s.io/client-go/rest"

	"github.com/vexxhost/atmosphere/internal/tls"
)

const (
	EnvVarApiIssuerKind = "API_ISSUER_KIND"
	EnvVarApiIssuerName = "API_ISSUER_NAME"
	EnvVarVncIssuerKind = "VNC_ISSUER_KIND"
	EnvVarVncIssuerName = "VNC_ISSUER_NAME"
)

func main() {
	config, err := rest.InClusterConfig()
	if err != nil {
		log.Fatal(err)
	}

	required := []string{
		EnvVarApiIssuerKind,
		EnvVarApiIssuerName,
		EnvVarVncIssuerKind,
		EnvVarVncIssuerName,
	}

	for _, env := range required {
		if os.Getenv(env) == "" {
			log.Fatal(fmt.Sprintf("missing required environment variable: %s", env))
		}
	}

	ctx := context.Background()
	go createCertificateSpec(ctx, config, tls.LibvirtCertificateTypeAPI)
	go createCertificateSpec(ctx, config, tls.LibvirtCertificateTypeVNC)

	<-ctx.Done()
}

func createCertificateSpec(ctx context.Context, config *rest.Config, certificateType tls.LibvirtCertificateType) {
	var issuerRef cmmeta.ObjectReference
	switch certificateType {
	case tls.LibvirtCertificateTypeAPI:
		issuerRef = cmmeta.ObjectReference{
			Kind: os.Getenv(EnvVarApiIssuerKind),
			Name: os.Getenv(EnvVarApiIssuerName),
		}
	case tls.LibvirtCertificateTypeVNC:
		issuerRef = cmmeta.ObjectReference{
			Kind: os.Getenv(EnvVarVncIssuerKind),
			Name: os.Getenv(EnvVarVncIssuerName),
		}
	}

	spec := &tls.LibvirtCertificateSpec{
		Type:      certificateType,
		IssuerRef: issuerRef,
	}

	manager, err := tls.NewLibvirtManager(config, spec)
	if err != nil {
		log.Fatal(err)
	}

	err = manager.Create(ctx)
	if err != nil {
		log.Fatal(err)
	}

	log.WithFields(log.Fields{
		"certificateType": certificateType,
	}).Info("certificate created")

	go manager.Watch(ctx)
}
