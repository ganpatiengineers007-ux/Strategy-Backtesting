package validation

import "svl/validator/internal/contracts"

// IsTerminal: job ki antim avastha hai ya nahi.
func IsTerminal(s contracts.JobStatus) bool {
	return s == contracts.Succeeded || s == contracts.Failed
}
