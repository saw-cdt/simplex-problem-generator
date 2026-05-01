import numpy as np
from scipy.optimize import linprog
from ..models.classifier_models import ClasificarRequest, ClasificarResponse

def clasificar_problema(request: ClasificarRequest) -> ClasificarResponse:
    c1, c2 = request.funcion_objetivo
    tipo = request.tipo_objetivo
    
    # Scipy linprog simpre minimiza, invertimos coeficientes si es de maximizar
    c_opt = [-c1, -c2] if tipo == "max" else [c1, c2]
    
    A_ub, b_ub = [], []
    A_eq, b_eq = [], []
    
    # Parseo de restricciones matemáticas explícitas para procesarse matricialmente
    for rest in request.restricciones:
        if rest.operador == "<=":
            A_ub.append([rest.x1, rest.x2])
            b_ub.append(rest.valor)
        elif rest.operador == ">=":
            A_ub.append([-rest.x1, -rest.x2])
            b_ub.append(-rest.valor)
        elif rest.operador == "=":
            A_eq.append([rest.x1, rest.x2])
            b_eq.append(rest.valor)
            
    A_ub = A_ub if len(A_ub) > 0 else None
    b_ub = b_ub if len(b_ub) > 0 else None
    A_eq = A_eq if len(A_eq) > 0 else None
    b_eq = b_eq if len(b_eq) > 0 else None

    # El método 'highs' es el solver oficial y moderno detrás de scipy.linprog
    res = linprog(c_opt, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
    
    # Status Scipy:
    # 0 = Éxito, 1 = Límite de iteraciones, 2 = Infactible, 3 = No acotada, 4 = Fallo numérico
    
    if res.status == 2:
        return ClasificarResponse(
            tipo_solucion="sin_solucion",
            explicacion="El solver determinó que la región factible está vacía (las restricciones son mutuamente excluyentes o se contraponen).",
            detalles_solver={"status": 2}
        )
        
    elif res.status == 3:
        return ClasificarResponse(
            tipo_solucion="no_acotada",
            explicacion="La región factible está abierta perimetralmente, permitiendo que la función objetivo (Z) progrese infinitamente hacia el óptimo.",
            detalles_solver={"status": 3}
        )
        
    elif res.status == 0:
        # Puesto que tenemos un óptimo, debemos diferenciar entre ÚNICA o MÚLTIPLES opciones
        # Matemáticamente, las soluciones múltiples se dan si y solo si
        # la función objetivo Z es linealmente dependiente a alguna restricción ACTIVA 
        # involucrada en el vértice óptimo.
        
        es_multiple = False
        
        if res.slack is not None and A_ub is not None:
            # res.slack contiene las holguras de las inecuaciones. 
            # Una holgura cercana a cero (0) indica que la inecuación se comporta como igualdad activa.
            for i, slack_val in enumerate(res.slack):
                if np.isclose(slack_val, 0):
                    a1, a2 = A_ub[i]
                    
                    # Para saber si la línea de la función objetivo Z (c1x1 + c2x2) y la ecuación limitante (a1x1 + a2x2)
                    # son paralelas, su producto cruzado debe tender a 0. |c1*a2 - c2*a1| == 0
                    cross_product = abs(c1 * a2 - c2 * a1)
                    if np.isclose(cross_product, 0) and not (c1 == 0 and c2 == 0):
                        es_multiple = True
                        break
                        
        # Adicionalmente, revisamos los ejes del plano cartesiano x1>=0, x2>=0
        # Estos son límites estructurales pasivos que si son tocados activamente (res.x = 0),
        # podrían ser paralelos a un coeficiente nulo de la función objetivo.
        if res.x is not None and not es_multiple:
            if np.isclose(res.x[0], 0) and c2 == 0 and c1 != 0: 
                es_multiple = True  # Solución reposa sobre el Eje Y infinito temporalmente
            if np.isclose(res.x[1], 0) and c1 == 0 and c2 != 0:
                es_multiple = True  # Solución reposa sobre el Eje X infinito temporalmente

        if es_multiple:
            return ClasificarResponse(
                tipo_solucion="multiple",
                explicacion="El óptimo se alcanza en un segmento de recta, debido a que la pendiente de la función objetivo Z es idéntica a una de las restricciones estructurales vinculantes en la región factible.",
                detalles_solver={"status": 0, "optimo": round(res.fun * (-1 if tipo=="max" else 1), 4)}
            )
        else:
            return ClasificarResponse(
                tipo_solucion="unica",
                explicacion="La trayectoria de optimización converge exactamente hacia un solo vértice geométrico del polígono de restricciones, haciéndolo el punto absoluto e indivisible de optimización.",
                detalles_solver={"status": 0, "optimo": round(res.fun * (-1 if tipo=="max" else 1), 4), "variables": list(np.round(res.x, 4))}
            )
    else:
        # Fallback numérico (ej. degeneración severa no calculable)
        return ClasificarResponse(
            tipo_solucion="error",
            explicacion="Hubo un comportamiento inestable numéricamente al calcular las matrices C y A.",
            detalles_solver={"status": res.status, "message": str(res.message)}
        )
