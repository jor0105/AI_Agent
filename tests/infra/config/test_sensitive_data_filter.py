import concurrent.futures
import threading

from createagents.infra import SensitiveDataFilter


class TestSensitiveDataFilter:
    def setup_method(self):
        SensitiveDataFilter.clear_cache()

    def test_filter_api_key(self):
        text = 'API_KEY=sk-1234567890abcdef'
        result = SensitiveDataFilter.filter(text)
        assert 'sk-1234567890abcdef' not in result
        assert '[API_KEY_REDACTED]' in result

    def test_filter_bearer_token(self):
        text = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
        result = SensitiveDataFilter.filter(text)
        assert 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' not in result
        assert (
            '[BEARER_TOKEN_REDACTED]' in result
            or '[JWT_TOKEN_REDACTED]' in result
        )

    def test_filter_jwt_token(self):
        text = (
            'Token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature'
        )
        result = SensitiveDataFilter.filter(text)
        assert 'eyJhbGciOiJIUzI1NiJ9' not in result
        assert '[JWT_TOKEN_REDACTED]' in result

    def test_filter_password(self):
        test_cases = [
            'password=mysecret123',
            'senha: secret456',
            'pwd="mypass789"',
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert '[PASSWORD_REDACTED]' in result
            assert 'mysecret' not in result
            assert 'secret456' not in result
            assert 'mypass789' not in result

    def test_filter_secret(self):
        text = 'secret_key=abcd1234efgh5678'
        result = SensitiveDataFilter.filter(text)
        assert 'abcd1234efgh5678' not in result
        assert '[SECRET_REDACTED]' in result

    def test_filter_email(self):
        text = 'Contato: usuario@example.com'
        result = SensitiveDataFilter.filter(text)
        assert 'usuario@example.com' not in result
        assert '[EMAIL_REDACTED]' in result

    def test_filter_cpf(self):
        test_cases = [
            'CPF: 123.456.789-00',
            'CPF: 12345678900',
            'CPF 123.456.789-00',
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert '123.456.789-00' not in result
            assert '12345678900' not in result
            assert '[CPF_REDACTED]' in result

    def test_filter_cnpj(self):
        test_cases = [
            'CNPJ: 12.345.678/0001-90',
            'CNPJ: 12345678000190',
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert '[CNPJ_REDACTED]' in result

    def test_filter_phone_br(self):
        test_cases = [
            ('Tel: (11) 98765-4321', '98765-4321'),
            ('Tel: 11987654321', '987654321'),
            ('Tel: +55 11 98765-4321', '98765'),
            ('Tel: +55 11 9 8765-4321', '8765'),
        ]
        for text, sensitive_part in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert (
                '[PHONE_BR_REDACTED]' in result
                or '[CPF_REDACTED]' in result
                or sensitive_part not in result
            ), f'Falhou para: {text}'

    def test_filter_credit_card(self):
        test_cases = [
            'Card: 4532-1234-5678-9010',
            'Card: 4532 1234 5678 9010',
            'Card: 4532123456789010',
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert '[CREDIT_CARD_REDACTED]' in result
            assert '4532' not in result or result.count('4532') < len(
                test_cases
            )

    def test_filter_cvv(self):
        text = 'CVV: 123'
        result = SensitiveDataFilter.filter(text)
        assert '[CVV_REDACTED]' in result
        assert '123' not in result or 'CVV' in result

    def test_filter_ipv4_private(self):
        test_cases = [
            'Server: 192.168.1.1',
            'Host: 10.0.0.1',
            'Localhost: 127.0.0.1',
            'Internal: 172.16.0.1',
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert '[IPV4_REDACTED]' in result

    def test_filter_url_with_credentials(self):
        text = 'DB: https://user:password123@database.example.com'
        result = SensitiveDataFilter.filter(text)
        assert 'password123' not in result
        assert (
            '[CREDENTIALS_REDACTED]' in result
            or '[PASSWORD_REDACTED]' in result
        )

    def test_filter_auth_header(self):
        text = 'Authorization: Basic dXNlcjpwYXNzd29yZA=='
        result = SensitiveDataFilter.filter(text)
        assert 'dXNlcjpwYXNzd29yZA==' not in result
        assert '[TOKEN_REDACTED]' in result

    def test_filter_multiple_sensitive_data(self):
        text = """
        User: user@example.com
        Password: mysecret123
        API_KEY: sk-proj-abc123def456ghi789jkl012mno345
        CPF: 123.456.789-00
        Card: 4532-1234-5678-9010
        """
        result = SensitiveDataFilter.filter(text)

        assert 'user@example.com' not in result
        assert 'mysecret123' not in result
        assert 'sk-proj-abc123def456ghi789jkl012mno345' not in result
        assert '123.456.789-00' not in result
        assert '4532-1234-5678-9010' not in result

        assert '[EMAIL_REDACTED]' in result
        assert '[PASSWORD_REDACTED]' in result
        assert '[API_KEY_REDACTED]' in result
        assert '[CPF_REDACTED]' in result
        assert '[CREDIT_CARD_REDACTED]' in result

    def test_filter_empty_string(self):
        result = SensitiveDataFilter.filter('')
        assert result == ''

    def test_filter_none(self):
        result = SensitiveDataFilter.filter(None)
        assert result is None

    def test_filter_normal_text(self):
        text = 'Esta é uma mensagem normal sem dados sensíveis'
        result = SensitiveDataFilter.filter(text)
        assert result == text

    def test_mask_partial(self):
        text = 'sk-1234567890abcdef'
        result = SensitiveDataFilter.mask_partial(text, 4)
        assert result.endswith('cdef')
        assert result.startswith('*')
        assert '1234567890ab' not in result

    def test_mask_partial_short_text(self):
        text = 'abc'
        result = SensitiveDataFilter.mask_partial(text, 4)
        assert result == '***'

    def test_is_sensitive_true(self):
        test_cases = [
            'password=secret',
            'email: user@test.com',
            'CPF: 123.456.789-00',
            'API_KEY=abcdef123456789',
        ]
        for text in test_cases:
            assert SensitiveDataFilter.is_sensitive(text), (
                f'Deveria detectar: {text}'
            )

    def test_is_sensitive_false(self):
        text = 'Esta é uma mensagem normal'
        assert not SensitiveDataFilter.is_sensitive(text)

    def test_is_sensitive_empty(self):
        assert not SensitiveDataFilter.is_sensitive('')

    def test_cache_functionality(self):
        text = 'password=secret123'
        result1 = SensitiveDataFilter.filter(text)
        result2 = SensitiveDataFilter.filter(text)
        assert result1 == result2
        assert '[PASSWORD_REDACTED]' in result1

    def test_clear_cache_old_method(self):
        text = 'password=secret123'
        SensitiveDataFilter.filter(text)
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize > 0
        SensitiveDataFilter.clear_cache()
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize == 0

    def test_filter_preserves_context(self):
        text = 'Usuário informou password=secret123 no formulário'
        result = SensitiveDataFilter.filter(text)
        assert 'Usuário informou' in result
        assert 'no formulário' in result
        assert '[PASSWORD_REDACTED]' in result
        assert 'secret123' not in result

    def test_filter_rg(self):
        test_cases = [
            'RG: 12.345.678-9',
            'RG: 12.345.678-X',
            'RG: 123456789',
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert '[RG_REDACTED]' in result

    def test_lru_cache_is_used(self):
        assert hasattr(SensitiveDataFilter._filter_cached, 'cache_info')
        SensitiveDataFilter.clear_cache()
        text = 'password=secret123'
        SensitiveDataFilter.filter(text)
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.hits >= 0
        assert cache_info.misses >= 1
        SensitiveDataFilter.filter(text)
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.hits >= 1

    def test_lru_cache_maxsize_constant(self):
        assert SensitiveDataFilter.DEFAULT_CACHE_SIZE == 1000
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.maxsize == SensitiveDataFilter.DEFAULT_CACHE_SIZE

    def test_lru_cache_evicts_old_entries(self):
        SensitiveDataFilter.clear_cache()
        for i in range(1100):
            SensitiveDataFilter.filter(f'password=secret{i}')
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize <= SensitiveDataFilter.DEFAULT_CACHE_SIZE

    def test_default_visible_chars_constant(self):
        assert SensitiveDataFilter.DEFAULT_VISIBLE_CHARS == 4

    def test_mask_partial_uses_default_visible_chars(self):
        text = 'sk-1234567890abcdef'
        result = SensitiveDataFilter.mask_partial(text)
        assert result.endswith('cdef')
        assert (
            len(result.replace('*', ''))
            == SensitiveDataFilter.DEFAULT_VISIBLE_CHARS
        )

    def test_mask_partial_with_custom_visible_chars(self):
        text = 'sk-1234567890abcdef'
        result = SensitiveDataFilter.mask_partial(text, 6)
        assert result.endswith('abcdef')
        assert len(result.replace('*', '')) == 6

    def test_clear_cache_clears_lru_cache(self):
        for i in range(10):
            SensitiveDataFilter.filter(f'password=secret{i}')
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize > 0
        SensitiveDataFilter.clear_cache()
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize == 0
        assert cache_info.hits == 0
        assert cache_info.misses == 0

    def test_lru_cache_thread_safe(self):
        SensitiveDataFilter.clear_cache()
        results = []
        errors = []
        lock = threading.Lock()

        def filter_text(i):
            try:
                result = SensitiveDataFilter.filter(f'password=secret{i % 10}')
                with lock:
                    results.append(result)
            # Capture worker failures for the assertion after all futures finish.
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(filter_text, i) for i in range(100)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(results) == 100
        assert all('[PASSWORD_REDACTED]' in r for r in results)

    def test_patterns_order_is_documented(self):
        docstring = SensitiveDataFilter.__doc__
        assert 'ordem' in docstring.lower() or 'order' in docstring.lower()
        assert 'JWT' in docstring
        assert 'API' in docstring

    def test_filter_performance_with_cache(self):
        import time

        text = 'password=secret123 email=user@test.com'
        SensitiveDataFilter.clear_cache()
        start = time.time()
        for _ in range(100):
            SensitiveDataFilter.filter(text)
        time_without_cache_benefit = time.time() - start
        start = time.time()
        for _ in range(100):
            SensitiveDataFilter.filter(text)
        time_with_cache = time.time() - start
        assert time_with_cache <= time_without_cache_benefit * 1.5

    def test_cache_handles_different_inputs(self):
        inputs = [
            'password=secret1',
            'password=secret2',
            'email=test@test.com',
            'CPF: 123.456.789-00',
            'normal text',
        ]
        SensitiveDataFilter.clear_cache()
        results = {}
        for inp in inputs:
            results[inp] = SensitiveDataFilter.filter(inp)
        for inp in inputs:
            result = SensitiveDataFilter.filter(inp)
            assert result == results[inp]
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.hits >= len(inputs)

    def test_constants_are_class_level(self):
        assert hasattr(SensitiveDataFilter, 'DEFAULT_CACHE_SIZE')
        assert hasattr(SensitiveDataFilter, 'DEFAULT_VISIBLE_CHARS')
        assert isinstance(SensitiveDataFilter.DEFAULT_CACHE_SIZE, int)
        assert isinstance(SensitiveDataFilter.DEFAULT_VISIBLE_CHARS, int)
        assert SensitiveDataFilter.DEFAULT_CACHE_SIZE > 0
        assert SensitiveDataFilter.DEFAULT_VISIBLE_CHARS > 0

    def test_filter_cached_is_internal_method(self):
        assert SensitiveDataFilter._filter_cached.__name__.startswith('_')
        SensitiveDataFilter.clear_cache()
        text = 'password=test123'
        SensitiveDataFilter.filter(text)
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize > 0

    def test_lru_cache_info_accessible(self):
        SensitiveDataFilter.clear_cache()
        for i in range(5):
            SensitiveDataFilter.filter(f'test{i}')
        info = SensitiveDataFilter._filter_cached.cache_info()
        assert hasattr(info, 'hits')
        assert hasattr(info, 'misses')
        assert hasattr(info, 'maxsize')
        assert hasattr(info, 'currsize')
        assert info.maxsize == 1000
        assert info.currsize == 5
        assert info.misses == 5
        assert info.hits == 0

    def test_concurrent_access_with_cache(self):
        SensitiveDataFilter.clear_cache()
        text = 'password=shared_secret'
        results = []
        lock = threading.Lock()

        def filter_concurrent():
            result = SensitiveDataFilter.filter(text)
            with lock:
                results.append(result)

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(filter_concurrent) for _ in range(100)]
            concurrent.futures.wait(futures)

        assert len(results) == 100
        assert len(set(results)) == 1
        assert '[PASSWORD_REDACTED]' in results[0]
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.hits > 90

    def test_filter_multiple_patterns_in_same_text(self):
        text = 'User: user@test.com, Password: secret123, API_KEY: sk-abc123def456, CPF: 123.456.789-00'
        result = SensitiveDataFilter.filter(text)
        assert 'user@test.com' not in result
        assert 'secret123' not in result
        assert 'sk-abc123def456' not in result
        assert '123.456.789-00' not in result
        assert '[EMAIL_REDACTED]' in result
        assert '[PASSWORD_REDACTED]' in result
        assert '[API_KEY_REDACTED]' in result
        assert '[CPF_REDACTED]' in result

    def test_is_sensitive_with_multiple_patterns(self):
        sensitive_texts = [
            'password=test',
            'user@example.com',
            'API_KEY=abc123def',
            '123.456.789-00',
            'Bearer token123',
        ]
        for text in sensitive_texts:
            assert SensitiveDataFilter.is_sensitive(text), (
                f'Should detect: {text}'
            )

    def test_mask_partial_with_zero_visible_chars(self):
        text = 'secretvalue'
        result = SensitiveDataFilter.mask_partial(text, 0)
        assert result == '*' * len(text)
        assert 'secretvalue' not in result

    def test_mask_partial_with_exact_length(self):
        text = 'test'
        result = SensitiveDataFilter.mask_partial(text, 4)
        assert result == '****'

    def test_filter_with_newlines_and_special_chars(self):
        text = """
        User info:
        Email: admin@company.com
        Password: P@ssw0rd!2024

        API Credentials:
        api_key: sk_live_abc123def456ghi789
        """
        result = SensitiveDataFilter.filter(text)
        assert 'admin@company.com' not in result
        assert '[EMAIL_REDACTED]' in result
        assert 'sk_live_abc123def456ghi789' not in result
        assert '[API_KEY_REDACTED]' in result or 'REDACTED' in result
        assert 'User info:' in result
        assert 'API Credentials:' in result

    def test_patterns_dict_is_class_attribute(self):
        assert hasattr(SensitiveDataFilter, '_PATTERNS')
        assert isinstance(SensitiveDataFilter._PATTERNS, dict)
        assert len(SensitiveDataFilter._PATTERNS) > 0

    def test_all_pattern_keys_are_descriptive(self):
        pattern_keys = SensitiveDataFilter._PATTERNS.keys()
        expected_keys = [
            'jwt_token',
            'api_key',
            'bearer_token',
            'secret',
            'password',
            'email',
            'cpf',
            'credit_card',
            'cvv',
        ]
        for key in expected_keys:
            assert key in pattern_keys, f"Pattern '{key}' should be defined"

    def test_filter_preserves_non_sensitive_urls(self):
        text = 'Visit https://example.com or http://test.com'
        result = SensitiveDataFilter.filter(text)
        assert 'https://example.com' in result
        assert 'http://test.com' in result

    def test_filter_case_sensitivity(self):
        test_cases = [
            ('password=secretvalue', 'PASSWORD=secretvalue'),
            ('api_key=test123456', 'API_KEY=test123456'),
            ('Bearer token123456', 'BEARER token123456'),
        ]
        for lower, upper in test_cases:
            result_lower = SensitiveDataFilter.filter(lower)
            result_upper = SensitiveDataFilter.filter(upper)
            assert (
                'REDACTED' in result_lower or 'secretvalue' not in result_lower
            )
            assert (
                'REDACTED' in result_upper or 'secretvalue' not in result_upper
            )

    def test_cache_info_after_clear(self):
        for i in range(10):
            SensitiveDataFilter.filter(f'password=test{i}')
        SensitiveDataFilter.clear_cache()
        info = SensitiveDataFilter._filter_cached.cache_info()
        assert info.currsize == 0
        assert info.hits == 0
        assert info.misses == 0

    def test_filter_with_very_long_text(self):
        sensitive_parts = [
            'password=secret123',
            'email@test.com',
            'API_KEY=sk-abc123',
        ]
        long_text = 'Normal text. ' * 1000
        for i, sensitive in enumerate(sensitive_parts):
            insert_pos = i * 300
            long_text = (
                long_text[:insert_pos] + sensitive + long_text[insert_pos:]
            )
        result = SensitiveDataFilter.filter(long_text)
        assert 'secret123' not in result
        assert 'email@test.com' not in result
        assert 'sk-abc123' not in result
        assert 'Normal text.' in result

    def test_is_sensitive_returns_false_for_none(self):
        result = SensitiveDataFilter.is_sensitive(None)
        assert result is False

    def test_mask_partial_with_negative_visible_chars(self):
        text = 'secretvalue'
        result = SensitiveDataFilter.mask_partial(text, -1)
        assert result == '*' * len(text)
        assert 'secretvalue' not in result

    def test_filter_preserves_formatting(self):
        text = '  Indented text with password=secret123  '
        result = SensitiveDataFilter.filter(text)
        assert result.startswith('  ')
        assert result.endswith('  ')
        assert 'Indented text' in result
