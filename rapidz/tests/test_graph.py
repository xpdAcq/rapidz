from operator import add, mul
import os

import pytest

nx = pytest.importorskip("networkx")

from rapidz import (
    Stream,
    create_graph,
    visualize,
    build_node_set,
)
from rapidz.utils_test import tmpfile

from ..graph import _clean_text


def test_build_node_set():
    source1 = Stream(stream_name="source1")
    source2 = Stream(stream_name="source2")

    n1 = source1.zip(source2)
    n2 = n1.map(add)
    n2.connect(source1)

    s = set()
    build_node_set(n2, s)
    print(s)
    for node in [source1, source2, n1, n2]:
        assert node in s


def test_create_graph():
    source1 = Stream(stream_name="source1")
    source2 = Stream(stream_name="source2")

    n1 = source1.zip(source2)
    n2 = n1.map(add)
    sink = n2.sink(source1.emit)

    g = nx.DiGraph()
    create_graph(n2, g)
    for t in [hash(a) for a in [source1, source2, n1, n2, sink]]:
        assert t in g
    for edge_nodes in [(source1, n1), (source2, n1), (n1, n2), (n2, sink)]:
        edge = tuple([hash(n) for n in edge_nodes])
        assert edge in g.edges


def test_create_cyclic_graph():
    source1 = Stream(stream_name="source1")
    source2 = Stream(stream_name="source2")

    n1 = source1.zip(source2)
    n2 = n1.map(add)
    n2.connect(source1)

    g = nx.DiGraph()
    create_graph(n2, g)
    for t in [hash(a) for a in [source1, source2, n1, n2]]:
        assert t in g


def test_create_file():
    source1 = Stream(stream_name="source1")
    source2 = Stream(stream_name="source2")

    n1 = source1.zip(source2)
    n2 = n1.map(add).scan(mul).map(lambda x: x + 1)
    n2.sink(source1.emit)

    with tmpfile(extension="png") as fn:
        visualize(n1, filename=fn)
        assert os.path.exists(fn)

    with tmpfile(extension="svg") as fn:
        n1.visualize(filename=fn, rankdir="LR")
        assert os.path.exists(fn)

    with tmpfile(extension="dot") as fn:
        n1.visualize(filename=fn, rankdir="LR")
        with open(fn) as f:
            text = f.read()

        for word in [
            "rankdir",
            "source1",
            "source2",
            "zip",
            "map",
            "add",
            "shape=box",
            "shape=ellipse",
        ]:
            assert word in text


def test_cleantext():
    text = "JFDSM*(@&$:FFDS:;;"
    expected_text = "JFDSM ;FFDS; "
    cleaned_text = _clean_text(text)
    assert cleaned_text == expected_text
