from typing import Dict, List

from openai import OpenAI

from src.domain.interfaces.chat_repository import ChatRepository
from src.infra.Config.environment import EnvironmentConfig


class ClientOpenAI:
    def get_client(self, api_key: str) -> OpenAI:
        client = OpenAI(api_key=api_key)
        return client


class OpenAIChatAdapter(ChatRepository):
    def __init__(self):
        env_config = EnvironmentConfig()
        api_key = env_config.get_api_key("OPENAI_API_KEY")
        self.__client = ClientOpenAI().get_client(api_key)

    def chat(
        self, model: str, prompt: str, user_input: str, history: List[Dict[str, str]]
    ) -> str:
        response = self.__client.responses.create(model=model, input=user_input)
        return response.output_text
