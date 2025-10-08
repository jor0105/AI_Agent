from typing import Dict

from src.application.chat_with_agent import ChatWithAgentUseCase
from src.application.get_config_new_agents import GetConfigNewAgentUseCase
from src.domain.Agents.agents import AIAgent
from src.infra.factories.chat_adapter_factory import ChatAdapterFactory


class AIAgentController:
    def __init__(self, model: str, name: str, prompt: str) -> None:
        self.__agent = AIAgent(model=model, name=name, prompt=prompt)
        chat_adapter = ChatAdapterFactory.create(model)
        self.__chat_use_case = ChatWithAgentUseCase(chat_adapter)

    def chat(self, user_input: str) -> str:
        return self.__chat_use_case.execute(self.__agent, user_input)

    def get_configs(self) -> Dict:
        return GetConfigNewAgentUseCase.execute(self.__agent)
