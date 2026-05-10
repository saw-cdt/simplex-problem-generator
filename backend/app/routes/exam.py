from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from ..models.generator_models import GenerateRequest
from ..services.generator_service import generate_mock_problem
from ..services.exam_service import (
    save_problem, get_problems, get_problem, remove_problem, clear_problems, count_problems
)
from ..services.latex_service import problems_to_latex_exam
from ..services.pdf_service import generate_pdf_from_latex
import base64

router = APIRouter()


class SaveProblemRequest(BaseModel):
    config: dict
    result: dict


class ExamGenerateRequest(BaseModel):
    instrucciones: str = ""


@router.post("/examen/guardar")
def guardar_problema(request: SaveProblemRequest):
    problem_id = save_problem(request.result)
    return {"id": problem_id, "total": count_problems()}


@router.get("/examen/problemas")
def listar_problemas():
    return {"problemas": get_problems(), "total": count_problems()}


@router.delete("/examen/problemas/{problem_id}")
def eliminar_problema(problem_id: str):
    if not remove_problem(problem_id):
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    return {"deleted": problem_id, "total": count_problems()}


@router.delete("/examen/limpiar")
def limpiar_problemas():
    count = clear_problems()
    return {"cleared": count}


@router.post("/examen/generar")
def generar_examen_completo(request: ExamGenerateRequest):
    problemas_list = get_problems()
    if not problemas_list:
        raise HTTPException(status_code=400, detail="No hay problemas guardados. Genera y guarda al menos uno.")

    problemas_data = [p['data'] for p in problemas_list]

    latex_str = problems_to_latex_exam(problemas_data, request.instrucciones)

    try:
        pdf_bytes = generate_pdf_from_latex(latex_str)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al compilar PDF: {str(e)}")

    return {
        "latex_code": latex_str,
        "pdf_base64": pdf_b64,
        "total_problemas": len(problemas_data),
    }
