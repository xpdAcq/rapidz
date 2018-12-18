"""Link pipelines together"""


def link(*args, **kwargs):
    """Link pipelines together sharing a common namespace

    Parameters
    ----------
    args : funcs
        Functions which take in nodes and kwargs and return a dict
    kwargs : Any
        The input namespace which is passed to the pipeline functions

    Returns
    -------

    """
    namespace = kwargs
    for pipe in args:
        new_namespace = pipe(**namespace)
        if new_namespace:
            namespace.update(**new_namespace)
    return namespace


def mutating_link(func, namespace, input_lut, output_lut):
    """Link pipeline chunk to other chunks while mutating the incoming and
    outgoing node names


    Parameters
    ----------
    func
    namespace
    input_lut
    output_lut

    Returns
    -------

    """

    # takes valid node name to qoi (abs -> qoi)
    for k, v in input_lut.items():
        namespace[v] = namespace[k]
        # namespace[k] = namespace[v]
    loc = func(**namespace)
    # takes output name and changes it (tomo -> abs_tomo)
    for k, v in output_lut.items():
        loc[v] = loc.pop(k)
    namespace.update(loc)
    # Note that this means that input_lut keys can't be a valid output
    # node name (qoi -> N/A)
    for k, v in input_lut.items():
        namespace.pop(v)
    return namespace
