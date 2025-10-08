from typing import Dict

from src.application.chat_with_agent import ChatWithAgentUseCase
from src.application.get_config_new_agents import GetConfigNewAgentsUseCase
from src.domain.agents.agent_domain import DomainAIAgent
from src.infra.factories.chat_adapter_factory import ChatAdapterFactory


class AIAgent:
    def __init__(self, model: str, name: str, instructions: str) -> None:
        self.__agent = DomainAIAgent(model=model, name=name, instructions=instructions)
        chat_adapter = ChatAdapterFactory.create(model)
        self.__chat_use_case = ChatWithAgentUseCase(chat_adapter)

    def chat(self, user_ask: str) -> str:
        return self.__chat_use_case.execute(self.__agent, user_ask)

    def get_configs(self) -> Dict:
        return GetConfigNewAgentsUseCase.execute(self.__agent)
