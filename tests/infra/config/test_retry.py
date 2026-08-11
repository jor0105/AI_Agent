from unittest.mock import AsyncMock, Mock, patch

import pytest

from createagents.infra import retry_with_backoff


class RetryableTestError(Exception):
    """Failure used to exercise the retry policy."""


@pytest.fixture(autouse=True)
def no_real_sleep():
    """Never block on the backoff delay; record it instead.

    Nothing in this module asserts on elapsed wall-clock time, so sleeping
    for real only made the suite slow and load-sensitive.
    """
    with patch('createagents.infra.config.retry.time.sleep') as sleep:
        yield sleep


@pytest.mark.unit
class TestRetryWithBackoff:
    def test_successful_execution_no_retry(self):
        mock_func = Mock(return_value='success')

        @retry_with_backoff(max_attempts=3)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == 'success'
        assert mock_func.call_count == 1

    def test_retry_on_exception(self):
        mock_func = Mock(
            side_effect=[Exception('Error 1'), Exception('Error 2'), 'success']
        )

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == 'success'
        assert mock_func.call_count == 3

    def test_max_attempts_reached_raises_exception(self):
        mock_func = Mock(side_effect=Exception('Persistent error'))

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(Exception, match='Persistent error'):
            test_func()

        assert mock_func.call_count == 3

    def test_only_specified_exceptions_trigger_retry(self):
        mock_func = Mock(side_effect=ValueError('Wrong exception'))

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, exceptions=(ConnectionError,)
        )
        def test_func():
            return mock_func()

        with pytest.raises(ValueError, match='Wrong exception'):
            test_func()

        assert mock_func.call_count == 1

    def test_multiple_exception_types(self):
        mock_func = Mock(
            side_effect=[
                ValueError('Error 1'),
                TypeError('Error 2'),
                'success',
            ]
        )

        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,
            exceptions=(ValueError, TypeError),
        )
        def test_func():
            return mock_func()

        result = test_func()

        assert result == 'success'
        assert mock_func.call_count == 3

    def test_default_parameters(self):
        call_count = [0]

        @retry_with_backoff()
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise RetryableTestError('Error')
            return 'success'

        result = test_func()

        assert result == 'success'
        assert call_count[0] == 2

    def test_function_with_arguments(self):
        mock_func = Mock(return_value='result')

        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        def test_func(a, b, c=None):
            return mock_func(a, b, c)

        result = test_func(1, 2, c=3)

        assert result == 'result'
        mock_func.assert_called_once_with(1, 2, 3)

    def test_preserves_function_metadata(self):
        @retry_with_backoff()
        def test_func():
            """Test docstring"""

        assert test_func.__name__ == 'test_func'
        assert test_func.__doc__ == 'Test docstring'

    def test_logging_on_retry(self):
        mock_func = Mock(side_effect=[Exception('Error'), 'success'])

        with patch(
            'createagents.infra.config.retry.LoggingConfig.get_logger'
        ) as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance

            @retry_with_backoff(max_attempts=3, initial_delay=0.01)
            def test_func():
                return mock_func()

            result = test_func()

            assert result == 'success'
            assert mock_log_instance.warning.call_count == 1

    def test_logging_on_final_failure(self):
        mock_func = Mock(side_effect=Exception('Persistent error'))

        with patch(
            'createagents.infra.config.retry.LoggingConfig.get_logger'
        ) as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance

            @retry_with_backoff(max_attempts=2, initial_delay=0.01)
            def test_func():
                return mock_func()

            with pytest.raises(Exception, match='Persistent error'):
                test_func()

            assert mock_log_instance.exception.call_count == 1

    def test_single_attempt(self):
        mock_func = Mock(side_effect=Exception('Error'))

        @retry_with_backoff(max_attempts=1, initial_delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(Exception, match='Error'):
            test_func()

        assert mock_func.call_count == 1

    def test_many_retries(self):
        call_count = [0]

        @retry_with_backoff(max_attempts=10, initial_delay=0.01)
        def test_func():
            call_count[0] += 1
            if call_count[0] < 10:
                raise RetryableTestError('Error')
            return 'success'

        result = test_func()

        assert result == 'success'
        assert call_count[0] == 10

    def test_exception_message_preserved(self):
        error_message = 'Specific error message'
        mock_func = Mock(side_effect=Exception(error_message))

        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(Exception, match=error_message):
            test_func()

    def test_different_exception_on_each_retry(self):
        exceptions = [
            ValueError('Error 1'),
            TypeError('Error 2'),
            KeyError('Error 3'),
        ]
        mock_func = Mock(side_effect=exceptions + ['success'])

        @retry_with_backoff(
            max_attempts=4,
            initial_delay=0.01,
            exceptions=(ValueError, TypeError, KeyError),
        )
        def test_func():
            return mock_func()

        result = test_func()

        assert result == 'success'
        assert mock_func.call_count == 4

    def test_nested_retry_decorators(self):
        call_count = [0]

        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise RetryableTestError('Error')
            return 'success'

        result = test_func()

        assert result == 'success'
        assert call_count[0] >= 2

    def test_return_value_types(self):
        test_cases = [
            42,
            'string',
            [1, 2, 3],
            {'key': 'value'},
            None,
            True,
        ]

        for expected_value in test_cases:
            mock_func = Mock(return_value=expected_value)

            @retry_with_backoff(max_attempts=2, initial_delay=0.01)
            def test_func(func=mock_func):
                return func()

            result = test_func()
            assert result == expected_value

    def test_callback_is_called_on_retry(self):
        callback_calls = []

        def on_retry_callback(attempt, exception):
            callback_calls.append((attempt, str(exception)))

        mock_func = Mock(
            side_effect=[Exception('Error 1'), Exception('Error 2'), 'success']
        )

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, on_retry=on_retry_callback
        )
        def test_func():
            return mock_func()

        result = test_func()

        assert result == 'success'
        assert len(callback_calls) == 2
        assert callback_calls[0] == (1, 'Error 1')
        assert callback_calls[1] == (2, 'Error 2')

    def test_callback_not_called_on_success(self):
        callback_calls = []

        def on_retry_callback(attempt, exception):
            callback_calls.append((attempt, str(exception)))

        mock_func = Mock(return_value='success')

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, on_retry=on_retry_callback
        )
        def test_func():
            return mock_func()

        result = test_func()

        assert result == 'success'
        assert len(callback_calls) == 0

    def test_callback_receives_correct_attempt_number(self):
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
                raise RetryableTestError('Error')
            return 'success'

        test_func()

        assert callback_data == [1, 2, 3]

    def test_callback_exception_does_not_break_retry(self):
        def failing_callback(attempt, exception):
            raise RuntimeError('Callback error')

        mock_func = Mock(side_effect=[Exception('Error'), 'success'])

        with patch(
            'createagents.infra.config.retry.LoggingConfig.get_logger'
        ) as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance

            @retry_with_backoff(
                max_attempts=3, initial_delay=0.01, on_retry=failing_callback
            )
            def test_func():
                return mock_func()

            result = test_func()

            assert result == 'success'
            assert mock_log_instance.warning.call_count >= 1

    def test_callback_with_none_does_not_error(self):
        mock_func = Mock(side_effect=[Exception('Error'), 'success'])

        @retry_with_backoff(max_attempts=3, initial_delay=0.01, on_retry=None)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == 'success'

    def test_callback_receives_exception_object(self):
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
                raise ValueError('First')
            elif len(received_exceptions) == 1:
                raise TypeError('Second')
            elif len(received_exceptions) == 2:
                raise KeyError('Third')
            return 'success'

        result = test_func()

        assert result == 'success'
        assert received_exceptions == ['ValueError', 'TypeError', 'KeyError']

    def test_jitter_and_callback_together(self):
        callback_calls = []

        def on_retry_callback(attempt, exception):
            callback_calls.append(attempt)

        attempts = []

        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.05,
            jitter=True,
            on_retry=on_retry_callback,
        )
        def test_func():
            attempts.append(len(attempts) + 1)
            if len(attempts) < 3:
                raise RetryableTestError(f'Error {len(attempts)}')
            return 'success'

        result = test_func()

        assert result == 'success'
        assert callback_calls == [1, 2]
        assert len(attempts) == 3

    def test_callback_can_access_exception_message(self):
        messages = []

        def on_retry_callback(attempt, exception):
            messages.append(str(exception))

        @retry_with_backoff(
            max_attempts=3, initial_delay=0.01, on_retry=on_retry_callback
        )
        def test_func():
            if len(messages) == 0:
                raise RetryableTestError('First error')
            elif len(messages) == 1:
                raise RetryableTestError('Second error')
            return 'success'

        result = test_func()

        assert result == 'success'
        assert messages == ['First error', 'Second error']

    def test_last_exception_raised_when_all_attempts_fail(self):
        attempt_count = [0]

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def test_func():
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise ValueError('First error')
            elif attempt_count[0] == 2:
                raise TypeError('Second error')
            else:
                raise KeyError('Third error')

        with pytest.raises(KeyError, match='Third error'):
            test_func()

        assert attempt_count[0] == 3

    def test_decorator_preserves_function_signature(self):
        @retry_with_backoff(max_attempts=2)
        def func_with_args(a, b, c=10, *args, **kwargs):
            """Test function"""
            return a + b + c

        assert func_with_args.__name__ == 'func_with_args'
        assert func_with_args.__doc__ == 'Test function'

        result = func_with_args(1, 2, c=3)
        assert result == 6

    def test_callback_with_multiple_exception_types(self):
        callback_data = []

        def tracking_callback(attempt, exception):
            callback_data.append(
                {
                    'attempt': attempt,
                    'type': type(exception).__name__,
                    'message': str(exception),
                }
            )

        attempt = [0]

        @retry_with_backoff(
            max_attempts=4, initial_delay=0.01, on_retry=tracking_callback
        )
        def test_func():
            attempt[0] += 1
            if attempt[0] == 1:
                raise ValueError('Value error')
            elif attempt[0] == 2:
                raise TypeError('Type error')
            elif attempt[0] == 3:
                raise KeyError('Key error')
            return 'success'

        result = test_func()

        assert result == 'success'
        assert len(callback_data) == 3
        assert callback_data[0]['type'] == 'ValueError'
        assert callback_data[1]['type'] == 'TypeError'
        assert callback_data[2]['type'] == 'KeyError'

    def test_exception_not_in_exceptions_tuple_fails_immediately(self):
        mock_func = Mock(side_effect=RuntimeError('Runtime error'))

        @retry_with_backoff(
            max_attempts=5,
            initial_delay=0.01,
            exceptions=(ValueError, TypeError),
        )
        def test_func():
            return mock_func()

        with pytest.raises(RuntimeError, match='Runtime error'):
            test_func()

        assert mock_func.call_count == 1

    @pytest.mark.parametrize('max_attempts', [0, -1])
    def test_non_positive_max_attempts_is_rejected(self, max_attempts):
        """A non-positive budget must fail loudly at decoration time.

        It used to skip the call and return None, so a bad
        `OLLAMA_MAX_RETRIES`/`OPENAI_MAX_RETRIES` value turned a typed
        response into None without ever touching the network.
        """
        with pytest.raises(ValueError, match='max_attempts must be >= 1'):
            retry_with_backoff(max_attempts=max_attempts, initial_delay=0.01)


@pytest.fixture
def recorded_sleeps(no_real_sleep):
    """Expose the recorded backoff delays to a test.

    Wall-clock assertions were flaky under load and could not distinguish
    a jittered delay from a plain one. Recording the requested delay proves
    the actual behaviour and runs instantly.
    """
    return no_real_sleep


def _delays(sleep_mock):
    return [call.args[0] for call in sleep_mock.call_args_list]


@pytest.mark.unit
class TestBackoffSchedule:
    """The delay sequence itself, measured deterministically."""

    @staticmethod
    def _always_failing(**decorator_kwargs):
        attempts = []

        @retry_with_backoff(**decorator_kwargs)
        def test_func():
            attempts.append(1)
            raise ConnectionError('boom')

        return test_func, attempts

    def test_delay_multiplies_by_the_backoff_factor(self, recorded_sleeps):
        func, _ = self._always_failing(
            max_attempts=4,
            initial_delay=1.0,
            backoff_factor=2.0,
            jitter=False,
            exceptions=(ConnectionError,),
        )

        with pytest.raises(ConnectionError):
            func()

        assert _delays(recorded_sleeps) == [1.0, 2.0, 4.0]

    def test_custom_backoff_factor_is_honoured(self, recorded_sleeps):
        func, _ = self._always_failing(
            max_attempts=3,
            initial_delay=0.1,
            backoff_factor=3.0,
            jitter=False,
            exceptions=(ConnectionError,),
        )

        with pytest.raises(ConnectionError):
            func()

        assert _delays(recorded_sleeps) == pytest.approx([0.1, 0.3])

    def test_no_sleep_happens_on_the_final_attempt(self, recorded_sleeps):
        func, attempts = self._always_failing(
            max_attempts=3,
            initial_delay=1.0,
            jitter=False,
            exceptions=(ConnectionError,),
        )

        with pytest.raises(ConnectionError):
            func()

        assert len(attempts) == 3
        assert len(_delays(recorded_sleeps)) == 2

    def test_zero_initial_delay_never_waits(self, recorded_sleeps):
        func, _ = self._always_failing(
            max_attempts=3,
            initial_delay=0.0,
            jitter=False,
            exceptions=(ConnectionError,),
        )

        with pytest.raises(ConnectionError):
            func()

        assert _delays(recorded_sleeps) == [0.0, 0.0]


@pytest.mark.unit
class TestJitter:
    """Jitter must be observable, not merely plausible."""

    @staticmethod
    def _run_once(recorded_sleeps, **decorator_kwargs):
        calls = []

        @retry_with_backoff(
            max_attempts=2,
            initial_delay=1.0,
            exceptions=(ConnectionError,),
            **decorator_kwargs,
        )
        def test_func():
            calls.append(1)
            if len(calls) < 2:
                raise ConnectionError('boom')
            return 'ok'

        assert test_func() == 'ok'
        return _delays(recorded_sleeps)

    def test_jitter_disabled_uses_the_exact_delay(self, recorded_sleeps):
        assert self._run_once(recorded_sleeps, jitter=False) == [1.0]

    def test_jitter_perturbs_the_delay(self, recorded_sleeps):
        with patch(
            'createagents.infra.config.retry.random.uniform', return_value=0.1
        ):
            delays = self._run_once(recorded_sleeps, jitter=True)

        # 1.0 * (1 + 0.1); without jitter this would be exactly 1.0.
        assert delays == pytest.approx([1.1])

    def test_jitter_is_on_by_default(self, recorded_sleeps):
        with patch(
            'createagents.infra.config.retry.random.uniform', return_value=-0.1
        ) as uniform:
            delays = self._run_once(recorded_sleeps)

        uniform.assert_called_once_with(-0.1, 0.1)
        assert delays == pytest.approx([0.9])

    def test_jitter_stays_within_ten_percent(self, recorded_sleeps):
        for factor in (-0.1, -0.05, 0.0, 0.05, 0.1):
            recorded_sleeps.reset_mock()
            with patch(
                'createagents.infra.config.retry.random.uniform',
                return_value=factor,
            ):
                delay = self._run_once(recorded_sleeps, jitter=True)[0]

            assert 0.9 <= delay <= 1.1


@pytest.fixture
def no_real_async_sleep():
    """Never block on the backoff delay in the async wrapper."""
    with patch(
        'createagents.infra.config.retry.asyncio.sleep',
        new_callable=AsyncMock,
    ) as sleep:
        yield sleep


@pytest.mark.unit
class TestAsyncRetryWithBackoff:
    """The decorator detects coroutine functions and awaits the retries."""

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self, no_real_async_sleep):
        calls = []

        @retry_with_backoff(max_attempts=3)
        async def test_func():
            calls.append(1)
            return 'success'

        assert await test_func() == 'success'
        assert len(calls) == 1
        no_real_async_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_retries_until_it_succeeds(self, no_real_async_sleep):
        attempts = []

        @retry_with_backoff(max_attempts=3, initial_delay=0.5, jitter=False)
        async def test_func():
            attempts.append(len(attempts) + 1)
            if len(attempts) < 3:
                raise ValueError('boom')
            return 'success'

        assert await test_func() == 'success'
        assert len(attempts) == 3
        assert _delays(no_real_async_sleep) == [0.5, 1.0]

    @pytest.mark.asyncio
    async def test_raises_the_last_exception_when_attempts_run_out(
        self, no_real_async_sleep
    ):
        @retry_with_backoff(max_attempts=2, jitter=False)
        async def test_func():
            raise ValueError('always fails')

        with pytest.raises(ValueError, match='always fails'):
            await test_func()

        assert no_real_async_sleep.call_count == 1

    @pytest.mark.asyncio
    async def test_does_not_retry_unlisted_exception(
        self, no_real_async_sleep
    ):
        attempts = []

        @retry_with_backoff(max_attempts=3, exceptions=(ValueError,))
        async def test_func():
            attempts.append(1)
            raise TypeError('not retried')

        with pytest.raises(TypeError, match='not retried'):
            await test_func()

        assert len(attempts) == 1
        no_real_async_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_retry_callback_receives_attempt_and_error(
        self, no_real_async_sleep
    ):
        seen = []

        @retry_with_backoff(
            max_attempts=3,
            jitter=False,
            on_retry=lambda attempt, exc: seen.append((attempt, str(exc))),
        )
        async def test_func():
            raise ValueError('boom')

        with pytest.raises(ValueError):
            await test_func()

        assert seen == [(1, 'boom'), (2, 'boom')]

    @pytest.mark.asyncio
    async def test_failing_callback_does_not_break_the_retry_loop(
        self, no_real_async_sleep
    ):
        def broken_callback(attempt, exc):
            raise RuntimeError('callback exploded')

        @retry_with_backoff(
            max_attempts=2, jitter=False, on_retry=broken_callback
        )
        async def test_func():
            raise ValueError('boom')

        with pytest.raises(ValueError, match='boom'):
            await test_func()

    @pytest.mark.asyncio
    async def test_jitter_keeps_the_delay_within_ten_percent(
        self, no_real_async_sleep
    ):
        @retry_with_backoff(max_attempts=2, initial_delay=1.0, jitter=True)
        async def test_func():
            raise ValueError('boom')

        with patch(
            'createagents.infra.config.retry.random.uniform', return_value=0.1
        ):
            with pytest.raises(ValueError):
                await test_func()

        assert _delays(no_real_async_sleep) == [pytest.approx(1.1)]

    @pytest.mark.asyncio
    async def test_zero_max_attempts_is_rejected(self, no_real_async_sleep):
        with pytest.raises(ValueError, match='max_attempts must be >= 1'):
            retry_with_backoff(max_attempts=0)
