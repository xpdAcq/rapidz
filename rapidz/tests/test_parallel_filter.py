from concurrent.futures import Future
from operator import add
import time

from tornado import gen
import pytest

from distributed.utils_test import inc, slowinc  # flake8: noqa
from rapidz import Stream
from rapidz.parallel import scatter
from rapidz.clients import thread_default_client, result_maybe

gen_test = pytest.mark.gen_test

test_params = ["thread",
               thread_default_client
               ]


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter_combine_latest(backend):
    source = Stream(asynchronous=True)

    s = scatter(source, backend=backend)
    futures = s.filter(lambda x: x % 2 == 0).combine_latest(s)
    L = futures.gather().sink_to_list()

    presents = source.filter(lambda x: x % 2 == 0).combine_latest(source)

    LL = presents.sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == LL
    s.default_client().shutdown()


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter_combine_latest_odd(backend):
    source = Stream(asynchronous=True)

    s = scatter(source, backend=backend)
    futures = s.filter(lambda x: x % 2 == 1).combine_latest(s)
    L = futures.gather().sink_to_list()

    presents = source.filter(lambda x: x % 2 == 1).combine_latest(source)

    LL = presents.sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == LL
    s.default_client().shutdown()


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter_combine_latest_emit_on(backend):
    source = Stream(asynchronous=True)

    s = scatter(source, backend=backend)
    futures = s.filter(lambda x: x % 2 == 1).combine_latest(s, emit_on=0)
    L = futures.gather().sink_to_list()

    presents = source.filter(lambda x: x % 2 == 1).combine_latest(source,
                                                                  emit_on=0)

    LL = presents.sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == LL
    s.default_client().shutdown()


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter_combine_latest_triple(backend):
    source = Stream(asynchronous=True)

    s = scatter(source, backend=backend)
    futures = s.filter(lambda x: x % 3 == 1).combine_latest(s)
    L = futures.gather().sink_to_list()

    presents = source.filter(lambda x: x % 3 == 1).combine_latest(source)

    LL = presents.sink_to_list()

    for i in range(10):
        yield source.emit(i)

    assert L == LL
    s.default_client().shutdown()


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_unique(backend):
    source = Stream(asynchronous=True)

    s = scatter(source, backend=backend)
    futures = s.unique()
    L = futures.gather().sink_to_list()

    presents = source.unique()

    LL = presents.sink_to_list()

    for i in range(10):
        if i % 2 == 1:
            i = i - 1
        yield source.emit(i)

    assert L == LL
    s.default_client().shutdown()
