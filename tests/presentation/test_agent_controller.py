from unittest.mock import Mock, patch

import pytest

from src.domain.exceptions import InvalidAgentConfigException
from src.presentation.agent_controller import AIAgent


@pytest.mark.unit
class TestAIAgent:
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

    def test_multiple_chat_calls(self):
        with patch(
            "src.presentation.agent_controller.AgentComposer.create_chat_use_case"
        ) as mock:
            mock_use_case = Mock()
            mock_output = Mock()
            mock_output.response = "Response"
            mock_use_case.execute.return_value = mock_output
            mock.return_value = mock_use_case

            controller = AIAgent(
                provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
            )

            controller.chat("Message 1")
            controller.chat("Message 2")

            assert mock_use_case.execute.call_count == 2

    def test_controller_manages_agent_state(self):
        with patch(
            "src.presentation.agent_controller.AgentComposer.create_chat_use_case"
        ) as mock_chat:
            with patch(
                "src.presentation.agent_controller.AgentComposer.create_get_config_use_case"
            ) as mock_config:
                mock_chat_use_case = Mock()
                mock_config_use_case = Mock()
                mock_chat.return_value = mock_chat_use_case
                mock_config.return_value = mock_config_use_case

                controller = AIAgent(
                    provider="openai",
                    model="gpt-5-nano",
                    name="Test",
                    instructions="Test",
                )

                assert hasattr(controller, "_AIAgent__agent")
                assert hasattr(controller, "_AIAgent__chat_use_case")
                assert hasattr(controller, "_AIAgent__get_config_use_case")

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
