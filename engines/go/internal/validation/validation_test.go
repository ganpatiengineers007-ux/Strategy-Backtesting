package validation

import (
	"testing"

	"svl/validator/internal/contracts"
)

func TestIsTerminal(t *testing.T) {
	if !IsTerminal(contracts.Succeeded) || !IsTerminal(contracts.Failed) {
		t.Fatal("SUCCEEDED/FAILED terminal hone chahiye")
	}
	if IsTerminal(contracts.Queued) || IsTerminal(contracts.Running) {
		t.Fatal("QUEUED/RUNNING terminal nahi")
	}
}
