import logging
from unittest.mock import Mock, patch

import pytest

from createagents.domain.interfaces.logger_interface import LoggerInterface
from createagents.infra.config.standard_logger import (
    StandardLogger,
    create_logger,
)


@pytest.mark.unit
class TestStandardLogger:
    def test_scenario_initialization_success(self):
        python_logger = logging.getLogger('test')
        logger = StandardLogger(python_logger)

        assert isinstance(logger, LoggerInterface)
        assert logger._logger == python_logger

    def test_scenario_debug_delegates_to_python_logger(self):
        python_logger = Mock(spec=logging.Logger)
        logger = StandardLogger(python_logger)

        logger.debug('test message', 'arg1', key='value')

        python_logger.debug.assert_called_once_with(
            'test message', 'arg1', key='value'
        )

    def test_scenario_info_delegates_to_python_logger(self):
        python_logger = Mock(spec=logging.Logger)
        logger = StandardLogger(python_logger)

        logger.info('info message', 'arg1', key='value')

        python_logger.info.assert_called_once_with(
            'info message', 'arg1', key='value'
        )

    def test_scenario_warning_delegates_to_python_logger(self):
        python_logger = Mock(spec=logging.Logger)
        logger = StandardLogger(python_logger)

        logger.warning('warning message', 'arg1', key='value')

        python_logger.warning.assert_called_once_with(
            'warning message', 'arg1', key='value'
        )

    def test_scenario_error_delegates_to_python_logger(self):
        python_logger = Mock(spec=logging.Logger)
        logger = StandardLogger(python_logger)

        logger.error('error message', 'arg1', key='value')

        python_logger.error.assert_called_once_with(
            'error message', 'arg1', key='value'
        )

    def test_scenario_critical_delegates_to_python_logger(self):
        python_logger = Mock(spec=logging.Logger)
        logger = StandardLogger(python_logger)

        logger.critical('critical message', 'arg1', key='value')

        python_logger.critical.assert_called_once_with(
            'critical message', 'arg1', key='value'
        )

    def test_scenario_implements_logger_interface(self):
        python_logger = logging.getLogger('test2')
        logger = StandardLogger(python_logger)

        assert isinstance(logger, LoggerInterface)
        assert callable(logger.debug)
        assert callable(logger.info)
        assert callable(logger.warning)
        assert callable(logger.error)
        assert callable(logger.critical)

    @patch('createagents.infra.config.standard_logger.LoggingConfig')
    def test_scenario_create_logger_factory(self, mock_logging_config):
        mock_python_logger = Mock(spec=logging.Logger)
        mock_logging_config.get_logger.return_value = mock_python_logger

        logger = create_logger('test.module')

        assert isinstance(logger, StandardLogger)
        assert isinstance(logger, LoggerInterface)
        mock_logging_config.get_logger.assert_called_once_with('test.module')

    def test_scenario_logger_with_exception_info(self):
        python_logger = Mock(spec=logging.Logger)
        logger = StandardLogger(python_logger)

        try:
            raise ValueError('test exception')
        except ValueError:
            logger.exception('Error occurred')

        python_logger.error.assert_called_once()
        call_args = python_logger.error.call_args
        assert call_args[0][0] == 'Error occurred'
        assert call_args[1]['exc_info'] is True

    def test_scenario_exception_preserves_explicit_exc_info(self):
        python_logger = Mock(spec=logging.Logger)
        logger = StandardLogger(python_logger)

        try:
            raise ValueError('test exception')
        except ValueError:
            LoggerInterface.exception(logger, 'Error occurred', exc_info=False)

        python_logger.error.assert_called_once_with(
            'Error occurred', exc_info=False
        )
