import pytest
from distributed.utils_test import (
    gen_cluster,
)  # flake8: noqa
from rapidz import Stream
from rapidz.parallel import scatter, NULL_COMPUTE


@gen_cluster(client=True)
def test_filter_combine_latest(c, s, a, b):
    source = Stream(asynchronous=True)

    s = scatter(source)
    futures = s.filter(lambda x: x % 2 == 0).combine_latest(s)
    L = futures.gather().sink_to_list()

    presents = source.filter(lambda x: x % 2 == 0).combine_latest(source)

    LL = presents.sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == LL

@pytest.mark.xfail
@gen_cluster(client=True)
def test_filter_combine_latest_odd(c, s, a, b):
    source = Stream(asynchronous=True)

    s = scatter(source)
    futures = s.filter(lambda x: x % 2 == 1).combine_latest(s)
    L = futures.gather().sink_to_list()

    presents = source.filter(lambda x: x % 2 == 1).combine_latest(source)

    LL = presents.sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == LL


@gen_cluster(client=True)
def test_filter_combine_latest_emit_on(c, s, a, b):
    source = Stream(asynchronous=True)

    s = scatter(source)
    futures = s.filter(lambda x: x % 2 == 1).combine_latest(s, emit_on=0)
    L = futures.gather().sink_to_list()

    presents = source.filter(lambda x: x % 2 == 1).combine_latest(source,
                                                                  emit_on=0)

    LL = presents.sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == LL


@gen_cluster(client=True)
def test_filter_combine_latest_triple(c, s, a, b):
    source = Stream(asynchronous=True)

    s = scatter(source)
    futures = s.filter(lambda x: x % 3 == 1).combine_latest(s)
    L = futures.gather().sink_to_list()

    presents = source.filter(lambda x: x % 3 == 1).combine_latest(source)

    LL = presents.sink_to_list()

    for i in range(10):
        yield source.emit(i)

    assert L == LL


@gen_cluster(client=True)
def test_unique(c, s, a, b):
    source = Stream(asynchronous=True)

    def acc_func(state, x):
        if x in state:
            return state, NULL_COMPUTE
        state.append(x)
        return state, x

    s = scatter(source)
    futures = s.accumulate(acc_func, start=[], returns_state=True)
    L = futures.gather().sink_to_list()

    presents = source.unique()

    LL = presents.sink_to_list()

    for i in range(10):
        if i % 2 == 1:
            i = i - 1
        yield source.emit(i)

    assert L == LL
