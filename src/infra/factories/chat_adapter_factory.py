from src.domain.interfaces.chat_repository import ChatRepository


class ChatAdapterFactory:
    adapters = {
        "gpt": "src.infra.adapters.OpenAI.openai_chat_adapter.OpenAIChatAdapter",
        # Adicione outros modelos aqui, exemplo:
        # "llama": "src.infra.adapters.Llama.llama_chat_adapter.LlamaChatAdapter",
    }

    @staticmethod
    def create(model: str) -> ChatRepository:
        for key, adapter_path in ChatAdapterFactory.adapters.items():
            if key in model:
                module_path, class_name = adapter_path.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                adapter_class = getattr(module, class_name)
                return adapter_class()
        raise ValueError("IA não suportada")
