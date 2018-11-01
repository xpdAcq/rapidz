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
