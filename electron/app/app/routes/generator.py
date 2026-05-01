from fastapi import APIRouter
from ..models.generator_models import GenerateRequest, GenerateResponse
from ..services.generator_service import generate_mock_problem

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
def generate_problem(request: GenerateRequest):
    """
    Recibe la configuración del problema y devuelve un modelo mock 
    del problema de programación lineal generado.
    """
    return generate_mock_problem(request)
