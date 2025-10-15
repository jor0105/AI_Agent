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
            assert delay2 >= 0.28

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
