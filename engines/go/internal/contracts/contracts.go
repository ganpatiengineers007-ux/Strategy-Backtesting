package contracts

type JobStatus string

const (
	Queued    JobStatus = "QUEUED"
	Running   JobStatus = "RUNNING"
	Succeeded JobStatus = "SUCCEEDED"
	Failed    JobStatus = "FAILED"
)
