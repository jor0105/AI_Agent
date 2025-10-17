from typing import Any, Dict, Optional

from src.application.dtos import CreateAgentInputDTO
from src.application.use_cases.chat_with_agent import ChatWithAgentUseCase
from src.application.use_cases.create_agent import CreateAgentUseCase
from src.application.use_cases.get_config_agents import GetAgentConfigUseCase
from src.domain.entities.agent_domain import Agent
from src.infra.factories.chat_adapter_factory import ChatAdapterFactory


class AgentComposer:
    """
    Composer responsável por criar e compor as dependências
    necessárias para os use cases relacionados a agentes.
    """

    @staticmethod
    def create_agent(
        provider: str,
        model: str,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        history_max_size: int = 10,
    ) -> Agent:
        """
        Cria um novo agente utilizando o CreateAgentUseCase.

        Args:
            provider: Provider específico ("openai" ou "ollama")
            model: Nome do modelo de IA
            name: Nome do agente (opcional)
            instructions: Instruções do agente (opcional)
            configs: Configurações extras do agente, como max_tokens e temperature (opcional)
            history_max_size: Tamanho máximo do histórico (padrão: 10)

        Returns:
            Agent: Nova instância do agente
        """
        if config is None:
            config = {}

        input_dto = CreateAgentInputDTO(
            provider=provider,
            model=model,
            name=name,
            instructions=instructions,
            config=config,
            history_max_size=history_max_size,
        )

        use_case = CreateAgentUseCase()

        return use_case.execute(input_dto)

    @staticmethod
    def create_chat_use_case(
        provider: str,
        model: str,
    ) -> ChatWithAgentUseCase:
        """
        Cria o ChatWithAgentUseCase com suas dependências injetadas.

        Args:
            provider: Provider específico ("openai" ou "ollama")
            model: Nome do modelo de IA

        Returns:
            ChatWithAgentUseCase: Use case configurado
        """
        chat_adapter = ChatAdapterFactory.create(provider, model)
        return ChatWithAgentUseCase(chat_repository=chat_adapter)

    @staticmethod
    def create_get_config_use_case() -> GetAgentConfigUseCase:
        """
        Cria o GetAgentConfigUseCase.

        Returns:
            GetAgentConfigUseCase: Use case configurado
        """
        return GetAgentConfigUseCase()
