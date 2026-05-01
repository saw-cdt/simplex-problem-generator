from fastapi import APIRouter
from ..models.classifier_models import ClasificarRequest, ClasificarResponse
from ..services.classifier_service import clasificar_problema

router = APIRouter()

@router.post("/classify", response_model=ClasificarResponse)
def classify_problem_route(request: ClasificarRequest):
    """
    Recibe una función objetivo manual y su sistema de restricciones
    y delega al solver algorítmico interno su clasificación matemática.
    """
    return clasificar_problema(request)
