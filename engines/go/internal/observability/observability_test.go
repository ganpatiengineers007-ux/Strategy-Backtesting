package observability

import "testing"

func TestCounters(t *testing.T) {
	c := NewCounters()
	c.Inc("runs")
	c.Inc("runs")
	if c.Get("runs") != 2 || c.Get("none") != 0 {
		t.Fatal("counter galat")
	}
}
