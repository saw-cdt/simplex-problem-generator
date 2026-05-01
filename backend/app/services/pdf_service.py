import os
import subprocess
import tempfile
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def generate_pdf_from_latex(latex_code: str) -> bytes:
    document = rf"""\documentclass[12pt]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage{{amsmath}}
\usepackage[margin=2cm]{{geometry}}
\pagestyle{{plain}}

\begin{{document}}

{latex_code}

\end{{document}}
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, "documento.tex")
        pdf_path = os.path.join(temp_dir, "documento.pdf")
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(document)
            
        pdflatex_bin = "pdflatex"
        if os.path.exists("/Library/TeX/texbin/pdflatex"):
            pdflatex_bin = "/Library/TeX/texbin/pdflatex"
            
        try:
            result = subprocess.run(
                [pdflatex_bin, "-interaction=nonstopmode", "-output-directory", temp_dir, tex_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=500, 
                detail="pdflatex no está instalado."
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=500, 
                detail="Timeout al compilar."
            )
        
        if not os.path.exists(pdf_path):
            stdout = result.stdout.decode('utf-8', errors='ignore')
            stderr = result.stderr.decode('utf-8', errors='ignore')
            print(f"[DEBUG] LaTeX returncode: {result.returncode}", flush=True)
            print(f"[DEBUG] LaTeX stderr: {stderr[:1000]}", flush=True)
            print(f"[DEBUG] LaTeX stdout tail: {stdout[-1000:]}", flush=True)
            logger.error(f"LaTeX error: {stderr[:1000]}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error al compilar LaTeX. Returncode: {result.returncode}, stderr: {stderr[:300]}"
            )
            
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
    return pdf_bytes