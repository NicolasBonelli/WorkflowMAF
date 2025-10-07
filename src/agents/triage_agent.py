from typing import Any
from pydantic import BaseModel
from agent_framework import ChatAgent
from src.models.request_models import RouterOutputModel
import logging

logger = logging.getLogger(__name__)

class RouterAgentService:
    """
    Este servicio envuelve un ChatAgent para clasificar el tipo de consulta.
    Debería devolver un JSON/estructura conforme a RouterOutputModel.
    """

    def __init__(self, chat_agent: ChatAgent):
        self._agent = chat_agent

    async def classify(self, user_input: str) -> RouterOutputModel:
        """
        Ejecuta el agente para clasificar el input.
        Pedimos al modelo que devuelva un JSON con 'tipo' y 'confidence'.
        """
        # Instrucciones que orienten al modelo a devolver JSON parseable
        prompt = (
            "Eres un clasificador. Dado un mensaje de un empleado, responde exclusivamente con JSON "
            "con los campos: tipo (it|hr|other), confidence (0-1) y details (breve). "
            "Ejemplo: {\"tipo\":\"it\",\"confidence\":0.95,\"details\":\"es un problema de login\"}\n\n"
            f"Mensaje: \"{user_input}\""
        )

        response = await self._agent.run(prompt)
        text = response.text.strip()
        logger.debug("RouterAgent raw response: %s", text)

        # Intentamos parsear con Pydantic
        try:
            # Si viene puro JSON lo parseamos
            import json
            payload = json.loads(text)
            model = RouterOutputModel(**payload)
            return model
        except Exception as exc:
            logger.warning("No se pudo parsear la salida del RouterAgent a JSON: %s", exc)
            # fallback simple: heurística por palabras clave
            low = user_input.lower()
            tipo = "other"
            if any(k in low for k in ["error", "login", "servidor", "pantalla", "crash", "bug"]):
                tipo = "it"
            elif any(k in low for k in ["vacaciones", "permiso", "sueldo", "contrato", "rrhh", "recurso humano", "beneficios"]):
                tipo = "hr"
            return RouterOutputModel(tipo=tipo, confidence=0.5, details="heuristic fallback")