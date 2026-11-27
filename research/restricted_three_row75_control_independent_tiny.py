"""Control-only injected three-row tests; no geometry, optimizer, parser or durability proof."""
from unittest.mock import patch
from research import restricted_three_row75 as w

def scenario(mode):
 ranks=[];events=[];publishes=[];calls=[]
 initial={'status':'active','points':['s0'],'n':4,'U':20,'state_hash':'s0','orders':None,'cursor':0,'pending':None,'counters':{'started':0,'completed':0,'accepted':0},'attempts':[],'artifacts':[]}
 def ranking(points,index,n,state_hash,check,work):ranks.append(state_hash);return {'blocks':[[0,1,2,1,1]],'sha256':'order-'+state_hash}
 def start(a):
  p=w.clone(a);p['counters']['started']+=1;p['pending']=p['counters']['started'];p['attempts'].append({'rows':[0,1,2]});return p
 def optimize(points,index,n,rows,check,work):
  i=len(calls);calls.append(i);score=20-i-(1 if mode=='accept' else 0)
  return {'score':score,'zero':False,'X':(0,),'Y':(0,1),'Z':(0,1),'points':['s'+str(i+1)],'optimum_established':True,'enumeration_exhausted':True,'domains':[]}
 def build(points,n,check,work):return (points,{},20-int(points[0][1:]))
 def accept(a,result,rebuilt):
  p=w.clone(a);p['points']=result['points'];p['state_hash']=result['points'][0];p['U']=result['score'];p['orders']=None;p['cursor']=0;p['pending']=None;p['counters']['completed']+=1;p['counters']['accepted']+=1
  return {'before_hash':a['state_hash']},p
 def nonimprove(a,result):
  p=w.clone(a);p['pending']=None;p['cursor']+=1;p['counters']['completed']+=1;return p
 with patch.object(w,'validate_authority',side_effect=lambda a:a),patch.object(w,'authority_bytes',return_value=b'stub'),patch.object(w.kernel,'normalized_sha256',side_effect=lambda n,p:p[0]),patch.object(w,'make_orders',side_effect=ranking),patch.object(w,'plan_start',side_effect=start),patch.object(w,'block_optimum',side_effect=optimize),patch.object(w,'build',side_effect=build),patch.object(w,'prepare_accept',side_effect=accept),patch.object(w,'plan_nonimprovement',side_effect=nonimprove):
  result=w.drive(initial,prepared=(['s0'],{},20),publish=lambda a,t:publishes.append(t),save_move=lambda m:{'path':'stub'},observe=events.append)
 if mode=='accept':
  assert result['status']=='block_cap' and result['decisions']==16 and result['authority']['counters']=={'started':16,'completed':16,'accepted':16}
  assert ranks==['s'+str(i) for i in range(16)] and [e['before_hash'] for e in events]==ranks
  assert publishes==['start','accept']*16 and len(calls)==16
 else:
  assert result['status']=='restricted_candidate_list_exhausted' and result['decisions']==1
  assert result['authority']['counters']=={'started':1,'completed':1,'accepted':0} and result['authority']['cursor']==1
  assert ranks==['s0'] and events[0]['before_hash']=='s0' and events[0]['strict'] is False and publishes==['start','complete']
scenario('accept');scenario('nonimprove')
print('PASS control-only stubs: global 16 starts across 16 accepts, cap before next ranking, old-state events, completed nonimprovement/list exhaustion; no geometric or durability claim')
