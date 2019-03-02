from rapidz import Stream
from operator import add

source1 = Stream(stream_name="source1")
source2 = Stream(stream_name="source2")
source3 = Stream(stream_name="awesome source")

n1 = source1.zip(source2)
n2 = n1.map(add)
n3 = n2.zip(source3)
L = n3.sink_to_list()


n2.visualize("simple.png")

# Rapidz can also visualize more complex graphs
n4 = source1.combine_latest(source2, n1, emit_on=(0, 1))
n4.connect(n3)
nm = n4.scatter(backend='thread').map(add)

# Rapidz can even graph cyclical graphs!
n3.connect(source3)

n2.visualize("complex.png")
