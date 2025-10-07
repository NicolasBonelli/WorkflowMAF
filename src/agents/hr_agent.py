from agent_framework import ChatAgent
import logging

logger = logging.getLogger(__name__)

class HRAgentService:
    def __init__(self, chat_agent: ChatAgent):
        self._agent = chat_agent

    async def handle(self, user_input: str) -> str:
        prompt = (
            "Actúa como asistente de Recursos Humanos. Responde de forma breve y profesional "
            "a la siguiente consulta del empleado.\n\n"
            f"Consulta: {user_input}\n\nRespuesta:"
        )
        response = await self._agent.run(prompt)
        logger.debug("HRAgent raw: %s", response.text)
        return response.text.strip()
