package steps

import "context"

type Step interface {
	Execute(context.Context) error
	Validate(context.Context) error
}
