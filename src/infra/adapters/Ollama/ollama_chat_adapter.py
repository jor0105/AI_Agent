import time
from typing import Dict, List, Optional

from ollama import chat

from src.application.interfaces.chat_repository import ChatRepository
from src.domain.exceptions import ChatException
from src.infra.config.environment import EnvironmentConfig
from src.infra.config.logging_config import LoggingConfig
from src.infra.config.metrics import ChatMetrics
from src.infra.config.retry import retry_with_backoff


class OllamaChatAdapter(ChatRepository):
    """Adapter para comunicação com Ollama."""

    def __init__(self):
        """Inicializa o adapter Ollama com configurações opcionais."""
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
        temperature: Optional[float],
        top_p: Optional[float],
        stop: Optional[List[str]],
    ) -> dict:
        """
        Chama a API do Ollama com retry automático.

        Args:
            model: Nome do modelo
            messages: Lista de mensagens
            temperature: Temperatura para geração
            top_p: Top-p sampling
            stop: Sequências de parada

        Returns:
            Resposta da API
        """
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if top_p is not None:
            options["top_p"] = top_p

        kwargs = {
            "model": model,
            "messages": messages,
            "host": self.__host,
        }

        if options:
            kwargs["options"] = options
        if stop is not None:
            kwargs["stop"] = stop

        return chat(**kwargs)

    def chat(
        self,
        model: str,
        instructions: str,
        user_ask: str,
        history: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """
        Envia mensagem para o Ollama e retorna a resposta.

        Args:
            model: Nome do modelo
            instructions: Instruções do sistema
            user_ask: Pergunta do usuário
            history: Histórico de conversas (lista de dicts com 'role' e 'content')
            temperature: Temperatura para geração (0.0-2.0)
            max_tokens: Máximo de tokens (não suportado no Ollama, ignorado)
            top_p: Top-p sampling (0.0-1.0)
            stop: Sequências de parada

        Returns:
            str: Resposta do modelo

        Raises:
            ChatException: Se houver erro na comunicação
        """
        start_time = time.time()

        try:
            self.__logger.debug(f"Iniciando chat com modelo {model} no Ollama")

            messages = []
            messages.append({"role": "system", "content": instructions})
            messages.extend(history)
            messages.append({"role": "user", "content": user_ask})

            response = self.__call_ollama_api(model, messages, temperature, top_p, stop)

            content = response["message"]["content"]

            if not content:
                self.__logger.warning("Ollama retornou resposta vazia")
                raise ChatException("Ollama retornou uma resposta vazia")

            latency = (time.time() - start_time) * 1000

            tokens_info = response.get("eval_count", None)

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

    def get_metrics(self) -> List[ChatMetrics]:
        return self.__metrics.copy()
