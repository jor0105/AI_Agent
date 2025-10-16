import time
from typing import Any, Dict, List

from src.application.interfaces.chat_repository import ChatRepository
from src.domain.exceptions import ChatException
from src.infra.adapters.OpenAI.client_openai import ClientOpenAI
from src.infra.config.environment import EnvironmentConfig
from src.infra.config.logging_config import LoggingConfig
from src.infra.config.metrics import ChatMetrics
from src.infra.config.retry import retry_with_backoff


class OpenAIChatAdapter(ChatRepository):
    """Adapter para comunicação com OpenAI API."""

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics: List[ChatMetrics] = []

        # Configurações de timeout e retry
        self.__timeout = int(EnvironmentConfig.get_env("OPENAI_TIMEOUT", "30"))
        self.__max_retries = int(EnvironmentConfig.get_env("OPENAI_MAX_RETRIES", "3"))

        try:
            api_key = EnvironmentConfig.get_api_key(ClientOpenAI.API_OPENAI_NAME)
            self.__client = ClientOpenAI.get_client(api_key)
            self.__logger.info(
                f"OpenAI adapter inicializado (timeout: {self.__timeout}s, "
                f"max_retries: {self.__max_retries})"
            )
        except EnvironmentError as e:
            self.__logger.error(f"Erro ao configurar OpenAI: {str(e)}")
            raise ChatException(f"Erro ao configurar OpenAI: {str(e)}", e)

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    def __call_openai_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
    ) -> Any:
        """
        Chama a API da OpenAI com retry automático.

        Args:
            model: Nome do modelo
            messages: Lista de mensagens
            config: Configurações internas da IA

        Returns:
            Resposta da API
        """
        response_api = self.__client.responses.create(
            model=model,
            input=messages,
        )

        return response_api

    def chat(
        self,
        model: str,
        instructions: str,
        config: Dict[str, Any],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> str:
        """
        Envia mensagem para OpenAI e retorna a resposta.

        Args:
            model: Nome do modelo
            instructions: Instruções do sistema
            config: Configurações internas da IA
            history: Histórico de conversas (lista de dicts com 'role' e 'content')
            user_ask: Pergunta do usuário

        Returns:
            str: Resposta do modelo

        Raises:
            ChatException: Se houver erro na comunicação
        """
        start_time = time.time()

        try:
            self.__logger.debug(f"Iniciando chat com modelo {model} na OpenAI")

            messages = []
            messages.append({"role": "system", "content": instructions})
            messages.extend(history)
            messages.append({"role": "user", "content": user_ask})

            # Chama a API da OpenAI com retry automático
            response_api = self.__call_openai_api(model, messages, config)

            content = response_api.output_text

            if not content:
                self.__logger.warning("OpenAI retornou resposta vazia")
                raise ChatException("OpenAI retornou uma resposta vazia")

            # Captura métricas
            latency = (time.time() - start_time) * 1000

            usage = getattr(response_api, "usage", None)
            if usage:
                tokens_used = getattr(usage, "total_tokens", None)
                prompt_tokens = getattr(usage, "input_tokens", None)
                completion_tokens = getattr(usage, "output_tokens", None)
            else:
                tokens_used = None
                prompt_tokens = None
                completion_tokens = None

            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                success=True,
            )
            self.__metrics.append(metrics)

            self.__logger.info(f"Chat concluído: {metrics}")
            self.__logger.debug(f"Resposta (primeiros 100 chars): {content[:100]}...")

            return content

        except ChatException:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message="OpenAI retornou resposta vazia",
            )
            self.__metrics.append(metrics)
            raise
        except AttributeError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Erro ao acessar resposta: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(f"Erro ao acessar resposta da OpenAI: {str(e)}")
            raise ChatException(
                f"Erro ao acessar resposta da OpenAI: {str(e)}", original_error=e
            )
        except IndexError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Formato inesperado: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(f"Resposta da OpenAI com formato inesperado: {str(e)}")
            raise ChatException(
                f"Resposta da OpenAI com formato inesperado: {str(e)}", original_error=e
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model, latency_ms=latency, success=False, error_message=str(e)
            )
            self.__metrics.append(metrics)
            self.__logger.error(f"Erro ao comunicar com OpenAI: {str(e)}")
            raise ChatException(
                f"Erro ao comunicar com OpenAI: {str(e)}", original_error=e
            )

    def get_metrics(self) -> List[ChatMetrics]:
        return self.__metrics.copy()
