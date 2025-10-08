from src.domain.Agents.agents import AIAgent
from src.domain.interfaces.chat_repository import ChatRepository


class ChatWithAgentUseCase:
    def __init__(self, chat_adapter: ChatRepository):
        self.__chat_adapter = chat_adapter

    def execute(self, agent: AIAgent, user_input: str) -> str:
        response = self.__chat_adapter.chat(
            model=agent.model,
            prompt=agent.prompt,
            user_input=user_input,
            history=agent.history,
        )

        agent.history.append({"role": "user", "content": user_input})
        agent.history.append({"role": "assistant", "content": response})

        return response
