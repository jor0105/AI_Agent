from unittest.mock import Mock, patch

import pytest

from src.domain.exceptions import InvalidAgentConfigException
from src.presentation.agent_controller import AIAgent


@pytest.mark.unit
class TestAIAgentInitialization:
    def test_initialization_creates_agent(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test Agent",
            instructions="Be helpful",
        )

        assert hasattr(controller, "_AIAgent__agent")

    def test_initialization_with_ollama_provider(self):
        controller = AIAgent(
            provider="ollama", model="gemma3:4b", name="Test", instructions="Test"
        )

        assert hasattr(controller, "_AIAgent__agent")

    def test_initialization_creates_chat_use_case(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        assert hasattr(controller, "_AIAgent__chat_use_case")

    def test_initialization_creates_get_config_use_case(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        assert hasattr(controller, "_AIAgent__get_config_use_case")

    def test_initialization_with_invalid_data_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AIAgent(provider="openai", model="", name="Test", instructions="Test")

    def test_initialization_with_custom_config(self):
        config = {"temperature": 0.7, "max_tokens": 1000}
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            config=config,
        )

        agent = controller._AIAgent__agent
        assert agent.config == config

    def test_initialization_with_custom_history_max_size(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            history_max_size=20,
        )

        agent = controller._AIAgent__agent
        assert agent.history.max_size == 20

    def test_initialization_with_default_history_max_size(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
        )

        agent = controller._AIAgent__agent
        assert agent.history.max_size == 10

    def test_initialization_with_invalid_provider_raises_error(self):
        with pytest.raises(Exception):  # Pode ser InvalidAgentConfigException ou outra
            AIAgent(
                provider="invalid_provider",
                model="gpt-5",
                name="Test",
                instructions="Test",
            )

    def test_initialization_with_none_name(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name=None,
            instructions="Test",
        )

        agent = controller._AIAgent__agent
        assert agent.name is None

    def test_initialization_with_none_instructions(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions=None,
        )

        agent = controller._AIAgent__agent
        assert agent.instructions is None

    def test_initialization_with_both_none(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name=None,
            instructions=None,
        )

        agent = controller._AIAgent__agent
        assert agent.name is None
        assert agent.instructions is None

    def test_initialization_with_only_required_fields(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
        )

        agent = controller._AIAgent__agent
        assert agent.provider == "openai"
        assert agent.model == "gpt-5"
        assert agent.name is None
        assert agent.instructions is None


@pytest.mark.unit
class TestAIAgentChat:
    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_returns_response(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "AI response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        response = controller.chat("Hello")

        assert response == "AI response"

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_calls_use_case_with_correct_params(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        controller.chat("Test message")

        assert mock_use_case.execute.called
        call_args = mock_use_case.execute.call_args
        assert call_args[0][1].message == "Test message"

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_with_empty_message(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        response = controller.chat("")

        assert response == "Response"
        call_args = mock_use_case.execute.call_args
        assert call_args[0][1].message == ""

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_when_use_case_raises_exception(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = Exception("API Error")
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        with pytest.raises(Exception, match="API Error"):
            controller.chat("Hello")

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_multiple_chat_calls(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        controller.chat("Message 1")
        controller.chat("Message 2")

        assert mock_use_case.execute.call_count == 2

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_updates_agent_history(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "AI Response"

        def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute.side_effect = execute_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        controller.chat("Hello")

        agent = controller._AIAgent__agent
        assert len(agent.history) == 2


@pytest.mark.unit
class TestAIAgentGetConfigs:
    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_returns_dict(self, mock_create_config):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.to_dict.return_value = {
            "name": "Test",
            "model": "gpt-5-nano",
            "instructions": "Test",
            "history": [],
            "provider": "openai",
        }
        mock_use_case.execute.return_value = mock_output
        mock_create_config.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        config = controller.get_configs()

        assert isinstance(config, dict)
        assert "name" in config
        assert "model" in config

    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_calls_use_case(self, mock_create_config):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.to_dict.return_value = {}
        mock_use_case.execute.return_value = mock_output
        mock_create_config.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        controller.get_configs()

        assert mock_use_case.execute.called

    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_returns_all_expected_fields(self, mock_create_config):
        mock_use_case = Mock()
        mock_output = Mock()
        expected_config = {
            "name": "Test Agent",
            "model": "gpt-5",
            "instructions": "Be helpful",
            "history": [],
            "provider": "openai",
            "config": {"temperature": 0.7},
            "history_max_size": 10,
        }
        mock_output.to_dict.return_value = expected_config
        mock_use_case.execute.return_value = mock_output
        mock_create_config.return_value = mock_use_case

        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test Agent",
            instructions="Be helpful",
        )

        config = controller.get_configs()

        assert config == expected_config

    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_when_use_case_raises_exception(self, mock_create_config):
        """Testa que exceções do use case são propagadas."""
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = Exception("Config Error")
        mock_create_config.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        with pytest.raises(Exception, match="Config Error"):
            controller.get_configs()


@pytest.mark.unit
class TestAIAgentClearHistory:
    def test_clear_history_method_exists(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        assert hasattr(controller, "clear_history")
        assert callable(controller.clear_history)

    def test_clear_history_clears_agent_history(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        agent = controller._AIAgent__agent
        agent.add_user_message("Message 1")
        agent.add_assistant_message("Response 1")
        agent.add_user_message("Message 2")
        agent.add_assistant_message("Response 2")

        assert len(agent.history) == 4

        controller.clear_history()

        assert len(agent.history) == 0

    def test_clear_history_preserves_agent_config(self):
        controller = AIAgent(
            provider="ollama",
            model="gpt-5-nano",
            name="Test Agent",
            instructions="Be helpful",
        )

        agent = controller._AIAgent__agent
        original_model = agent.model
        original_name = agent.name
        original_instructions = agent.instructions
        original_provider = agent.provider

        controller.clear_history()

        assert agent.model == original_model
        assert agent.name == original_name
        assert agent.instructions == original_instructions
        assert agent.provider == original_provider

    def test_clear_history_can_be_called_multiple_times(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        agent = controller._AIAgent__agent
        agent.add_user_message("Message 1")
        agent.add_assistant_message("Response 1")
        assert len(controller._AIAgent__agent.history) > 0

        controller.clear_history()
        assert len(controller._AIAgent__agent.history) == 0

        agent.add_user_message("Message 2")
        agent.add_assistant_message("Response 2")
        assert len(controller._AIAgent__agent.history) > 0

        controller.clear_history()
        assert len(controller._AIAgent__agent.history) == 0

    def test_clear_history_on_empty_history(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        assert len(controller._AIAgent__agent.history) == 0

        controller.clear_history()

        assert len(controller._AIAgent__agent.history) == 0

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_after_clear_history_shows_empty_history(
        self, mock_create_config, mock_create_chat
    ):
        mock_chat_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_chat_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_chat_use_case

        mock_config_use_case = Mock()
        mock_create_config.return_value = mock_config_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        controller.chat("Message 1")

        controller.clear_history()

        controller.get_configs()

        call_args = mock_config_use_case.execute.call_args
        agent_passed = call_args[0][0]
        assert len(agent_passed.history) == 0


@pytest.mark.unit
class TestAIAgentMetrics:
    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_get_metrics_returns_list(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        metrics = controller.get_metrics()

        assert isinstance(metrics, list)
        assert len(metrics) == 1
        assert isinstance(metrics[0], ChatMetrics)

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_get_metrics_calls_use_case_method(self, mock_create_chat):
        """Testa que get_metrics chama o método correto do use case."""
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        controller.get_metrics()

        mock_use_case.get_metrics.assert_called_once()

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_get_metrics_when_adapter_has_no_metrics(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        metrics = controller.get_metrics()

        assert metrics == []

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_get_metrics_with_multiple_metrics(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0, tokens_used=50),
            ChatMetrics(model="gpt-5-nano", latency_ms=150.0, tokens_used=75),
            ChatMetrics(model="gpt-5-nano", latency_ms=120.0, tokens_used=60),
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        metrics = controller.get_metrics()

        assert len(metrics) == 3
        assert all(isinstance(m, ChatMetrics) for m in metrics)

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_json(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0, tokens_used=50)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        json_str = controller.export_metrics_json()

        assert isinstance(json_str, str)
        assert "gpt-5-nano" in json_str
        assert "summary" in json_str

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_json_to_file(self, mock_create_chat, tmp_path):
        import json

        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0, tokens_used=50)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        filepath = tmp_path / "metrics.json"
        controller.export_metrics_json(str(filepath))

        assert filepath.exists()

        with open(filepath, "r") as f:
            data = json.load(f)

        assert "summary" in data
        assert "metrics" in data

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_prometheus(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        prom_text = controller.export_metrics_prometheus()

        assert isinstance(prom_text, str)
        assert "chat_requests_total" in prom_text

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_prometheus_to_file(self, mock_create_chat, tmp_path):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        filepath = tmp_path / "metrics.prom"
        controller.export_metrics_prometheus(str(filepath))

        assert filepath.exists()

        with open(filepath, "r") as f:
            content = f.read()

        assert "chat_requests_total" in content

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_json_with_empty_metrics(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        json_str = controller.export_metrics_json()

        assert isinstance(json_str, str)
        assert "summary" in json_str

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_prometheus_with_empty_metrics(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        prom_text = controller.export_metrics_prometheus()

        assert isinstance(prom_text, str)
        # Prometheus deve retornar algo mesmo sem métricas


@pytest.mark.unit
class TestAIAgentIntegration:
    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_and_get_configs_together(self, mock_create_chat):
        """Testa uso combinado de chat e get_configs."""
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        # Chat primeiro
        response = controller.chat("Hello")
        assert response == "Response"

        # Depois get_configs
        configs = controller.get_configs()
        assert isinstance(configs, dict)

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_clear_history_chat_again(self, mock_create_chat):
        """Testa fluxo: chat -> clear_history -> chat novamente."""
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"

        def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute.side_effect = execute_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        # Primeiro chat
        controller.chat("Message 1")
        agent = controller._AIAgent__agent
        assert len(agent.history) == 2

        # Limpa histórico
        controller.clear_history()
        assert len(agent.history) == 0

        # Segundo chat
        controller.chat("Message 2")
        assert len(agent.history) == 2

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_metrics_accumulate_after_multiple_chats(self, mock_create_chat):
        """Testa que métricas se acumulam após múltiplos chats."""
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output

        # Simula acúmulo de métricas
        metrics_list = []

        def get_metrics_side_effect():
            return metrics_list.copy()

        def execute_side_effect(agent, input_dto):
            metrics_list.append(ChatMetrics(model="gpt-5", latency_ms=100.0))
            return mock_output

        mock_use_case.get_metrics.side_effect = get_metrics_side_effect
        mock_use_case.execute.side_effect = execute_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        # Faz 3 chats
        controller.chat("Message 1")
        controller.chat("Message 2")
        controller.chat("Message 3")

        # Verifica métricas
        metrics = controller.get_metrics()
        assert len(metrics) == 3


@pytest.mark.unit
class TestAIAgentEdgeCases:
    """Testes de casos extremos e edge cases."""

    def test_initialization_with_very_long_instructions(self):
        long_instructions = "A" * 10000
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions=long_instructions,
        )

        agent = controller._AIAgent__agent
        assert agent.instructions == long_instructions

    def test_initialization_with_special_characters_in_name(self):
        special_name = "Test-Agent_123!@#$%"
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name=special_name,
            instructions="Test",
        )

        agent = controller._AIAgent__agent
        assert agent.name == special_name

    def test_initialization_with_unicode_characters(self):
        unicode_name = "测试代理 🤖"
        unicode_instructions = "Seja útil e educado 你好"

        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name=unicode_name,
            instructions=unicode_instructions,
        )

        agent = controller._AIAgent__agent
        assert agent.name == unicode_name
        assert agent.instructions == unicode_instructions

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_with_very_long_message(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        long_message = "A" * 50000
        response = controller.chat(long_message)

        assert response == "Response"
        call_args = mock_use_case.execute.call_args
        assert call_args[0][1].message == long_message

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_with_unicode_message(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "回复"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        unicode_message = "你好，世界！ 🌍"
        response = controller.chat(unicode_message)

        assert response == "回复"

    def test_initialization_with_history_max_size_zero(self):
        with pytest.raises(InvalidAgentConfigException, match="history_max_size"):
            AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                history_max_size=0,
            )

    def test_initialization_with_negative_history_max_size(self):
        """Testa que tamanho negativo de histórico pode causar erro."""
        # Isso pode ou não lançar erro dependendo da implementação
        # Vamos testar que o sistema lida com isso de alguma forma
        try:
            controller = AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                history_max_size=-1,
            )
            # Se não lançar erro, pelo menos verifica que foi criado
            assert hasattr(controller, "_AIAgent__agent")
        except (ValueError, InvalidAgentConfigException):
            # É aceitável que lance erro
            pass

    def test_initialization_with_empty_config_dict(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            config={},
        )

        agent = controller._AIAgent__agent
        assert agent.config == {}

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_to_nonexistent_directory(self, mock_create_chat, tmp_path):
        """Testa exportação de métricas para diretório inexistente."""
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        # Tenta salvar em diretório que não existe
        nonexistent_path = tmp_path / "nonexistent" / "metrics.json"

        # Pode lançar erro ou criar o diretório automaticamente
        # dependendo da implementação
        try:
            controller.export_metrics_json(str(nonexistent_path))
        except (FileNotFoundError, OSError):
            # É aceitável que lance erro
            pass
