"""Strict finite quotas, canonical identity and immutable bounded output only."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys

MiB = 1024*1024
LIMITS = {'raw_triples':1100000,'pair_lines':900000,'intersections':1700000,
          'comparisons':23000,'recoveries':827024,'cost_columns':5625,'publications':4}


def require(condition,message):
    if not condition:
        raise ValueError(message)


def compact(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized_sha256(points,n):
    """Exact serialization of src/verify.py:55, with points,n API ordering."""
    return sha(compact({'n':n,'points':[list(p) for p in sorted(points)]}))


def validate_points(values,n):
    require(type(n) is int and n in (5,75),'supported fixed grid order')
    require(type(values) in (tuple,list) and len(values) == 2*n-1,'point container/cardinality')
    cells = []
    for value in values:
        require(type(value) in (tuple,list) and len(value) == 2,'cell shape')
        x,y = value
        require(type(x) is int and type(y) is int and 0 <= x < n and 0 <= y < n,'strict in-grid cells')
        cells.append((x,y))
    cells = tuple(sorted(cells))
    require(len(set(cells)) == len(cells),'distinct cells')
    loads = tuple(sum(y == r for x,y in cells) for r in range(n))
    require(sorted(loads) == [1]+[2]*(n-1),'row-valid singleton loads')
    return cells


def decode(raw):
    def pairs(items):
        result = {}
        for key,value in items:
            require(key not in result,'duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON token')
    return json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=constant)


class QuotaExceeded(ValueError):
    pass


class GraphBudget:
    GRAPH_CAP = 16*MiB
    AUX_CAP = 16*MiB
    NODE_CAP = 100000
    DEPTH_CAP = 64

    def check(self,*roots,reserve=0,check=lambda:None):
        require(type(reserve) is int and 0 <= reserve <= self.GRAPH_CAP,'graph reserve')
        seen = set()
        stack = [(value,0) for value in roots]
        size = count = 0
        while stack:
            auxiliary = (sys.getsizeof(seen)+len(seen)*sys.getsizeof(id(None))+sys.getsizeof(stack)
                         +len(stack)*(sys.getsizeof((None,0))+sys.getsizeof(0))+256)
            require(auxiliary <= self.AUX_CAP,'graph walker auxiliary cap')
            value,depth = stack.pop()
            require(depth <= self.DEPTH_CAP,'graph depth cap')
            identity = id(value)
            if identity in seen:
                continue
            seen.add(identity)
            count += 1
            size += sys.getsizeof(value)
            require(count <= self.NODE_CAP and size+reserve <= self.GRAPH_CAP,'retained object graph cap')
            if count % 256 == 0:
                check()
            if type(value) is dict:
                for key,item in value.items():
                    stack.append((key,depth+1))
                    stack.append((item,depth+1))
            elif type(value) in (list,tuple):
                for item in value:
                    stack.append((item,depth+1))
            else:
                require(type(value) in (str,int,bool,float,bytes,type(None)),'graph value type')
                require(type(value) is not float or math.isfinite(value),'finite graph float')
        return {'bytes':size,'nodes':count}


class Budget:
    def __init__(self,check=lambda:None):
        self.check = check
        self.counts = dict.fromkeys(LIMITS,0)
        self.components = {}
        self.live_roots = ()

    def checkpoint(self):
        self.check()

    def set_roots(self,*roots):
        self.live_roots = roots

    def check_graph(self,*roots,reserve=2*MiB):
        self.checkpoint()
        return GraphBudget().check(*self.live_roots,*roots,reserve=reserve,check=self.checkpoint)

    def charge(self,kind,component,*,timed=True):
        require(type(kind) is str and kind in LIMITS,'counter kind')
        require(type(component) is str and 0 < len(component) <= 64,'counter component')
        require(type(timed) is bool and (timed or kind == 'publications'),'geometry cannot bypass deadline')
        if timed:
            self.checkpoint()
        require(type(self.counts[kind]) is int and self.counts[kind] >= 0,'counter state')
        if self.counts[kind] >= LIMITS[kind]:
            raise QuotaExceeded(kind+' cap before operation')
        if component not in self.components:
            require(len(self.components) < 16,'component count cap')
            self.components[component] = dict.fromkeys(LIMITS,0)
        self.counts[kind] += 1
        self.components[component][kind] += 1

    def snapshot(self):
        return {'totals':dict(self.counts),'limits':dict(LIMITS),
                'components':{name:dict(values) for name,values in self.components.items()}}


class ImmutableStore:
    """Four attempted publications maximum; uncertainty is sticky."""
    def __init__(self,out,budget):
        self.out = Path(out)
        self.budget = budget
        self.uncertain = False
        self.references = {}

    def prepare(self,value,cap):
        require(type(cap) is int and 0 < cap <= 128*1024,'artifact byte cap')
        raw = compact(value)
        require(len(raw) <= cap,'encoded artifact byte cap')
        self.budget.check_graph(value,raw)
        return raw

    def commit_prepared(self,name,raw,cap,*,urgent=False):
        require(type(name) is str and 0 < len(name) <= 128 and Path(name).name == name
                and name not in ('.','..'),'artifact basename')
        require(type(raw) is bytes and type(cap) is int and 0 < len(raw) <= cap <= 128*1024,'prepared artifact cap')
        require(type(urgent) is bool,'urgent flag')
        self.budget.charge('publications','persistence',timed=not urgent)
        path = self.out/name
        opened = False
        try:
            with path.open('xb') as output:
                opened = True
                require(output.write(raw) == len(raw),'complete artifact write')
                output.flush()
                os.fsync(output.fileno())
            directory = os.open(self.out,os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except Exception:
            if opened:
                self.uncertain = True
            raise
        reference = {'path':name,'sha256':sha(raw),'bytes':len(raw)}
        self.references[name] = reference
        return dict(reference)


def safe_file_identity(path):
    try:
        target = Path(path)
        require(target.stat().st_size <= 128*1024,'bounded source identity size')
        with target.open('rb') as source:
            raw = source.read(128*1024+1)
        require(len(raw) <= 128*1024,'bounded source identity read')
        return {'sha256':sha(raw),'bytes':len(raw),'error':None}
    except Exception as exc:
        return {'sha256':None,'bytes':None,'error':type(exc).__name__+': '+str(exc)[:1000]}
