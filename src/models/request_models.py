from pydantic import BaseModel

class RouterOutputModel(BaseModel):
    """
    Modelo Pydantic que el Router Agent debe devolver.
    campo 'tipo' deberá ser una de: 'it', 'hr', 'other'
    """
    tipo: str
    confidence: float | None = None
    details: str | None = None