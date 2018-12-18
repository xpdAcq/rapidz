from rapidz import Stream
from rapidz.link import link, mutating_link


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
    def make_a():
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
    L = ab["out_b"].sink_to_list()
    L2 = abc["out_c"].sink_to_list()
    for i in range(10):
        ab["in_a"].emit(i)
    assert L == [(i + 1) * 2 for i in range(10)]
    assert L2 == [((i + 1) * 2) + i + 1 for i in range(10)]


def test_mutate_link():
    def make_a(**kwargs):
        in_a = Stream()
        out_a = in_a.map(lambda x: x + 1)
        return locals()

    def make_a2(**kwargs):
        in_a2 = Stream()
        out_a2 = in_a2.map(lambda x: x - 1)
        return locals()

    # This is a pipeline chunk factory, it could be applied to numerous
    # pipeline chunks
    def make_b(qoi, **kwargs):
        out_b = qoi.map(lambda x: x * 2)
        return locals()

    ns = link(make_a, make_a2, **{})
    ns = mutating_link(
        make_b, ns,
        {'out_a': 'qoi'},
        {'out_b': 'a_out_b'})
    ml = mutating_link(
        make_b, ns,
        {'out_a2': 'qoi'},
        {'out_b': 'a2_out_b'}
    )
    ns.update(ml)
    assert 'out_b' not in ns
    assert 'qoi' not in ns
    assert 'a2_out_b' in ns

    L = ns['a_out_b'].sink_to_list()
    LL = ns['a2_out_b'].sink_to_list()

    for i in range(10):
        ns["in_a"].emit(i)
        ns["in_a2"].emit(i)

    assert L == [(i + 1) * 2 for i in range(10)]
    assert LL == [(i - 1) * 2 for i in range(10)]
