from src.application.dtos import CreateAgentInputDTO
from src.application.use_cases.chat_with_agent import ChatWithAgentUseCase
from src.application.use_cases.create_agent import CreateAgentUseCase
from src.application.use_cases.get_config_new_agents import GetAgentConfigUseCase
from src.domain.entities.agent_domain import Agent
from src.domain.exceptions import InvalidAgentConfigException
from src.infra.factories.chat_adapter_factory import ChatAdapterFactory, ProviderType


class AgentComposer:
    """
    Composer responsável por criar e compor as dependências
    necessárias para os use cases relacionados a agentes.
    """

    @staticmethod
    def create_agent(
        provider: ProviderType,
        model: str,
        name: str,
        instructions: str,
        history_max_size: int = 10,
    ) -> Agent:
        """
        Cria um novo agente utilizando o CreateAgentUseCase.

        Args:
            model: Nome do modelo de IA
            name: Nome do agente
            instructions: Instruções do agente
            provider: Provider específico ("openai" ou "ollama")
            history_max_size: Tamanho máximo do histórico (padrão: 10)

        Returns:
            Agent: Nova instância do agente

        Raises:
            InvalidAgentConfigException: Se os dados forem inválidos
        """
        try:
            input_dto = CreateAgentInputDTO(
                model=model,
                name=name,
                instructions=instructions,
                provider=provider,
                history_max_size=history_max_size,
            )

            use_case = CreateAgentUseCase()

            return use_case.execute(input_dto)

        except Exception as e:
            if isinstance(e, InvalidAgentConfigException):
                raise
            raise InvalidAgentConfigException("composer", str(e))

    @staticmethod
    def create_chat_use_case(
        provider: ProviderType,
        model: str,
    ) -> ChatWithAgentUseCase:
        """
        Cria o ChatWithAgentUseCase com suas dependências injetadas.

        Args:
            model: Nome do modelo de IA
            provider: Provider específico ("openai" ou "ollama")

        Returns:
            ChatWithAgentUseCase: Use case configurado

        Raises:
            InvalidModelException: Se o modelo não for suportado
            AdapterNotFoundException: Se o adapter não for encontrado
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
