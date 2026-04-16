package main

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	"github.com/vexxhost/atmosphere/internal/wait"
)

func main() {
	var (
		namespace  string
		timeout    time.Duration
		kubeconfig string
		forFlag    string
	)

	rootCmd := &cobra.Command{
		Use:   "atmosphere-wait",
		Short: "Wait for Kubernetes resources using Watch API",
		Long: `Wait for Kubernetes resources to reach a desired state using the
Watch API for instant notification instead of polling.`,
	}

	rootCmd.PersistentFlags().StringVarP(&namespace, "namespace", "n", "default", "Kubernetes namespace")
	rootCmd.PersistentFlags().DurationVar(&timeout, "timeout", 600*time.Second, "Timeout duration")
	rootCmd.PersistentFlags().StringVar(&kubeconfig, "kubeconfig", "", "Path to kubeconfig file")
	rootCmd.PersistentFlags().StringVar(&forFlag, "for", "", "Condition to wait for (e.g., condition=Available)")

	rootCmd.AddCommand(&cobra.Command{
		Use:   "deployment <name>",
		Short: "Wait for a Deployment to meet a condition",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			condType, condStatus := parseConditionFlag(forFlag)
			cs, err := wait.NewClientset(kubeconfig)
			if err != nil {
				return err
			}
			fmt.Fprintf(os.Stderr, "Waiting for deployment %s/%s condition %s=%s...\n", namespace, args[0], condType, condStatus)
			if err := wait.ForDeployment(cmd.Context(), cs, namespace, args[0], condType, condStatus, timeout); err != nil {
				return err
			}
			fmt.Fprintf(os.Stderr, "condition met\n")
			return nil
		},
	})

	rootCmd.AddCommand(&cobra.Command{
		Use:   "statefulset <name>",
		Short: "Wait for a StatefulSet to have all replicas ready",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			cs, err := wait.NewClientset(kubeconfig)
			if err != nil {
				return err
			}
			fmt.Fprintf(os.Stderr, "Waiting for statefulset %s/%s to be ready...\n", namespace, args[0])
			if err := wait.ForStatefulSetReady(cmd.Context(), cs, namespace, args[0], timeout); err != nil {
				return err
			}
			fmt.Fprintf(os.Stderr, "ready\n")
			return nil
		},
	})

	rootCmd.AddCommand(&cobra.Command{
		Use:   "secret <name>",
		Short: "Wait for a Secret to exist",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			cs, err := wait.NewClientset(kubeconfig)
			if err != nil {
				return err
			}
			fmt.Fprintf(os.Stderr, "Waiting for secret %s/%s...\n", namespace, args[0])
			if err := wait.ForSecret(cmd.Context(), cs, namespace, args[0], timeout); err != nil {
				return err
			}
			fmt.Fprintf(os.Stderr, "exists\n")
			return nil
		},
	})

	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}

func parseConditionFlag(flag string) (condType, condStatus string) {
	if flag == "" {
		return "Available", "True"
	}
	if len(flag) > 10 && flag[:10] == "condition=" {
		rest := flag[10:]
		for i := 0; i < len(rest); i++ {
			if rest[i] == '=' {
				return rest[:i], rest[i+1:]
			}
		}
		return rest, "True"
	}
	return flag, "True"
}
