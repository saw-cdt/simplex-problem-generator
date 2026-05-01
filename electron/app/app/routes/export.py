from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
from ..services.pdf_service import generate_pdf_from_latex

router = APIRouter()

class ExportRequest(BaseModel):
    latex_code: str

@router.post("/export/pdf")
def export_pdf_route(request: ExportRequest):
    """
    Recibe un string con el código LaTeX del problema y retorna el archivo
    físico .pdf descargable compilado al vuelo.
    """
    pdf_bytes = generate_pdf_from_latex(request.latex_code)
    
    # Devolver binario forzando descarga de adjunto con Response y headers MIME
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="problema_simplex.pdf"'
        }
    )
