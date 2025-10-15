from src.application.dtos import ChatInputDTO, ChatOutputDTO
from src.application.interfaces.chat_repository import ChatRepository
from src.domain.entities.agent_domain import Agent
from src.domain.exceptions import ChatException
from src.infra.config.logging_config import LoggingConfig


class ChatWithAgentUseCase:
    """Use Case para realizar chat com um agente."""

    def __init__(self, chat_repository: ChatRepository):
        """
        Inicializa o Use Case com suas dependências.

        Args:
            chat_repository: Repositório para comunicação com IA
        """
        self.__chat_repository = chat_repository
        self.__logger = LoggingConfig.get_logger(__name__)

    def execute(self, agent: Agent, input_dto: ChatInputDTO) -> ChatOutputDTO:
        """
        Envia mensagem ao agente e retorna a resposta.

        Args:
            agent: Instância do agente
            input_dto: DTO com a mensagem do usuário

        Returns:
            ChatOutputDTO: DTO com a resposta do agente

        Raises:
            ValueError: Se os dados de entrada forem inválidos
            ChatException: Se houver erro durante a comunicação com a IA
        """
        input_dto.validate()

        self.__logger.info(
            f"Executando chat com agente '{agent.name}' (modelo: {agent.model})"
        )
        self.__logger.debug(f"Mensagem do usuário: {input_dto.message[:100]}...")

        try:
            response = self.__chat_repository.chat(
                model=agent.model,
                instructions=agent.instructions,
                user_ask=input_dto.message,
                history=agent.history.to_dict_list(),
                temperature=input_dto.temperature,
                max_tokens=input_dto.max_tokens,
                top_p=input_dto.top_p,
                stop=input_dto.stop,
            )

            if not response:
                self.__logger.error("Resposta vazia recebida do repositório")
                raise ChatException("Resposta vazia recebida do repositório")

            output_dto = ChatOutputDTO(response=response)

            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(response)

            self.__logger.info("Chat executado com sucesso")
            self.__logger.debug(f"Resposta (primeiros 100 chars): {response[:100]}...")

            return output_dto

        except ChatException:
            self.__logger.error("ChatException durante execução do chat")
            raise
        except (ValueError, TypeError, KeyError) as e:
            error_map = {
                ValueError: (
                    "Erro de validação",
                    "Erro de validação durante o chat: {}",
                ),
                TypeError: ("Erro de tipo", "Erro de tipo durante o chat: {}"),
                KeyError: (
                    "Erro ao processar resposta",
                    "Erro ao processar resposta da IA: {}",
                ),
            }
            msg, user_msg = error_map.get(type(e), ("Erro", "Erro durante o chat: {}"))
            self.__logger.error(f"{msg}: {str(e)}")
            raise ChatException(user_msg.format(str(e)))
        except Exception as e:
            self.__logger.error(f"Erro inesperado: {str(e)}")
            raise ChatException(
                f"Erro inesperado durante comunicação com IA: {str(e)}",
                original_error=e,
            )

    def get_metrics(self):
        """
        Retorna as métricas coletadas pelo repositório de chat.

        Returns:
            List[ChatMetrics]: Lista de métricas se o repositório suportar,
                              lista vazia caso contrário.
        """
        if hasattr(self.__chat_repository, "get_metrics"):
            return self.__chat_repository.get_metrics()
        return []
