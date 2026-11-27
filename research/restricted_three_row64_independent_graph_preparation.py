"""Preparation of the synthetic graph, before any new fixed64 implementation comparison."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from research import restricted_three_row64_independent_synthetic_graph as graph


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def old_association(v):
    def normalize(values,n):
        assert n==75
        return tuple(tuple(p) for p in values)
    with patch.object(graph.shared.kernel,'validate_points',normalize),\
         patch.object(graph.shared.kernel,'normalized_sha256',lambda n,p:graph.BEFORE):
        return graph.shared.authenticate_chain(v['docs'],v['docs'][graph.OLD_METADATA],v['pins'])


def recent_association(v):
    d=v['docs'];a=d[graph.adapter.AUTHORITY]['payload']
    return graph.adapter.associated(d[graph.adapter.REPORT],d[graph.adapter.RECEIPT],d[graph.adapter.MANIFEST],a,
        d[graph.adapter.INITIAL],graph.adapter.EXPECTED,v['authority_raw'],d[graph.AUDIT]['chain'],v['runtime'])


def run():
    sources={str(Path(p).relative_to(graph.ROOT)):sha(p) for p in
             (__file__,graph.__file__,graph.shared.__file__,graph.adapter.__file__)}
    assert sources['research/two_row_suffix75.py']=='fe01dcecf582480754fc076a9a04a2f6d2a24d14d76bb55280f09f0db06cc9f1'
    assert sources['research/restricted_three_row_actual_chain_adapter.py']=='0d5537eb46a898a84cb89ba4aceff2a817c122f8b5873492e5cce06e226ad50c'
    v=graph.fixture();assert old_association(v)==tuple(map(tuple,graph.OLD_POINTS))
    pins,resource,count=recent_association(v);assert count==228 and len(pins)==229
    assert set(v['docs'][graph.adapter.INITIAL])=={'n','points','score','state_hash','counters','order_sha256','handoff'}
    assert len(v['docs'])==45 and len(v['source_roles'])==6 and len(v['metadata']['artifacts'])==51
    assert set(v['docs'])|v['source_roles']==set(v['metadata']['artifacts'])
    mutations=[
        ('old_report_not_accepted',old_association,lambda v:v['docs'][graph.OLD_REPORT].__setitem__('accepted',False)),
        ('old_receipt_drift',old_association,lambda v:v['docs'][graph.OLD_RECEIPT].__setitem__('sources_unchanged',False)),
        ('old_audit_not_accepted',old_association,lambda v:v['docs'][graph.OLD_AUDIT].__setitem__('accepted',False)),
        ('old_audit_chain_failed',old_association,lambda v:v['docs'][graph.OLD_AUDIT]['chain'].__setitem__('artifact_chain_passed',False)),
        ('old_guard_wrong_audit',old_association,lambda v:v['docs'][graph.OLD_GUARD].__setitem__('audit_output_sha256','0'*64)),
        ('old_move_wrong_final_score',old_association,lambda v:v['docs'][graph.MOVES[-1]].__setitem__('score',64)),
        ('old_boundary_wrong_identity',old_association,lambda v:v['docs'][graph.OLD_BOUNDARY].__setitem__('normalized_sha256','0'*64)),
        ('old_best_valid',old_association,lambda v:v['docs'][graph.OLD_BEST].__setitem__('valid',True)),
        ('recent_report_not_accepted',recent_association,lambda v:v['docs'][graph.adapter.REPORT].__setitem__('accepted',False)),
        ('recent_report_wrong_order',recent_association,lambda v:v['docs'][graph.adapter.REPORT].__setitem__('order_sha256','0'*64)),
        ('recent_receipt_drift',recent_association,lambda v:v['docs'][graph.adapter.RECEIPT].__setitem__('sources_unchanged',False)),
        ('recent_receipt_bad_argv',recent_association,lambda v:v['docs'][graph.adapter.RECEIPT]['argv'].__setitem__(1,'wrong.py')),
        ('recent_manifest_self',recent_association,lambda v:v['docs'][graph.adapter.MANIFEST].__setitem__(str(graph.ROOT/graph.adapter.MANIFEST),graph.H)),
        ('recent_manifest_missing',recent_association,lambda v:v['docs'][graph.adapter.MANIFEST].pop('/synthetic-only/source-0')),
        ('recent_charge_after_complete',recent_association,lambda v:v['docs'][graph.adapter.REPORT].__setitem__('last_attempted_charge',dict(started=16,completed=16,accepted=1))),
        ('recent_wrong_publications',recent_association,lambda v:v['docs'][graph.adapter.REPORT].__setitem__('authority_publications',33)),
        ('recent_uncertain',recent_association,lambda v:v['docs'][graph.adapter.REPORT].__setitem__('authority_uncertain',True)),
        ('recent_metadata_error',recent_association,lambda v:v['docs'][graph.adapter.REPORT].__setitem__('witness_metadata_error','synthetic failure')),
        ('recent_initial_old_counters',recent_association,lambda v:v['docs'][graph.adapter.INITIAL].__setitem__('counters',dict(started=16,completed=16,accepted=1))),
        ('recent_initial_bad_handoff',recent_association,lambda v:v['docs'][graph.adapter.INITIAL]['handoff'].__setitem__('score',64)),
    ]
    rejected=[]
    for name,check,mutate in mutations:
        v=graph.fixture();mutate(v)
        try:check(v)
        except ValueError as error:rejected.append(dict(case=name,error=str(error)))
        else:raise AssertionError('accepted synthetic corruption '+name)
    assert all(sha(graph.ROOT/p)==s for p,s in sources.items())
    return dict(passed=True,sources=sources,artifact_roles=51,total_roles_with_metadata=52,json_roles=45,text_roles=6,
                pure_association_successes=2,corruption_rejections=rejected,
                scope='Synthetic graph preparation and frozen old pure-interface conformance only. Declared hash labels, identity/structure spies and n4 point arrays; no actual inputs, geometry, byte authentication or new fixed64 implementation comparison.',
                limitations='This is not a fixed64 wrapper PASS. Full new association, real synthetic-byte authentication, orchestration, call ownership and frozen-source review remain pending author implementation.')


if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row64-independent-graph-preparation.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(passed=True,pure_successes=2,rejections=len(result['corruption_rejections']),
                         source_sha256=sha(__file__),graph_sha256=sha(graph.__file__),evidence_sha256=sha(path))))
