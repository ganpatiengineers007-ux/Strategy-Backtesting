from backend.api.common import guarded, make_router
from backend.services import strategy_service


def list_all():
    return strategy_service.list_strategies()


def get_one(strategy_id: str):
    return strategy_service.get_strategy(strategy_id)


router = make_router()
if router is not None:
    router.get("/strategies")(guarded(list_all))
    router.get("/strategies/{strategy_id}")(guarded(get_one))
