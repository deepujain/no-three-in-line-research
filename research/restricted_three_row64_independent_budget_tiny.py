"""Synthetic graph-budget limits and strict JSON checks; no actual inputs."""
from research import restricted_three_row64 as w
b=w.GraphBudget();assert b.check({'a':[1,2,3]})['nodes']>0
for value in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}'):
 try:w.decode_json(value)
 except ValueError:pass
 else:raise AssertionError('invalid JSON accepted')
for value in (set([1]),[[object()]]):
 try:b.check(value)
 except ValueError:pass
 else:raise AssertionError('non-JSON node accepted')
value=0
for _ in range(65):value=[value]
try:b.check(value)
except ValueError:pass
else:raise AssertionError('depth cap not applied')
for key in ('NODE_CAP','GRAPH_CAP','AUX_CAP'):
 q=w.GraphBudget();setattr(q,key,1)
 try:q.check({'a':[1,2]})
 except ValueError:pass
 else:raise AssertionError(key+' not applied')
print('PASS synthetic graph node/depth/byte/aux caps and duplicate/nonfinite JSON rejection; no parser transient memory claim')
