package net

import (
	"os"
	"os/exec"
)

func Hostname() (string, error) {
	return os.Hostname()
}

func FQDN() (string, error) {
	cmd := exec.Command("/bin/hostname", "--fqdn")
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}

	return string(out), nil
}
