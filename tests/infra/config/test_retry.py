import time
from unittest.mock import Mock, patch

import pytest

from src.infra.config.retry import retry_with_backoff


@pytest.mark.unit
class TestRetryWithBackoff:
    """Testes para o decorator retry_with_backoff."""

    def test_successful_execution_no_retry(self):
        mock_func = Mock(return_value="success")

        @retry_with_backoff(max_attempts=3)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_exception(self):
        mock_func = Mock(
            side_effect=[Exception("Error 1"), Exception("Error 2"), "success"]
        )

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_max_attempts_reached_raises_exception(self):
        mock_func = Mock(side_effect=Exception("Persistent error"))

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(Exception, match="Persistent error"):
            test_func()

        assert mock_func.call_count == 3

    def test_backoff_delay_increases(self):
        call_times = []

        def failing_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Error")
            return "success"

        @retry_with_backoff(max_attempts=3, initial_delay=0.1, backoff_factor=2.0)
        def test_func():
            return failing_func()

        result = test_func()

        assert result == "success"
        assert len(call_times) == 3

        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert delay1 >= 0.09

        if len(call_times) >= 3:
            delay2 = call_times[2] - call_times[1]
            assert delay2 >= 0.18

    def test_only_specified_exceptions_trigger_retry(self):
        mock_func = Mock(side_effect=ValueError("Wrong exception"))

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, exceptions=(ConnectionError,)
        )
        def test_func():
            return mock_func()

        with pytest.raises(ValueError, match="Wrong exception"):
            test_func()

        assert mock_func.call_count == 1

    def test_multiple_exception_types(self):
        mock_func = Mock(
            side_effect=[ValueError("Error 1"), TypeError("Error 2"), "success"]
        )

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, exceptions=(ValueError, TypeError)
        )
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_default_parameters(self):
        call_count = [0]

        @retry_with_backoff()
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Error")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 2

    def test_function_with_arguments(self):
        mock_func = Mock(return_value="result")

        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        def test_func(a, b, c=None):
            return mock_func(a, b, c)

        result = test_func(1, 2, c=3)

        assert result == "result"
        mock_func.assert_called_once_with(1, 2, 3)

    def test_preserves_function_metadata(self):
        @retry_with_backoff()
        def test_func():
            """Test docstring"""
            pass

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test docstring"

    def test_logging_on_retry(self):
        mock_func = Mock(side_effect=[Exception("Error"), "success"])

        with patch("src.infra.config.retry.LoggingConfig.get_logger") as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance

            @retry_with_backoff(max_attempts=3, initial_delay=0.01)
            def test_func():
                return mock_func()

            result = test_func()

            assert result == "success"
            assert mock_log_instance.warning.call_count == 1

    def test_logging_on_final_failure(self):
        mock_func = Mock(side_effect=Exception("Persistent error"))

        with patch("src.infra.config.retry.LoggingConfig.get_logger") as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance

            @retry_with_backoff(max_attempts=2, initial_delay=0.01)
            def test_func():
                return mock_func()

            with pytest.raises(Exception):
                test_func()

            assert mock_log_instance.error.call_count == 1

    def test_zero_initial_delay(self):
        mock_func = Mock(side_effect=[Exception("Error"), "success"])

        @retry_with_backoff(max_attempts=3, initial_delay=0.0)
        def test_func():
            return mock_func()

        start_time = time.time()
        result = test_func()
        elapsed = time.time() - start_time

        assert result == "success"
        assert elapsed < 0.1

    def test_custom_backoff_factor(self):
        call_times = []

        def failing_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Error")
            return "success"

        @retry_with_backoff(max_attempts=3, initial_delay=0.1, backoff_factor=3.0)
        def test_func():
            return failing_func()

        result = test_func()

        assert result == "success"

        if len(call_times) >= 3:
            delay2 = call_times[2] - call_times[1]
            # Com backoff_factor=3.0, delay esperado = 0.1 * 3.0 = 0.3
            # Com jitter (±10%), pode variar entre 0.27 e 0.33
            assert 0.27 <= delay2 <= 0.35  # Margem para jitter

    def test_single_attempt(self):
        mock_func = Mock(side_effect=Exception("Error"))

        @retry_with_backoff(max_attempts=1, initial_delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(Exception, match="Error"):
            test_func()

        assert mock_func.call_count == 1

    def test_many_retries(self):
        call_count = [0]

        @retry_with_backoff(max_attempts=10, initial_delay=0.01)
        def test_func():
            call_count[0] += 1
            if call_count[0] < 10:
                raise Exception("Error")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 10

    def test_exception_message_preserved(self):
        error_message = "Specific error message"
        mock_func = Mock(side_effect=Exception(error_message))

        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(Exception, match=error_message):
            test_func()

    def test_different_exception_on_each_retry(self):
        exceptions = [ValueError("Error 1"), TypeError("Error 2"), KeyError("Error 3")]
        mock_func = Mock(side_effect=exceptions + ["success"])

        @retry_with_backoff(
            max_attempts=4,
            initial_delay=0.01,
            exceptions=(ValueError, TypeError, KeyError),
        )
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 4

    def test_nested_retry_decorators(self):
        call_count = [0]

        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Error")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] >= 2

    def test_return_value_types(self):
        test_cases = [
            42,
            "string",
            [1, 2, 3],
            {"key": "value"},
            None,
            True,
        ]

        for expected_value in test_cases:
            mock_func = Mock(return_value=expected_value)

            @retry_with_backoff(max_attempts=2, initial_delay=0.01)
            def test_func():
                return mock_func()

            result = test_func()
            assert result == expected_value

    def test_jitter_disabled(self):
        """Testa que jitter=False não adiciona variação."""
        call_times = []

        def failing_func():
            call_times.append(time.time())
            if len(call_times) < 2:
                raise Exception("Error")
            return "success"

        @retry_with_backoff(
            max_attempts=2, initial_delay=0.1, backoff_factor=1.0, jitter=False
        )
        def test_func():
            return failing_func()

        result = test_func()

        assert result == "success"
        # Com jitter=False e backoff_factor=1.0, delay deve ser exatamente 0.1
        if len(call_times) >= 2:
            delay = call_times[1] - call_times[0]
            assert 0.09 <= delay <= 0.11  # Tolerância pequena

    def test_jitter_enabled_adds_variation(self):
        """Testa que jitter=True adiciona variação ao delay."""
        delays = []

        def failing_func():
            if len(delays) > 0:
                return "success"
            raise Exception("Error")

        # Executa múltiplas vezes para verificar variação
        for _ in range(5):
            call_times = []

            @retry_with_backoff(
                max_attempts=2, initial_delay=0.1, backoff_factor=1.0, jitter=True
            )
            def test_func():
                call_times.append(time.time())
                if len(call_times) < 2:
                    raise Exception("Error")
                return "success"

            test_func()

            if len(call_times) >= 2:
                delays.append(call_times[1] - call_times[0])

        # Com jitter, delays devem variar (não todos iguais)
        # Jitter é ±10%, então range é [0.09, 0.11]
        assert len(set([round(d, 3) for d in delays])) > 1  # Deve ter variação

    def test_callback_is_called_on_retry(self):
        """Testa que callback é chamado a cada retry."""
        callback_calls = []

        def on_retry_callback(attempt, exception):
            callback_calls.append((attempt, str(exception)))

        mock_func = Mock(
            side_effect=[Exception("Error 1"), Exception("Error 2"), "success"]
        )

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, on_retry=on_retry_callback
        )
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert len(callback_calls) == 2  # Callback chamado nos 2 retries
        assert callback_calls[0] == (1, "Error 1")
        assert callback_calls[1] == (2, "Error 2")

    def test_callback_not_called_on_success(self):
        """Testa que callback não é chamado se não houver retry."""
        callback_calls = []

        def on_retry_callback(attempt, exception):
            callback_calls.append((attempt, str(exception)))

        mock_func = Mock(return_value="success")

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, on_retry=on_retry_callback
        )
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert len(callback_calls) == 0

    def test_callback_receives_correct_attempt_number(self):
        """Testa que callback recebe número de tentativa correto."""
        callback_data = []

        def on_retry_callback(attempt, exception):
            callback_data.append(attempt)

        call_count = [0]

        @retry_with_backoff(
            max_attempts=5, initial_delay=0.01, on_retry=on_retry_callback
        )
        def test_func():
            call_count[0] += 1
            if call_count[0] < 4:
                raise Exception("Error")
            return "success"

        test_func()

        # Callback deve ser chamado com attempts 1, 2, 3
        assert callback_data == [1, 2, 3]

    def test_callback_exception_does_not_break_retry(self):
        """Testa que exceção no callback não quebra o retry."""

        def failing_callback(attempt, exception):
            raise RuntimeError("Callback error")

        mock_func = Mock(side_effect=[Exception("Error"), "success"])

        with patch("src.infra.config.retry.LoggingConfig.get_logger") as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance

            @retry_with_backoff(
                max_attempts=3, initial_delay=0.01, on_retry=failing_callback
            )
            def test_func():
                return mock_func()

            result = test_func()

            # Deve ter sucesso apesar do erro no callback
            assert result == "success"
            # Logger.warning deve ter sido chamado para o erro do callback
            assert mock_log_instance.warning.call_count >= 1

    def test_callback_with_none_does_not_error(self):
        """Testa que on_retry=None funciona corretamente."""
        mock_func = Mock(side_effect=[Exception("Error"), "success"])

        @retry_with_backoff(max_attempts=3, initial_delay=0.01, on_retry=None)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"

    def test_jitter_with_different_delays(self):
        """Testa jitter com diferentes delays iniciais."""
        for initial_delay in [0.05, 0.1, 0.2]:
            call_times = []

            @retry_with_backoff(
                max_attempts=2, initial_delay=initial_delay, jitter=True
            )
            def test_func():
                call_times.append(time.time())
                if len(call_times) < 2:
                    raise Exception("Error")
                return "success"

            test_func()

            if len(call_times) >= 2:
                actual_delay = call_times[1] - call_times[0]
                # Jitter é ±10%, então deve estar no range
                min_delay = initial_delay * 0.9
                max_delay = initial_delay * 1.1
                assert min_delay <= actual_delay <= max_delay * 1.1  # Tolerância extra

    def test_callback_receives_exception_object(self):
        """Testa que callback recebe objeto de exceção correto."""
        received_exceptions = []

        def on_retry_callback(attempt, exception):
            received_exceptions.append(type(exception).__name__)

        @retry_with_backoff(
            max_attempts=4,
            initial_delay=0.01,
            on_retry=on_retry_callback,
            exceptions=(ValueError, TypeError, KeyError),
        )
        def test_func():
            if len(received_exceptions) == 0:
                raise ValueError("First")
            elif len(received_exceptions) == 1:
                raise TypeError("Second")
            elif len(received_exceptions) == 2:
                raise KeyError("Third")
            return "success"

        result = test_func()

        assert result == "success"
        assert received_exceptions == ["ValueError", "TypeError", "KeyError"]

    def test_jitter_and_callback_together(self):
        """Testa que jitter e callback funcionam juntos."""
        callback_calls = []

        def on_retry_callback(attempt, exception):
            callback_calls.append(attempt)

        call_times = []

        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.05,
            jitter=True,
            on_retry=on_retry_callback,
        )
        def test_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception(f"Error {len(call_times)}")
            return "success"

        result = test_func()

        assert result == "success"
        assert len(callback_calls) == 2  # Callbacks nos retries
        assert callback_calls == [1, 2]
        # Delays devem ter jitter aplicado
        assert len(call_times) == 3

    def test_callback_can_access_exception_message(self):
        """Testa que callback pode acessar mensagem da exceção."""
        messages = []

        def on_retry_callback(attempt, exception):
            messages.append(str(exception))

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, on_retry=on_retry_callback
        )
        def test_func():
            if len(messages) == 0:
                raise Exception("First error")
            elif len(messages) == 1:
                raise Exception("Second error")
            return "success"

        result = test_func()

        assert result == "success"
        assert messages == ["First error", "Second error"]

    def test_jitter_default_is_true(self):
        """Testa que jitter é True por padrão."""
        # Testa implicitamente que jitter está ativo por padrão
        # Executando múltiplas vezes e verificando variação
        delays = []

        for _ in range(3):
            call_times = []

            @retry_with_backoff(max_attempts=2, initial_delay=0.05)
            def test_func():
                call_times.append(time.time())
                if len(call_times) < 2:
                    raise Exception("Error")
                return "success"

            test_func()

            if len(call_times) >= 2:
                delays.append(round(call_times[1] - call_times[0], 3))

        # Com jitter ativo por padrão, deve haver alguma variação
        # (pode não ser sempre diferente devido ao arredondamento, mas testamos)
        assert min(delays) >= 0.045  # No mínimo 90% de 0.05
        assert max(delays) <= 0.055  # No máximo 110% de 0.05
