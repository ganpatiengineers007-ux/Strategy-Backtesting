from persistence.repositories import RunRepository
from registry.registry import Registry


def get_registry():
    return Registry()


def get_repository(root="runs"):
    return RunRepository(root)
