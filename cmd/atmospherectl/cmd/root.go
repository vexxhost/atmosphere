package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"k8s.io/cli-runtime/pkg/genericclioptions"
	_ "k8s.io/client-go/plugin/pkg/client/auth"
)

var (
	kubeconfigArgs = genericclioptions.NewConfigFlags(false)

	rootCmd = &cobra.Command{
		Use: "atmospherectl",
	}
)

func init() {
	kubeconfigArgs.AddFlags(rootCmd.PersistentFlags())
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
