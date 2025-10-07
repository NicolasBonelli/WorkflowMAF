from agent_framework import ChatAgent
import logging

logger = logging.getLogger(__name__)

class ITDiagnoseService:
    def __init__(self, chat_agent: ChatAgent):
        self._agent = chat_agent

    async def diagnose(self, user_input: str) -> str:
        prompt = (
            "Eres un agente técnico que diagnostica problemas. "
            "Describe brevemente la posible causa y qué logs/datos pedirías para investigar más."
            f"\n\nProblema: {user_input}\n\nDiagnóstico:"
        )
        response = await self._agent.run(prompt)
        logger.debug("ITDiagnoseAgent raw: %s", response.text)
        return response.text.strip()
