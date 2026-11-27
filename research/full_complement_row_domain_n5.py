"""One fixed n5 row-domain diagnostic. No production imports or input loader."""
import hashlib
from itertools import combinations
import json

FIXTURE_BYTES = b'{"n":5,"points":[[0,0],[0,1],[0,2],[0,3],[0,4],[1,0],[1,1],[1,2],[1,3]]}'
FIXTURE_SHA = '5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37'
FIXTURE = ((0,0),(0,1),(0,2),(0,3),(0,4),(1,0),(1,1),(1,2),(1,3))
LIMITS = {'determinants':6000, 'line_keys':2000, 'line_incidences':600}
COMPONENTS = ('producer','direct_oracle','raw_line_oracle','unary_line_oracle','synthetic')


def require(condition, message):
    if not condition:
        raise ValueError(message)


class BudgetExceeded(ValueError):
    pass


class Budget:
    def __init__(self):
        self.counts = dict.fromkeys(LIMITS, 0)
        self.components = {name:dict.fromkeys(LIMITS, 0) for name in COMPONENTS}

    def charge(self, kind, component):
        require(kind in LIMITS and component in self.components, 'counter role')
        if self.counts[kind] >= LIMITS[kind]:
            raise BudgetExceeded(kind + ' cap before operation')
        self.counts[kind] += 1
        self.components[component][kind] += 1

    def snapshot(self):
        return {'totals':dict(self.counts),
                'components':{k:dict(v) for k,v in self.components.items()},
                'limits':dict(LIMITS)}


def validate_fixture(points, n):
    require(type(n) is int and n == 5, 'fixed n5')
    require(type(points) in (tuple,list) and len(points) == 9, 'nine-point container')
    cells = []
    for point in points:
        require(type(point) in (tuple,list) and len(point) == 2, 'cell shape')
        x,y = point
        require(type(x) is int and type(y) is int, 'strict cell integers')
        require(0 <= x < 5 and 0 <= y < 5, 'cell bounds')
        cells.append((x,y))
    canonical = tuple(sorted(cells))
    require(len(set(canonical)) == 9, 'distinct cells')
    require(tuple(sum(y == r for x,y in canonical) for r in range(5)) == (2,2,2,2,1), 'fixed row loads')
    raw = json.dumps({'n':n,'points':canonical},sort_keys=True,separators=(',',':')).encode('ascii')
    require(raw == FIXTURE_BYTES and hashlib.sha256(raw).hexdigest() == FIXTURE_SHA, 'fixed fixture identity')
    return canonical


def _collinear(a,b,c,budget):
    budget.charge('determinants','producer')
    return (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0])


def make_domains(points, n, budget):
    """Only the fixed diagnostic is accepted; all geometry follows validation."""
    points = validate_fixture(points,n)
    require(type(budget) is Budget, 'shared strict budget')
    baseline = 0
    conflicts = {}
    for a,b,c in combinations(points,3):
        if _collinear(a,b,c,budget):
            baseline += 1
            rows = tuple(sorted((a[1],b[1],c[1])))
            require(len(set(rows)) == 3, 'row-valid conflict')
            conflicts[rows] = conflicts.get(rows,0) + 1
    result = []
    for row in range(5):
        current = tuple(x for x,y in points if y == row)
        retained = tuple(p for p in points if p[1] != row)
        unary = []
        for x in range(5):
            cost = 0
            for a,b in combinations(retained,2):
                cost += _collinear((x,row),a,b,budget)
            unary.append(cost)
        best = tuple(sorted(sorted(range(5),key=lambda x:(unary[x],x))[:len(current)]))
        domain = set(current) | set(best)
        for x in range(5):
            if len(domain) == 4:
                break
            domain.add(x)
        result.append({'row':row,'current':current,'unary':tuple(unary),'best':best,
                       'best_score':baseline-sum(unary[x] for x in current)+sum(unary[x] for x in best),
                       'domain':tuple(sorted(domain))})
    return {'n':5,'fixture_sha256':FIXTURE_SHA,'baseline':baseline,'rows':result,
            'current_conflicts':[{'rows':rows,'count':count} for rows,count in sorted(conflicts.items())]}
