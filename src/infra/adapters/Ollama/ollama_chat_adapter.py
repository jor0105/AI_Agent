import subprocess
import time
from typing import Any, Dict, List, Optional

from ollama import ChatResponse, chat

from src.application.interfaces.chat_repository import ChatRepository
from src.domain.exceptions import ChatException
from src.infra.config.environment import EnvironmentConfig
from src.infra.config.logging_config import LoggingConfig
from src.infra.config.metrics import ChatMetrics
from src.infra.config.retry import retry_with_backoff


class OllamaChatAdapter(ChatRepository):
    """Adapter para comunicação com Ollama."""

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics: List[ChatMetrics] = []

        # Carrega configurações opcionais do ambiente
        self.__host = EnvironmentConfig.get_env("OLLAMA_HOST", "http://localhost:11434")
        self.__max_retries = int(EnvironmentConfig.get_env("OLLAMA_MAX_RETRIES", "3"))

        self.__logger.info(
            f"Ollama adapter inicializado (host: {self.__host}, "
            f"max_retries: {self.__max_retries})"
        )

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    def __call_ollama_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
    ) -> ChatResponse:
        """
        Chama a API do Ollama com retry automático.

        Args:
            model: Nome do modelo
            messages: Lista de mensagens
            config: Configurações internas da IA

        Returns:
            Resposta da API
        """

        response_api: ChatResponse = chat(
            model=model,
            messages=messages,
        )

        return response_api

    def __stop_model(self, model: str) -> None:
        """
        Para o modelo Ollama após o uso para liberar memória.

        Args:
            model: Nome do modelo a ser parado
        """
        try:
            subprocess.run(
                ["ollama", "stop", model],
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.__logger.debug(f"Modelo {model} parado com sucesso")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.__logger.warning(f"Não foi possível parar o modelo {model}: {str(e)}")
        except Exception as e:
            self.__logger.warning(f"Erro ao tentar parar o modelo {model}: {str(e)}")

    def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Dict[str, Any],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> str:
        """
        Envia mensagem para o Ollama e retorna a resposta.

        Args:
            model: Nome do modelo
            instructions: Instruções do sistema (opcional)
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
            self.__logger.debug(f"Iniciando chat com modelo {model} no Ollama")

            messages = []
            if instructions and instructions.strip():
                messages.append({"role": "system", "content": instructions})
            messages.extend(history)
            messages.append({"role": "user", "content": user_ask})

            response_api = self.__call_ollama_api(model, messages, config)

            content = response_api.message.content

            if not content:
                self.__logger.warning("Ollama retornou resposta vazia")
                raise ChatException("Ollama retornou uma resposta vazia")

            latency = (time.time() - start_time) * 1000

            tokens_info = response_api.get("eval_count", None)

            metrics = ChatMetrics(
                model=model, latency_ms=latency, tokens_used=tokens_info, success=True
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
                error_message="Ollama retornou resposta vazia",
            )
            self.__metrics.append(metrics)
            raise
        except KeyError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Chave ausente: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(
                f"Resposta do Ollama com formato inválido. Chave ausente: {str(e)}"
            )
            raise ChatException(
                f"Resposta do Ollama com formato inválido. Chave ausente: {str(e)}",
                original_error=e,
            )
        except TypeError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Erro de tipo: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(
                f"Erro de tipo ao processar resposta do Ollama: {str(e)}"
            )
            raise ChatException(
                f"Erro de tipo ao processar resposta do Ollama: {str(e)}",
                original_error=e,
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model, latency_ms=latency, success=False, error_message=str(e)
            )
            self.__metrics.append(metrics)
            self.__logger.error(f"Erro ao comunicar com Ollama: {str(e)}")
            raise ChatException(
                f"Erro ao comunicar com Ollama: {str(e)}", original_error=e
            )
        finally:
            # Para o modelo automaticamente para liberar memória
            self.__stop_model(model)

    def get_metrics(self) -> List[ChatMetrics]:
        return self.__metrics.copy()
