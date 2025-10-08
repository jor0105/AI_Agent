from src.domain.Agents.agents import AIAgent
from src.application.chat_with_agent import ChatWithAgentUseCase
from src.infra.factories.chat_adapter_factory import ChatAdapterFactory
from typing import Dict

class AIAgentController:
    def __init__(self, model: str, name: str, prompt: str) -> None:
        self.__agent = AIAgent(
            model=model,
            name=name,
            prompt=prompt
        )
        chat_adapter = ChatAdapterFactory.create(model)
        self.__use_case = ChatWithAgentUseCase(chat_adapter)

    def chat(self, user_input: str) -> str:
        return self.__use_case.execute(self.__agent, user_input)
        
    def get_configs(self) -> Dict:
        return {
            "Name": self.__agent.name,
            "Model": self.__agent.model,
            "Prompt": self.__agent.prompt,
            "History": self.__agent.history
        }