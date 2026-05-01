import random
import numpy as np
from scipy.optimize import linprog
from ..models.generator_models import GenerateRequest, GenerateResponse, ObjectiveFunction, Constraint

def get_random_operator(prob_le=0.6, prob_ge=0.3) -> str:
    """Retorna un operador aleatorio: <=, >= o ="""
    r = random.random()
    if r < prob_le:
        return "<="
    elif r < prob_le + prob_ge:
        return ">="
    else:
        return "="

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
    n = len(coefs)
    terms = []
    for i, coef in enumerate(coefs):
        if coef != 0:
            var = get_variable_name(i)
            is_first = len(terms) == 0
            terms.append(formatear_termino(coef, var, is_first=is_first))
    
    if not terms:
        left_side = "0"
    else:
        left_side = "".join(terms)
    
    return f"{tipo.capitalize()} Z = {left_side}"

def build_constraint_string(coefs: list[float], operador: str, valor: float) -> str:
    terms = []
    for i, coef in enumerate(coefs):
        if coef != 0:
            var = get_variable_name(i)
            is_first = len(terms) == 0
            terms.append(formatear_termino(coef, var, is_first=is_first))
    
    if not terms:
        left_side = "0"
    else:
        left_side = "".join(terms)
    
    return f"{left_side} {operador} {int(valor) if valor == int(valor) else valor}"

def create_constraint(coefs: list[float], op: str, val: float) -> Constraint:
    return Constraint(
        coeficientes=coefs,
        operador=op,
        valor=val,
        string_repr=build_constraint_string(coefs, op, val)
    )

def format_response(tipo: str, coefs_obj: list[float], constraints_raw: list, 
                    num_vars: int, num_res: int, exp: str, nombre: str = "", matricula: str = "") -> GenerateResponse:
    obj_fun = ObjectiveFunction(tipo=tipo, coeficientes=coefs_obj, string_repr=build_obj_string(tipo, coefs_obj))
    constraints = [create_constraint(coefs, op, val) for coefs, op, val in constraints_raw]
    
    import base64
    from .latex_service import problem_to_latex
    from .pdf_service import generate_pdf_from_latex
    
    latex_str = problem_to_latex(obj_fun, constraints, num_vars, nombre, matricula)
    
    try:
        pdf_bytes = generate_pdf_from_latex(latex_str)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    except Exception as e:
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

def check_degeneracy(res, num_vars: int) -> bool:
    if res.slack is None or res.x is None:
        return False
    active_constraints = sum(np.isclose(res.slack, 0))
    active_bounds = sum(np.isclose(res.x, 0))
    return (active_constraints + active_bounds) > num_vars

def build_constraint_matrices(constraints_raw: list) -> tuple:
    """Convierte restricciones al formato de scipy linprog"""
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
    
    A_ub = A_ub if A_ub else None
    b_ub = b_ub if b_ub else None
    A_eq = A_eq if A_eq else None
    b_eq = b_eq if b_eq else None
    
    return A_ub, b_ub, A_eq, b_eq

def generate_random_problem(tipo: str, sol: str, num_vars: int, num_res: int) -> GenerateResponse:
    max_retries = 500
    for _ in range(max_retries):
        coefs_obj = [float(random.randint(1, 10)) for _ in range(num_vars)]
        
        constraints_raw = []
        
        def add_constraint(coefs, op, val):
            constraints_raw.append((coefs, op, val))
        
        if sol == "unica":
            for _ in range(num_res):
                coefs = [float(random.randint(0, 5)) for _ in range(num_vars)]
                if all(c == 0 for c in coefs):
                    coefs[random.randint(0, num_vars - 1)] = 1.0
                b = float(random.randint(10, 40))
                op = get_random_operator()
                add_constraint(coefs, op, b)
            
            A_ub, b_ub, A_eq, b_eq = build_constraint_matrices(constraints_raw)
            c_opt = [-c for c in coefs_obj] if tipo == "max" else coefs_obj
            res = linprog(c_opt, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
            
            if res.status == 0 and not check_degeneracy(res, num_vars):
                return format_response(tipo, coefs_obj, constraints_raw, num_vars, num_res,
                    "Generado aleatoriamente (Solución Única). Verificado con SciPy.")
                
        elif sol == "multiple":
            base_coefs = [float(random.randint(1, 5)) for _ in range(num_vars)]
            b = float(random.randint(20, 40))
            op_base = get_random_operator(0.8, 0.1)
            add_constraint(base_coefs, op_base, b)
            
            for i in range(min(num_vars, num_res - 1)):
                axis_coefs = [0.0] * num_vars
                axis_coefs[i] = 1.0
                b_axis = float(random.randint(10, 30))
                op_axis = get_random_operator(0.9, 0.0)
                add_constraint(axis_coefs, op_axis, b_axis)
            
            for _ in range(num_res - num_vars - 1):
                if num_res - num_vars - 1 <= 0: break
                coefs = [float(random.randint(0, 3)) for _ in range(num_vars)]
                b = float(random.randint(5, 20))
                op = get_random_operator()
                add_constraint(coefs, op, b)
            
            A_ub, b_ub, A_eq, b_eq = build_constraint_matrices(constraints_raw)
            mult = float(random.randint(1, 3))
            coefs_obj_m = [c * mult for c in base_coefs]
            c_opt = [-c for c in coefs_obj_m] if tipo == "max" else coefs_obj_m
            res = linprog(c_opt, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
            
            if res.status == 0:
                return format_response(tipo, coefs_obj_m, constraints_raw, num_vars, num_res,
                    "Generado aleatoriamente (Solución Múltiple).")
                
        elif sol == "sin_solucion":
            base_coefs = [float(random.randint(1, 5)) for _ in range(num_vars)]
            b1 = float(random.randint(5, 15))
            b2 = float(random.randint(20, 50))
            
            add_constraint(base_coefs, "<=", b1)
            add_constraint(base_coefs, ">=", b2)
            
            if num_res > 2:
                for _ in range(num_res - 2):
                    coefs = [float(random.randint(0, 3)) for _ in range(num_vars)]
                    if all(c == 0 for c in coefs):
                        coefs[random.randint(0, num_vars - 1)] = 1.0
                    b = float(random.randint(10, 25))
                    op = get_random_operator()
                    add_constraint(coefs, op, b)
            
            A_ub, b_ub, A_eq, b_eq = build_constraint_matrices(constraints_raw)
            c_opt = [-c for c in coefs_obj] if tipo == "max" else coefs_obj
            res = linprog(c_opt, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
            
            if res.status == 2:
                return format_response(tipo, coefs_obj, constraints_raw, num_vars, num_res,
                    "Generado aleatoriamente (Infactible). SciPy confirmó región vacía.")
                
        elif sol == "no_acotada":
            if tipo == "max":
                coefs = [float(random.randint(-5, -1)) if i == 0 else float(random.randint(1, 5)) 
                        for i in range(num_vars)]
                b = float(random.randint(5, 15))
                op = get_random_operator(0.5, 0.5)
                add_constraint(coefs, op, b)
                
                for _ in range(num_res - 1):
                    coefs_extra = [float(random.randint(0, 3)) for _ in range(num_vars)]
                    if all(c == 0 for c in coefs_extra):
                        coefs_extra[random.randint(0, num_vars - 1)] = 1.0
                    b_extra = float(random.randint(10, 25))
                    op_extra = get_random_operator()
                    add_constraint(coefs_extra, op_extra, b_extra)
                
                A_ub, b_ub, A_eq, b_eq = build_constraint_matrices(constraints_raw)
                res = linprog([-c for c in coefs_obj], A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
                if res.status == 3:
                    return format_response(tipo, coefs_obj, constraints_raw, num_vars, num_res,
                        "Generado aleatoriamente (No acotada).")
            else:
                coefs_obj_n = [-float(random.randint(1, 10)) for _ in range(num_vars)]
                coefs = [float(random.randint(1, 5)) for _ in range(num_vars)]
                b = float(random.randint(10, 20))
                op = get_random_operator(0.2, 0.7)
                add_constraint(coefs, op, b)
                
                for _ in range(num_res - 1):
                    coefs_extra = [float(random.randint(0, 3)) for _ in range(num_vars)]
                    if all(c == 0 for c in coefs_extra):
                        coefs_extra[random.randint(0, num_vars - 1)] = 1.0
                    b_extra = float(random.randint(10, 25))
                    op_extra = get_random_operator()
                    add_constraint(coefs_extra, op_extra, b_extra)
                
                A_ub, b_ub, A_eq, b_eq = build_constraint_matrices(constraints_raw)
                res = linprog(coefs_obj_n, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
                if res.status == 3:
                    return format_response(tipo, coefs_obj_n, constraints_raw, num_vars, num_res,
                        "Generado aleatoriamente (No acotada).")

    return None

def validate_custom_problem(tipo: str, coefs_obj: list[float], constraints_raw: list) -> tuple:
    """Valida un problema custom con el solver"""
    A_ub, b_ub, A_eq, b_eq = build_constraint_matrices(constraints_raw)
    
    c_opt = [-c for c in coefs_obj] if tipo == "max" else coefs_obj
    res = linprog(c_opt, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
    
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
                    cross = abs(sum(coefs_obj[j] * a[j] for j in range(len(coefs_obj))) * 0 - 
                              sum(a[j] * coefs_obj[j] for j in range(len(coefs_obj))))
                    if cross < 1e-6:
                        es_multiple = True
                        break
        if es_multiple:
            return "multiple", f"Óptimo: {res.fun * (-1 if tipo == 'max' else 1):.2f}"
        else:
            return "unica", f"Óptimo: {res.fun * (-1 if tipo == 'max' else 1):.2f}, variables: {res.x.tolist()}"
    
    return "error", f"Error del solver: {res.message}"

def generate_mock_problem(request: GenerateRequest) -> GenerateResponse:
    tipo = request.tipo_objetivo
    sol = request.tipo_solucion
    num_vars = request.num_variables
    num_res = request.num_restricciones
    nombre = request.nombre
    matricula = request.matricula
    
    if request.tipo_restricciones == "aleatorias":
        result = generate_random_problem(tipo, sol, num_vars, num_res)
        if result:
            result.funcion_objetivo.string_repr = build_obj_string(tipo, result.funcion_objetivo.coeficientes)
            result.latex_code = result.latex_code
            return result
    
    if request.tipo_restricciones == "fijas" and request.restricciones_custom:
        if request.funcion_objetivo_custom:
            coefs_obj = request.funcion_objetivo_custom
        else:
            coefs_obj = [3.0] * num_vars
        
        constraints_raw = [(list(c.coeficientes), c.operador, c.valor) for c in request.restricciones_custom]
        
        tipo_detectado, detalles = validate_custom_problem(tipo, coefs_obj, constraints_raw)
        
        return format_response(
            tipo, coefs_obj, constraints_raw, num_vars, len(constraints_raw),
            f"Custom: {detalles}", nombre, matricula
        )
    
    mod = random.randint(1, 5)
    coefs_obj = [3.0 * mod] * num_vars
    constraints_raw = []
    explicacion = "Fallback: problema fijo no validado por solver."
    
    if sol == "unica":
        for i in range(min(num_res, 3)):
            coefs = [0.0] * num_vars
            coefs[i] = 1.0 if i < num_vars else 0.0
            if i < num_vars:
                coefs[i] = float(4 + i * 2)
            else:
                coefs[i % num_vars] = float(4 + i)
            b = float((4 + i * 4) * mod)
            constraints_raw.append((coefs, "<=", b))
    elif sol == "multiple":
        base = [2.0 + i for i in range(num_vars)]
        constraints_raw.append((base, "<=", 12.0 * mod))
        for i in range(min(num_vars, num_res - 1)):
            coefs = [0.0] * num_vars
            coefs[i] = 1.0
            constraints_raw.append((coefs, "<=", 10.0 * mod))
        coefs_obj = [c * 2 for c in base]
    elif sol == "sin_solucion":
        ones = [1.0] * num_vars
        constraints_raw.append((ones, "<=", 2.0 * mod))
        constraints_raw.append((ones, ">=", 5.0 * mod))
    elif sol == "no_acotada":
        if tipo == "max":
            coefs = [1.0] * (num_vars - 1) + [-1.0]
            constraints_raw.append((coefs, "<=", 2.0 * mod))
        else:
            coefs_obj = [-2.0 * mod] * num_vars
            ones = [1.0] * num_vars
            constraints_raw.append((ones, ">=", 10.0 * mod))
    
    return format_response(tipo, coefs_obj, constraints_raw, num_vars, len(constraints_raw),
                          explicacion, nombre, matricula)