"""Finite artificial graph/fsync proposal. Execute only in a separately owned gate.

Opaque keys and buffers are not valid line geometry, an input fixture or a timing forecast.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from research import full_complement_row75_core as core

CORE_SHA = 'aa463fe45df59865660659a58a4f23d70ca677f232859fd228a4b4a7c4010f2b'


def durable_evidence(path,value):
    """Separate bounded receipt; not one of the four tested Store publications."""
    raw = (json.dumps(value,sort_keys=True,indent=2)+'\n').encode('ascii')
    core.require(len(raw) <= 64*1024,'envelope evidence cap')
    with path.open('xb') as output:
        core.require(output.write(raw) == len(raw),'complete evidence write')
        output.flush()
        os.fsync(output.fileno())
    directory = os.open(path.parent,os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def run():
    core.require(core.sha(Path(core.__file__).read_bytes()) == CORE_SHA,'frozen core')
    budget = core.Budget()
    matrix = [[10878 for column in range(75)] for row in range(75)]
    opaque = {(i,i+1,-i):1 << (i % 149) for i in range(11026)}
    budget.set_roots(matrix)
    graph = budget.check_graph(opaque)
    # Explicit reserve fills the remainder of the total16MiB graph budget.
    graph_at_reserve = core.GraphBudget().check(matrix,opaque,reserve=16*core.MiB-graph['bytes'])
    rejected_graph = False
    try:
        core.GraphBudget().check(matrix,opaque,reserve=16*core.MiB-graph['bytes']+1)
    except ValueError:
        rejected_graph = True
    core.require(rejected_graph,'graph cap refusal')
    # Live encoded buffers and unary/table graph together are deliberately artificial.
    publication_sizes = (64*1024,16*1024,128*1024,128*1024)
    with tempfile.TemporaryDirectory(prefix='full-row-envelope-') as temporary:
        store = core.ImmutableStore(temporary,budget)
        refs = []
        for ordinal,size in enumerate(publication_sizes):
            raw = b'x'*size
            budget.check_graph(opaque,raw)
            reference = store.commit_prepared('opaque-'+str(ordinal)+'.bin',raw,size)
            core.require((Path(temporary)/reference['path']).stat().st_size == size
                         and hashlib.sha256((Path(temporary)/reference['path']).read_bytes()).hexdigest() == reference['sha256'],
                         'real opaque publication bytes')
            refs.append(reference)
            del raw
        rejected_fifth = False
        try:
            store.commit_prepared('opaque-fifth.bin',b'x',1)
        except core.QuotaExceeded:
            rejected_fifth = True
        core.require(rejected_fifth and not (Path(temporary)/'opaque-fifth.bin').exists(),'fifth refused before file creation')
        core.require(not store.uncertain,'clean artificial fsync sequence')
    del opaque
    budget.set_roots(matrix)
    core.require(core.sha(Path(core.__file__).read_bytes()) == CORE_SHA,'post core identity')
    return {'passed':True,'core_sha256':CORE_SHA,'source_sha256':core.sha(Path(__file__).read_bytes()),
            'opaque_keys':11026,'matrix_cells':5625,'graph':graph,'near_cap_graph':graph_at_reserve,
            'graph_overcap_rejected':rejected_graph,'publication_sizes':publication_sizes,
            'four_real_file_and_directory_fsync_publications':True,'fifth_rejected_before_creation':rejected_fifth,
            'operation_counts':budget.snapshot(),'real_geometric_operations':0,
            'receipt_acceptance_required':True,'failure_or_partial_artifact_invalidates_receipt':True,
            'scope':'Artificial opaque graph and bytes only, no valid input/line schema or geometry. Not a reachable-state, RSS maximum or timing proof.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    failed = args.output.with_name(args.output.stem+'-failure.json')
    if args.output.exists() or failed.exists():
        raise FileExistsError('immutable evidence exists')
    try:
        result = run()
        durable_evidence(args.output,result)
    except Exception as exc:
        durable_evidence(failed,{'passed':False,'error':type(exc).__name__+': '+str(exc)[:1000],
                                'scope':'Artificial envelope failed; no retry; partial output invalid.'})
        raise
    print(json.dumps({'passed':True,'output':str(args.output)},sort_keys=True))


if __name__ == '__main__':
    main()
