from agent_framework import ChatAgent
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ITResolveService:
    def __init__(self, chat_agent: ChatAgent):
        self._agent = chat_agent

    async def resolve(self, diagnostic_text: str, user_input: str) -> str:
        """
        Recibe el diagnóstico del agente anterior y la descripción del usuario,
        y propone pasos de solución concretos. Esta clase podría además llamar
        una tool externa (por ejemplo una función que consulta KB), aquí solo generamos
        una respuesta por el LLM.
        """
        prompt = (
            "Eres un agente técnico encargado de proponer pasos de resolución concretos y seguros. "
            "Recibe el diagnóstico y la descripción del usuario. Devuelve una lista numerada corta de acciones.\n\n"
            f"Descripción del usuario: {user_input}\n"
            f"Diagnóstico previo: {diagnostic_text}\n\n"
            "Solución propuesta:"
        )
        response = await self._agent.run(prompt)
        logger.debug("ITResolveAgent raw: %s", response.text)
        return response.text.strip()
