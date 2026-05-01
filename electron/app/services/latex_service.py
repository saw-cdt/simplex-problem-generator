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

def problem_to_latex(obj: ObjectiveFunction, restricciones: list[Constraint],
                     num_variables: int = 2, nombre: str = "", matricula: str = "") -> str:
    lines = []
    
    lines.append(r"\begin{center}")
    lines.append(r"\textbf{\Large EXAMEN DE PROGRAMACIÓN LINEAL}")
    lines.append(r"\end{center}")
    lines.append(r"\vspace{0.3cm}")
    
    lines.append(r"\begin{center}")
    lines.append(r"\begin{tabular}{p{0.4\linewidth} p{0.4\linewidth}}")
    lines.append(r"\textbf{Nombre:} \underline{\hspace{5cm}} & \textbf{Matrícula:} \underline{\hspace{4cm}} \\")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{center}")
    lines.append(r"\vspace{0.5cm}")
    
    lines.append(r"\textbf{Función Objetivo:}")
    lines.append(r"\vspace{0.2cm}")
    
    terms = []
    for i, coef in enumerate(obj.coeficientes):
        if coef != 0:
            var = get_variable_name_latex(i)
            is_first = len(terms) == 0
            terms.append(formatear_termino_latex(coef, var, is_first=is_first))
    
    if not terms:
        right_side = "0"
    else:
        right_side = "".join(terms)
    
    tipo_str = r"\textbf{Maximizar }" if obj.tipo.lower() == "max" else r"\textbf{Minimizar }"
    lines.append(r"\begin{center}")
    lines.append(f"{tipo_str}$Z = {right_side}$")
    lines.append(r"\end{center}")
    lines.append(r"\vspace{0.8cm}")
    
    lines.append(r"\textbf{Restricciones:}")
    lines.append(r"\vspace{0.2cm}")
    lines.append(r"\begin{enumerate}")
    lines.append(r"\setlength{\itemsep}{0.3cm}")
    
    for rest in restricciones:
        terms_r = []
        for i, coef in enumerate(rest.coeficientes):
            if coef != 0:
                var = get_variable_name_latex(i)
                is_first = len(terms_r) == 0
                terms_r.append(formatear_termino_latex(coef, var, is_first=is_first))
        
        if not terms_r:
            left_r = "0"
        else:
            left_r = "".join(terms_r)
        
        val = int(rest.valor) if rest.valor == int(rest.valor) else round(rest.valor, 2)
        
        op_map = {"<=": r"\leq", ">=": r"\geq", "=": "="}
        op_latex = op_map.get(rest.operador, rest.operador)
        
        lines.append(r"\item $")
        lines.append(f"{left_r} {op_latex} {val}")
        lines.append(r"$")
    
    lines.append(r"\end{enumerate}")
    lines.append(r"\vspace{0.5cm}")
    
    lines.append(r"\textbf{Restricciones de no negatividad:}")
    lines.append(r"\vspace{0.2cm}")
    lines.append(r"\begin{center}")
    
    var_names = [get_variable_name_latex(i) for i in range(num_variables)]
    nn_str = ", ".join(var_names) + r" \geq 0"
    lines.append(f"${nn_str}$")
    
    lines.append(r"\end{center}")
    
    return "\n".join(lines)