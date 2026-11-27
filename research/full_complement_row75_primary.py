"""Full-complement row costs from one current pair-count line table."""
from itertools import combinations
from math import gcd,isqrt
from research import full_complement_row75_core as core


def line_key(first,second,budget):
    budget.charge('pair_lines','primary')
    a,b = second[1]-first[1],first[0]-second[0]
    c = first[1]*second[0]-first[0]*second[1]
    divisor = gcd(gcd(abs(a),abs(b)),abs(c))
    core.require(divisor > 0,'distinct line endpoints')
    a,b,c = a//divisor,b//divisor,c//divisor
    if a < 0 or a == 0 and b < 0:
        a,b,c = -a,-b,-c
    return a,b,c


def costs(points,n,budget):
    points = core.validate_points(points,n)
    current = [tuple(x for x,y in points if y == row) for row in range(n)]
    matrix = [[0]*n for row in range(n)]
    table = {}
    baseline = 0
    try:
        for first,second in combinations(points,2):
            key = line_key(first,second,budget)
            table[key] = table.get(key,0)+1
            core.require(len(table) <= 11026,'current line-key cap')
        budget.check_graph(points,current,matrix,table)
        pairs = sum(table.values())
        core.require(pairs == len(points)*(len(points)-1)//2,'all current pairs counted')
        for key,pair_count in table.items():
            budget.charge('recoveries','primary')
            discriminant = 1+8*pair_count
            root = isqrt(discriminant)
            core.require(root*root == discriminant and root % 2 == 1,'triangular pair multiplicity')
            count = (root+1)//2
            core.require(2 <= count <= len(points) and count*(count-1)//2 == pair_count,'exact line multiplicity')
            if key[0] == 0:
                core.require(count == 2,'horizontal row capacity')
            else:
                core.require(count <= n,'nonhorizontal row capacity')
            table[key] = count
            baseline += count*(count-1)*(count-2)//6
        budget.check_graph(points,current,matrix,table)
        for (a,b,c),count in table.items():
            if a == 0:
                continue
            for row in range(n):
                budget.charge('intersections','primary')
                numerator = -(b*row+c)
                if numerator % a:
                    continue
                x = numerator//a
                if not 0 <= x < n:
                    continue
                retained_count = count-int(x in current[row])
                core.require(retained_count >= 0,'retained multiplicity')
                matrix[row][x] += retained_count*(retained_count-1)//2
        core.require(sum(matrix[row][x] for row in range(n) for x in current[row]) == 3*baseline,
                     'occupied unary sum is three raw score')
        core.require(all(type(value) is int and 0 <= value <= (len(points)-1)*(len(points)-2)//2
                         for vector in matrix for value in vector),'unary integer range')
        return {'baseline':baseline,'costs':matrix}
    finally:
        table.clear()


def row_records(points,n,matrix,baseline,budget):
    """Yield provisional lexical minima once, allowing immediate zero handling."""
    points = core.validate_points(points,n)
    core.require(type(matrix) is list and len(matrix) == n and all(type(v) is list and len(v) == n for v in matrix),
                 'unary matrix shape')
    core.require(type(baseline) is int and baseline >= 0,'baseline score')
    for row in range(n):
        current = tuple(x for x,y in points if y == row)
        best = []
        for x,cost in enumerate(matrix[row]):
            budget.charge('cost_columns','selection')
            core.require(type(cost) is int and cost >= 0,'strict unary cost')
            item = cost,x
            budget.charge('comparisons','selection')
            if not best or item < best[0]:
                best.insert(0,item)
            else:
                budget.charge('comparisons','selection')
                if len(best) == 1 or item < best[1]:
                    best.insert(1,item)
            del best[len(current):]
        chosen = tuple(sorted(x for cost,x in best))
        score = baseline-sum(matrix[row][x] for x in current)+sum(matrix[row][x] for x in chosen)
        core.require(0 <= score <= baseline and len(chosen) == len(current),'provisional same-load minimum')
        yield {'row':row,'current':current,'best':chosen,'best_score':score}
