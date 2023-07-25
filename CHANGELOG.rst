===================
rapidz Change Log
===================

.. current developments

v0.2.1
====================

**Fixed:**

* Change "graph.node" to "graph.nodes" in the project

* Use "pd.date_range" instead of "pd.DatetimeIndex" in test_dataframe.py

**Authors:**

* st3107



v0.2.0
====================

**Added:**

* ``index`` method to ``orderedweakrefset.OrderedWeakrefSet``

**Changed:**

* ``accumulate`` nodes now take in an additional optional kwarg
  ``reset_stream``.
  If provided, when this stream emits the ``accumulate`` node will be reset
  to it's initial state.
* Plotting handles cyclic graphs better and ``emit_on`` edges
* Updated ``plot_graph.py`` example to match the new syntax
* ``rapidz.core.unique`` does the correct thing with non-hashable data
  and now inits the cache when it sees the first piece of data
* Make ``rapidz.graph.readable_graph`` more usable by having it take in a
  networkx graph rather than a node

**Authors:**

* Christopher J. Wright



v0.1.2
====================

**Changed:**

* ``run_tests.py`` now runs the streamin dataframe tests

**Fixed:**

* The streaming dataframe tests now work with pytest properly
* ``link.link`` properly splays out ``kwargs`` in namespaces

**Authors:**

* Christopher J. Wright



v0.1.1
====================

**Added:**

* Named parallel backends have graphviz colors associated with them


**Changed:**

* ``future_maybe`` now gets inside ``MutableMappings``


**Fixed:**

* Removed auto registry from dask ``scatter`` node




v0.1.0
====================

**Added:**

* Add node init args and kwargs capture for provanance
* rever setup


**Changed:**

* Don't run tests on dataframe




