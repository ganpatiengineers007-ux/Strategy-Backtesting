from backend.api.common import guarded, make_router
from backend.services import dataset_service


def list_all():
    return dataset_service.list_datasets()


router = make_router()
if router is not None:
    router.get("/datasets")(guarded(list_all))
