package observability

import "sync"

// Counters: thread-safe naam-wale counter.
type Counters struct {
	mu sync.Mutex
	m  map[string]int
}

func NewCounters() *Counters { return &Counters{m: map[string]int{}} }

func (c *Counters) Inc(name string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.m[name]++
}

func (c *Counters) Get(name string) int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.m[name]
}
