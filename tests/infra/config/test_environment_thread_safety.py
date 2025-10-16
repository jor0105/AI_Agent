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

    def test_reload_thread_safety(self):
        """Testa que reload() é thread-safe."""
        os.environ["RELOAD_VAR"] = "initial"
        EnvironmentConfig.get_env("RELOAD_VAR")

        results = []
        errors = []
        lock = threading.Lock()

        def reload_config():
            try:
                EnvironmentConfig.reload()
                with lock:
                    results.append("success")
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(reload_config) for _ in range(50)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(results) == 50
        del os.environ["RELOAD_VAR"]

    def test_concurrent_reload_and_get(self):
        """Testa reload e get concorrentes."""
        os.environ["CONCURRENT_VAR"] = "value"

        results = []
        errors = []
        lock = threading.Lock()

        def reload_action():
            try:
                EnvironmentConfig.reload()
                with lock:
                    results.append("reload")
            except Exception as e:
                with lock:
                    errors.append(str(e))

        def get_action():
            try:
                value = EnvironmentConfig.get_env("CONCURRENT_VAR")
                with lock:
                    results.append(f"get:{value}")
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            reload_futures = [executor.submit(reload_action) for _ in range(10)]
            get_futures = [executor.submit(get_action) for _ in range(30)]
            concurrent.futures.wait(reload_futures + get_futures)

        assert len(errors) == 0
        assert len(results) == 40
        del os.environ["CONCURRENT_VAR"]

    def test_get_api_key_with_empty_value_thread_safe(self):
        """Testa que validação de vazio é thread-safe."""
        os.environ["EMPTY_API_KEY"] = ""

        results = []
        errors = []
        lock = threading.Lock()

        def get_empty_key():
            try:
                key = EnvironmentConfig.get_api_key("EMPTY_API_KEY")
                with lock:
                    results.append(key)
            except EnvironmentError:
                with lock:
                    errors.append("expected_error")
            except Exception as e:
                with lock:
                    errors.append(f"unexpected:{str(e)}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_empty_key) for _ in range(20)]
            concurrent.futures.wait(futures)

        # Todos devem ter lançado EnvironmentError
        assert len(results) == 0
        assert len(errors) == 20
        assert all(e == "expected_error" for e in errors)
        del os.environ["EMPTY_API_KEY"]

    def test_get_api_key_strips_whitespace_thread_safe(self):
        """Testa que strip é thread-safe."""
        os.environ["WHITESPACE_API"] = "  spaced_value  "

        results = []
        lock = threading.Lock()

        def get_stripped():
            key = EnvironmentConfig.get_api_key("WHITESPACE_API")
            with lock:
                results.append(key)

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(get_stripped) for _ in range(30)]
            concurrent.futures.wait(futures)

        # Todos devem ter o valor sem espaços
        assert all(r == "spaced_value" for r in results)
        assert len(results) == 30
        del os.environ["WHITESPACE_API"]

    def test_get_env_does_not_cache_empty_thread_safe(self):
        """Testa que valores vazios não são cacheados em ambiente concorrente."""
        os.environ["EMPTY_ENV_VAR"] = ""

        results = []
        lock = threading.Lock()

        def get_empty_env():
            value = EnvironmentConfig.get_env("EMPTY_ENV_VAR", "default")
            with lock:
                results.append(value)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_empty_env) for _ in range(20)]
            concurrent.futures.wait(futures)

        # Todos devem retornar default
        assert all(r == "default" for r in results)
        # Cache não deve conter a chave vazia
        assert "EMPTY_ENV_VAR" not in EnvironmentConfig._cache
        del os.environ["EMPTY_ENV_VAR"]

    def test_concurrent_cache_operations(self):
        """Testa operações concorrentes de cache."""
        os.environ["CACHE_OP_VAR"] = "test"

        operations = []
        lock = threading.Lock()

        def read_cache():
            value = EnvironmentConfig.get_env("CACHE_OP_VAR")
            with lock:
                operations.append(("read", value))

        def clear_cache():
            EnvironmentConfig.clear_cache()
            with lock:
                operations.append(("clear", None))

        def reload_config():
            EnvironmentConfig.reload()
            with lock:
                operations.append(("reload", None))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            read_futures = [executor.submit(read_cache) for _ in range(30)]
            clear_futures = [executor.submit(clear_cache) for _ in range(5)]
            reload_futures = [executor.submit(reload_config) for _ in range(5)]

            all_futures = read_futures + clear_futures + reload_futures
            concurrent.futures.wait(all_futures)

        # Deve ter executado todas as operações sem erro
        assert len(operations) == 40
        del os.environ["CACHE_OP_VAR"]

    def test_massive_concurrent_access(self):
        """Teste de stress com muitas threads."""
        os.environ["STRESS_VAR"] = "stress_value"

        results = []
        errors = []
        lock = threading.Lock()

        def access_env():
            try:
                value = EnvironmentConfig.get_env("STRESS_VAR")
                with lock:
                    results.append(value)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        # 100 threads fazendo 1000 acessos
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(access_env) for _ in range(1000)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert all(r == "stress_value" for r in results)
        assert len(results) == 1000
        del os.environ["STRESS_VAR"]
