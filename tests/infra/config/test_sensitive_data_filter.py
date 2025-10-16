import concurrent.futures
import threading

from src.infra.config.sensitive_data_filter import SensitiveDataFilter


class TestSensitiveDataFilter:
    """Testes para filtragem de dados sensíveis."""

    def setup_method(self):
        """Limpa o cache antes de cada teste."""
        SensitiveDataFilter.clear_cache()

    def test_filter_api_key(self):
        """Testa filtragem de API keys."""
        text = "API_KEY=sk-1234567890abcdef"
        result = SensitiveDataFilter.filter(text)
        assert "sk-1234567890abcdef" not in result
        assert "[API_KEY_REDACTED]" in result

    def test_filter_bearer_token(self):
        """Testa filtragem de Bearer tokens."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = SensitiveDataFilter.filter(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "[BEARER_TOKEN_REDACTED]" in result or "[JWT_TOKEN_REDACTED]" in result

    def test_filter_jwt_token(self):
        """Testa filtragem de JWT tokens."""
        text = "Token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
        result = SensitiveDataFilter.filter(text)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        assert "[JWT_TOKEN_REDACTED]" in result

    def test_filter_password(self):
        """Testa filtragem de senhas."""
        test_cases = [
            "password=mysecret123",
            "senha: secret456",
            'pwd="mypass789"',
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert "[PASSWORD_REDACTED]" in result
            assert "mysecret" not in result
            assert "secret456" not in result
            assert "mypass789" not in result

    def test_filter_secret(self):
        """Testa filtragem de secrets."""
        text = "secret_key=abcd1234efgh5678"
        result = SensitiveDataFilter.filter(text)
        assert "abcd1234efgh5678" not in result
        assert "[SECRET_REDACTED]" in result

    def test_filter_email(self):
        """Testa filtragem de emails."""
        text = "Contato: usuario@example.com"
        result = SensitiveDataFilter.filter(text)
        assert "usuario@example.com" not in result
        assert "[EMAIL_REDACTED]" in result

    def test_filter_cpf(self):
        """Testa filtragem de CPF."""
        test_cases = [
            "CPF: 123.456.789-00",
            "CPF: 12345678900",
            "CPF 123.456.789-00",
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert "123.456.789-00" not in result
            assert "12345678900" not in result
            assert "[CPF_REDACTED]" in result

    def test_filter_cnpj(self):
        """Testa filtragem de CNPJ."""
        test_cases = [
            "CNPJ: 12.345.678/0001-90",
            "CNPJ: 12345678000190",
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert "[CNPJ_REDACTED]" in result

    def test_filter_phone_br(self):
        """Testa filtragem de telefones brasileiros."""
        test_cases = [
            ("Tel: (11) 98765-4321", "98765-4321"),  # Com celular (9)
            ("Tel: 11987654321", "987654321"),
            ("Tel: +55 11 98765-4321", "98765"),
            ("Tel: +55 11 9 8765-4321", "8765"),
        ]
        for text, sensitive_part in test_cases:
            result = SensitiveDataFilter.filter(text)
            # Verifica que foi redacted OU que o padrão específico não está visível
            assert (
                "[PHONE_BR_REDACTED]" in result
                or "[CPF_REDACTED]" in result  # Pode ser capturado como CPF
                or sensitive_part not in result
            ), f"Falhou para: {text}"

    def test_filter_credit_card(self):
        """Testa filtragem de cartões de crédito."""
        test_cases = [
            "Card: 4532-1234-5678-9010",
            "Card: 4532 1234 5678 9010",
            "Card: 4532123456789010",
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert "[CREDIT_CARD_REDACTED]" in result
            assert "4532" not in result or result.count("4532") < len(test_cases)

    def test_filter_cvv(self):
        """Testa filtragem de CVV."""
        text = "CVV: 123"
        result = SensitiveDataFilter.filter(text)
        assert "[CVV_REDACTED]" in result
        assert "123" not in result or "CVV" in result

    def test_filter_ipv4_private(self):
        """Testa filtragem de IPs privados."""
        test_cases = [
            "Server: 192.168.1.1",
            "Host: 10.0.0.1",
            "Localhost: 127.0.0.1",
            "Internal: 172.16.0.1",
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert "[IPV4_REDACTED]" in result

    def test_filter_url_with_credentials(self):
        """Testa filtragem de URLs com credenciais."""
        text = "DB: https://user:password123@database.example.com"
        result = SensitiveDataFilter.filter(text)
        # Verifica que a senha foi removida de alguma forma
        assert "password123" not in result
        # Pode ser capturado por url_with_password OU password pattern
        assert "[CREDENTIALS_REDACTED]" in result or "[PASSWORD_REDACTED]" in result

    def test_filter_auth_header(self):
        """Testa filtragem de headers de autenticação."""
        text = "Authorization: Basic dXNlcjpwYXNzd29yZA=="
        result = SensitiveDataFilter.filter(text)
        assert "dXNlcjpwYXNzd29yZA==" not in result
        assert "[TOKEN_REDACTED]" in result

    def test_filter_multiple_sensitive_data(self):
        """Testa filtragem de múltiplos dados sensíveis."""
        text = """
        User: user@example.com
        Password: mysecret123
        API_KEY: sk-proj-abc123def456ghi789jkl012mno345
        CPF: 123.456.789-00
        Card: 4532-1234-5678-9010
        """
        result = SensitiveDataFilter.filter(text)

        # Verifica que os dados sensíveis foram removidos
        assert "user@example.com" not in result
        assert "mysecret123" not in result
        assert "sk-proj-abc123def456ghi789jkl012mno345" not in result
        assert "123.456.789-00" not in result
        assert "4532-1234-5678-9010" not in result

        # Verifica que placeholders foram adicionados
        assert "[EMAIL_REDACTED]" in result
        assert "[PASSWORD_REDACTED]" in result
        assert "[API_KEY_REDACTED]" in result
        assert "[CPF_REDACTED]" in result
        assert "[CREDIT_CARD_REDACTED]" in result

    def test_filter_empty_string(self):
        """Testa filtragem de string vazia."""
        result = SensitiveDataFilter.filter("")
        assert result == ""

    def test_filter_none(self):
        """Testa filtragem de None."""
        result = SensitiveDataFilter.filter(None)
        assert result is None

    def test_filter_normal_text(self):
        """Testa que texto normal não é alterado."""
        text = "Esta é uma mensagem normal sem dados sensíveis"
        result = SensitiveDataFilter.filter(text)
        assert result == text

    def test_mask_partial(self):
        """Testa mascaramento parcial."""
        text = "sk-1234567890abcdef"
        result = SensitiveDataFilter.mask_partial(text, 4)
        assert result.endswith("cdef")
        assert result.startswith("*")
        assert "1234567890ab" not in result

    def test_mask_partial_short_text(self):
        """Testa mascaramento parcial com texto curto."""
        text = "abc"
        result = SensitiveDataFilter.mask_partial(text, 4)
        assert result == "***"

    def test_is_sensitive_true(self):
        """Testa detecção de texto sensível."""
        test_cases = [
            "password=secret",
            "email: user@test.com",
            "CPF: 123.456.789-00",
            "API_KEY=abcdef123456789",  # API key mais longa
        ]
        for text in test_cases:
            assert SensitiveDataFilter.is_sensitive(text), f"Deveria detectar: {text}"

    def test_is_sensitive_false(self):
        """Testa que texto normal não é detectado como sensível."""
        text = "Esta é uma mensagem normal"
        assert not SensitiveDataFilter.is_sensitive(text)

    def test_is_sensitive_empty(self):
        """Testa detecção com string vazia."""
        assert not SensitiveDataFilter.is_sensitive("")

    def test_cache_functionality(self):
        """Testa que o cache funciona corretamente."""
        text = "password=secret123"

        # Primeira chamada
        result1 = SensitiveDataFilter.filter(text)

        # Segunda chamada (deve usar cache)
        result2 = SensitiveDataFilter.filter(text)

        assert result1 == result2
        assert "[PASSWORD_REDACTED]" in result1

    def test_clear_cache_old_method(self):
        """Testa limpeza do cache (método legado)."""
        text = "password=secret123"
        SensitiveDataFilter.filter(text)

        # Verifica que cache tem conteúdo via cache_info
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize > 0

        # Limpa cache
        SensitiveDataFilter.clear_cache()

        # Verifica que cache está vazio
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize == 0

    def test_filter_preserves_context(self):
        """Testa que o contexto ao redor é preservado."""
        text = "Usuário informou password=secret123 no formulário"
        result = SensitiveDataFilter.filter(text)

        assert "Usuário informou" in result
        assert "no formulário" in result
        assert "[PASSWORD_REDACTED]" in result
        assert "secret123" not in result

    def test_filter_rg(self):
        """Testa filtragem de RG."""
        test_cases = [
            "RG: 12.345.678-9",
            "RG: 12.345.678-X",
            "RG: 123456789",
        ]
        for text in test_cases:
            result = SensitiveDataFilter.filter(text)
            assert "[RG_REDACTED]" in result

    def test_lru_cache_is_used(self):
        """Testa que LRU cache está sendo usado."""
        # Verifica que o método _filter_cached tem o decorador lru_cache
        assert hasattr(SensitiveDataFilter._filter_cached, "cache_info")

        # Limpa cache
        SensitiveDataFilter.clear_cache()

        # Faz primeira chamada
        text = "password=secret123"
        SensitiveDataFilter.filter(text)

        # Verifica estatísticas do cache
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.hits >= 0
        assert cache_info.misses >= 1

        # Segunda chamada (deve usar cache)
        SensitiveDataFilter.filter(text)

        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.hits >= 1

    def test_lru_cache_maxsize_constant(self):
        """Testa que DEFAULT_CACHE_SIZE é usado corretamente."""
        assert SensitiveDataFilter.DEFAULT_CACHE_SIZE == 1000

        # Verifica que o cache tem o maxsize correto
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.maxsize == SensitiveDataFilter.DEFAULT_CACHE_SIZE

    def test_lru_cache_evicts_old_entries(self):
        """Testa que LRU cache remove entradas antigas."""
        SensitiveDataFilter.clear_cache()

        # Adiciona muitas entradas diferentes ao cache
        for i in range(1100):  # Mais que DEFAULT_CACHE_SIZE
            SensitiveDataFilter.filter(f"password=secret{i}")

        cache_info = SensitiveDataFilter._filter_cached.cache_info()

        # Cache não deve exceder maxsize
        assert cache_info.currsize <= SensitiveDataFilter.DEFAULT_CACHE_SIZE

    def test_default_visible_chars_constant(self):
        """Testa que DEFAULT_VISIBLE_CHARS está definida."""
        assert SensitiveDataFilter.DEFAULT_VISIBLE_CHARS == 4

    def test_mask_partial_uses_default_visible_chars(self):
        """Testa que mask_partial usa DEFAULT_VISIBLE_CHARS por padrão."""
        text = "sk-1234567890abcdef"
        result = SensitiveDataFilter.mask_partial(text)

        # Deve mostrar os últimos 4 caracteres por padrão
        assert result.endswith("cdef")
        assert len(result.replace("*", "")) == SensitiveDataFilter.DEFAULT_VISIBLE_CHARS

    def test_mask_partial_with_custom_visible_chars(self):
        """Testa mask_partial com valor customizado."""
        text = "sk-1234567890abcdef"
        result = SensitiveDataFilter.mask_partial(text, 6)

        # Deve mostrar os últimos 6 caracteres
        assert result.endswith("abcdef")
        assert len(result.replace("*", "")) == 6

    def test_clear_cache_clears_lru_cache(self):
        """Testa que clear_cache limpa o LRU cache."""
        # Popula o cache
        for i in range(10):
            SensitiveDataFilter.filter(f"password=secret{i}")

        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize > 0

        # Limpa o cache
        SensitiveDataFilter.clear_cache()

        # Verifica que foi limpo
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize == 0
        assert cache_info.hits == 0
        assert cache_info.misses == 0

    def test_lru_cache_thread_safe(self):
        """Testa que LRU cache é thread-safe."""
        SensitiveDataFilter.clear_cache()

        results = []
        errors = []
        lock = threading.Lock()

        def filter_text(i):
            try:
                result = SensitiveDataFilter.filter(f"password=secret{i % 10}")
                with lock:
                    results.append(result)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(filter_text, i) for i in range(100)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(results) == 100
        # Todos os resultados devem ter PASSWORD_REDACTED
        assert all("[PASSWORD_REDACTED]" in r for r in results)

    def test_patterns_order_is_documented(self):
        """Testa que a ordem dos padrões está documentada."""
        # Verifica que a docstring menciona a ordem
        docstring = SensitiveDataFilter.__doc__
        assert "ordem" in docstring.lower() or "order" in docstring.lower()
        assert "JWT" in docstring
        assert "API" in docstring

    def test_filter_performance_with_cache(self):
        """Testa que cache melhora performance."""
        import time

        text = "password=secret123 email=user@test.com"

        # Limpa cache
        SensitiveDataFilter.clear_cache()

        # Primeira execução (sem cache)
        start = time.time()
        for _ in range(100):
            SensitiveDataFilter.filter(text)
        time_without_cache_benefit = time.time() - start

        # Agora com cache populado
        start = time.time()
        for _ in range(100):
            SensitiveDataFilter.filter(text)
        time_with_cache = time.time() - start

        # Com cache deve ser mais rápido ou similar
        # (segunda execução beneficia do cache)
        assert time_with_cache <= time_without_cache_benefit * 1.5

    def test_cache_handles_different_inputs(self):
        """Testa que cache lida com diferentes inputs corretamente."""
        inputs = [
            "password=secret1",
            "password=secret2",
            "email=test@test.com",
            "CPF: 123.456.789-00",
            "normal text",
        ]

        SensitiveDataFilter.clear_cache()

        # Processa cada input
        results = {}
        for inp in inputs:
            results[inp] = SensitiveDataFilter.filter(inp)

        # Processa novamente (deve usar cache)
        for inp in inputs:
            result = SensitiveDataFilter.filter(inp)
            assert result == results[inp]

        # Verifica cache info
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.hits >= len(inputs)

    def test_constants_are_class_level(self):
        """Testa que constantes são de nível de classe."""
        # Verifica que as constantes existem na classe
        assert hasattr(SensitiveDataFilter, "DEFAULT_CACHE_SIZE")
        assert hasattr(SensitiveDataFilter, "DEFAULT_VISIBLE_CHARS")

        # Verifica que são inteiros
        assert isinstance(SensitiveDataFilter.DEFAULT_CACHE_SIZE, int)
        assert isinstance(SensitiveDataFilter.DEFAULT_VISIBLE_CHARS, int)

        # Verifica valores razoáveis
        assert SensitiveDataFilter.DEFAULT_CACHE_SIZE > 0
        assert SensitiveDataFilter.DEFAULT_VISIBLE_CHARS > 0

    def test_filter_cached_is_internal_method(self):
        """Testa que _filter_cached é método interno."""
        # Verifica que método começa com underscore (convenção Python)
        assert SensitiveDataFilter._filter_cached.__name__.startswith("_")

        # Verifica que filter() chama _filter_cached
        SensitiveDataFilter.clear_cache()
        text = "password=test123"
        SensitiveDataFilter.filter(text)

        # Cache deve ter sido usado
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.currsize > 0

    def test_lru_cache_info_accessible(self):
        """Testa que cache_info está acessível para monitoramento."""
        SensitiveDataFilter.clear_cache()

        # Faz algumas chamadas
        for i in range(5):
            SensitiveDataFilter.filter(f"test{i}")

        # Obtém info do cache
        info = SensitiveDataFilter._filter_cached.cache_info()

        # Verifica estrutura do cache_info
        assert hasattr(info, "hits")
        assert hasattr(info, "misses")
        assert hasattr(info, "maxsize")
        assert hasattr(info, "currsize")

        assert info.maxsize == 1000
        assert info.currsize == 5
        assert info.misses == 5
        assert info.hits == 0

    def test_concurrent_access_with_cache(self):
        """Testa acesso concorrente com cache."""
        SensitiveDataFilter.clear_cache()

        # Mesmo texto para múltiplas threads (deve usar cache)
        text = "password=shared_secret"

        results = []
        lock = threading.Lock()

        def filter_concurrent():
            result = SensitiveDataFilter.filter(text)
            with lock:
                results.append(result)

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(filter_concurrent) for _ in range(100)]
            concurrent.futures.wait(futures)

        # Todos devem ter o mesmo resultado
        assert len(results) == 100
        assert len(set(results)) == 1  # Todos iguais
        assert "[PASSWORD_REDACTED]" in results[0]

        # Cache deve ter sido usado extensivamente
        cache_info = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info.hits > 90  # A maioria deve ter sido cache hit
