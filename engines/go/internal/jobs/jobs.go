package jobs

import "svl/validator/internal/contracts"

var allowed = map[contracts.JobStatus][]contracts.JobStatus{
	contracts.Queued:  {contracts.Running, contracts.Failed},
	contracts.Running: {contracts.Succeeded, contracts.Failed},
}

// CanTransition: job ki avastha ka sahi badlaav hai ya nahi (Python ke JobStatus ke saath same).
func CanTransition(from, to contracts.JobStatus) bool {
	for _, t := range allowed[from] {
		if t == to {
			return true
		}
	}
	return false
}
