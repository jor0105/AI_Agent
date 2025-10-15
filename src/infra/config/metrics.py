"""
Sistema de métricas para monitoramento de uso de chat.

Este módulo fornece estruturas para capturar e armazenar
métricas de performance e uso dos adapters de chat.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ChatMetrics:
    """
    Métricas de uma interação de chat.

    Attributes:
        model: Nome do modelo utilizado
        latency_ms: Latência da requisição em milissegundos
        tokens_used: Total de tokens utilizados (se disponível)
        prompt_tokens: Tokens do prompt (se disponível)
        completion_tokens: Tokens da resposta (se disponível)
        timestamp: Timestamp da requisição
        success: Se a requisição foi bem-sucedida
        error_message: Mensagem de erro (se houver)
    """

    model: str
    latency_ms: float
    tokens_used: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Converte métricas para dicionário."""
        return {
            "model": self.model,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message,
        }

    def __str__(self) -> str:
        """String representation das métricas."""
        tokens_info = f", tokens={self.tokens_used}" if self.tokens_used else ""
        status = "✓" if self.success else "✗"
        return f"[{status}] {self.model}: {self.latency_ms:.2f}ms{tokens_info}"


class MetricsCollector:
    """
    Coletor de métricas para análise agregada.
    """

    def __init__(self):
        self._metrics: list[ChatMetrics] = []

    def add(self, metrics: ChatMetrics) -> None:
        """Adiciona métricas à coleção."""
        self._metrics.append(metrics)

    def get_all(self) -> list[ChatMetrics]:
        """Retorna todas as métricas coletadas."""
        return self._metrics.copy()

    def get_summary(self) -> dict:
        """Retorna resumo estatístico das métricas."""
        if not self._metrics:
            return {"total_requests": 0}

        total_requests = len(self._metrics)
        successful = sum(1 for m in self._metrics if m.success)
        failed = total_requests - successful

        latencies = [m.latency_ms for m in self._metrics]
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        total_tokens = sum(
            m.tokens_used for m in self._metrics if m.tokens_used is not None
        )

        return {
            "total_requests": total_requests,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_requests) * 100,
            "avg_latency_ms": avg_latency,
            "min_latency_ms": min_latency,
            "max_latency_ms": max_latency,
            "total_tokens": total_tokens,
        }

    def clear(self) -> None:
        self._metrics.clear()

    def export_json(self, filepath: Optional[str] = None) -> str:
        """
        Exporta métricas em formato JSON.

        Args:
            filepath: Caminho do arquivo para salvar (opcional).
                     Se não fornecido, retorna apenas a string JSON.

        Returns:
            str: String JSON com todas as métricas
        """
        data = {
            "summary": self.get_summary(),
            "metrics": [m.to_dict() for m in self._metrics],
        }

        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    def export_prometheus(self) -> str:
        """
        Exporta métricas em formato compatível com Prometheus.

        Gera métricas no formato de texto do Prometheus:
        - chat_requests_total: Total de requisições
        - chat_requests_success_total: Total de requisições bem-sucedidas
        - chat_requests_failed_total: Total de requisições falhadas
        - chat_latency_ms: Histograma de latência
        - chat_tokens_total: Total de tokens utilizados

        Returns:
            str: Métricas no formato Prometheus
        """
        if not self._metrics:
            return "# No metrics available\n"

        summary = self.get_summary()

        lines = []

        # Total de requisições
        lines.append("# HELP chat_requests_total Total number of chat requests")
        lines.append("# TYPE chat_requests_total counter")
        lines.append(f"chat_requests_total {summary['total_requests']}")
        lines.append("")

        # Requisições bem-sucedidas
        lines.append(
            "# HELP chat_requests_success_total Total number of successful chat requests"
        )
        lines.append("# TYPE chat_requests_success_total counter")
        lines.append(f"chat_requests_success_total {summary['successful']}")
        lines.append("")

        # Requisições falhadas
        lines.append(
            "# HELP chat_requests_failed_total Total number of failed chat requests"
        )
        lines.append("# TYPE chat_requests_failed_total counter")
        lines.append(f"chat_requests_failed_total {summary['failed']}")
        lines.append("")

        # Latência (resumo)
        lines.append("# HELP chat_latency_ms_avg Average latency in milliseconds")
        lines.append("# TYPE chat_latency_ms_avg gauge")
        lines.append(f"chat_latency_ms_avg {summary['avg_latency_ms']:.2f}")
        lines.append("")

        lines.append("# HELP chat_latency_ms_min Minimum latency in milliseconds")
        lines.append("# TYPE chat_latency_ms_min gauge")
        lines.append(f"chat_latency_ms_min {summary['min_latency_ms']:.2f}")
        lines.append("")

        lines.append("# HELP chat_latency_ms_max Maximum latency in milliseconds")
        lines.append("# TYPE chat_latency_ms_max gauge")
        lines.append(f"chat_latency_ms_max {summary['max_latency_ms']:.2f}")
        lines.append("")

        # Total de tokens
        lines.append("# HELP chat_tokens_total Total number of tokens used")
        lines.append("# TYPE chat_tokens_total counter")
        lines.append(f"chat_tokens_total {summary['total_tokens']}")
        lines.append("")

        # Métricas por modelo
        lines.append("# HELP chat_requests_by_model Total requests by model")
        lines.append("# TYPE chat_requests_by_model counter")

        model_counts = {}
        for m in self._metrics:
            model_counts[m.model] = model_counts.get(m.model, 0) + 1

        for model, count in model_counts.items():
            lines.append(f'chat_requests_by_model{{model="{model}"}} {count}')

        return "\n".join(lines)

    def export_prometheus_to_file(self, filepath: str) -> None:
        """
        Exporta métricas para arquivo no formato Prometheus.

        Args:
            filepath: Caminho do arquivo para salvar
        """
        content = self.export_prometheus()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
