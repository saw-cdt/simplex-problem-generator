from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class ConstraintInput(BaseModel):
    coeficientes: List[float]
    operador: Literal["<=", ">=", "="]
    valor: float

class GenerateRequest(BaseModel):
    tipo_objetivo: Literal["max", "min"]
    tipo_solucion: Literal["unica", "multiple", "sin_solucion", "no_acotada"]
    tipo_restricciones: Literal["fijas", "aleatorias"]
    num_variables: int = Field(default=2, ge=2, le=10)
    num_restricciones: int = Field(default=3, ge=1, le=10)
    
    restricciones_custom: Optional[List[ConstraintInput]] = None
    funcion_objetivo_custom: Optional[List[float]] = None
    
    nombre: str = ""
    matricula: str = ""

class ObjectiveFunction(BaseModel):
    tipo: Literal["max", "min"]
    coeficientes: List[float]
    string_repr: str

class Constraint(BaseModel):
    coeficientes: List[float]
    operador: Literal["<=", ">=", "="]
    valor: float
    string_repr: str

class GenerateResponse(BaseModel):
    funcion_objetivo: ObjectiveFunction
    restricciones: List[Constraint]
    num_variables: int
    num_restricciones: int
    explicacion: str
    latex_code: str = ""
    pdf_base64: str = ""
    status: str = "success"