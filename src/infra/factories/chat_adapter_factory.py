from src.domain.interfaces.chat_repository import ChatRepository


class ChatAdapterFactory:
    @staticmethod
    def create(model: str) -> ChatRepository:
        if "gpt" in model:
            from src.infra.adapters.OpenAI.openai_chat_adapter import OpenAIChatAdapter

            return OpenAIChatAdapter()
        else:
            raise ValueError("IA não suportada")
