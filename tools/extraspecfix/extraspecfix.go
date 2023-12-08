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
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"

	"github.com/vexxhost/atmosphere/internal/portforwardutil"

	"github.com/erikgeiser/promptkit/confirmation"
	"github.com/nsf/jsondiff"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"gopkg.in/ini.v1"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/tools/portforward"
	"k8s.io/client-go/util/homedir"
)

var (
	kubeconfig string

	portForward   *portforward.PortForwarder
	db            *gorm.DB
	instanceExtra InstanceExtra
	key           string

	flavor *InstanceExtraFlavor

	rootCmd = &cobra.Command{
		Use:   "extraspecfix",
		Short: "Utility to fix extra_specs in the database",
		PersistentPreRun: func(cmd *cobra.Command, args []string) {
			instanceUUID := args[0]
			key = args[1]

			config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
			if err != nil {
				log.Fatal(err)
			}

			databaseConnection, err := GetDatabaseConnection(config)
			if err != nil {
				log.Fatal(err)
			}

			portForward, err = databaseConnection.PortForwarder()
			if err != nil {
				log.Fatal(err)
			}

			go func() {
				err := portForward.ForwardPorts()
				if err != nil {
					log.Fatal(err)
				}
			}()

			<-portForward.Ready

			dsn := fmt.Sprintf(
				"%s:%s@tcp(%s:%d)/%s",
				databaseConnection.Username,
				databaseConnection.Password,
				"localhost",
				3306,
				databaseConnection.Database,
			)
			// TODO: write a custom dialer?
			db, err = gorm.Open(mysql.Open(dsn), &gorm.Config{})
			if err != nil {
				log.Fatal(err)
			}

			tx := db.Where(&InstanceExtra{InstanceUUID: instanceUUID}).First(&instanceExtra)
			if tx.Error != nil {
				log.Fatal(err)
			}

			err = StrictUnmarshal([]byte(instanceExtra.Flavor), &flavor)
			if err != nil {
				log.Fatal(err)
			}
		},
		PersistentPostRun: func(cmd *cobra.Command, args []string) {
			serializedFlavor, err := json.Marshal(flavor)
			if err != nil {
				log.Fatal(err)
			}

			diffOpts := jsondiff.DefaultConsoleOptions()
			diff, output := jsondiff.Compare(
				[]byte(instanceExtra.Flavor),
				[]byte(serializedFlavor),
				&diffOpts,
			)

			if diff == jsondiff.FullMatch {
				log.Info("no changes")
				os.Exit(0)
			}

			fmt.Println(output)

			input := confirmation.New("Are you ready?", confirmation.Undecided)
			ready, err := input.RunPrompt()
			if err != nil || !ready {
				log.Info("operation cancelled")
				os.Exit(0)
			}

			db.Model(&instanceExtra).Update("flavor", string(serializedFlavor))
			portForward.Close()
		},
	}
	setCmd = &cobra.Command{
		Use:   "set [instance uuid] [key] [value]",
		Short: "Set an extra spec on an instance",
		Args:  cobra.MatchAll(cobra.ExactArgs(3), cobra.OnlyValidArgs),
		Run: func(cmd *cobra.Command, args []string) {
			value := args[2]
			flavor.Current.Data.ExtraSpecs[key] = value
		},
	}
)

func init() {
	homedir := homedir.HomeDir()
	rootCmd.PersistentFlags().StringVar(
		&kubeconfig,
		"kubeconfig",
		filepath.Join(homedir, ".kube", "config"),
		"absolute path to the kubeconfig file",
	)

	rootCmd.AddCommand(setCmd)
}

type InstanceExtra struct {
	ID           uint   `gorm:"primaryKey"`
	InstanceUUID string `gorm:"column:instance_uuid"`
	Flavor       string `gorm:"column:flavor"`
}

type InstanceExtraFlavor struct {
	Old     *InstanceExtraFlavorObject `json:"old"`
	Current *InstanceExtraFlavorObject `json:"cur"`
	New     *InstanceExtraFlavorObject `json:"new"`
}

type InstanceExtraFlavorObject struct {
	Name      string                        `json:"nova_object.name"`
	Namespace string                        `json:"nova_object.namespace"`
	Version   string                        `json:"nova_object.version"`
	Changes   []string                      `json:"nova_object.changes"`
	Data      InstanceExtraFlavorObjectData `json:"nova_object.data"`
}

type InstanceExtraFlavorObjectData struct {
	ID          int64             `json:"id"`
	FlavorID    string            `json:"flavorid"`
	Name        string            `json:"name"`
	Description *string           `json:"description"`
	VCPUs       int64             `json:"vcpus"`
	VCPUWeight  int64             `json:"vcpu_weight"`
	MemoryMB    int64             `json:"memory_mb"`
	RootGB      int64             `json:"root_gb"`
	EphemeralGB int64             `json:"ephemeral_gb"`
	Swap        int64             `json:"swap"`
	RxTxFactor  json.Number       `json:"rxtx_factor"`
	IsPublic    bool              `json:"is_public"`
	Disabled    bool              `json:"disabled"`
	ExtraSpecs  map[string]string `json:"extra_specs"`
	CreatedAt   string            `json:"created_at"`
	UpdatedAt   *string           `json:"updated_at"`
	DeletedAt   *string           `json:"deleted_at"`
	Deleted     bool              `json:"deleted"`
}

func (InstanceExtra) TableName() string {
	return "instance_extra"
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func StrictUnmarshal(data []byte, v interface{}) error {
	dec := json.NewDecoder(bytes.NewReader(data))
	dec.DisallowUnknownFields()
	return dec.Decode(v)
}

type DatabaseConnection struct {
	config    *rest.Config
	clientset *kubernetes.Clientset
	Username  string
	Password  string
	Service   *v1.Service
	Database  string
}

func (db *DatabaseConnection) PortForwarder() (*portforward.PortForwarder, error) {
	return portforwardutil.NewForService(db.config, db.Service, 3306)
}

func GetDatabaseConnection(config *rest.Config) (*DatabaseConnection, error) {
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	secret, err := clientset.CoreV1().Secrets("openstack").Get(
		context.TODO(),
		"nova-etc",
		metav1.GetOptions{},
	)
	if err != nil {
		return nil, err
	}

	cfg, err := ini.Load(secret.Data["nova.conf"])
	if err != nil {
		return nil, err
	}

	connection := cfg.Section("database").Key("connection").String()

	parsedConnection, err := url.Parse(connection)
	if err != nil {
		return nil, err
	}

	username := parsedConnection.User.Username()
	password, _ := parsedConnection.User.Password()
	database := strings.TrimLeft(parsedConnection.Path, "/")

	hostname := parsedConnection.Hostname()
	parts := strings.SplitN(hostname, ".", 3)
	service := &v1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      parts[0],
			Namespace: parts[1],
		},
	}

	return &DatabaseConnection{
		config:    config,
		clientset: clientset,
		Username:  username,
		Password:  password,
		Service:   service,
		Database:  database,
	}, nil
}
