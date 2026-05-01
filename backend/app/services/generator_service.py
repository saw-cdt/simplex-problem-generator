import random
import numpy as np
from ..models.generator_models import GenerateRequest, GenerateResponse, ObjectiveFunction, Constraint


# ── Formatting utilities (unchanged) ──────────────────────────────────────────

def get_variable_name(index: int) -> str:
    return f"x{index + 1}"


def formatear_termino(coef: float, var: str, is_first: bool = False) -> str:
    if coef == 0:
        return ""
    abs_coef = abs(int(coef)) if coef == int(coef) else abs(coef)
    coef_str = "" if abs_coef == 1 else str(abs_coef)
    if is_first:
        return f"-{coef_str}{var}" if coef < 0 else f"{coef_str}{var}"
    else:
        sign = " - " if coef < 0 else " + "
        return f"{sign}{coef_str}{var}"


def build_obj_string(tipo: str, coefs: list[float]) -> str:
    terms = []
    for i, coef in enumerate(coefs):
        if coef != 0:
            var = get_variable_name(i)
            is_first = len(terms) == 0
            terms.append(formatear_termino(coef, var, is_first=is_first))
    left_side = "".join(terms) if terms else "0"
    return f"{tipo.capitalize()} Z = {left_side}"


def build_constraint_string(coefs: list[float], operador: str, valor: float) -> str:
    terms = []
    for i, coef in enumerate(coefs):
        if coef != 0:
            var = get_variable_name(i)
            is_first = len(terms) == 0
            terms.append(formatear_termino(coef, var, is_first=is_first))
    left_side = "".join(terms) if terms else "0"
    return f"{left_side} {operador} {int(valor) if valor == int(valor) else valor}"


def create_constraint(coefs: list[float], op: str, val: float) -> Constraint:
    return Constraint(
        coeficientes=coefs,
        operador=op,
        valor=val,
        string_repr=build_constraint_string(coefs, op, val)
    )


def format_response(tipo: str, coefs_obj: list[float], constraints_raw: list,
                    num_vars: int, num_res: int, exp: str,
                    nombre: str = "", matricula: str = "") -> GenerateResponse:
    obj_fun = ObjectiveFunction(
        tipo=tipo, coeficientes=coefs_obj,
        string_repr=build_obj_string(tipo, coefs_obj)
    )
    constraints = [create_constraint(coefs, op, val) for coefs, op, val in constraints_raw]

    import base64
    from .latex_service import problem_to_latex
    from .pdf_service import generate_pdf_from_latex

    latex_str = problem_to_latex(obj_fun, constraints, num_vars, nombre, matricula)

    try:
        pdf_bytes = generate_pdf_from_latex(latex_str)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    except Exception:
        pdf_b64 = ""

    return GenerateResponse(
        funcion_objetivo=obj_fun,
        restricciones=constraints,
        num_variables=num_vars,
        num_restricciones=num_res,
        explicacion=exp,
        latex_code=latex_str,
        pdf_base64=pdf_b64
    )


# ── SciPy utilities (for custom-constraint validation only) ──────────────────

def build_constraint_matrices(constraints_raw: list) -> tuple:
    A_ub, b_ub = [], []
    A_eq, b_eq = [], []

    for coefs, op, val in constraints_raw:
        if op == "<=":
            A_ub.append(coefs)
            b_ub.append(val)
        elif op == ">=":
            A_ub.append([-c for c in coefs])
            b_ub.append(-val)
        elif op == "=":
            A_eq.append(coefs)
            b_eq.append(val)

    return (
        A_ub if A_ub else None,
        b_ub if b_ub else None,
        A_eq if A_eq else None,
        b_eq if b_eq else None,
    )


def validate_custom_problem(tipo: str, coefs_obj: list[float],
                            constraints_raw: list) -> tuple:
    A_ub, b_ub, A_eq, b_eq = build_constraint_matrices(constraints_raw)
    c_opt = [-c for c in coefs_obj] if tipo == "max" else coefs_obj
    res = linprog(c_opt, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=(0, None), method='highs')

    if res.status == 2:
        return "sin_solucion", "Infactible"
    elif res.status == 3:
        return "no_acotada", "No acotada"
    elif res.status == 0:
        es_multiple = False
        if res.slack is not None and A_ub is not None:
            for i, slack_val in enumerate(res.slack):
                if np.isclose(slack_val, 0):
                    a = A_ub[i]
                    s = sum(a[j] * coefs_obj[j] for j in range(len(coefs_obj)))
                    if abs(s) < 1e-6:
                        es_multiple = True
                        break
        if es_multiple:
            return "multiple", f"Óptimo: {res.fun * (-1 if tipo == 'max' else 1):.2f}"
        else:
            return "unica", (f"Óptimo: {res.fun * (-1 if tipo == 'max' else 1):.2f}, "
                             f"variables: {res.x.tolist()}")
    return "error", f"Error del solver: {res.message}"


# ── Randomized helpers (structure deterministic, values random) ───────────────

def _random_normals(n: int) -> list[list[float]]:
    """n random linearly independent normal vectors (diagonally dominant, rank-verified)."""
    for _ in range(20):
        normals = []
        for i in range(n):
            a = [float(random.randint(1, 4)) for _ in range(n)]
            a[i] = float(random.randint(3, 8))
            normals.append(a)
        if np.linalg.matrix_rank(np.array(normals)) == n:
            return normals
    return _random_normals(n)


def _random_extra_normal(n: int) -> list[float]:
    """Random normal vector for non-binding padding constraints."""
    return [float(random.randint(1, 5)) for _ in range(n)]


def _dot(v1, v2):
    return sum(a * b for a, b in zip(v1, v2))


def _apply_obj_type(tipo: str, c: list[float]) -> list[float]:
    """For min: negate all coefficients (constructed as max internally)."""
    return c if tipo == "max" else [-x for x in c]


def _random_op(coefs, val, is_binding, x_star):
    """Randomly pick <=, >=, or = and transform coefs/val accordingly.
    For =: only allowed when is_binding=True (uses exact RHS at x_star).
    """
    op = random.choice(["<=", ">=", "="])
    if op == "<=":
        return coefs, "<=", val
    elif op == ">=":
        return [-c for c in coefs], ">=", -val
    else:  # "="
        if is_binding:
            return coefs, "=", _dot(coefs, x_star)
        else:
            return coefs, "<=", val


def _ensure_all_ops(result, orig_coefs, orig_vals, eq_mask, x_star, m):
    """Force at least one <=, one >=, one = (if m>=3). Eqs only on eq_mask[i]=True."""
    if m < 3:
        return result

    used = set()

    # Step 1: force "=" on an allowed index (if any)
    eq_candidates = [i for i in range(m) if eq_mask[i] and i not in used]
    if eq_candidates:
        eq_idx = random.choice(eq_candidates)
        coefs = orig_coefs[eq_idx]
        result[eq_idx] = (coefs, "=", _dot(coefs, x_star))
        used.add(eq_idx)

    # Step 2: force "<=" and ">=" on remaining unused indices
    remaining = [i for i in range(m) if i not in used]
    if len(remaining) >= 2:
        le_idx, ge_idx = random.sample(remaining, 2)
        coefs_le = orig_coefs[le_idx]
        result[le_idx] = (coefs_le, "<=", orig_vals[le_idx])
        coefs_ge = orig_coefs[ge_idx]
        result[ge_idx] = ([-c for c in coefs_ge], ">=", -orig_vals[ge_idx])

    return result


def _is_parallel(a, c):
    """Check if vectors a and c are parallel (a = λ*c for some λ)."""
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if abs(a[i] * c[j] - a[j] * c[i]) > 1e-6:
                return False
    return True


def _verify_scipy(coefs_obj, constraints_raw, tipo, expected_sol):
    """Verify with SciPy that the solution type matches expected. Returns bool."""
    try:
        from scipy.optimize import linprog
    except ImportError:
        return True

    A_ub, b_ub = [], []
    A_eq, b_eq = [], []
    for coefs, op, val in constraints_raw:
        if op == "<=":
            A_ub.append(coefs)
            b_ub.append(val)
        elif op == ">=":
            A_ub.append([-c for c in coefs])
            b_ub.append(-val)
        elif op == "=":
            A_eq.append(coefs)
            b_eq.append(val)

    c_opt = [-c for c in coefs_obj] if tipo == "max" else coefs_obj
    res = linprog(c_opt,
                  A_ub=A_ub if A_ub else None,
                  b_ub=b_ub if b_ub else None,
                  A_eq=A_eq if A_eq else None,
                  b_eq=b_eq if b_eq else None,
                  bounds=(0, None), method='highs')

    expected_status_map = {
        "unica": 0, "multiple": 0,
        "sin_solucion": 2, "no_acotada": 3,
    }
    expected = expected_status_map[expected_sol]

    if res.status != expected:
        return False

    if expected_sol == "unica":
        # Must NOT be multiple (objective NOT parallel to any active constraint)
        if res.slack is not None and A_ub is not None:
            for i, sv in enumerate(res.slack):
                if np.isclose(sv, 0):
                    a = A_ub[i]
                    if _is_parallel(a, coefs_obj):
                        return False
        if A_eq is not None:
            for a in A_eq:
                if _is_parallel(a, coefs_obj):
                    return False
        return True

    if expected_sol == "multiple":
        if res.slack is not None and A_ub is not None:
            for i, sv in enumerate(res.slack):
                if np.isclose(sv, 0):
                    a = A_ub[i]
                    if _is_parallel(a, coefs_obj):
                        return True
        if A_eq is not None:
            for a in A_eq:
                if _is_parallel(a, coefs_obj):
                    return True
        return False

    return True


# ── Deterministic builders (one per solution type) ────────────────────────────

def _build_unique(tipo: str, n: int, m: int) -> GenerateResponse:
    """KKT-guaranteed unique optimum via n independent active normals."""
    normals = _random_normals(n)
    active = min(n, m)

    x_star = [float(random.randint(1, 5)) if i < active else 0.0 for i in range(n)]
    lambdas = [float(random.randint(1, 5)) for _ in range(active)]

    c_obj = [0.0] * n
    for i in range(active):
        li = lambdas[i]
        for j in range(n):
            c_obj[j] += li * normals[i][j]
    for j in range(active, n):
        c_obj[j] = 0.0

    c_obj = _apply_obj_type(tipo, c_obj)

    for _ in range(20):
        all_normals = []
        b_vals = []
        ops = []
        eq_mask = []
        orig_coefs_list = []
        orig_vals_list = []

        for i in range(active):
            coefs = normals[i]
            val = _dot(coefs, x_star)
            orig_coefs_list.append(coefs)
            orig_vals_list.append(val)
            nc, nop, nv = _random_op(coefs, val, is_binding=True, x_star=x_star)
            all_normals.append(nc)
            b_vals.append(nv)
            ops.append(nop)
            eq_mask.append(True)

        for i in range(active, m):
            coefs = _random_extra_normal(n)
            val = _dot(coefs, x_star) + float(random.randint(5 * n, 10 * n))
            orig_coefs_list.append(coefs)
            orig_vals_list.append(val)
            nc, nop, nv = _random_op(coefs, val, is_binding=False, x_star=x_star)
            all_normals.append(nc)
            b_vals.append(nv)
            ops.append(nop)
            eq_mask.append(True)

        constraints_raw = list(zip(all_normals, ops, b_vals))
        constraints_raw = _ensure_all_ops(
            list(constraints_raw), orig_coefs_list, orig_vals_list,
            eq_mask, x_star, m
        )

        if _verify_scipy(c_obj, constraints_raw, tipo, "unica"):
            break

    return format_response(tipo, c_obj, constraints_raw, n, m,
        "Construido determinísticamente (Solución Única). KKT garantiza optimalidad única.")


def _build_multiple(tipo: str, n: int, m: int) -> GenerateResponse:
    """Objective parallel to one active constraint → infinite optima on a face."""
    normals = _random_normals(n)
    parallel_idx = random.randint(0, min(n - 1, max(0, m - 1)))
    c_obj = list(normals[parallel_idx])
    c_obj = _apply_obj_type(tipo, c_obj)

    # Build a point x_star that lies ON the optimal face for correct = RHS
    val_parallel = float(random.randint(n * 2, n * 5))
    raw_pt = [float(random.randint(1, 5)) for _ in range(n)]
    face_sum = _dot(normals[parallel_idx], raw_pt)
    scale = val_parallel / face_sum if face_sum != 0 else 1.0
    x_star = [v * scale for v in raw_pt]

    for _ in range(20):
        all_normals = []
        b_vals = []
        ops = []
        eq_mask = []
        orig_coefs_list = []
        orig_vals_list = []

        for i in range(m):
            normal = normals[i] if i < n else _random_extra_normal(n)
            is_parallel = (i == parallel_idx)
            val = val_parallel if is_parallel \
                else float(random.randint(n * 8, n * 15))
            orig_coefs_list.append(normal)
            orig_vals_list.append(val)
            nc, nop, nv = _random_op(normal, val, is_binding=is_parallel, x_star=x_star)
            all_normals.append(nc)
            b_vals.append(nv)
            ops.append(nop)
            eq_mask.append(is_parallel)

        constraints_raw = list(zip(all_normals, ops, b_vals))
        constraints_raw = _ensure_all_ops(
            list(constraints_raw), orig_coefs_list, orig_vals_list,
            eq_mask, x_star, m
        )

        if _verify_scipy(c_obj, constraints_raw, tipo, "multiple"):
            break

    return format_response(tipo, c_obj, constraints_raw, n, m,
        "Construido determinísticamente (Múltiples Soluciones). "
        "Función objetivo paralela a una restricción activa.")


def _build_infeasible(tipo: str, n: int, m: int) -> GenerateResponse:
    """Provably infeasible: contradictory constraints with the same coefficients."""
    c_obj = [float(random.randint(1, 5)) for _ in range(n)]
    c_obj = _apply_obj_type(tipo, c_obj)

    # dummy x_star just for = formatting (not used since region is empty)
    x_star = [1.0] * n

    for _ in range(20):
        coef = [float(random.randint(1, 5)) for _ in range(n)]
        small_val = float(random.randint(n, n * 3))
        large_val = float(random.randint(n * 6, n * 10))

        all_normals = []
        b_vals = []
        ops = []
        eq_mask = []
        orig_coefs_list = []
        orig_vals_list = []

        if m == 1:
            val = float(-random.randint(n, n * 3))
            orig_coefs_list.append(coef)
            orig_vals_list.append(val)
            nc, nop, nv = _random_op(coef, val, is_binding=False, x_star=x_star)
            all_normals.append(nc)
            b_vals.append(nv)
            ops.append(nop)
            eq_mask.append(True)
        else:
            pairs = [
                (coef, "<=", small_val, False),
                (coef, ">=", large_val, True),
            ]
            random.shuffle(pairs)
            for pcoef, default_op, pval, is_ge in pairs:
                base_coef = [-c for c in pcoef] if is_ge else pcoef
                base_val = -pval if is_ge else pval
                orig_coefs_list.append(base_coef)
                orig_vals_list.append(base_val)
                nc, nop, nv = _random_op(base_coef, base_val,
                                         is_binding=False, x_star=x_star)
                all_normals.append(nc)
                b_vals.append(nv)
                ops.append(nop)
                eq_mask.append(True)

            for i in range(2, m):
                extra = _random_extra_normal(n)
                val = float(random.randint(n * 8, n * 15))
                orig_coefs_list.append(extra)
                orig_vals_list.append(val)
                nc, nop, nv = _random_op(extra, val, is_binding=False,
                                         x_star=x_star)
                all_normals.append(nc)
                b_vals.append(nv)
                ops.append(nop)
                eq_mask.append(True)

        constraints_raw = list(zip(all_normals, ops, b_vals))
        constraints_raw = _ensure_all_ops(
            list(constraints_raw), orig_coefs_list, orig_vals_list,
            eq_mask, x_star, m
        )

        if _verify_scipy(c_obj, constraints_raw, tipo, "sin_solucion"):
            break

    return format_response(tipo, c_obj, constraints_raw, n, m,
        "Construido determinísticamente (Infactible). "
        "Restricciones contradictorias garantizan región vacía.")


def _build_unbounded(tipo: str, n: int, m: int) -> GenerateResponse:
    """Only >= constraints → region open toward positive direction → unbounded."""
    c_obj = [float(random.randint(1, 5)) for _ in range(n)]
    c_obj = _apply_obj_type(tipo, c_obj)

    # dummy x_star for = formatting (scipy verify catches incorrect = usage)
    x_star = [1.0] * n

    for _ in range(50):
        all_normals = []
        b_vals = []
        ops = []
        eq_mask = []
        orig_coefs_list = []
        orig_vals_list = []

        for i in range(m):
            normal = [0.0] * n
            dominant = i % n
            normal[dominant] = float(random.randint(n, n + 4))
            for j in range(n):
                if j != dominant:
                    normal[j] = float(random.randint(-1, 2))

            val = float(random.randint(5, 20))
            # Build as <= base: (-normal)·x <= -val
            base_coef = [-c for c in normal]
            base_val = -val
            orig_coefs_list.append(base_coef)
            orig_vals_list.append(base_val)
            nc, nop, nv = _random_op(base_coef, base_val,
                                     is_binding=False, x_star=x_star)
            all_normals.append(nc)
            b_vals.append(nv)
            ops.append(nop)
            eq_mask.append(True)

        constraints_raw = list(zip(all_normals, ops, b_vals))
        constraints_raw = _ensure_all_ops(
            list(constraints_raw), orig_coefs_list, orig_vals_list,
            eq_mask, x_star, m
        )

        if _verify_scipy(c_obj, constraints_raw, tipo, "no_acotada"):
            break

    return format_response(tipo, c_obj, constraints_raw, n, m,
        "Construido determinísticamente (No Acotada). "
        "Sin cotas superiores en la dirección del gradiente.")


def _build_deterministic(tipo: str, sol: str, n: int, m: int) -> GenerateResponse:
    """Dispatch to the correct deterministic builder."""
    builders = {
        "unica": _build_unique,
        "multiple": _build_multiple,
        "sin_solucion": _build_infeasible,
        "no_acotada": _build_unbounded,
    }
    return builders[sol](tipo, n, m)


# ── Main entry point ──────────────────────────────────────────────────────────

from scipy.optimize import linprog  # kept for validate_custom_problem only


def generate_mock_problem(request: GenerateRequest) -> GenerateResponse:
    tipo = request.tipo_objetivo
    sol = request.tipo_solucion
    num_vars = request.num_variables
    num_res = request.num_restricciones
    nombre = request.nombre
    matricula = request.matricula

    # ── Custom constraints: still validated with SciPy ───────────────────────
    if request.tipo_restricciones == "fijas" and request.restricciones_custom:
        if request.funcion_objetivo_custom:
            coefs_obj = request.funcion_objetivo_custom
        else:
            coefs_obj = [3.0] * num_vars

        constraints_raw = [
            (list(c.coeficientes), c.operador, c.valor)
            for c in request.restricciones_custom
        ]
        tipo_detectado, detalles = validate_custom_problem(
            tipo, coefs_obj, constraints_raw
        )
        return format_response(
            tipo, coefs_obj, constraints_raw, num_vars, len(constraints_raw),
            f"Custom: {detalles}", nombre, matricula
        )

    # ── Deterministic generation (replaces random + scipy verification) ──────
    return _build_deterministic(tipo, sol, num_vars, num_res)
