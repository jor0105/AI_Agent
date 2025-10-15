import concurrent.futures
import os
import threading

import pytest

from src.infra.config.environment import EnvironmentConfig


@pytest.mark.unit
class TestEnvironmentConfigThreadSafety:
    """Testes para thread-safety do Singleton."""

    def setup_method(self):
        EnvironmentConfig.reset()
        os.environ["TEST_VAR"] = "test_value"

    def teardown_method(self):
        EnvironmentConfig.reset()
        if "TEST_VAR" in os.environ:
            del os.environ["TEST_VAR"]

    def test_singleton_is_thread_safe(self):
        instances = []
        lock = threading.Lock()

        def create_instance():
            config = EnvironmentConfig()
            with lock:
                instances.append(config)

        threads = [threading.Thread(target=create_instance) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(set(id(inst) for inst in instances)) == 1

    def test_concurrent_get_env_is_safe(self):
        results = []
        lock = threading.Lock()

        def get_value():
            value = EnvironmentConfig.get_env("TEST_VAR")
            with lock:
                results.append(value)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_value) for _ in range(50)]
            concurrent.futures.wait(futures)

        assert all(v == "test_value" for v in results)
        assert len(results) == 50

    def test_cache_is_consistent_across_threads(self):
        EnvironmentConfig.get_env("TEST_VAR")

        results = []
        lock = threading.Lock()

        def get_cached_value():
            value = EnvironmentConfig.get_env("TEST_VAR")
            with lock:
                results.append(value)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_cached_value) for _ in range(30)]
            concurrent.futures.wait(futures)

        assert all(v == "test_value" for v in results)

    def test_get_api_key_is_thread_safe(self):
        os.environ["API_KEY_TEST"] = "secret123"

        results = []
        lock = threading.Lock()

        def get_key():
            try:
                key = EnvironmentConfig.get_api_key("API_KEY_TEST")
                with lock:
                    results.append(key)
            except Exception as e:
                with lock:
                    results.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(get_key) for _ in range(40)]
            concurrent.futures.wait(futures)

        assert all(r == "secret123" for r in results)

        del os.environ["API_KEY_TEST"]


@pytest.mark.unit
class TestEnvironmentConfigNewFeatures:
    def setup_method(self):
        EnvironmentConfig.reset()

    def teardown_method(self):
        EnvironmentConfig.reset()

    def test_get_env_with_default_value(self):
        value = EnvironmentConfig.get_env("NONEXISTENT_VAR", "default_value")
        assert value == "default_value"

    def test_get_env_returns_actual_value_when_exists(self):
        os.environ["EXISTING_VAR"] = "real_value"
        value = EnvironmentConfig.get_env("EXISTING_VAR", "default_value")
        assert value == "real_value"
        del os.environ["EXISTING_VAR"]

    def test_get_env_caches_value(self):
        os.environ["CACHE_TEST"] = "value1"

        value1 = EnvironmentConfig.get_env("CACHE_TEST")
        assert value1 == "value1"

        os.environ["CACHE_TEST"] = "value2"

        value2 = EnvironmentConfig.get_env("CACHE_TEST")
        assert value2 == "value1"  # Cache retorna valor antigo

        del os.environ["CACHE_TEST"]

    def test_clear_cache_works(self):
        os.environ["CLEAR_TEST"] = "value1"

        value1 = EnvironmentConfig.get_env("CLEAR_TEST")
        assert value1 == "value1"

        os.environ["CLEAR_TEST"] = "value2"
        EnvironmentConfig.clear_cache()

        value2 = EnvironmentConfig.get_env("CLEAR_TEST")
        assert value2 == "value2"

        del os.environ["CLEAR_TEST"]
