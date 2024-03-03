package deploy

import (
	"context"
	"crypto/sha1"
	"fmt"
	"slices"
	"sync"

	log "github.com/sirupsen/logrus"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/utils/ptr"
	"sigs.k8s.io/controller-runtime/pkg/client"

	"github.com/vexxhost/atmosphere/internal/deploy/util"
)

type ImageManager struct {
	functions  *util.OnceValueMap
	lock       *sync.Mutex
	logger     *log.Entry
	managerSet *ManagerSet
}

func NewImageManager(managerSet *ManagerSet) *ImageManager {
	return &ImageManager{
		functions:  util.NewOnceValueMap(),
		lock:       &sync.Mutex{},
		logger:     log.WithField("manager", "image"),
		managerSet: managerSet,
	}
}

func (m *ImageManager) Pull(ctx context.Context, imageName string, nodeSelector map[string]string) error {
	logger := m.logger.WithFields(log.Fields{
		"image": imageName,
	})

	return m.functions.Do(imageName, func() error {
		if err := m.managerSet.Namespace.Create(ctx, "openstack"); err != nil {
			return err
		}

		var nodeList corev1.NodeList
		err := m.managerSet.Client.List(ctx, &nodeList, &client.ListOptions{
			LabelSelector: labels.SelectorFromValidatedSet(nodeSelector),
		})
		if err != nil {
			return err
		}

		if len(nodeList.Items) == 0 {
			err := fmt.Errorf("no matching nodes found with %s", nodeSelector)

			logger.Error(err)
			return err
		}

		nodeNeedsPull := map[string]bool{}
		imageNeedsPull := false
		for _, node := range nodeList.Items {
			nodeNeedsPull[node.Name] = true

			for _, image := range node.Status.Images {
				if slices.Contains(image.Names, imageName) {
					nodeNeedsPull[node.Name] = false
					break
				}
			}

			if nodeNeedsPull[node.Name] == true {
				imageNeedsPull = true
				break
			}
		}

		if imageNeedsPull == false {
			logger.Info("Image already pulled")
			return nil
		}

		logger.Info("Pulling image")

		if m.managerSet.Options.DryRun == false {
			hash := sha1.Sum([]byte(imageName))
			podLabels := map[string]string{
				"application": "atmosphere",
				"component":   "image-puller",
				"image":       fmt.Sprintf("%x", hash[:]),
			}

			ds := appsv1.DaemonSet{
				ObjectMeta: metav1.ObjectMeta{
					GenerateName: "image-puller-",
					Namespace:    "openstack",
				},
				Spec: appsv1.DaemonSetSpec{
					Selector: &metav1.LabelSelector{
						MatchLabels: podLabels,
					},
					Template: corev1.PodTemplateSpec{
						ObjectMeta: metav1.ObjectMeta{
							Labels: podLabels,
						},
						Spec: corev1.PodSpec{
							Containers: []corev1.Container{
								{
									Name:    "image",
									Image:   imageName,
									Command: []string{"sleep", "3600"},
								},
							},
							NodeSelector:                  nodeSelector,
							TerminationGracePeriodSeconds: ptr.To(int64(0)),
						},
					},
				},
			}

			err := m.managerSet.Client.Create(ctx, &ds)
			if err != nil {
				logger.Error(err)
				return err
			}
			defer m.managerSet.Client.Delete(ctx, &ds)

			if err := util.WaitForDaemonSet(ctx, m.managerSet.Client, client.ObjectKey{
				Name:      ds.Name,
				Namespace: ds.Namespace,
			}); err != nil {
				logger.Error(err)
				return err
			}
		}

		logger.Info("Pulled image")

		return nil
	})
}
