"""Prepare/audit ONLY fresh n3/n5 construct/root host gates; never launches one.

Root separately invokes the reviewed public worker CLI. No host monitor,
geometry constructor, numerical search, retry, sleep or source migration here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
FROZEN = {
    'core': '27beb80326431e952bc5523065d94866982326b46eed6d9ec2541ea49b8a1670',
    'state': '860711b8e83d0f3e738ebeedc535e0953e903a01551b1e22ad3bb20f49fa3b11',
    'cursor': '738a545abc1909bc126ca916d225dfef90bea8b974142a5885cb9e2f632e2422',
    'checkpoint': 'ac57fd572e85d0653efc72b9cda73bc8274a96f154d37150ec3e6419c27c4770',
    'model': 'b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a',
    'verifier': 'e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c',
    'line-model': 'd789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897',
    'worker': '7f8c8a166d4e79f881a644b69b6f0bb0c949ef524c97eb792f81b09c0e835738',
    'owned-helper': 'c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48',
}
# Explicit tiny oracle fixtures, serialized only. Reviewer compares these with
# the frozen oracle before authorizing host gates; no oracle is called here.
TINY_MAPS = {
    3: [[[0, 1], [1, 0], [1, 2], [2, 1]], [[0, 0], [2, 2]]],
    5: [[[0, 1], [1, 4], [3, 0], [4, 3]], [[0, 2], [2, 0], [2, 4], [4, 2]],
        [[0, 3], [1, 0], [3, 4], [4, 1]], [[1, 2], [2, 1], [2, 3], [3, 2]],
        [[0, 0], [4, 4]], [[1, 1], [3, 3]]],
}
GATES = (('n3-construct', 3, 'construct'), ('n3-root', 3, 'root'),
         ('n5-construct', 5, 'construct'), ('n5-root', 5, 'root'))


def load_worker():
    from research import near_quarter_packed_worker as worker
    worker.source_check(FROZEN)
    return worker


def script_sha():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def exclusive_json(path, value, worker):
    raw = worker.canonical(value)
    if len(raw) > worker.RECEIPT_CAP:
        raise ValueError('preflight metadata byte bound')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        worker.write_all(fd, raw, lambda: None)
        os.fsync(fd)
    finally:
        os.close(fd)
    worker.fsync_dir(Path(path).parent)
    return worker.sha(raw)


def prepare(output):
    worker = load_worker()
    output = Path(output).absolute()
    if output.is_symlink():
        raise ValueError('symlink output')
    output.mkdir(mode=0o700)  # Never reuse/overwrite a prepared or attempted set.
    output = output.resolve()
    requests = []
    for index, (name, n, operation) in enumerate(GATES, 1):
        request = {'chain_dir': str(output/(name+'.chain')), 'stage_id': f'{index:032x}',
            'operation': operation, 'n': n, 'declaration_b64': worker.declaration(n),
            'expected_map_json_sha256': worker.sha(worker.canonical(TINY_MAPS[n])),
            'expected_parent': worker.ZERO_HEX, 'max_new_nodes': 0, 'seconds': 5,
            'rss_mib': 256}
        request_sha = exclusive_json(output/(name+'.request.json'), request, worker)
        requests.append({'name': name, 'request_sha256': request_sha})
    plan = {'schema': 1, 'status': 'prepared_not_run', 'script_sha256': script_sha(),
            'sources': FROZEN, 'requests': requests,
            'scope': 'four individually reviewed fresh chains; construct/root only; max_new_nodes0; no counted search',
            'seconds': 5, 'rss_mib': 256, 'worker_reserve_seconds': 2}
    exclusive_json(output/'plan.json', plan, worker)
    print(str(output/'plan.json'))


def audit(output, gate_name):
    started = time.monotonic_ns()
    worker = load_worker()
    output = Path(output).resolve()
    plan = worker.strict_json(worker.read_bounded(output/'plan.json', worker.RECEIPT_CAP), worker.RECEIPT_CAP)
    worker.keys(plan, ('schema', 'status', 'script_sha256', 'sources', 'requests', 'scope',
                       'seconds', 'rss_mib', 'worker_reserve_seconds'))
    if (plan['schema'] != 1 or type(plan['schema']) is not int or plan['status'] != 'prepared_not_run' or
        plan['script_sha256'] != script_sha() or plan['sources'] != FROZEN or
        plan['seconds'] != 5 or plan['rss_mib'] != 256 or plan['worker_reserve_seconds'] != 2):
        raise ValueError('frozen preflight plan differs')
    if type(plan['requests']) is not list or len(plan['requests']) != len(GATES):
        raise ValueError('four exact requests required')
    for saved, (name, _, _) in zip(plan['requests'], GATES):
        worker.keys(saved, ('name', 'request_sha256'))
        if saved['name'] != name:
            raise ValueError('gate order/names differ')
        worker.hexstr(saved['request_sha256'], zero=False)
    index = [x[0] for x in GATES].index(gate_name)
    name, n, operation = GATES[index]
    request_raw = worker.read_bounded(output/(name+'.request.json'), worker.JSON_CAP)
    if worker.sha(request_raw) != plan['requests'][index]['request_sha256']:
        raise ValueError('request hash differs')
    request = worker.strict_json(request_raw)
    expected_request = {'chain_dir': str(output/(name+'.chain')), 'stage_id': f'{index+1:032x}',
        'operation': operation, 'n': n, 'declaration_b64': worker.declaration(n),
        'expected_map_json_sha256': worker.sha(worker.canonical(TINY_MAPS[n])),
        'expected_parent': worker.ZERO_HEX, 'max_new_nodes': 0, 'seconds': 5, 'rss_mib': 256}
    if worker.canonical(request) != worker.canonical(expected_request):
        raise ValueError('fixed no-search request differs')
    returned_raw = worker.read_bounded(output/(name+'.return.json'), worker.HEAD_CAP)
    if not returned_raw.endswith(b'\n'):
        raise ValueError('public CLI return framing')
    returned = worker.strict_json(returned_raw[:-1], worker.HEAD_CAP)
    worker.keys(returned, ('result', 'receipt_sha256', 'stage_id', 'lease_retained',
        'invocation_started_ns', 'coordination_finished_ns', 'complete_invocation_ns', 'timing_scope'))
    if (returned['result'] != 'accepted' or returned['stage_id'] != request['stage_id'] or
            returned['lease_retained'] is not False):
        raise ValueError('gate did not freshly accept; stop, do not retry')
    for k in ('invocation_started_ns', 'coordination_finished_ns', 'complete_invocation_ns'):
        worker.integer(returned[k], 1)
    if returned['coordination_finished_ns']-returned['invocation_started_ns'] != returned['complete_invocation_ns']:
        raise ValueError('complete coordination timing differs')
    chain = Path(request['chain_dir'])
    if os.path.lexists(chain/'writer.lease'):
        raise ValueError('lease remains; explicit reconciliation required')
    head_raw, head = worker._read_head(chain)
    if head['last_receipt_sha256'] != returned['receipt_sha256']:
        raise ValueError('accepted HEAD/return receipt differs')
    receipt_raw = worker.read_bounded(chain/(head['last_receipt_sha256']+'.receipt.json'), worker.RECEIPT_CAP)
    receipt = worker.validate_receipt(receipt_raw, head=head, sources=FROZEN)
    stage = chain/('stage-'+request['stage_id'])
    job_raw = worker.read_bounded(stage/'job.json', worker.JSON_CAP)
    job = worker.validate_job(worker.strict_json(job_raw))
    job_sha = worker.sha(job_raw)
    if (job_sha != head['last_job_sha256'] or job['sources'] != FROZEN or job['accepted_record'] is not None or
        job['lease_token']['expected_parent'] != worker.ZERO_HEX or
        job['chain_dir'] != request['chain_dir'] or job['stage_id'] != request['stage_id'] or
        any(job[k] != request[k] for k in ('operation', 'n', 'max_new_nodes', 'expected_map_json_sha256')) or
        job['declaration'] != request['declaration_b64'] or job['limits'] != {'guard_seconds': 5, 'rss_mib': 256} or
        job['timing']['precommit_deadline_ns']-job['timing']['worker_deadline_ns'] != 2_000_000_000 or
        job['timing']['precommit_deadline_ns']-job['timing']['invocation_started_ns'] != 5_000_000_000):
        raise ValueError('exact source/job/lease/timing declaration differs')
    report_raw = worker.read_bounded(stage/'report.json', worker.JSON_CAP)
    report, _ = worker.validate_report(report_raw, job, job_sha, receipt['prior_accepted_record'])
    worker.validate_gate(receipt['gate'], 5, 256)
    if (worker.sha(report_raw) != receipt['report_sha256'] or
        report['status'] != ('constructed' if operation == 'construct' else 'root_ready_no_search') or
        (report['nodes_before'], report['new_nodes'], report['nodes_total']) != (0, 0, 0) or
        any(report['domain_counters'][k] for k in ('domain_probes', 'batch_probes', 'cursor_checks')) or
        receipt['search_performed'] or receipt['search_complete'] or receipt['witness_sha256'] is not None):
        raise ValueError('preflight performed counted search/domain work or changed artifacts')
    worker.source_check(FROZEN)
    evidence = {'schema': 1, 'gate': name, 'status': 'accepted_no_search_preflight',
        'script_sha256': script_sha(), 'sources': FROZEN, 'request_sha256': worker.sha(request_raw),
        'job_sha256': job_sha, 'report_sha256': worker.sha(report_raw),
        'receipt_sha256': worker.sha(receipt_raw), 'head_sha256': worker.sha(head_raw),
        'supervisor_return_sha256': worker.sha(returned_raw), 'supervisor_return': returned,
        'helper_gate': receipt['gate'], 'precommit_timing': receipt['timing'],
        'audit_elapsed_ns': time.monotonic_ns()-started,
        'timing_scope': 'helper RSS/wall scope separate from full supervisor coordination; this later bounded audit is outside both',
        'search_performed': False, 'search_complete': False}
    exclusive_json(output/(name+'.audited.json'), evidence, worker)
    print(worker.canonical({'gate': name, 'status': evidence['status'], 'nodes': 0}).decode('ascii'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    make = sub.add_parser('prepare')
    make.add_argument('output')
    check = sub.add_parser('audit')
    check.add_argument('output')
    check.add_argument('--gate', choices=[g[0] for g in GATES], required=True)
    args = parser.parse_args()
    if args.mode == 'prepare':
        prepare(args.output)
    else:
        audit(args.output, args.gate)


if __name__ == '__main__':
    main()
