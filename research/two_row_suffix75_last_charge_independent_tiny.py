"""Synthetic n4 producer charge timing; no actual artifacts or input."""
from research import two_row_suffix75 as w
points=((0,0),(0,1),(1,2),(2,1),(2,3),(3,2),(3,3))
base={'row_started':308,'row_completed':308,'pair_started':95,'pair_completed':95,'accepted':28}
a=w.new_authority(points,4,base=base,row_complete=True)
p=w.plan_start(a)
charge=dict(p['counters'])
rows=p['attempts'][-1]['rows']
cols=[[x for x,y in p['points'] if y==r] for r in rows]
result={'score':p['U'],'X':cols[0],'Y':cols[1],'zero':False,'enumeration_complete':True}
finished=w.plan_nonimprovement(p,result)
assert charge==dict(base,pair_started=96,pair_completed=95)
assert finished['counters']==dict(base,pair_started=96,pair_completed=96)
print('PASS synthetic producer captures pre-completion 96/95; final completion is 96/96; result control stubbed')
