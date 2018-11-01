Collections API
===============

Collections
-----------

.. currentmodule:: rapidz.collection

.. autosummary::
   Streaming
   Streaming.map_partitions
   Streaming.accumulate_partitions
   Streaming.verify

Batch
-----

.. currentmodule:: rapidz.batch

.. autosummary::
   Batch
   Batch.filter
   Batch.map
   Batch.pluck
   Batch.to_dataframe
   Batch.to_stream

Dataframes
----------

.. currentmodule:: rapidz.dataframe

.. autosummary::
   DataFrame
   DataFrame.groupby
   DataFrame.rolling
   DataFrame.assign
   DataFrame.sum
   DataFrame.mean
   DataFrame.cumsum
   DataFrame.cumprod
   DataFrame.cummin
   DataFrame.cummax

.. autosummary::
   GroupBy
   GroupBy.count
   GroupBy.mean
   GroupBy.size
   GroupBy.std
   GroupBy.sum
   GroupBy.var

.. autosummary::
   Rolling
   Rolling.aggregate
   Rolling.count
   Rolling.max
   Rolling.mean
   Rolling.median
   Rolling.min
   Rolling.quantile
   Rolling.std
   Rolling.sum
   Rolling.var

.. autosummary::
   DataFrame.window
   Window.apply
   Window.count
   Window.groupby
   Window.sum
   Window.size
   Window.std
   Window.var

.. autosummary::
   Rolling.aggregate
   Rolling.count
   Rolling.max
   Rolling.mean
   Rolling.median
   Rolling.min
   Rolling.quantile
   Rolling.std
   Rolling.sum
   Rolling.var

.. autosummary::
   Random

Details
-------

.. currentmodule:: rapidz.collection

.. autoclass:: Streaming
   :members:

.. currentmodule:: rapidz.batch

.. autoclass:: Batch
   :members:
   :inherited-members:

.. currentmodule:: rapidz.dataframe

.. autoclass:: DataFrame
   :members:
   :inherited-members:

.. autoclass:: Rolling
   :members:

.. autoclass:: Window
   :members:

.. autoclass:: GroupBy
   :members:

.. autoclass:: Random
