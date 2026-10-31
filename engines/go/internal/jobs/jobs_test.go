package jobs

import (
	"testing"

	"svl/validator/internal/contracts"
)

func TestCanTransition(t *testing.T) {
	if !CanTransition(contracts.Queued, contracts.Running) || !CanTransition(contracts.Running, contracts.Succeeded) {
		t.Fatal("QUEUED->RUNNING aur RUNNING->SUCCEEDED allowed hone chahiye")
	}
	if CanTransition(contracts.Succeeded, contracts.Running) || CanTransition(contracts.Queued, contracts.Succeeded) {
		t.Fatal("ye transitions allowed nahi")
	}
}
