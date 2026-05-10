from ..models.generator_models import ObjectiveFunction, Constraint


def get_variable_name_latex(index: int) -> str:
    return f"x_{{{index + 1}}}"


def formatear_termino_latex(coef: float, var: str, is_first: bool = False) -> str:
    if coef == 0:
        return ""

    coef_val = int(coef) if coef == int(coef) else round(coef, 2)
    abs_coef = abs(coef_val)
    coef_str = "" if abs_coef == 1 else str(abs_coef)

    if is_first:
        return f"-{coef_str}{var}" if coef < 0 else f"{coef_str}{var}"
    else:
        sign = " - " if coef < 0 else " + "
        return f"{sign}{coef_str}{var}"


def _build_objective_math(obj, num_vars):
    terms = []
    for i, coef in enumerate(obj.coeficientes):
        if coef != 0:
            var = get_variable_name_latex(i)
            is_first = len(terms) == 0
            terms.append(formatear_termino_latex(coef, var, is_first=is_first))

    right_side = "".join(terms) if terms else "0"
    tipo_str = r"\text{Maximizar}" if obj.tipo.lower() == "max" else r"\text{Minimizar}"
    return f"${tipo_str}\\quad Z = {right_side}$"


def _build_constraint_item(rest, n_vars):
    op_map = {"<=": r"\leq", ">=": r"\geq", "=": "="}
    terms = []
    for i, coef in enumerate(rest.coeficientes):
        if i >= n_vars:
            break
        if coef != 0:
            var = get_variable_name_latex(i)
            is_first = len(terms) == 0
            terms.append(formatear_termino_latex(coef, var, is_first=is_first))

    left = "".join(terms) if terms else "0"
    val = int(rest.valor) if rest.valor == int(rest.valor) else round(rest.valor, 2)
    op_latex = op_map.get(rest.operador, rest.operador)
    return f"$\\displaystyle {left} {op_latex} {val}$"


def _exam_header(instrucciones=""):
    lines = []

    lines.append(r"\begin{center}")
    lines.append(r"{\LARGE\textbf{EXAMEN DE PROGRAMACI\'ON LINEAL}}")
    lines.append(r"\vspace{1cm}")
    lines.append(r"\begin{tabular}{rl}")
    lines.append(r"\textbf{Nombre:}    & \underline{\hspace{8cm}} \\[0.4cm]")
    lines.append(r"\textbf{Matr\'icula:} & \underline{\hspace{8cm}} \\[0.4cm]")
    lines.append(r"\textbf{Aula:}      & \underline{\hspace{8cm}}")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{center}")

    if instrucciones.strip():
        lines.append(r"\vspace{0.5cm}")
        lines.append(r"\noindent\textbf{Instrucciones:}")
        lines.append(r"")
        lines.append(r"\noindent " + instrucciones)

    return lines


def _problem_body(obj, restricciones, num_vars, numero_problema=None):
    lines = []

    if numero_problema is not None:
        lines.append(r"\vspace{0.5cm}")
        lines.append(r"\hrule")
        lines.append(r"\vspace{0.4cm}")
        lines.append(r"\textbf{Problema " + str(numero_problema) + r"}")
        lines.append(r"\vspace{0.3cm}")
    else:
        lines.append(r"\vspace{0.6cm}")
        lines.append(r"\hrule")
        lines.append(r"\vspace{0.5cm}")

    lines.append(r"\begin{center}")
    lines.append(_build_objective_math(obj, num_vars))
    lines.append(r"\end{center}")
    lines.append(r"\vspace{0.4cm}")

    lines.append(r"\noindent\textbf{Sujeto a:}")
    lines.append(r"")
    lines.append(r"\begin{enumerate}")
    lines.append(r"\setlength{\itemsep}{2pt}")
    lines.append(r"\setlength{\leftmargin}{2cm}")

    for rest in restricciones:
        lines.append(r"\item " + _build_constraint_item(rest, num_vars))

    lines.append(r"\end{enumerate}")
    lines.append(r"\vspace{0.3cm}")

    nn_vars = ", ".join([get_variable_name_latex(i) for i in range(num_vars)])
    lines.append(r"\noindent$" + nn_vars + r" \geq 0$")

    return lines


def problem_to_latex(obj: ObjectiveFunction, restricciones: list[Constraint],
                     num_variables: int = 2, nombre: str = "", matricula: str = "",
                     aula: str = "", instrucciones: str = "",
                     numero_problema: int = 1) -> str:
    lines = _exam_header(instrucciones)
    lines.extend(_problem_body(obj, restricciones, num_variables))
    return "\n".join(lines)


def problems_to_latex_exam(problemas: list[dict], instrucciones: str = "") -> str:
    lines = _exam_header(instrucciones)

    for idx, prob in enumerate(problemas):
        num = idx + 1
        obj = prob.get('funcion_objetivo', {})
        restricciones = prob.get('restricciones', [])
        num_vars = prob.get('num_variables', 2)

        rest_objs = []
        for r in restricciones:
            rest_objs.append(Constraint(
                coeficientes=r.get('coeficientes', []),
                operador=r.get('operador', '<='),
                valor=r.get('valor', 0),
                string_repr=""
            ))

        obj_model = ObjectiveFunction(
            tipo=obj.get('tipo', 'max'),
            coeficientes=obj.get('coeficientes', []),
            string_repr=""
        )

        lines.extend(_problem_body(obj_model, rest_objs, num_vars, num))

    return "\n".join(lines)
