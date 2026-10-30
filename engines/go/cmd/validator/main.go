package main

import (
	"fmt"

	"svl/validator/internal/contracts"
	"svl/validator/internal/validation"
)

func main() {
	fmt.Println("validator ready; SUCCEEDED terminal =", validation.IsTerminal(contracts.Succeeded))
}
