package steps

import (
	"context"

	log "github.com/sirupsen/logrus"
)

type Step interface {
	Logger() *log.Entry
	Execute(context.Context) error
	Validate(context.Context) (*ValidationResult, error)
}
