import pytest

from createagents.domain.interfaces.logger_interface import LoggerInterface


@pytest.mark.unit
class TestLoggerInterface:
    def test_scenario_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            LoggerInterface()

    def test_scenario_concrete_implementation_must_implement_all_methods(
        self,
    ):
        class IncompleteLogger(LoggerInterface):
            def debug(self, message: str, *args, **kwargs) -> None:
                pass

        with pytest.raises(TypeError):
            IncompleteLogger()

    def test_scenario_concrete_implementation_with_all_methods(self):
        class CompleteLogger(LoggerInterface):
            def debug(self, message: str, *args, **kwargs) -> None:
                pass

            def info(self, message: str, *args, **kwargs) -> None:
                pass

            def warning(self, message: str, *args, **kwargs) -> None:
                pass

            def error(self, message: str, *args, **kwargs) -> None:
                pass

            def critical(self, message: str, *args, **kwargs) -> None:
                pass

        logger = CompleteLogger()
        assert isinstance(logger, LoggerInterface)

    def test_scenario_debug_method_signature(self):
        class TestLogger(LoggerInterface):
            def __init__(self):
                self.logs = []

            def debug(self, message: str, *args, **kwargs) -> None:
                self.logs.append(('debug', message, args, kwargs))

            def info(self, message: str, *args, **kwargs) -> None:
                pass

            def warning(self, message: str, *args, **kwargs) -> None:
                pass

            def error(self, message: str, *args, **kwargs) -> None:
                pass

            def critical(self, message: str, *args, **kwargs) -> None:
                pass

        logger = TestLogger()
        logger.debug('test message', 'arg1', key='value')
        assert logger.logs[0] == (
            'debug',
            'test message',
            ('arg1',),
            {'key': 'value'},
        )

    def test_scenario_info_method_signature(self):
        class TestLogger(LoggerInterface):
            def __init__(self):
                self.logs = []

            def debug(self, message: str, *args, **kwargs) -> None:
                pass

            def info(self, message: str, *args, **kwargs) -> None:
                self.logs.append(('info', message, args, kwargs))

            def warning(self, message: str, *args, **kwargs) -> None:
                pass

            def error(self, message: str, *args, **kwargs) -> None:
                pass

            def critical(self, message: str, *args, **kwargs) -> None:
                pass

        logger = TestLogger()
        logger.info('info message', 'arg1', key='value')
        assert logger.logs[0] == (
            'info',
            'info message',
            ('arg1',),
            {'key': 'value'},
        )

    def test_scenario_warning_method_signature(self):
        class TestLogger(LoggerInterface):
            def __init__(self):
                self.logs = []

            def debug(self, message: str, *args, **kwargs) -> None:
                pass

            def info(self, message: str, *args, **kwargs) -> None:
                pass

            def warning(self, message: str, *args, **kwargs) -> None:
                self.logs.append(('warning', message, args, kwargs))

            def error(self, message: str, *args, **kwargs) -> None:
                pass

            def critical(self, message: str, *args, **kwargs) -> None:
                pass

        logger = TestLogger()
        logger.warning('warning message', 'arg1', key='value')
        assert logger.logs[0] == (
            'warning',
            'warning message',
            ('arg1',),
            {'key': 'value'},
        )

    def test_scenario_error_method_signature(self):
        class TestLogger(LoggerInterface):
            def __init__(self):
                self.logs = []

            def debug(self, message: str, *args, **kwargs) -> None:
                pass

            def info(self, message: str, *args, **kwargs) -> None:
                pass

            def warning(self, message: str, *args, **kwargs) -> None:
                pass

            def error(self, message: str, *args, **kwargs) -> None:
                self.logs.append(('error', message, args, kwargs))

            def critical(self, message: str, *args, **kwargs) -> None:
                pass

        logger = TestLogger()
        logger.error('error message', 'arg1', key='value')
        assert logger.logs[0] == (
            'error',
            'error message',
            ('arg1',),
            {'key': 'value'},
        )

    def test_scenario_critical_method_signature(self):
        class TestLogger(LoggerInterface):
            def __init__(self):
                self.logs = []

            def debug(self, message: str, *args, **kwargs) -> None:
                pass

            def info(self, message: str, *args, **kwargs) -> None:
                pass

            def warning(self, message: str, *args, **kwargs) -> None:
                pass

            def error(self, message: str, *args, **kwargs) -> None:
                pass

            def critical(self, message: str, *args, **kwargs) -> None:
                self.logs.append(('critical', message, args, kwargs))

        logger = TestLogger()
        logger.critical('critical message', 'arg1', key='value')
        assert logger.logs[0] == (
            'critical',
            'critical message',
            ('arg1',),
            {'key': 'value'},
        )
