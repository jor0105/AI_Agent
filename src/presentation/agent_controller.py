from typing import Any, Dict, List, Optional

from src.application.dtos import ChatInputDTO
from src.application.use_cases.chat_with_agent import ChatWithAgentUseCase
from src.application.use_cases.get_config_new_agents import GetAgentConfigUseCase
from src.domain.entities.agent_domain import Agent
from src.infra.config.metrics import ChatMetrics
from src.infra.factories.chat_adapter_factory import ProviderType
from src.main.composers.agent_composer import AgentComposer


class AIAgent:
    """
    Controller da camada de apresentação para interação com agentes de IA.
    Responsável por coordenar as requisições e respostas.
    """

    def __init__(
        self,
        provider: ProviderType,
        model: str,
        name: str,
        instructions: str,
        history_max_size: int = 10,
    ) -> None:
        """
        Inicializa o controller criando um agente e suas dependências.

        Args:
            provider: Provider específico ("openai" ou "ollama") - define qual API usar
            model: Nome do modelo de IA
            name: Nome do agente
            instructions: Instruções/prompt do agente
            history_max_size: Tamanho máximo do histórico (padrão: 10)
        """
        self.__agent: Agent = AgentComposer.create_agent(
            provider=provider,
            model=model,
            name=name,
            instructions=instructions,
            history_max_size=history_max_size,
        )

        self.__chat_use_case: ChatWithAgentUseCase = AgentComposer.create_chat_use_case(
            provider=provider, model=model
        )
        self.__get_config_use_case: GetAgentConfigUseCase = (
            AgentComposer.create_get_config_use_case()
        )

    def chat(
        self,
        message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """
        Envia uma mensagem ao agente e retorna a resposta.

        Args:
            message: Mensagem do usuário
            temperature: Temperatura para geração (0.0-2.0, opcional)
            max_tokens: Máximo de tokens na resposta (opcional)
            top_p: Top-p sampling (0.0-1.0, opcional)
            stop: Sequências de parada (opcional)

        Returns:
            str: Resposta do agente
        """
        input_dto = ChatInputDTO(
            message=message,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
        )
        output_dto = self.__chat_use_case.execute(self.__agent, input_dto)
        return output_dto.response

    def get_configs(self) -> Dict[str, Any]:
        """
        Retorna as configurações do agente.

        Returns:
            Dict: Configurações do agente
        """
        output_dto = self.__get_config_use_case.execute(self.__agent)
        return output_dto.to_dict()

    def clear_history(self) -> None:
        self.__agent.clear_history()

    def get_metrics(self) -> List[ChatMetrics]:
        """
        Retorna as métricas de performance do adapter de chat.

        Returns:
            List[ChatMetrics]: Lista de métricas coletadas durante as interações
        """
        return self.__chat_use_case.get_metrics()

    def export_metrics_json(self, filepath: Optional[str] = None) -> str:
        """
        Exporta métricas em formato JSON.

        Args:
            filepath: Caminho do arquivo para salvar (opcional)

        Returns:
            str: String JSON com as métricas
        """
        from src.infra.config.metrics import MetricsCollector

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        return collector.export_json(filepath)

    def export_metrics_prometheus(self, filepath: Optional[str] = None) -> str:
        """
        Exporta métricas em formato Prometheus.

        Args:
            filepath: Caminho do arquivo para salvar (opcional)

        Returns:
            str: Métricas no formato Prometheus
        """
        from src.infra.config.metrics import MetricsCollector

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        metrics_text = collector.export_prometheus()

        if filepath:
            collector.export_prometheus_to_file(filepath)

        return metrics_text
