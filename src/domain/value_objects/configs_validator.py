from typing import Set

from src.domain.exceptions.domain_exceptions import InvalidAgentConfigException


class SupportedConfigs:
    """
    Value Object responsável por gerenciar e validar configurações suportadas para agentes de IA.

    Responsabilidades:
    - Definir configurações suportadas
    - Validar valores de configurações específicas
    - Prover interface para validação automática
    """

    __AVAILABLE_CONFIGS: Set[str] = {"temperature", "max_tokens", "top_p"}

    @classmethod
    def get_available_configs(cls) -> Set[str]:
        """
        Retorna o conjunto de configurações suportadas.

        Returns:
            Set[str]: Conjunto com nomes das configurações disponíveis
        """
        return cls.__AVAILABLE_CONFIGS.copy()

    @staticmethod
    def validate_temperature(value: float) -> None:
        """
        Valida o parâmetro temperature.

        Args:
            value: Valor da temperatura (deve estar entre 0.0 e 2.0)

        Raises:
            InvalidAgentConfigException: Se o valor estiver fora do intervalo permitido
        """
        if value is not None and not (0.0 <= value <= 2.0):
            raise InvalidAgentConfigException(
                "temperature", "deve ser um float entre 0.0 e 2.0"
            )

    @staticmethod
    def validate_max_tokens(value: int) -> None:
        """
        Valida o parâmetro max_tokens.

        Args:
            value: Valor de max_tokens (deve ser um inteiro maior que zero)

        Raises:
            InvalidAgentConfigException: Se o valor for inválido
        """
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise InvalidAgentConfigException(
                "max_tokens", "deve ser um inteiro maior que zero"
            )

    @staticmethod
    def validate_top_p(value: float) -> None:
        """
        Valida o parâmetro top_p.

        Args:
            value: Valor de top_p (deve estar entre 0.0 e 1.0)

        Raises:
            InvalidAgentConfigException: Se o valor estiver fora do intervalo permitido
        """
        if value is not None and not (0.0 <= value <= 1.0):
            raise InvalidAgentConfigException(
                "top_p", "deve ser um float entre 0.0 e 1.0"
            )

    @classmethod
    def validate_config(cls, key: str, value) -> None:
        """
        Valida uma configuração específica com base na chave.

        Args:
            key: Nome da configuração
            value: Valor da configuração

        Raises:
            InvalidAgentConfigException: Se a validação falhar
        """
        validators = {
            "temperature": cls.validate_temperature,
            "max_tokens": cls.validate_max_tokens,
            "top_p": cls.validate_top_p,
        }
        validator = validators.get(key)
        if validator:
            validator(value)
