from src.domain.interfaces.chat_repository import ChatRepository


class ChatAdapterFactory:
    models_ai = {
        "gpt": "src.infra.adapters.OpenAI.openai_chat_adapter.OpenAIChatAdapter",
        # Adicione outros modelos aqui, exemplo:
        # "llama": "src.infra.adapters.Llama.llama_chat_adapter.LlamaChatAdapter",
    }

    @staticmethod
    def create(model: str) -> ChatRepository:
        adapter_path = None
        for key in ChatAdapterFactory.models_ai:
            if model.lower().startswith(key):
                adapter_path = ChatAdapterFactory.models_ai[key]
                break
        if not adapter_path:
            raise ValueError(f"IA não suportada: {model}")
        try:
            module_path, class_name = adapter_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            adapter_class = getattr(module, class_name)
            return adapter_class()
        except (ImportError, AttributeError, Exception) as e:
            raise ImportError(
                f"Erro ao importar ou instanciar o adaptador '{adapter_path}': {e}"
            )
