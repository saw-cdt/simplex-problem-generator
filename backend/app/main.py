from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import generator, classifier, export, exam

app = FastAPI(title="Simplex Desktop API")

# Configure CORS for Electron/React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local desktop app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generator.router, prefix="/api", tags=["generator"])
app.include_router(classifier.router, prefix="/api", tags=["classifier"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(exam.router, prefix="/api", tags=["exam"])

@app.get("/")
def read_root():
    return {"status": "Backend is running"}
