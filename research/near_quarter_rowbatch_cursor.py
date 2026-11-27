"""Bounded local row-fill cursor; no geometry allocation or search entrypoint."""
from dataclasses import dataclass

NONE, SINGLE, PAIR, END = range(4)
MAX_DOMAIN = 1521
MAX_ID = 1560


def bounded_tuple(values, limit):
    result = []
    for value in values:
        if len(result) == limit:
            raise ValueError('bounded sequence exceeded')
        result.append(value)
    return tuple(result)


@dataclass(frozen=True)
class Cursor:
    kind: int
    i: int = 0
    j: int = 0


@dataclass(frozen=True)
class Domain:
    ids: tuple
    weights: tuple
    deficit: int
    remaining: int

    def __post_init__(self):
        ids = bounded_tuple(self.ids, MAX_DOMAIN)
        weights = bounded_tuple(self.weights, MAX_DOMAIN)
        if (len(ids) != len(weights) or
                any(type(v) is not int or not 1 <= v <= MAX_ID for v in ids) or len(set(ids)) != len(ids) or
                any(type(w) is not int or w not in (1, 2) for w in weights) or
                type(self.deficit) is not int or self.deficit not in (1, 2) or
                type(self.remaining) is not int or not 0 <= self.remaining <= 39):
            raise ValueError('invalid bounded row domain')
        object.__setattr__(self, 'ids', ids)
        object.__setattr__(self, 'weights', weights)

    def validate(self, cursor):
        if (type(cursor) is not Cursor or
                any(type(v) is not int for v in (cursor.kind, cursor.i, cursor.j))):
            raise ValueError('invalid cursor types')
        k, i, j = cursor.kind, cursor.i, cursor.j
        if k == END and i == j == 0:
            return
        if self.remaining and k == SINGLE and 0 <= i < len(self.ids) and j == 0:
            if self.weights[i] == self.deficit:
                return
        if (self.remaining >= 2 and self.deficit == 2 and k == PAIR and
                0 <= i < j < len(self.ids) and self.weights[i] == self.weights[j] == 1):
            return
        raise ValueError('noncanonical cursor')

    def _pair(self, start_i, start_j, check):
        if self.deficit != 2 or self.remaining < 2:
            return Cursor(END)
        for i in range(start_i, len(self.ids)):
            check()
            if self.weights[i] != 1:
                continue
            for j in range(max(i+1, start_j if i == start_i else i+1), len(self.ids)):
                check()
                if self.weights[j] == 1:
                    return Cursor(PAIR, i, j)
        return Cursor(END)

    def first(self, check=lambda: None):
        check()
        if not self.remaining:
            return Cursor(END)
        for i, weight in enumerate(self.weights):
            check()
            if weight == self.deficit:
                return Cursor(SINGLE, i)
        return self._pair(0, 1, check)

    def successor(self, cursor, check=lambda: None):
        check()
        self.validate(cursor)
        if cursor.kind == END:
            return cursor
        if cursor.kind == SINGLE:
            for i in range(cursor.i+1, len(self.ids)):
                check()
                if self.weights[i] == self.deficit:
                    return Cursor(SINGLE, i)
            return self._pair(0, 1, check)
        return self._pair(cursor.i, cursor.j+1, check)

    def batch(self, cursor):
        self.validate(cursor)
        if cursor.kind == END:
            raise ValueError('END has no batch')
        return ((self.ids[cursor.i],) if cursor.kind == SINGLE else
                (self.ids[cursor.i], self.ids[cursor.j]))
