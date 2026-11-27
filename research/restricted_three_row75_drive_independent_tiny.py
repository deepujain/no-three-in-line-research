"""Synthetic n4 drive interruption tests; no actual inputs or durable storage."""
from research import restricted_three_row75 as w
points=((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))
a=w.new_authority(points,4)
assert a['U']>0 and a['orders']['blocks']

def fail_start(value,tag):
 if tag=='start':raise w.SearchStop('injected start publication interruption')
r=w.drive(a,publish=fail_start)
assert r['status']=='error' and 'unresolved charge' in r['error'] and r['attempted_charge']['started']==1 and r['authority']['counters']['started']==0

saved=[];written=[]
def save_zero(points):saved.append(tuple(points));return {'path':'valid149.json','sha256':'a'*64,'bytes':1}
def save_move(move):return {'path':'move.json','sha256':'b'*64,'bytes':1}
def fail_zero(value,tag):
 if tag=='accept_zero':raise w.SearchStop('injected zero publication interruption')
 written.append((tag,w.clone(value)))
r=w.drive(a,publish=fail_zero,save_zero=save_zero,save_move=save_move)
assert saved and r['status']=='error' and 'saved witness lacks durable zero authority' in r['error']
assert r['authority']['U']>0 and r['authority']['pending']==1 and written[-1][0]=='start'
print('PASS real synthetic n4 drive: unresolved start rejected; saved zero survives failed authority publication; no real filesystem durability tested')
