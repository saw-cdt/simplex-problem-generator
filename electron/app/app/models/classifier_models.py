from pydantic import BaseModel
from typing import Literal, List, Optional

class RestriccionInput(BaseModel):
    x1: float
    x2: float
    operador: Literal["<=", ">=", "="]
    valor: float

class ClasificarRequest(BaseModel):
    tipo_objetivo: Literal["max", "min"]
    funcion_objetivo: List[float]  # [c1, c2]
    restricciones: List[RestriccionInput]

class ClasificarResponse(BaseModel):
    tipo_solucion: Literal["unica", "multiple", "sin_solucion", "no_acotada", "error"]
    explicacion: str
    detalles_solver: dict
