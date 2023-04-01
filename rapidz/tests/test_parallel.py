from concurrent.futures import Future
from operator import add
import time

from tornado import gen
import pytest


from distributed.utils_test import inc, slowinc  # flake8: noqa, gen_test,
from rapidz import Stream
from rapidz.parallel import scatter
from rapidz.clients import thread_default_client

gen_test = pytest.mark.gen_test

test_params = ["thread", thread_default_client]


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_scatter_gather(backend):
    source = Stream(asynchronous=True)
    futures = scatter(source, backend=backend)
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == list(range(5))
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_map(backend):
    source = Stream(asynchronous=True)
    futures = scatter(source, backend=backend).map(inc)
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == [1, 2, 3, 4, 5]
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_scan(backend):
    source = Stream(asynchronous=True)
    futures = scatter(source, backend=backend).map(inc).scan(add)
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == [1, 3, 6, 10, 15]
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_scan_state(backend):
    source = Stream(asynchronous=True)

    def f(acc, i):
        acc = acc + i
        return acc, acc

    L = (
        scatter(source, backend=backend)
        .scan(f, returns_state=True)
        .gather()
        .sink_to_list()
    )
    for i in range(3):
        yield source.emit(i)

    assert L == [0, 1, 3]


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_zip(backend):
    a = Stream(asynchronous=True)
    b = Stream(asynchronous=True)
    c = scatter(a, backend=backend).zip(scatter(b, backend=backend))

    L = c.gather().sink_to_list()

    yield a.emit(1)
    yield b.emit("a")
    yield a.emit(2)
    yield b.emit("b")

    assert L == [(1, "a"), (2, "b")]


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_starmap(backend):
    def add(x, y, z=0):
        return x + y + z

    source = Stream(asynchronous=True)
    futures = scatter(source, backend=backend).starmap(add, z=10)
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit((i, i))

    assert len(L) == len(futures_L)
    assert L == [10, 12, 14, 16, 18]


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_starmap_args(backend):
    def add(x, y, z=0):
        return x + y + z

    source = Stream(asynchronous=True)
    futures = scatter(source, backend=backend).starmap(add, 10)
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert len(L) == len(futures_L)
    assert L == [i + 10 for i in range(5)]


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_buffer2(backend):
    source = Stream(asynchronous=True)
    futures = scatter(source, backend=backend)
    futures_L = futures.sink_to_list()
    L = futures.buffer(10).gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)
    assert len(futures_L) == 5
    while len(L) < len(futures_L):
        yield gen.sleep(.01)

    assert L == [0, 1, 2, 3, 4]
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@pytest.mark.slow
@gen_test()
def test_buffer(backend):
    source = Stream(asynchronous=True)
    L = (
        source.scatter(backend=backend)
        .map(slowinc, delay=0.5)
        .buffer(5)
        .gather()
        .sink_to_list()
    )

    start = time.time()
    for i in range(5):
        yield source.emit(i)
    end = time.time()
    assert end - start < 0.5

    for i in range(5, 10):
        yield source.emit(i)

    end2 = time.time()
    assert end2 - start > (0.5 / 3)

    while len(L) < 10:
        yield gen.sleep(0.01)
        assert time.time() - start < 5

    assert L == list(map(inc, range(10)))


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter(backend):
    source = Stream(asynchronous=True)
    futures = scatter(source, backend=backend).filter(lambda x: x % 2 == 0)
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == [0, 2, 4]
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter_buffer(backend):
    source = Stream(asynchronous=True)
    futures = scatter(source, backend=backend).filter(lambda x: x % 2 == 0)
    futures_L = futures.sink_to_list()
    L = futures.buffer(10).gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)
    while len(L) < 3:
        yield gen.sleep(.01)

    assert L == [0, 2, 4]
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter_map(backend):
    source = Stream(asynchronous=True)
    futures = (
        scatter(source, backend=backend).filter(lambda x: x % 2 == 0).map(inc)
    )
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == [1, 3, 5]
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter_starmap(backend):
    source = Stream(asynchronous=True)
    futures1 = scatter(source, backend=backend).filter(lambda x: x[1] % 2 == 0)
    futures = futures1.starmap(add)
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit((i, i))

    assert L == [0, 4, 8]
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter_pluck(backend):
    source = Stream(asynchronous=True)
    futures1 = scatter(source, backend=backend).filter(lambda x: x[1] % 2 == 0)
    futures = futures1.pluck(0)
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit((i, i))

    assert L == [0, 2, 4]
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_filter_zip(backend):
    source = Stream(asynchronous=True)
    s = scatter(source, backend=backend)
    futures = s.filter(lambda x: x % 2 == 0).zip(s)
    futures_L = futures.sink_to_list()
    L = futures.gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)

    assert L == [(a, a) for a in [0, 2, 4]]
    assert all(isinstance(f[0], Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test()
def test_double_scatter(backend):
    source1 = Stream(asynchronous=True)
    source2 = Stream(asynchronous=True)
    sm = (
        source1.scatter(backend=backend)
        .zip(source2.scatter(backend=backend))
        .starmap(add)
    )
    futures_L = sm.sink_to_list()
    r = sm.buffer(10).gather()
    L = r.sink_to_list()

    for i in range(5):
        yield source1.emit(i)
        yield source2.emit(i)

    while len(L) < len(futures_L):
        yield gen.sleep(.01)

    assert L == [i + i for i in range(5)]
    assert all(isinstance(f, Future) for f in futures_L)


@pytest.mark.parametrize("backend", test_params)
@gen_test
def test_pluck(backend):
    source = Stream(asynchronous=True)
    L = source.scatter(backend=backend).pluck(0).gather().sink_to_list()

    for i in range(5):
        yield source.emit((i, i))

    assert L == list(range(5))


@pytest.mark.parametrize("backend", test_params)
@gen_test
def test_combined_latest(backend):
    def delay(x):
        time.sleep(.5)
        return x

    source = Stream(asynchronous=True)
    source2 = Stream(asynchronous=True)
    futures = (
        source.scatter(backend=backend)
        .map(delay)
        .combine_latest(source2.scatter(backend=backend), emit_on=1)
    )
    futures_L = futures.sink_to_list()
    L = futures.buffer(10).gather().sink_to_list()

    for i in range(5):
        yield source.emit(i)
        yield source.emit(i)
        yield source2.emit(i)

    while len(L) < len(futures_L):
        yield gen.sleep(.01)
    assert L == [(i, i) for i in range(5)]
