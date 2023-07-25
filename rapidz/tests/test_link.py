from rapidz import Stream
from rapidz.link import link


def test_link():
    def make_a():
        source = Stream()
        out_a = source.map(lambda x: x + 1)
        return locals()

    def make_b(out_a, **kwargs):
        out_b = out_a.map(lambda x: x * 2)
        return locals()

    ns = link(make_a, make_b)
    L = ns["out_b"].sink_to_list()
    for i in range(10):
        ns["source"].emit(i)
    assert L == [(i + 1) * 2 for i in range(10)]


def test_double_link():
    def make_a(**kwargs):
        in_a = Stream()
        out_a = in_a.map(lambda x: x + 1)
        return locals()

    def make_b(out_a, **kwargs):
        out_b = out_a.map(lambda x: x * 2)
        return locals()

    def make_c(out_a, out_b, **kwargs):
        out_c = out_a.zip(out_b).map(sum)
        return locals()

    ab = link(make_a, make_b)
    abc = link(make_c, **ab)
    assert set(abc.keys()) == {'in_a', 'out_a', 'out_b', 'out_c'}
    L = ab["out_b"].sink_to_list()
    L2 = abc["out_c"].sink_to_list()
    for i in range(10):
        ab["in_a"].emit(i)
    assert L == [(i + 1) * 2 for i in range(10)]
    assert L2 == [((i + 1) * 2) + i + 1 for i in range(10)]
