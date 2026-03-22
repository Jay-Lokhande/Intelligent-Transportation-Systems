from its_route_planner.pareto import dominates, insert_nondominated


def test_dominates():
    assert dominates((1.0, 2.0, 3.0), (2.0, 3.0, 4.0))
    assert not dominates((1.0, 2.0, 3.0), (1.0, 2.0, 3.0))
    assert not dominates((1.0, 5.0, 0.0), (5.0, 1.0, 0.0))


def test_insert_nondominated():
    labels: list[tuple[float, float, float]] = []
    assert insert_nondominated(labels, (1.0, 5.0, 0.0))
    assert insert_nondominated(labels, (5.0, 1.0, 0.0))
    assert len(labels) == 2
    assert not insert_nondominated(labels, (6.0, 2.0, 0.0))
    assert insert_nondominated(labels, (1.0, 1.0, 0.0))
    assert len(labels) == 1
    assert labels[0] == (1.0, 1.0, 0.0)
