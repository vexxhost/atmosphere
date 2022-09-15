package phases

import (
	"context"
	"sync"

	"github.com/vexxhost/atmosphere/internal/pkg/deployment/steps"
)

type Phase struct {
	Steps []steps.Step
}

func (p *Phase) Execute(ctx context.Context, diff bool) error {
	var wg sync.WaitGroup

	for _, step := range p.Steps {
		wg.Add(1)
		go step.Execute(ctx, diff, &wg)
	}

	wg.Wait()

	return nil
}

func (p *Phase) Validate(ctx context.Context, diff bool) error {
	for _, step := range p.Steps {
		if _, err := step.Validate(ctx, diff); err != nil {
			return err
		}
	}

	return nil
}
