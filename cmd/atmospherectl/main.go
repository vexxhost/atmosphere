package main

import (
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"

	"github.com/vexxhost/atmosphere/cmd/atmospherectl/cmd"
)

func init() {
	log.SetLogger(zap.New())
}

func main() {
	cmd.Execute()
}
