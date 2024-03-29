# flake8: noqa
import asyncio
from time import time
from distributed.utils_test import loop, inc, loop_in_thread, cleanup  # noqa
from tornado import gen

from rapidz import Stream


def test_await_syntax():  # noqa
    L = []

    async def write(x):
        await gen.sleep(0.1)
        L.append(x)

    async def f():
        source = Stream(asynchronous=True)
        source.map(inc).buffer(3).sink(write)

        start = time()
        for x in range(6):
            await source.emit(x)
        stop = time()

        assert 0.2 < stop - start < 0.4
        assert 2 <= len(L) <= 4

    asyncio.run(f())
