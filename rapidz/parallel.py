from concurrent.futures import Future
from functools import wraps
from builtins import zip as szip

from rapidz import apply
from rapidz.core import _truthy, args_kwargs, move_to_first
from rapidz.core import get_io_loop
from rapidz.clients import DEFAULT_BACKENDS, FILL_COLOR_LOOKUP
from operator import getitem

from tornado import gen

from . import core, sources
from .core import Stream

from collections import Sequence, deque, Iterable
from toolz import pluck as _pluck

NULL_COMPUTE = "~~NULL_COMPUTE~~"


def future_chain(present_future, past_future=None):
    # If the most recent compute result is NULL then return a previous one
    if present_future == NULL_COMPUTE:
        if past_future is None:
            print('hi')
            return NULL_COMPUTE
        else:
            return past_future
    return present_future


def return_null(func):
    @wraps(func)
    def inner(x, *args, **kwargs):
        tv = func(x, *args, **kwargs)
        if tv:
            return x
        else:
            return NULL_COMPUTE

    return inner


def filter_null_wrapper(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if any(a == NULL_COMPUTE for a in args) or any(
            v == NULL_COMPUTE for v in kwargs.values()
        ):
            return NULL_COMPUTE
        else:
            return func(*args, **kwargs)

    return inner


class ParallelStream(Stream):
    """ A Parallel stream using multiple backends

    This object is fully compliant with the ``rapidz.core.Stream`` object but
    uses a client for execution.  Operations like ``map`` and
    ``accumulate`` submit functions to run on the client instance
    and pass around futures.
    Time-based operations like ``timed_window``, buffer, and so on operate as
    normal.

    Typically one transfers between normal Stream and ParallelStream
    objects using the ``Stream.scatter()`` and ``ParallelStream.gather()`` methods.

    Examples
    --------
    >>> from dask.distributed import Client
    >>> client = Client()

    >>> from rapidz import Stream
    >>> source = Stream()
    >>> source.scatter().map(func).accumulate(binop).gather().sink(...)

    This runs on thread backends
    >>> from rapidz import Stream
    >>> source = Stream()
    >>> source.scatter(backend='thread').map(func).accumulate(binop).gather().sink(...)

    ParallelStream also supports arbitrary backends, the backend must provide
    a function which returns the `Client` like object to be used. The same
    `Client` like object must be returned by the function so that all the nodes
    can interact with the same resource pool.
    >>> import distributed
    >>> source = Stream()
    >>> (source.scatter(backend=distributed.default_client).map(func).accumulate(binop).gather().sink(...))

    See Also
    --------
    dask.distributed.Client
    """

    def __init__(self, *args, backend="dask", **kwargs):
        super().__init__(*args, **kwargs)
        self._graphviz_fillcolor = FILL_COLOR_LOOKUP.get(backend, "chartreuse")
        upstream_backends = set(
            [getattr(u, "default_client", None) for u in self.upstreams]
        )
        if None in upstream_backends:
            upstream_backends.remove(None)
        if len(upstream_backends) > 1:
            raise RuntimeError("Mixing backends is not supported")
        elif upstream_backends:
            self.default_client = upstream_backends.pop()
        else:
            self.default_client = DEFAULT_BACKENDS.get(backend, backend)
        if "loop" not in kwargs and getattr(
            self.default_client(), "loop", None
        ):
            loop = self.default_client().loop
            self._set_loop(loop)
            if kwargs.get("ensure_io_loop", False) and not self.loop:
                self._set_asynchronous(False)
            if self.loop is None and self.asynchronous is not None:
                self._set_loop(get_io_loop(self.asynchronous))


@args_kwargs
@core.Stream.register_api()
@ParallelStream.register_api()
class scatter(ParallelStream):
    @gen.coroutine
    def update(self, x, who=None):
        client = self.default_client()
        future = yield client.scatter(x, asynchronous=True)
        f = yield self._emit(future)
        raise gen.Return(f)


@args_kwargs
@ParallelStream.register_api()
class gather(core.Stream):
    """ Wait on and gather results from ParallelStream to local Stream

    This waits on every result in the stream and then gathers that result back
    to the local stream.  Warning, this can restrict parallelism.  It is common
    to combine a ``gather()`` node with a ``buffer()`` to allow unfinished
    futures to pile up.

    Examples
    --------
    >>> local_stream = dask_stream.buffer(20).gather()

    See Also
    --------
    buffer
    scatter
    """

    def __init__(self, *args, backend="dask", **kwargs):
        super().__init__(*args, **kwargs)
        upstream_backends = set(
            [getattr(u, "default_client", None) for u in self.upstreams]
        )
        if None in upstream_backends:
            upstream_backends.remove(None)
        if len(upstream_backends) > 1:
            raise RuntimeError("Mixing backends is not supported")
        elif upstream_backends:
            self.default_client = upstream_backends.pop()
        else:
            self.default_client = DEFAULT_BACKENDS.get(backend, backend)
        if "loop" not in kwargs and getattr(
            self.default_client(), "loop", None
        ):
            loop = self.default_client().loop
            self._set_loop(loop)
            if kwargs.get("ensure_io_loop", False) and not self.loop:
                self._set_asynchronous(False)
            if self.loop is None and self.asynchronous is not None:
                self._set_loop(get_io_loop(self.asynchronous))

    @gen.coroutine
    def update(self, x, who=None):
        client = self.default_client()
        result = yield client.gather(x, asynchronous=True)
        if (
            not (
                isinstance(result, Sequence)
                and any(r == NULL_COMPUTE for r in result)
            )
            and result != NULL_COMPUTE
        ):
            result2 = yield self._emit(result)
            raise gen.Return(result2)


@args_kwargs
@ParallelStream.register_api()
class map(ParallelStream):
    def __init__(self, upstream, func, *args, **kwargs):
        self.func = filter_null_wrapper(func)
        stream_name = kwargs.pop("stream_name", None)
        self.kwargs = kwargs
        self.args = args

        ParallelStream.__init__(self, upstream, stream_name=stream_name)

    def update(self, x, who=None):
        client = self.default_client()
        result = client.submit(self.func, x, *self.args, **self.kwargs)
        return self._emit(result)


@args_kwargs
@ParallelStream.register_api()
class accumulate(ParallelStream):
    def __init__(
        self,
        upstream,
        func,
        start=core.no_default,
        returns_state=False,
        **kwargs
    ):
        self.func = filter_null_wrapper(func)
        self.state = start
        self.returns_state = returns_state
        stream_name = kwargs.pop("stream_name", None)
        self.kwargs = kwargs
        ParallelStream.__init__(self, upstream, stream_name=stream_name)

    def update(self, x, who=None):
        if self.state is core.no_default:
            self.state = x
            return self._emit(self.state)
        else:
            client = self.default_client()
            result = client.submit(self.func, self.state, x, **self.kwargs)
            if self.returns_state:
                state = client.submit(getitem, result, 0)
                result = client.submit(getitem, result, 1)
            else:
                state = result
            self.state = state
            return self._emit(result)


@args_kwargs
@ParallelStream.register_api()
class starmap(ParallelStream):
    def __init__(self, upstream, func, *args, **kwargs):
        self.func = func
        stream_name = kwargs.pop("stream_name", None)
        self.kwargs = kwargs
        self.args = args

        ParallelStream.__init__(self, upstream, stream_name=stream_name)

    def update(self, x: Future, who=None):
        client = self.default_client()
        result = client.submit(
            filter_null_wrapper(apply),
            filter_null_wrapper(self.func),
            x,
            self.args,
            self.kwargs,
        )
        return self._emit(result)


@args_kwargs
@ParallelStream.register_api()
class filter(ParallelStream):
    def __init__(self, upstream, predicate, *args, **kwargs):
        if predicate is None:
            predicate = _truthy
        self.predicate = return_null(predicate)
        stream_name = kwargs.pop("stream_name", None)
        self.kwargs = kwargs
        self.args = args

        ParallelStream.__init__(self, upstream, stream_name=stream_name)

    def update(self, x, who=None):
        client = self.default_client()
        result = client.submit(self.predicate, x, *self.args, **self.kwargs)
        return self._emit(result)


@args_kwargs
@ParallelStream.register_api()
class pluck(ParallelStream):
    def __init__(self, upstream, pick, **kwargs):
        self.pick = pick
        super().__init__(upstream, **kwargs)

    def update(self, x, who=None):
        client = self.default_client()
        if isinstance(self.pick, Sequence):
            return self._emit(
                client.submit(filter_null_wrapper(_pluck), self.pick, x)
            )
        else:
            return self._emit(
                client.submit(filter_null_wrapper(getitem), x, self.pick)
            )


@args_kwargs
@ParallelStream.register_api()
class buffer(ParallelStream, core.buffer):
    pass


@args_kwargs
@ParallelStream.register_api()
class combine_latest(ParallelStream):
    def __init__(self, *upstreams, **kwargs):
        emit_on = kwargs.pop("emit_on", None)
        first = kwargs.pop("first", None)

        self.last = [None for _ in upstreams]
        self.missing = set(upstreams)
        if emit_on is not None:
            if not isinstance(emit_on, Iterable):
                emit_on = (emit_on,)
            emit_on = tuple(
                upstreams[x] if isinstance(x, int) else x for x in emit_on
            )
            self.emit_on = emit_on
        else:
            self.emit_on = upstreams
        ParallelStream.__init__(self, upstreams=upstreams, **kwargs)
        if first:
            move_to_first(self, first)
        self.future_buffers = {up: None for up in upstreams}

    def update(self, x, who=None):
        if self.missing and who in self.missing:
            self.missing.remove(who)

        self.last[self.upstreams.index(who)] = x
        if not self.missing and who in self.emit_on:
            tup = tuple(self.last)
            client = self.default_client()
            l = []
            # we only want to fall back on prior data if it is not the
            # incoming data
            # It is fine to not emit if the incoming data is bad, but in
            # serial mode the bad data would have never gotten to the node
            # so we need to have the buffered data only be good data
            for t, up in szip(tup, self.upstreams):
                if up == who:
                    a = t
                else:
                    a = client.submit(future_chain, t, self.future_buffers[up])
                    self.future_buffers[up] = a
                l.append(a)
            tup = tuple(l)
            return self._emit(tup)


@args_kwargs
@ParallelStream.register_api()
class delay(ParallelStream, core.delay):
    pass


@args_kwargs
@ParallelStream.register_api()
class latest(ParallelStream, core.latest):
    pass

# TODO: needs to be filter proofed
@args_kwargs
@ParallelStream.register_api()
class partition(ParallelStream, core.partition):
    pass


@args_kwargs
@ParallelStream.register_api()
class rate_limit(ParallelStream, core.rate_limit):
    pass


# TODO: needs to be filter proofed
@args_kwargs
@ParallelStream.register_api()
class sliding_window(ParallelStream, core.sliding_window):
    pass


@args_kwargs
@ParallelStream.register_api()
class timed_window(ParallelStream, core.timed_window):
    pass


@args_kwargs
@ParallelStream.register_api()
class union(ParallelStream, core.union):
    pass

# TODO: needs to be filter proofed
@args_kwargs
@ParallelStream.register_api()
class zip(ParallelStream):
    def __init__(self, *upstreams, **kwargs):
        self.maxsize = kwargs.pop("maxsize", 10)
        first = kwargs.pop("first", None)
        self.literals = [
            (i, val)
            for i, val in enumerate(upstreams)
            if not isinstance(val, Stream)
        ]

        self.buffers = {
            upstream: deque()
            for upstream in upstreams
            if isinstance(upstream, Stream)
        }

        upstreams2 = [
            upstream for upstream in upstreams if isinstance(upstream, Stream)
        ]

        ParallelStream.__init__(self, upstreams=upstreams2, **kwargs)
        if first:
            move_to_first(self, first)
        self.future_buffers = {upstream: None for upstream in upstreams
                               if isinstance(upstream, Stream)}

    def pack_literals(self, tup):
        """ Fill buffers for literals whenever we empty them """
        inp = list(tup)[::-1]
        out = []
        for i, val in self.literals:
            while len(out) < i:
                out.append(inp.pop())
            out.append(val)

        while inp:
            out.append(inp.pop())

        return tuple(out)

    def update(self, x, who=None):
        L = self.buffers[who]  # get buffer for stream
        L.append(x)
        if len(L) == 1 and all(self.buffers.values()):
            client = self.default_client()

            tup = tuple(client.submit(future_chain, self.buffers[up][0], self.future_buffers[up]) for up in self.upstreams)
            for buf in self.buffers.values():
                buf.popleft()
            for t, up in szip(tup, self.upstreams):
                self.future_buffers[up] = t
            if self.literals:
                tup = self.pack_literals(tup)
            return self._emit(tup)


@args_kwargs
@ParallelStream.register_api()
class zip_latest(ParallelStream, core.zip_latest):
    pass


@args_kwargs
@ParallelStream.register_api(staticmethod)
class filenames(ParallelStream, sources.filenames):
    pass


@args_kwargs
@ParallelStream.register_api(staticmethod)
class from_textfile(ParallelStream, sources.from_textfile):
    pass


def is_unique(x, past):
    if x in past:
        return NULL_COMPUTE
    return x

@args_kwargs
@ParallelStream.register_api()
class unique(ParallelStream):
    """ Avoid sending through repeated elements

    This deduplicates a stream so that only new elements pass through.
    You can control how much of a history is stored with the ``history=``
    parameter.  For example setting ``history=1`` avoids sending through
    elements when one is repeated right after the other.

    Examples
    --------
    >>> source = Stream()
    >>> source.unique(history=1).sink(print)
    >>> for x in [1, 1, 2, 2, 2, 1, 3]:
    ...     source.emit(x)
    1
    2
    1
    3
    """

    def __init__(self, upstream, history=None, **kwargs):
        self.history = history
        self.past = []
        ParallelStream.__init__(self, upstream, **kwargs)

    def update(self, x, who=None):
        client = self.default_client()
        ret = client.submit(is_unique, x, self.past)
        self.past.append(ret)
        return self._emit(ret)
