validate:
	./scripts/validate_repo.sh

test:
	python -m pytest -q

demo:
	python -m cli.main demo
