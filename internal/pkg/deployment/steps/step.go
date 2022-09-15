package steps

import (
	"context"
	"sync"

	log "github.com/sirupsen/logrus"
)

type Step interface {
	Logger() *log.Entry
	Execute(context.Context, bool, *sync.WaitGroup) error
	Validate(context.Context, bool) (*ValidationResult, error)
}
