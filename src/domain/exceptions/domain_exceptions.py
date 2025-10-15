class AgentException(Exception):
    """Exceção base para erros relacionados a agentes."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InvalidAgentConfigException(AgentException):
    """Exceção lançada quando a configuração do agente é inválida."""

    def __init__(self, field: str, reason: str):
        message = f"Configuração inválida no campo '{field}': {reason}"
        super().__init__(message)


class InvalidModelException(AgentException):
    """Exceção lançada quando o modelo de IA especificado não é suportado."""

    def __init__(self, model: str):
        message = f"Modelo de IA não suportado: '{model}'"
        super().__init__(message)


class ChatException(Exception):
    """Exceção base para erros durante a comunicação com IA."""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class AdapterNotFoundException(ChatException):
    """Exceção lançada quando o adapter de chat não é encontrado."""

    def __init__(self, adapter_name: str):
        message = f"Adapter não encontrado: '{adapter_name}'"
        super().__init__(message)
