from typing import Dict, List

from src.domain.interfaces.chat_repository import ChatRepository
from src.infra.adapters.OpenAI.client_openai import ClientOpenAI
from src.infra.config.environment import EnvironmentConfig


class OpenAIChatAdapter(ChatRepository):
    def __init__(self):
        api_key = EnvironmentConfig.get_api_key(ClientOpenAI.API_OPENAI_NAME)
        self.__client = ClientOpenAI().get_client(api_key)

    def chat(
        self, model: str, instructions: str, user_input: List[Dict[str, str]]
    ) -> str:
        response = self.__client.responses.create(
            model=model,
            instructions=instructions,
            input=user_input,
        )
        return response.output_text
