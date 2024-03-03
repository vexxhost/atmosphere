package util

import "sync"

type OnceValueMap struct {
	functions map[string]*func() error
	lock      *sync.Mutex
}

func NewOnceValueMap() *OnceValueMap {
	return &OnceValueMap{
		functions: make(map[string]*func() error),
		lock:      &sync.Mutex{},
	}
}

func (o *OnceValueMap) Get(key string) *func() error {
	o.lock.Lock()
	defer o.lock.Unlock()

	return o.functions[key]
}

func (o *OnceValueMap) Set(key string, f func() error) *func() error {
	o.lock.Lock()
	defer o.lock.Unlock()

	fn := sync.OnceValue[error](f)
	o.functions[key] = &fn
	return o.functions[key]
}

func (o *OnceValueMap) Do(key string, f func() error) error {
	var fn *func() error

	fn = o.Get(key)
	if fn == nil {
		fn = o.Set(key, f)
	}

	return (*fn)()
}
