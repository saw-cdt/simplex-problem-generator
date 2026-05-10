from ..models.classifier_models import ClasificarRequest, ClasificarResponse
from .simplex_service import classify_problem_manual


def clasificar_problema(request: ClasificarRequest) -> ClasificarResponse:
    c1, c2 = request.funcion_objetivo
    tipo = request.tipo_objetivo

    A, b, ops = [], [], []
    for rest in request.restricciones:
        A.append([rest.x1, rest.x2])
        b.append(rest.valor)
        ops.append(rest.operador)

    result = classify_problem_manual([c1, c2], A, b, ops, tipo)

    tipo_solucion = result['tipo_solucion']
    opt_val = result.get('optimal_value')
    vars_val = result.get('variables')

    explicaciones = {
        'unica': "La trayectoria de optimización converge exactamente hacia un solo vértice geométrico del polígono de restricciones, haciéndolo el punto absoluto e indivisible de optimización.",
        'multiple': "El óptimo se alcanza en un segmento de recta, debido a que la pendiente de la función objetivo Z es idéntica a una de las restricciones estructurales vinculantes en la región factible.",
        'sin_solucion': "El solver determinó que la región factible está vacía (las restricciones son mutuamente excluyentes o se contraponen).",
        'no_acotada': "La región factible está abierta perimetralmente, permitiendo que la función objetivo (Z) progrese infinitamente hacia el óptimo.",
        'error': "Hubo un comportamiento inestable numéricamente al procesar las matrices.",
    }

    detalles = {}
    if opt_val is not None:
        detalles['optimo'] = round(opt_val, 4)
    if vars_val is not None:
        detalles['variables'] = list(vars_val)

    return ClasificarResponse(
        tipo_solucion=tipo_solucion,
        explicacion=explicaciones.get(tipo_solucion, "Error del solver manual."),
        detalles_solver=detalles
    )
