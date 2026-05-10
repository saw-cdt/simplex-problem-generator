"""
Two-Phase Simplex Method — Manual Implementation
No SciPy optimization libraries used for resolution.
Algorithm implements pivoting by hand as required by the project rubric.
"""

EPS = 1e-10


def _round_val(x):
    return round(x, 6)


def solve_simplex(c, A, b, operators, obj_type='max'):
    """
    Solve a Linear Programming problem using the Two-Phase Simplex Method.

    Args:
        c: objective coefficients (list of floats), e.g. [3, 5]
        A: constraint matrix (list of lists), e.g. [[1, 0], [0, 2]]
        b: RHS vector (list of floats), e.g. [4, 12]
        operators: list of '<=', '>=', '=' per constraint
        obj_type: 'max' or 'min'

    Returns:
        dict with:
            status: 'optimal_unique' | 'optimal_multiple' | 'infeasible' | 'unbounded'
            optimal_value: float or None
            variables: list of decision variable values
    """
    n = len(c)
    m = len(A)

    # Normalize: handle negative b values
    A = [row[:] for row in A]
    b = b[:]
    ops = operators[:]
    for i in range(m):
        if b[i] < 0:
            b[i] = -b[i]
            A[i] = [-x for x in A[i]]
            if ops[i] == '<=':
                ops[i] = '>='
            elif ops[i] == '>=':
                ops[i] = '<='

    # Convert to max form
    if obj_type == 'min':
        c = [-x for x in c]

    # Count variables
    num_slack = 0
    num_artificial = 0
    row_info = []

    for op in ops:
        if op == '<=':
            num_slack += 1
            row_info.append({'type': 'slack', 'slack_idx': num_slack - 1, 'art_idx': -1})
        elif op == '>=':
            num_slack += 1
            num_artificial += 1
            row_info.append({'type': 'surplus', 'slack_idx': num_slack - 1, 'art_idx': num_artificial - 1})
        elif op == '=':
            num_artificial += 1
            row_info.append({'type': 'equality', 'slack_idx': -1, 'art_idx': num_artificial - 1})

    total_vars = n + num_slack + num_artificial

    if num_artificial == 0:
        tableau = _build_phase_two_tableau(c, A, b, ops, n, num_slack)
        basic_vars = _identify_basic_vars_phase_two(tableau, n, num_slack, row_info)
        total_vars_p2 = n + num_slack
        status, tableau, basic_vars = _simplex_iterate(tableau, basic_vars, total_vars_p2, is_phase_one=False)
        if status == 'unbounded':
            return {'status': 'unbounded', 'optimal_value': None, 'variables': []}
        return _extract_solution(tableau, basic_vars, n, num_slack, obj_type)

    # ── Phase I: Minimize sum of artificial variables ──────────────────────
    tableau = _build_phase_one_tableau(A, b, ops, n, num_slack, num_artificial, row_info)
    basic_vars = _identify_basic_vars(tableau, n, num_slack, num_artificial, row_info)

    status, tableau, basic_vars = _simplex_iterate(tableau, basic_vars, total_vars, is_phase_one=True)

    if status == 'unbounded':
        return {'status': 'unbounded', 'optimal_value': None, 'variables': []}

    # Check if Phase I found feasible solution
    w_value = _round_val(-tableau[0][-1])  # Phase I objective is max -W, so W = -Z
    if w_value > EPS:
        return {'status': 'infeasible', 'optimal_value': None, 'variables': []}

    # Check if any artificial variables remain basic with nonzero value
    for i in range(1, len(tableau)):
        bv = basic_vars[i]
        if bv and bv.startswith('a') and abs(tableau[i][-1]) > EPS:
            return {'status': 'infeasible', 'optimal_value': None, 'variables': []}

    # ── Phase II: Solve original problem ───────────────────────────────────
    phase2_tableau = _build_phase_two_from_phase_one(tableau, basic_vars, c, n, num_slack, num_artificial, row_info, total_vars)

    # Re-identify basic vars for Phase II (artificials may have been removed)
    basic_vars_p2 = _identify_basic_vars_phase_two(phase2_tableau, n, num_slack, row_info)

    status_p2, phase2_tableau, basic_vars_p2 = _simplex_iterate(phase2_tableau, basic_vars_p2, n + num_slack, is_phase_one=False)

    if status_p2 == 'unbounded':
        return {'status': 'unbounded', 'optimal_value': None, 'variables': []}

    return _extract_solution(phase2_tableau, basic_vars_p2, n, num_slack, obj_type)


# ═══════════════════════════════════════════════════════════════════════════════
#  Tableau Building
# ═══════════════════════════════════════════════════════════════════════════════

def _build_phase_one_tableau(A, b, ops, n, num_slack, num_artificial, row_info):
    m = len(A)
    total_vars = n + num_slack + num_artificial
    tableau = [[0.0] * (total_vars + 1) for _ in range(m + 1)]

    slack_pos = n
    art_pos = n + num_slack

    for i in range(m):
        row = i + 1
        for j in range(n):
            tableau[row][j] = A[i][j]

        ri = row_info[i]
        if ri['type'] == 'slack':
            tableau[row][slack_pos + ri['slack_idx']] = 1.0
        elif ri['type'] == 'surplus':
            tableau[row][slack_pos + ri['slack_idx']] = -1.0
            tableau[row][art_pos + ri['art_idx']] = 1.0
        elif ri['type'] == 'equality':
            tableau[row][art_pos + ri['art_idx']] = 1.0

        tableau[row][-1] = b[i]

    # Phase I objective: maximize -W = -sum(artificials)
    # In canonical form, Z row: express -W in terms of non-basic variables
    z_row = [0.0] * (total_vars + 1)

    # Set artificial variable coefficients to 1 (since we're maximizing -W = -∑a_i)
    art_start = n + num_slack
    for j in range(art_start, art_start + num_artificial):
        z_row[j] = 1.0

    # Eliminate basic artificial variables from Z row
    for i in range(m):
        row = i + 1
        ri = row_info[i]
        if ri['type'] in ('surplus', 'equality'):
            for j in range(total_vars + 1):
                z_row[j] -= tableau[row][j]

    tableau[0] = z_row
    return tableau


def _build_phase_two_tableau(c, A, b, ops, n, num_slack):
    m = len(A)
    total_vars = n + num_slack
    tableau = [[0.0] * (total_vars + 1) for _ in range(m + 1)]

    slack_pos = n
    for i in range(m):
        row = i + 1
        for j in range(n):
            tableau[row][j] = A[i][j]

        if ops[i] == '<=':
            tableau[row][slack_pos] = 1.0
        elif ops[i] == '>=':
            tableau[row][slack_pos] = -1.0

        slack_pos += 1
        tableau[row][-1] = b[i]

    # Objective row: Z - c^T x = 0 → Z row = [-c1, -c2, ..., -cn, 0, ..., 0 | 0]
    for j in range(n):
        tableau[0][j] = -c[j]
    tableau[0][-1] = 0.0

    return tableau


def _build_phase_two_from_phase_one(phase1_tableau, basic_vars, c, n, num_slack, num_artificial, row_info, total_vars_p1):
    """Drop artificial columns and restore original objective."""
    m = len(phase1_tableau) - 1
    total_vars_p2 = n + num_slack
    phase2_tableau = [[0.0] * (total_vars_p2 + 1) for _ in range(m + 1)]

    # Copy constraint rows (skip artificial columns)
    art_start = n + num_slack
    for i in range(1, m + 1):
        for j in range(n + num_slack):
            phase2_tableau[i][j] = phase1_tableau[i][j]
        phase2_tableau[i][-1] = phase1_tableau[i][-1]

    # Restore original objective row
    for j in range(n):
        phase2_tableau[0][j] = -c[j]

    # Eliminate basic variables from Z row to restore canonical form
    for i in range(1, m + 1):
        bv = basic_vars[i]
        if bv is None:
            continue

        col = _var_label_to_col(bv, n, num_slack)
        if col is None or col >= total_vars_p2:
            continue

        coef = phase2_tableau[0][col]
        if abs(coef) > EPS:
            factor = coef / phase2_tableau[i][col] if abs(phase2_tableau[i][col]) > EPS else 0
            for j in range(total_vars_p2 + 1):
                phase2_tableau[0][j] -= factor * phase2_tableau[i][j]

    return phase2_tableau


# ═══════════════════════════════════════════════════════════════════════════════
#  Simplex Iteration Engine
# ═══════════════════════════════════════════════════════════════════════════════

def _simplex_iterate(tableau, basic_vars, num_cols, is_phase_one=False):
    max_iter = 200
    iteration = 0

    while iteration < max_iter:
        iteration += 1

        # Find entering variable (most negative in Z row)
        pivot_col = -1
        most_negative = -EPS
        for j in range(num_cols):
            if tableau[0][j] < most_negative:
                most_negative = tableau[0][j]
                pivot_col = j

        if pivot_col == -1:
            # Optimal reached
            return 'optimal', tableau, basic_vars

        # Find leaving variable (minimum ratio test)
        pivot_row = -1
        min_ratio = float('inf')
        for i in range(1, len(tableau)):
            if tableau[i][pivot_col] > EPS:
                ratio = tableau[i][-1] / tableau[i][pivot_col]
                if ratio < min_ratio - EPS:
                    min_ratio = ratio
                    pivot_row = i
                elif abs(ratio - min_ratio) < EPS and ratio < min_ratio:
                    # Tie-breaking: prefer the smaller index (Bland's rule not needed here)
                    pass

        if pivot_row == -1:
            # No positive entry in pivot column → unbounded
            return 'unbounded', tableau, basic_vars

        # Pivot
        pivot_element = tableau[pivot_row][pivot_col]

        # Normalize pivot row
        for j in range(len(tableau[0])):
            tableau[pivot_row][j] /= pivot_element

        # Eliminate column in all other rows
        for i in range(len(tableau)):
            if i == pivot_row:
                continue
            factor = tableau[i][pivot_col]
            if abs(factor) > EPS:
                for j in range(len(tableau[0])):
                    tableau[i][j] -= factor * tableau[pivot_row][j]

        # Update basic variable
        basic_vars[pivot_row] = _col_to_label(pivot_col)

    return 'optimal', tableau, basic_vars


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _identify_basic_vars(tableau, n, num_slack, num_artificial, row_info):
    m = len(tableau) - 1
    basic_vars = ['Z'] + [None] * m
    total_vars = n + num_slack + num_artificial

    for i in range(1, m + 1):
        for j in range(total_vars):
            if abs(tableau[i][j] - 1.0) < EPS:
                # Check this column is unit vector
                is_unit = True
                for k in range(1, m + 1):
                    if k != i and abs(tableau[k][j]) > EPS:
                        is_unit = False
                        break
                if abs(tableau[0][j]) > EPS:
                    # Z row has nonzero entry — not a basic column in canonical form
                    pass
                if is_unit:
                    basic_vars[i] = _col_to_label(j)
                    break

    # Fallback: assign based on typical initial basis
    if any(bv is None for bv in basic_vars[1:]):
        slack_pos = n
        art_pos = n + num_slack
        for i in range(m):
            if basic_vars[i + 1] is not None:
                continue
            ri = row_info[i]
            if ri['type'] == 'slack':
                basic_vars[i + 1] = f's{ri["slack_idx"] + 1}'
            elif ri['type'] in ('surplus', 'equality'):
                basic_vars[i + 1] = f'a{ri["art_idx"] + 1}'

    return basic_vars


def _identify_basic_vars_phase_two(tableau, n, num_slack, row_info):
    m = len(tableau) - 1
    basic_vars = ['Z'] + [None] * m
    total_vars = n + num_slack

    for i in range(1, m + 1):
        for j in range(total_vars):
            if abs(tableau[i][j] - 1.0) < EPS:
                is_unit = True
                for k in range(1, m + 1):
                    if k != i and abs(tableau[k][j]) > EPS:
                        is_unit = False
                        break
                if is_unit:
                    basic_vars[i] = _col_to_label(j)
                    break

    if any(bv is None for bv in basic_vars[1:]):
        slack_pos = n
        for i in range(m):
            if basic_vars[i + 1] is not None:
                continue
            basic_vars[i + 1] = f's{slack_pos + 1}'
            slack_pos += 1

    return basic_vars


def _col_to_label(col):
    if col < 26:
        return f'x{col + 1}'
    s_idx = col - 26
    return f's{s_idx + 1}'


def _var_label_to_col(label, n, num_slack):
    if label.startswith('x'):
        idx = int(label[1:]) - 1
        if 0 <= idx < n:
            return idx
    elif label.startswith('s'):
        idx = int(label[1:]) - 1
        if 0 <= idx < num_slack:
            return n + idx
    elif label.startswith('a'):
        return None
    return None


def _extract_solution(tableau, basic_vars, n, num_slack, obj_type):
    """Read optimal solution from final tableau."""
    m = len(tableau) - 1

    optimal_value = _round_val(tableau[0][-1])
    if obj_type == 'min':
        optimal_value = -optimal_value

    variables = [0.0] * n
    for i in range(1, m + 1):
        bv = basic_vars[i]
        if bv and bv.startswith('x'):
            idx = int(bv[1:]) - 1
            if 0 <= idx < n:
                variables[idx] = _round_val(tableau[i][-1])

    # Check for multiple solutions: any non-basic variable with zero in Z row
    is_multiple = False
    total_vars = n + num_slack
    basic_cols = set()
    for i in range(1, m + 1):
        bv = basic_vars[i]
        if bv:
            col = _var_label_to_col(bv, n, num_slack)
            if col is not None:
                basic_cols.add(col)

    for j in range(total_vars):
        if j not in basic_cols and abs(tableau[0][j]) < EPS:
            # Zero reduced cost for non-basic variable → multiple optima
            # But exclude artificial/slack-only cases that are degenerate
            if j < n or (j >= n and abs(tableau[0][j]) < 1e-8):
                is_multiple = True
                break

    status = 'optimal_multiple' if is_multiple else 'optimal_unique'

    return {
        'status': status,
        'optimal_value': optimal_value,
        'variables': variables,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Public API for verification (replaces SciPy)
# ═══════════════════════════════════════════════════════════════════════════════

def verify_solution_type(c, A, b, operators, obj_type, expected_type):
    """
    Verify that an LP problem matches the expected solution type.
    Used by the generator to validate generated problems.
    """
    result = solve_simplex(c, A, b, operators, obj_type)

    status_map = {
        'unica': 'optimal_unique',
        'multiple': 'optimal_multiple',
        'sin_solucion': 'infeasible',
        'no_acotada': 'unbounded',
    }

    expected_status = status_map.get(expected_type)
    if expected_status is None:
        return False

    return result['status'] == expected_status


def classify_problem_manual(c, A, b, operators, obj_type):
    """
    Classify an LP problem into one of: unica, multiple, sin_solucion, no_acotada, error.
    """
    result = solve_simplex(c, A, b, operators, obj_type)

    status_map = {
        'optimal_unique': 'unica',
        'optimal_multiple': 'multiple',
        'infeasible': 'sin_solucion',
        'unbounded': 'no_acotada',
    }

    simplex_status = status_map.get(result['status'], 'error')

    return {
        'tipo_solucion': simplex_status,
        'optimal_value': result.get('optimal_value'),
        'variables': result.get('variables'),
    }
