"""Isolated exact read-only admission query; not imported by the live core.

Equivalence is for coherent valid packed states and their fixed orbit map.
No state/physical counter is updated. Stops and unusable-state errors propagate.
"""
from research.near_quarter_packed_state import line_span


def _probe_cells(state, cells, check):
    """Geometry-only primitive for <=4candidate cells; no family interpretation."""
    state._usable()
    check()
    if not 1 <= len(cells) <= 4:
        raise ValueError('bounded candidate cells required')
    cells = tuple(cells)
    if any(type(cell) is not int or not 0 <= cell < state.n*state.n for cell in cells):
        raise ValueError('candidate cell outside grid')
    if len(set(cells)) != len(cells):
        return False  # Never call line_span with equal candidate endpoints.
    points, rows, columns = [], {}, {}
    for cell in cells:
        check()
        x, y = cell % state.n, cell//state.n
        points.append((x, y))
        rows[y] = rows.get(y, 0)+1
        columns[x] = columns.get(x, 0)+1
        if state.occupied[cell] or state.blocked[cell]:
            return False  # Occupancy or two-old/one-new triple.
    if any(state.rows[y]+count > 2 for y, count in rows.items()) or any(
            state.columns[x]+count > 2 for x, count in columns.items()):
        return False
    for i, (ax, ay) in enumerate(points):
        for j in range(i+1, len(points)):
            bx, by = points[j]
            for k in range(j+1, len(points)):
                check()
                cx, cy = points[k]
                if (bx-ax)*(cy-ay) == (by-ay)*(cx-ax):
                    return False  # Three-new triple.
            check()
            start, step, length = line_span(cells[i], cells[j], state.n, check)
            for offset in range(length):
                check()
                if state.occupied[start+offset*step]:
                    return False  # One-old/two-new triple.
    check()
    return True


def probe_orbit(state, variable, check=None):
    """Same admission boolean as push on a coherent state, without mutation."""
    state._usable()
    if type(variable) is not int or not 1 <= variable <= state.bounds['orbits']:
        raise ValueError('invalid packed orbit ID')
    check = state._check if check is None else check
    check()
    four = variable <= state.bounds['four']
    if (any(state._selected_ids[i] == variable for i in range(state._selected_count)) or
            (four and state.four_selected >= state.bounds['m']) or
            (not four and state.diagonal_selected >= 1)):
        return False
    begin, end = state._orbit_offsets[variable-1], state._orbit_offsets[variable]
    cells = tuple(state._orbit_cells[index] for index in range(begin, end))
    return _probe_cells(state, cells, check)
