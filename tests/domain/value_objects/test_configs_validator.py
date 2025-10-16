import pytest

from src.domain.exceptions.domain_exceptions import InvalidAgentConfigException
from src.domain.value_objects.configs_validator import SupportedConfigs


@pytest.mark.unit
class TestSupportedConfigs:
    """Testes para SupportedConfigs value object."""

    def test_get_available_configs(self):
        configs = SupportedConfigs.get_available_configs()

        assert isinstance(configs, set)
        assert "temperature" in configs
        assert "max_tokens" in configs
        assert "top_p" in configs

    def test_get_available_configs_returns_copy(self):
        configs1 = SupportedConfigs.get_available_configs()
        configs2 = SupportedConfigs.get_available_configs()

        assert configs1 == configs2
        assert configs1 is not configs2

    def test_available_configs_immutable(self):
        configs = SupportedConfigs.get_available_configs()
        original_size = len(configs)

        configs.add("new_config")

        new_configs = SupportedConfigs.get_available_configs()
        assert len(new_configs) == original_size
        assert "new_config" not in new_configs


@pytest.mark.unit
class TestTemperatureValidation:
    """Testes para validação de temperature."""

    def test_validate_temperature_valid_min(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_temperature(0.0)

    def test_validate_temperature_valid_max(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_temperature(2.0)

    def test_validate_temperature_valid_mid_range(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_temperature(1.0)
        SupportedConfigs.validate_temperature(0.5)
        SupportedConfigs.validate_temperature(1.5)

    def test_validate_temperature_none(self):
        # None é aceito (significa não especificado)
        SupportedConfigs.validate_temperature(None)

    def test_validate_temperature_below_min(self):
        with pytest.raises(InvalidAgentConfigException, match="temperature"):
            SupportedConfigs.validate_temperature(-0.1)

    def test_validate_temperature_above_max(self):
        with pytest.raises(InvalidAgentConfigException, match="temperature"):
            SupportedConfigs.validate_temperature(2.1)

    def test_validate_temperature_far_out_of_range(self):
        with pytest.raises(InvalidAgentConfigException, match="temperature"):
            SupportedConfigs.validate_temperature(10.0)

        with pytest.raises(InvalidAgentConfigException, match="temperature"):
            SupportedConfigs.validate_temperature(-5.0)


@pytest.mark.unit
class TestMaxTokensValidation:
    """Testes para validação de max_tokens."""

    def test_validate_max_tokens_valid_small(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_max_tokens(1)

    def test_validate_max_tokens_valid_large(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_max_tokens(10000)

    def test_validate_max_tokens_valid_typical(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_max_tokens(100)
        SupportedConfigs.validate_max_tokens(500)
        SupportedConfigs.validate_max_tokens(2000)

    def test_validate_max_tokens_none(self):
        # None é aceito (significa não especificado)
        SupportedConfigs.validate_max_tokens(None)

    def test_validate_max_tokens_zero(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens(0)

    def test_validate_max_tokens_negative(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens(-1)

        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens(-100)

    def test_validate_max_tokens_string(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens("100")

    def test_validate_max_tokens_float(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            SupportedConfigs.validate_max_tokens(100.5)


@pytest.mark.unit
class TestTopPValidation:
    """Testes para validação de top_p."""

    def test_validate_top_p_valid_min(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_top_p(0.0)

    def test_validate_top_p_valid_max(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_top_p(1.0)

    def test_validate_top_p_valid_mid_range(self):
        # Não deve lançar exceção
        SupportedConfigs.validate_top_p(0.5)
        SupportedConfigs.validate_top_p(0.9)
        SupportedConfigs.validate_top_p(0.95)

    def test_validate_top_p_none(self):
        # None é aceito (significa não especificado)
        SupportedConfigs.validate_top_p(None)

    def test_validate_top_p_below_min(self):
        with pytest.raises(InvalidAgentConfigException, match="top_p"):
            SupportedConfigs.validate_top_p(-0.1)

    def test_validate_top_p_above_max(self):
        with pytest.raises(InvalidAgentConfigException, match="top_p"):
            SupportedConfigs.validate_top_p(1.1)

    def test_validate_top_p_far_out_of_range(self):
        with pytest.raises(InvalidAgentConfigException, match="top_p"):
            SupportedConfigs.validate_top_p(2.0)

        with pytest.raises(InvalidAgentConfigException, match="top_p"):
            SupportedConfigs.validate_top_p(-1.0)


@pytest.mark.unit
class TestValidateConfig:
    """Testes para validação automática de configs."""

    def test_validate_config_temperature(self):
        # Válido
        SupportedConfigs.validate_config("temperature", 0.7)

        # Inválido
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("temperature", 3.0)

    def test_validate_config_max_tokens(self):
        # Válido
        SupportedConfigs.validate_config("max_tokens", 100)

        # Inválido
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("max_tokens", -10)

    def test_validate_config_top_p(self):
        # Válido
        SupportedConfigs.validate_config("top_p", 0.9)

        # Inválido
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config("top_p", 1.5)

    def test_validate_config_unknown_key(self):
        # Chave desconhecida não lança erro (é ignorada)
        SupportedConfigs.validate_config("unknown_key", 123)

    def test_validate_config_all_supported(self):
        # Testa todas as configs suportadas
        SupportedConfigs.validate_config("temperature", 0.8)
        SupportedConfigs.validate_config("max_tokens", 500)
        SupportedConfigs.validate_config("top_p", 0.95)

    def test_validate_config_with_none_values(self):
        # None deve ser aceito para todas as configs
        SupportedConfigs.validate_config("temperature", None)
        SupportedConfigs.validate_config("max_tokens", None)
        SupportedConfigs.validate_config("top_p", None)
