from typing import Dict, List

from src.domain.interfaces.chat_repository import ChatRepository
from src.infra.adapters.OpenAI.client_openai import ClientOpenAI
from src.infra.config.environment import EnvironmentConfig


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
