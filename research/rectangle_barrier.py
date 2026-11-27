"""Bounded exact BFS in a fixed-score uncolored-rectangle component.

Only frontier exhaustion is complete. Time/state cutoffs explicitly leave an
incomplete component. Canonical point-set hashes remove matching-color copies.
Every newly best state is independently audited and its full move path retained.
Resume is for trusted, unmodified local checkpoints: reconstructed states are
checked, but prior enumeration/completion records are not independently replayed.
"""

import argparse
from collections import Counter, deque
import itertools
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.trade_search import checked_full_state, rectangle_proposal, _prune
from src.verify import normalized_sha256, verify_certificate, verify_certificate_bruteforce


def _checked_state(n, points, score):
    state = {"n": n, "points": [list(point) for point in sorted(points)],
             "state_kind": "valid_full_search_state" if score == 0 else "invalid_full_search_state",
             "valid": score == 0, "collinear_triple_count": score}
    _, actual, digest = checked_full_state(state, n)
    if actual != score:
        raise RuntimeError("BFS score disagrees with independent checkers")
    state["normalized_sha256"] = digest
    state["independent_audit"] = ["integer_normalized_slopes", "integer_cross_products"]
    return state


def _valid_certificate(n, points):
    certificate = {"n": n, "points": [list(point) for point in sorted(points)],
                   "metadata": {"novelty_claim": False}}
    checks = [verify_certificate(certificate), verify_certificate_bruteforce(certificate)]
    if not all(check["valid"] for check in checks):
        raise ValueError("incumbent failed independent validation")
    certificate["metadata"].update({"normalized_sha256": checks[0]["normalized_sha256"],
                                    "independent_validation": [check["algorithm"] for check in checks]})
    return certificate


def barrier_search(source, threshold, seconds=60, max_states=1000, baseline=None,
                   on_improvement=None, resume=None, on_checkpoint=None,
                   checkpoint_every=1):
    if type(threshold) is not int or threshold < 0:
        raise ValueError("threshold must be a nonnegative integer")
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError("seconds must be finite and nonnegative")
    if type(max_states) is not int or max_states < 1:
        raise ValueError("max_states must be positive")
    if type(checkpoint_every) is not int or checkpoint_every < 1:
        raise ValueError("checkpoint_every must be positive")
    started = time.monotonic()
    deadline = started + seconds
    n = source["n"]
    points, source_score, source_hash = checked_full_state(source, n)
    if threshold < source_score:
        raise ValueError("threshold must include the source score")
    incumbent = _valid_certificate(n, [] if baseline is None else baseline["points"])
    if baseline is not None:
        original = [verify_certificate(baseline), verify_certificate_bruteforce(baseline)]
        if not all(check["valid"] for check in original):
            raise ValueError("baseline failed independent validation")
    source_subset = _valid_certificate(n, _prune(points))
    if len(source_subset["points"]) > len(incumbent["points"]):
        incumbent = source_subset
    states = {source_hash: {"points": frozenset(points), "score": source_score,
                            "parent": None, "old_edges": None, "depth": 0,
                            "neighborhood_complete": False, "next_pair_index": 0}}
    frontier = deque([source_hash])
    report = {"audit": "threshold_component_of_uncolored_rectangle_graph", "n": n,
              "source_normalized_sha256": source_hash, "source_score": source_score,
              "threshold": threshold, "seconds_budget": seconds, "max_states": max_states,
              "status": "incomplete", "neighborhoods_started": 0, "neighborhoods_completed": 0,
              "old_edge_pairs_examined": 0, "legal_switches_examined": 0,
              "within_threshold_transitions": 0, "duplicate_within_threshold_transitions": 0,
              "best_score": source_score, "improvements": [],
              "scope": "The connected component containing this fixed full state using uncolored two-edge rectangle switches while every visited state has score at most threshold. Exhaustion is a finite component result, not global nonexistence or a bound for other moves/states.",
              "source_state": _checked_state(n, points, source_score), "novelty_claim": False,
              "checkpoint_format": "rectangle_barrier_v1",
              "counter_scope": "cumulative enumeration work, including repeated scans after threshold raises or state-limit retries",
              "checkpoint_trust_model": "Resume requires a trusted, unmodified local checkpoint. Reconstructed states, move legality, hashes, scores, offset ranges and frontier consistency are checked; previous enumeration/completion claims are trusted rather than independently replayed.",
              "completeness_basis": "fresh exhaustive enumeration",
              "prior_elapsed_seconds": 0.0, "resume_count": 0}
    pair_count = len(points) * (len(points) - 1) // 2
    if resume is not None:
        if resume.get("source_normalized_sha256") != source_hash or resume.get("threshold", -1) > threshold:
            raise ValueError("resume source must match and threshold cannot decrease")
        restored = {}
        for item in resume.get("nodes", []):
            digest = item["normalized_sha256"]
            parent = item["parent_normalized_sha256"]
            old = None if item["old_edges"] is None else tuple(map(tuple, item["old_edges"]))
            if parent is None:
                if digest != source_hash or restored:
                    raise ValueError("resume must begin with its unique source node")
                recovered, recovered_score = frozenset(points), source_score
            else:
                if parent not in restored or old is None or len(old) != 2 or not set(old).issubset(restored[parent]["points"]):
                    raise ValueError("resume contains an invalid parent move")
                proposal = rectangle_proposal(set(restored[parent]["points"]), *old)
                if proposal is None:
                    raise ValueError("resume contains an illegal rectangle switch")
                delta, recovered = proposal
                recovered, recovered_score = frozenset(recovered), restored[parent]["score"] + delta
            if (digest in restored or normalized_sha256(n, recovered) != digest
                    or recovered_score != item["score"] or recovered_score > threshold
                    or item["depth"] != (0 if parent is None else restored[parent]["depth"] + 1)):
                raise ValueError("resume node hash, score or depth disagrees with reconstruction")
            complete = item["neighborhood_complete"]
            offset = item.get("next_pair_index", pair_count if complete else 0)
            if type(complete) is not bool or type(offset) is not int or not 0 <= offset <= pair_count or complete != (offset == pair_count):
                raise ValueError("resume contains an invalid pair-scan offset")
            restored[digest] = {"points": recovered, "score": recovered_score, "parent": parent,
                                "old_edges": old, "depth": item["depth"],
                                "neighborhood_complete": complete, "next_pair_index": offset}
        if not restored or len(restored) > max_states:
            raise ValueError("resume has no states or exceeds max_states")
        states = restored
        raised = threshold > resume["threshold"]
        if raised:
            for node in states.values():
                node["neighborhood_complete"], node["next_pair_index"] = False, 0
            frontier = deque(states)
        else:
            pending = [digest for digest, node in states.items() if not node["neighborhood_complete"]]
            stored_frontier = resume.get("frontier_state_hashes", pending)
            if len(stored_frontier) != len(set(stored_frontier)) or set(stored_frontier) != set(pending):
                raise ValueError("resume frontier does not match unfinished states")
            frontier = deque(stored_frontier)
        for key in ("neighborhoods_started", "neighborhoods_completed", "old_edge_pairs_examined",
                    "legal_switches_examined", "within_threshold_transitions", "duplicate_within_threshold_transitions"):
            report[key] = resume.get(key, 0)
        report["prior_elapsed_seconds"] = resume.get("prior_elapsed_seconds", 0) + resume.get("elapsed_seconds", 0)
        report["resume_count"] = resume.get("resume_count", 0) + 1
        report["resumed_from_threshold"] = resume["threshold"]
        report["threshold_was_raised"] = raised
        report["completeness_basis"] = ("all restored and newly reached neighborhoods rescanned after threshold increase" if raised
                                         else "trusted local checkpoint scan records plus current exhaustive continuation")
        report["best_score"] = min(node["score"] for node in states.values())
        report["improvements"] = resume.get("improvements", [])
        for improvement in report["improvements"]:
            state = improvement["state"]
            _checked_state(n, set(map(tuple, state["points"])), state["collinear_triple_count"])
        if "incumbent" in resume:
            candidate = _valid_certificate(n, resume["incumbent"]["points"])
            if len(candidate["points"]) > len(incumbent["points"]):
                incumbent = candidate

    def path_to(digest):
        steps = []
        while states[digest]["parent"] is not None:
            item = states[digest]
            first, second = item["old_edges"]
            steps.append({"from_normalized_sha256": item["parent"], "to_normalized_sha256": digest,
                          "old_edges": [list(first), list(second)],
                          "replacement_edges": [[first[0], second[1]], [second[0], first[1]]],
                          "resulting_score": item["score"]})
            digest = item["parent"]
        return list(reversed(steps))

    def snapshot():
        report["discovered_state_count"] = len(states)
        report["pending_frontier_count"] = len(frontier)
        report["frontier_state_hashes"] = list(frontier)
        report["state_score_histogram"] = dict(sorted(Counter(node["score"] for node in states.values()).items()))
        report["first_exit_state_hashes"] = [digest for digest, node in states.items() if node["depth"] == 1]
        report["nodes"] = [{"normalized_sha256": digest, "score": node["score"],
                            "parent_normalized_sha256": node["parent"], "depth": node["depth"],
                            "old_edges": None if node["old_edges"] is None else [list(p) for p in node["old_edges"]],
                            "neighborhood_complete": node["neighborhood_complete"],
                            "next_pair_index": node["next_pair_index"]}
                           for digest, node in states.items()]
        report["incumbent"] = incumbent
        report["elapsed_seconds"] = time.monotonic() - started
        return report

    if on_checkpoint:
        on_checkpoint(snapshot())

    cutoff = False
    while frontier and not cutoff:
        if time.monotonic() >= deadline:
            report["status"] = "timeout_incomplete"
            break
        digest = frontier[0]
        node = states[digest]
        current = set(node["points"])
        if node["next_pair_index"] == 0:
            report["neighborhoods_started"] += 1
        all_pairs = itertools.combinations(sorted(current), 2)
        for pair_index, (first, second) in enumerate(itertools.islice(all_pairs, node["next_pair_index"], None), node["next_pair_index"]):
            if time.monotonic() >= deadline:
                report["status"] = "timeout_incomplete"
                report["unfinished_node_normalized_sha256"] = digest
                cutoff = True
                break
            report["old_edge_pairs_examined"] += 1
            proposal = rectangle_proposal(current, first, second)
            if proposal is None:
                node["next_pair_index"] = pair_index + 1
                continue
            delta, changed = proposal
            report["legal_switches_examined"] += 1
            changed_score = node["score"] + delta
            if changed_score > threshold:
                node["next_pair_index"] = pair_index + 1
                continue
            report["within_threshold_transitions"] += 1
            changed_hash = normalized_sha256(n, changed)
            if changed_hash in states:
                report["duplicate_within_threshold_transitions"] += 1
                node["next_pair_index"] = pair_index + 1
                continue
            if len(states) >= max_states:
                report["status"] = "state_limit_incomplete"
                report["unfinished_node_normalized_sha256"] = digest
                report["unrecorded_neighbor_normalized_sha256"] = changed_hash
                cutoff = True
                break
            states[changed_hash] = {"points": frozenset(changed), "score": changed_score,
                                    "parent": digest, "old_edges": (first, second),
                                    "depth": node["depth"] + 1, "neighborhood_complete": False,
                                    "next_pair_index": 0}
            frontier.append(changed_hash)
            node["next_pair_index"] = pair_index + 1
            if changed_score < report["best_score"]:
                state = _checked_state(n, changed, changed_score)
                report["best_score"] = changed_score
                improvement = {"state": state, "path": path_to(changed_hash)}
                report["improvements"].append(improvement)
                candidate = _valid_certificate(n, _prune(changed))
                if len(candidate["points"]) > len(incumbent["points"]):
                    incumbent = candidate
                if on_improvement:
                    on_improvement(improvement, incumbent)
                if on_checkpoint:
                    on_checkpoint(snapshot())
        if not cutoff:
            node["neighborhood_complete"] = True
            frontier.popleft()
            report["neighborhoods_completed"] += 1
            if on_checkpoint and report["neighborhoods_completed"] % checkpoint_every == 0:
                on_checkpoint(snapshot())
    else:
        if not cutoff:
            report["status"] = "complete_frontier_exhausted"
    snapshot()
    if on_checkpoint:
        on_checkpoint(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--baseline", type=Path, default=ROOT / "data/published-n78.json")
    parser.add_argument("--threshold", type=int, default=12)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--max-states", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=ROOT / "data/trades-barrier-audit.json")
    parser.add_argument("--resume", type=Path, help="resume a checkpoint; threshold may stay equal or increase")
    parser.add_argument("--checkpoint-every", type=int, default=1, help="completed neighborhoods between checkpoints")
    args = parser.parse_args(argv)
    resumed = json.loads(args.resume.read_text()) if args.resume else None
    source = json.loads(args.source.read_text()) if args.source else resumed["source_state"] if resumed else json.loads((ROOT / "data/trades-n79-seed270079-state.json").read_text())
    baseline = json.loads(args.baseline.read_text()) if args.baseline else None
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def checkpoint(report):
        temporary = args.output.with_name(args.output.name + ".tmp")
        temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        temporary.replace(args.output)

    def save_immediately(improvement, incumbent):
        print(json.dumps({"event": "independently_checked_better_state", "score": improvement["state"]["collinear_triple_count"],
                          "path_length": len(improvement["path"]), "incumbent_point_count": len(incumbent["points"])}), flush=True)

    report = barrier_search(source, args.threshold, args.seconds, args.max_states, baseline, save_immediately,
                            resumed, checkpoint, args.checkpoint_every)
    print(json.dumps({key: report[key] for key in ("status", "elapsed_seconds", "best_score", "discovered_state_count",
                                                  "neighborhoods_completed", "pending_frontier_count", "state_score_histogram")}, sort_keys=True))
    return 0 if report["status"] == "complete_frontier_exhausted" else 2


if __name__ == "__main__":
    sys.exit(main())
