package steps

import (
	"context"
	"sync"

	log "github.com/sirupsen/logrus"
)

type Step interface {
	Logger() *log.Entry
	Execute(context.Context, *sync.WaitGroup) error
	Validate(context.Context) (*ValidationResult, error)
}
