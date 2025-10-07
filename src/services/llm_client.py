import os
import logging
from agent_framework.azure import AzureOpenAIChatClient  
from agent_framework import ChatAgent
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LLMClientWrapper:
    def __init__(self, endpoint: str, deployment_name: str, api_key: str):
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        self.api_key = api_key
        # construimos el cliente de Azure OpenAI con la key
        self._client = AzureOpenAIChatClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
            deployment_name=deployment_name
        )

    async def create_chat_agent(self, instructions: str, name: str = "agent") -> ChatAgent:
        agent = ChatAgent(
            chat_client=self._client,
            instructions=instructions,
        )
        return agent
