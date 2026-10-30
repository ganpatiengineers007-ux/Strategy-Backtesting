from registry.registry import Registry


def test_two_strategies_registered():
    assert {'gamma_blast', 'three_pm_momentum'} <= set(Registry().discover())
