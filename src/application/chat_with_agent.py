from src.domain.agents.agent_domain import DomainAIAgent
from src.domain.interfaces.chat_repository import ChatRepository


class ChatWithAgentUseCase:
    def __init__(self, chat_adapter: ChatRepository):
        self.__chat_adapter = chat_adapter

    def execute(self, agent: DomainAIAgent, user_ask: str) -> str:
        agent.update_history({"role": "user", "content": user_ask})

        response = self.__chat_adapter.chat(
            model=agent.model,
            instructions=agent.instructions,
            user_input=agent.history,
        )

        agent.update_history({"role": "assistant", "content": response})

        return response
