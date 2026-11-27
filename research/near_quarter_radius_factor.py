"""Degree-only residual radius f-factor relaxation; no geometry or traversal."""
import math
from importlib.metadata import version
import threading
import time


def radius_factor(demands, edges, deadline, *, clock=time.monotonic, solver_class=None):
    """Return SAT/UNSAT/unknown; a SAT edge witness is checked independently.

    Caller must supply the complete admissible multigraph. UNSAT is a trusted
    native solver result, not a standalone proof certificate. Budget expiry or
    an interrupt returns unknown and can never be used as an obstruction.
    """
    from pysat.card import CardEnc, EncType
    from pysat.formula import IDPool
    if solver_class is None:
        from pysat.solvers import Solver
        solver_class=Solver
    if not math.isfinite(deadline) or not 1<=len(demands)<=40 or any(type(d) is not int or not 0<=d<=2 for d in demands):
        raise ValueError('invalid bounded demands or deadline')
    edges=list(edges)
    if len(edges)>1521:
        raise ValueError('too many edges')
    incident=[[] for _ in demands]
    for i,edge in enumerate(edges,1):
        if not isinstance(edge,(tuple,list)) or len(edge)!=2:
            raise ValueError('invalid edge')
        u,v=edge
        if type(u) is not int or type(v) is not int or not 0<=u<len(demands) or not 0<=v<len(demands) or u==v:
            raise ValueError('invalid endpoints')
        incident[u].append(i);incident[v].append(i)
    if clock()>=deadline:
        return {'status':'unknown','reason':'deadline'}
    if any(len(incident[i])<d for i,d in enumerate(demands)):
        if clock()>=deadline:
            return {'status':'unknown','reason':'deadline'}
        return {'status':'unsat','basis':'degree_shortfall','edge_count':len(edges)}
    pool=IDPool(start_from=len(edges)+1)
    solver=solver_class(name='glucose3')
    timer=None; interrupted=threading.Event()
    try:
        clauses=0;literals=0
        for i,d in enumerate(demands):
            if clock()>=deadline:
                return {'status':'unknown','reason':'deadline'}
            encoding=CardEnc.equals(lits=incident[i],bound=d,vpool=pool,encoding=EncType.seqcounter)
            for clause in encoding.clauses:
                if clock()>=deadline:
                    return {'status':'unknown','reason':'deadline'}
                solver.add_clause(clause);clauses+=1;literals+=len(clause)
        remaining=deadline-clock()
        if remaining<=0:
            return {'status':'unknown','reason':'deadline'}
        def interrupt():
            interrupted.set()
            solver.interrupt()
        timer=threading.Timer(remaining,interrupt);timer.daemon=True;timer.start()
        try:
            answer=solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel();timer.join();timer=None
        if interrupted.is_set() or clock()>=deadline or answer is None:
            return {'status':'unknown','reason':'interrupted_or_deadline'}
        common={'backend':'glucose3','encoding':'seqcounter','python_sat_version':version('python-sat'),'edge_count':len(edges),'variables':max(len(edges),pool.top), 'clauses':clauses,'literals':literals}
        if answer is False:
            return {'status':'unsat','basis':'trusted_native_solver',**common}
        if answer is not True:
            raise RuntimeError('unexpected solver result')
        model=solver.get_model()
        if model is None:
            raise RuntimeError('solver returned no SAT model')
        selected={x for x in model if 1<=x<=len(edges)}
        degrees=[0]*len(demands)
        for edge_id in selected:
            u,v=edges[edge_id-1];degrees[u]+=1;degrees[v]+=1
        if degrees!=list(demands):
            raise RuntimeError('invalid SAT degree witness')
        if clock()>=deadline:
            return {'status':'unknown','reason':'deadline'}
        return {'status':'sat','selected_edge_indices':sorted(i-1 for i in selected),**common}
    finally:
        if timer is not None:
            timer.cancel();timer.join()
        solver.delete()
