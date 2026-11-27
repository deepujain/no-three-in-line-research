"""Pure source-delta and stubbed orchestration audit; no native/n79 work."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import boolean_scaffold_cnf as c
from research import fixed_pool_boolean_scaffold157 as gate
from research.boolean_scaffold_cnf_independent_tiny_audit import make_inputs, valuation
from research.boolean_scaffold_independent_tiny_oracle import valid


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = Path(gate.__file__).read_text()
    assert digest(Path(gate.__file__)) == '54b3271f388cc144437ba860b7e4641f1e61efe6a4b34d6e61a358ac52c9964d'
    for before, after in [
        ('native.run_child(command, seconds, pins, latest_end=deadline-3)', 'native.run_child(command, seconds, pins)'),
        ('native.run_child(command, seconds, pins, latest_end=deadline-1)', 'native.run_child(command, seconds, pins)'),
        ('runtime = native.runtime_contract(runtime_manifest)', 'runtime = json.loads(Path(runtime_manifest).read_text())')]:
        assert source.count(before) == 1
        source = source.replace(before, after)
    assert hashlib.sha256(source.encode()).hexdigest() == '86f24958bae78cab9fffe3e1d92fd66706a22b13c5c43462433bde532b18ca87'
    assert digest(Path(c.__file__)) == '0697d3367f169e4dd28e3c7a4b061c89037f418aae950d6114160783c3ba08d9'
    outcomes = []
    for label, points in [('ready', [(1, 2), (3, 0)]), ('matching_obstruction', [(0, 1), (2, 3)])]:
        A = {(i, i) for i in range(4)}; S = A | {(3, 2)}
        args = make_inputs(A, points); old, pool, arcs, tables, conflicts = args
        layout = c.Layout(2, 2, 4, 2); values = valuation(layout, old, pool, arcs, (0, 1), 2)
        raw = ' '.join(str(i if values[i] else -i) for i in sorted(values)); calls = []
        def child(command, seconds, pins, *, latest_end):
            assert (seconds, latest_end) == (10, 22)
            calls.append({'seconds': seconds, 'latest_end': latest_end})
            path = Path(command[command.index('--cnf')+1])
            return {'reason': 'exited', 'returncode': 0, 'cleanup': {'clean': True},
                'stdout': json.dumps({'answer': 'SAT', 'model': raw, 'cnf_sha256': digest(path),
                                      'pgid': os.getpgrp(), 'sid': os.getsid(0)})}
        report = {'sat_invocations': 0, 'checker_invocations': 0, 'counters': gate.old.new_counters()}
        with tempfile.TemporaryDirectory() as tmp, patch.object(gate.native, 'run_child', child):
            out = Path(tmp)
            gate.execute(4, old, S, pool, arcs, tables, conflicts, out, report,
                         lambda: None, {}, 25, clock=lambda: 0, seed_count=2)
            assert report['sat_invocations'] == len(calls) == 1 and report['checker_invocations'] == 0
            assert report['complete'] and report['root']['status'] == label
            diagnostic = json.loads((out/'valid149-diagnostic.json').read_text())
            assert valid(set(map(tuple, diagnostic['points']))) and diagnostic['metadata']['root_ready'] is False
            if label == 'ready':
                ready = json.loads((out/'root-ready149.json').read_text()); P = set(map(tuple, ready['points']))
                plan = set(map(tuple, ready['metadata']['residual_plan']))
                assert ready['metadata']['root_ready'] and not ready['metadata']['residual_plan_joint_geometry_checked']
                assert all(valid(P | {p}) for p in plan) and not valid(P | plan)
            else:
                assert not (out/'root-ready149.json').exists()
                assert report['root']['matching_cover']['matching_size'] == 1
            outcomes.append({'case': label, 'calls': calls, 'status': report['status'], 'native_processes_launched': 0})
    # A genuinely contradictory tiny encoding (two arcs required, only one
    # available) exercises the checker deadline keyword with both calls stubbed.
    args = make_inputs({(0, 0), (1, 1), (2, 2)}, [(0, 1)])
    A, pool, arcs, tables, conflicts = args
    assert any(not clause for _, clause in c.iter_clauses(*args, c.Layout(1, 1, 3, 2)))
    calls = []
    def child(command, seconds, pins, *, latest_end):
        cnf = Path(command[command.index('--cnf')+1]); proof = Path(command[command.index('--proof')+1])
        calls.append({'seconds': seconds, 'latest_end': latest_end})
        if len(calls) == 1:
            assert (seconds, latest_end) == (10, 22); proof.write_text('0\n')
            answer = {'answer': 'UNSAT', 'cnf_sha256': digest(cnf), 'proof_sha256': digest(proof),
                      'proof_bytes': 2, 'pgid': os.getpgrp(), 'sid': os.getsid(0)}
        else:
            assert len(calls) == 2 and (seconds, latest_end) == (5, 24)
            answer = {'accepted': True, 'cnf_sha256': digest(cnf), 'proof_sha256': digest(proof)}
        return {'reason': 'exited', 'returncode': 0, 'cleanup': {'clean': True}, 'stdout': json.dumps(answer)}
    report = {'sat_invocations': 0, 'checker_invocations': 0, 'counters': gate.old.new_counters()}
    with tempfile.TemporaryDirectory() as tmp, patch.object(gate.native, 'run_child', child):
        gate.execute(3, A, set(A) | {(2, 1)}, pool, arcs, tables, conflicts, Path(tmp),
                     report, lambda: None, {}, 25, clock=lambda: 0, seed_count=2)
        assert report['sat_invocations'] == report['checker_invocations'] == 1
        assert report['status'] == 'checked_fixed_pool_unsat' and report['complete'] and report['closure']
        assert not (Path(tmp)/'valid149-diagnostic.json').exists()
    outcomes.append({'case': 'stubbed_unsat_checker_binding', 'calls': calls,
                     'status': report['status'], 'native_processes_launched': 0})
    paths = ['research/boolean_scaffold_cnf.py', 'research/fixed_pool_boolean_scaffold157.py',
             'research/boolean_scaffold_native.py', 'tests/test_fixed_pool_boolean_scaffold.py',
             'research/boolean_scaffold_cnf_independent_tiny_audit.py',
             'data/boolean-scaffold-cnf-independent-tiny-audit.json',
             'research/boolean-scaffold-cnf-independent-source-review.md']
    result = {'status': 'PASS', 'scope': 'Exact three-change source delta and fully stubbed tiny pipelines only; no native or n79 work.',
              'prior_orchestrator_recovered_exactly': True, 'encoder_unchanged': True,
              'outcomes': outcomes, 'pins': {p: digest(ROOT/p) for p in paths},
              'script_sha256': digest(Path(__file__))}
    path = ROOT/'data/boolean-scaffold-independent-source-delta-audit.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True)); print('audit_sha256', digest(path))


if __name__ == '__main__':
    main()
