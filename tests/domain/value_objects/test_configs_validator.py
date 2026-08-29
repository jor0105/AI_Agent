from typing import cast

import pytest

from createagents.domain import InvalidAgentConfigException, SupportedConfigs


@pytest.mark.unit
class TestSupportedConfigs:
    def test_get_available_configs(self):
        configs = SupportedConfigs.get_available_configs()

        assert isinstance(configs, set)
        assert 'temperature' in configs
        assert 'max_tokens' in configs
        assert 'top_p' in configs

    def test_get_available_configs_returns_copy(self):
        configs1 = SupportedConfigs.get_available_configs()
        configs2 = SupportedConfigs.get_available_configs()

        assert configs1 == configs2
        assert configs1 is not configs2

    def test_available_configs_immutable(self):
        configs = SupportedConfigs.get_available_configs()
        original_size = len(configs)

        configs.add('new_config')

        new_configs = SupportedConfigs.get_available_configs()
        assert len(new_configs) == original_size
        assert 'new_config' not in new_configs


@pytest.mark.unit
class TestTemperatureValidation:
    @pytest.mark.parametrize(
        'value', [0.0, 2.0, 1.0, 0.5, 1.5, None, 0.123456789, 1.999999999]
    )
    def test_validate_temperature_accepts_valid_values(self, value):
        assert SupportedConfigs.validate_temperature(value) is None

    @pytest.mark.parametrize('value', [-0.1, 2.1, 10.0, -5.0, -0.01, 2.01])
    def test_validate_temperature_rejects_invalid_values(self, value):
        with pytest.raises(InvalidAgentConfigException, match='temperature'):
            SupportedConfigs.validate_temperature(value)


@pytest.mark.unit
class TestMaxTokensValidation:
    @pytest.mark.parametrize(
        'value', [1, 100, 500, 2000, 10000, None, 1000000]
    )
    def test_validate_max_tokens_accepts_valid_values(self, value):
        assert SupportedConfigs.validate_max_tokens(value) is None

    @pytest.mark.parametrize('value', [0, -1, -100, '100', 100.5])
    def test_validate_max_tokens_rejects_invalid_values(self, value):
        with pytest.raises(InvalidAgentConfigException, match='max_tokens'):
            SupportedConfigs.validate_max_tokens(value)


@pytest.mark.unit
class TestTopPValidation:
    @pytest.mark.parametrize(
        'value', [0.0, 1.0, 0.5, 0.9, 0.95, None, 0.123456789, 0.999999999]
    )
    def test_validate_top_p_accepts_valid_values(self, value):
        assert SupportedConfigs.validate_top_p(value) is None

    @pytest.mark.parametrize('value', [-0.1, 1.1, 2.0, -1.0, -0.01, 1.01])
    def test_validate_top_p_rejects_invalid_values(self, value):
        with pytest.raises(InvalidAgentConfigException, match='top_p'):
            SupportedConfigs.validate_top_p(value)


@pytest.mark.unit
class TestValidateConfig:
    def test_validate_config_temperature(self):
        assert SupportedConfigs.validate_config('temperature', 0.7) is None

        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('temperature', 3.0)

    def test_validate_config_max_tokens(self):
        assert SupportedConfigs.validate_config('max_tokens', 100) is None

        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('max_tokens', -10)

    def test_validate_config_top_p(self):
        assert SupportedConfigs.validate_config('top_p', 0.9) is None

        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('top_p', 1.5)

    def test_validate_config_unknown_key(self):
        assert SupportedConfigs.validate_config('unknown_key', 123) is None

    def test_validate_config_all_supported(self):
        assert SupportedConfigs.validate_config('temperature', 0.8) is None
        assert SupportedConfigs.validate_config('max_tokens', 500) is None
        assert SupportedConfigs.validate_config('top_p', 0.95) is None

    def test_validate_config_with_none_values(self):
        assert SupportedConfigs.validate_config('temperature', None) is None
        assert SupportedConfigs.validate_config('max_tokens', None) is None
        assert SupportedConfigs.validate_config('top_p', None) is None

    def test_validate_config_boundary_values(self):
        """Test validation with exact boundary values."""
        assert SupportedConfigs.validate_config('temperature', 0.0) is None
        assert SupportedConfigs.validate_config('temperature', 2.0) is None

        assert SupportedConfigs.validate_config('top_p', 0.0) is None
        assert SupportedConfigs.validate_config('top_p', 1.0) is None

        assert SupportedConfigs.validate_config('max_tokens', 1) is None

    def test_validate_config_just_outside_boundaries(self):
        """Test validation with values just outside the boundaries."""
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('temperature', -0.01)
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('temperature', 2.01)

        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('top_p', -0.01)
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('top_p', 1.01)

        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('max_tokens', 0)

    def test_get_available_configs_contains_all_supported(self):
        configs = SupportedConfigs.get_available_configs()
        expected_configs = {
            'temperature',
            'max_tokens',
            'top_p',
            'think',
            'top_k',
            'stream',
        }
        assert configs == expected_configs

    def test_validate_max_tokens_with_large_value(self):
        assert SupportedConfigs.validate_max_tokens(1000000) is None

    def test_validate_temperature_precision(self):
        assert SupportedConfigs.validate_temperature(0.123456789) is None
        assert SupportedConfigs.validate_temperature(1.999999999) is None

    def test_validate_top_p_precision(self):
        assert SupportedConfigs.validate_top_p(0.123456789) is None
        assert SupportedConfigs.validate_top_p(0.999999999) is None


@pytest.mark.unit
class TestThinkValidation:
    def test_validate_think_with_boolean_true(self):
        assert SupportedConfigs.validate_think(True) is None

    def test_validate_think_with_boolean_false(self):
        assert SupportedConfigs.validate_think(False) is None

    def test_validate_think_with_none(self):
        assert SupportedConfigs.validate_think(None) is None

    def test_validate_think_with_valid_string_high(self):
        assert SupportedConfigs.validate_think('high') is None
        assert SupportedConfigs.validate_think('HIGH') is None
        assert SupportedConfigs.validate_think('High') is None

    def test_validate_think_with_valid_string_low(self):
        assert SupportedConfigs.validate_think('low') is None
        assert SupportedConfigs.validate_think('LOW') is None
        assert SupportedConfigs.validate_think('Low') is None

    def test_validate_think_with_valid_string_medium(self):
        assert SupportedConfigs.validate_think('medium') is None
        assert SupportedConfigs.validate_think('MEDIUM') is None
        assert SupportedConfigs.validate_think('Medium') is None

    def test_validate_think_with_invalid_string(self):
        with pytest.raises(InvalidAgentConfigException, match='think'):
            SupportedConfigs.validate_think('enabled')

    def test_validate_think_with_dict_should_fail(self):
        # Dicts are no longer accepted
        with pytest.raises(InvalidAgentConfigException, match='think'):
            SupportedConfigs.validate_think(
                cast(bool | str | None, {'type': 'enabled'})
            )

    def test_validate_think_with_empty_dict_should_fail(self):
        # Empty dicts are no longer accepted
        with pytest.raises(InvalidAgentConfigException, match='think'):
            SupportedConfigs.validate_think(cast(bool | str | None, {}))

    def test_validate_think_with_invalid_string_value(self):
        with pytest.raises(InvalidAgentConfigException, match='think'):
            SupportedConfigs.validate_think('true')

    def test_validate_think_with_invalid_type_int(self):
        with pytest.raises(InvalidAgentConfigException, match='think'):
            SupportedConfigs.validate_think(cast(bool | str | None, 1))

    def test_validate_think_with_invalid_type_float(self):
        with pytest.raises(InvalidAgentConfigException, match='think'):
            SupportedConfigs.validate_think(cast(bool | str | None, 0.5))

    def test_validate_think_with_invalid_type_list(self):
        with pytest.raises(InvalidAgentConfigException, match='think'):
            SupportedConfigs.validate_think(
                cast(bool | str | None, ['enabled'])
            )

    def test_validate_think_error_message_format(self):
        with pytest.raises(InvalidAgentConfigException) as exc_info:
            SupportedConfigs.validate_think('invalid')

        error_msg = str(exc_info.value)
        assert (
            'high' in error_msg.lower()
            or 'low' in error_msg.lower()
            or 'medium' in error_msg.lower()
        )


@pytest.mark.unit
class TestTopKValidation:
    def test_validate_top_k_with_valid_small_value(self):
        assert SupportedConfigs.validate_top_k(1) is None

    def test_validate_top_k_with_valid_medium_value(self):
        assert SupportedConfigs.validate_top_k(50) is None

    def test_validate_top_k_with_valid_large_value(self):
        assert SupportedConfigs.validate_top_k(1000) is None

    def test_validate_top_k_with_none(self):
        assert SupportedConfigs.validate_top_k(None) is None

    def test_validate_top_k_with_zero(self):
        with pytest.raises(InvalidAgentConfigException, match='top_k'):
            SupportedConfigs.validate_top_k(0)

    def test_validate_top_k_with_negative_value(self):
        with pytest.raises(InvalidAgentConfigException, match='top_k'):
            SupportedConfigs.validate_top_k(-1)

    def test_validate_top_k_with_large_negative_value(self):
        with pytest.raises(InvalidAgentConfigException, match='top_k'):
            SupportedConfigs.validate_top_k(-100)

    def test_validate_top_k_with_float_value(self):
        with pytest.raises(InvalidAgentConfigException, match='top_k'):
            SupportedConfigs.validate_top_k(cast(int | None, 10.5))

    def test_validate_top_k_with_string_value(self):
        with pytest.raises(InvalidAgentConfigException, match='top_k'):
            SupportedConfigs.validate_top_k(cast(int | None, '10'))

    def test_validate_top_k_with_boolean_value(self):
        with pytest.raises(InvalidAgentConfigException, match='top_k'):
            SupportedConfigs.validate_top_k(False)

    def test_validate_top_k_error_message_format(self):
        with pytest.raises(InvalidAgentConfigException) as exc_info:
            SupportedConfigs.validate_top_k(0)

        error_msg = str(exc_info.value)
        assert 'top_k' in error_msg
        assert 'integer' in error_msg.lower()
        assert 'greater than zero' in error_msg.lower()


@pytest.mark.unit
class TestStreamValidation:
    def test_validate_stream_scenarios_accepts_boolean(self):
        assert SupportedConfigs.validate_stream(True) is None
        assert SupportedConfigs.validate_stream(False) is None
        assert SupportedConfigs.validate_stream(None) is None

    def test_validate_stream_scenarios_rejects_invalid_types(self):
        with pytest.raises(InvalidAgentConfigException, match='stream'):
            SupportedConfigs.validate_stream(cast(bool | None, 'yes'))
        with pytest.raises(InvalidAgentConfigException, match='stream'):
            SupportedConfigs.validate_stream(cast(bool | None, 1))


@pytest.mark.unit
class TestValidateConfigExtended:
    def test_validate_config_think_with_boolean(self):
        assert SupportedConfigs.validate_config('think', True) is None
        assert SupportedConfigs.validate_config('think', False) is None

    def test_validate_config_think_with_valid_string(self):
        assert SupportedConfigs.validate_config('think', 'low') is None
        assert SupportedConfigs.validate_config('think', 'medium') is None
        assert SupportedConfigs.validate_config('think', 'high') is None

    def test_validate_config_think_with_invalid_string(self):
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('think', 'invalid')

    def test_validate_config_top_k_with_valid_value(self):
        assert SupportedConfigs.validate_config('top_k', 40) is None

    def test_validate_config_top_k_with_invalid_value(self):
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('top_k', 0)

        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('top_k', -5)

    def test_validate_config_all_supported_configs(self):
        assert SupportedConfigs.validate_config('temperature', 0.7) is None
        assert SupportedConfigs.validate_config('max_tokens', 100) is None
        assert SupportedConfigs.validate_config('top_p', 0.9) is None
        assert SupportedConfigs.validate_config('think', True) is None
        assert SupportedConfigs.validate_config('top_k', 50) is None

    def test_get_available_configs_includes_think_and_top_k(self):
        configs = SupportedConfigs.get_available_configs()

        assert 'think' in configs
        assert 'top_k' in configs

    def test_get_available_configs_complete_set(self):
        configs = SupportedConfigs.get_available_configs()
        expected = {
            'temperature',
            'max_tokens',
            'top_p',
            'think',
            'top_k',
            'stream',
        }

        assert configs == expected

    def test_validate_config_stream_scenarios(self):
        SupportedConfigs.validate_config('stream', True)
        SupportedConfigs.validate_config('stream', False)
        with pytest.raises(InvalidAgentConfigException):
            SupportedConfigs.validate_config('stream', 'enabled')
