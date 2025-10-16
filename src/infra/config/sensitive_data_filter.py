"""
Filtro de dados sensíveis para logs.

Este módulo fornece funcionalidades para remover ou mascarar
dados sensíveis dos logs, garantindo conformidade com LGPD/GDPR
e segurança de credenciais.
"""

import re
from functools import lru_cache
from typing import Dict, Pattern


class SensitiveDataFilter:
    """
    Filtro para remover dados sensíveis de logs.

    Protege contra vazamento de:
    - Credenciais (API keys, tokens, passwords)
    - Dados pessoais (emails, CPF, telefones)
    - Dados financeiros (cartões de crédito)
    - Secrets e chaves

    IMPORTANTE: A ordem dos padrões é significativa!
    Padrões mais específicos devem vir primeiro para evitar
    que padrões genéricos capturem incorretamente.

    Ordem atual:
    1. JWT tokens (mais específico)
    2. API keys
    3. Bearer tokens
    4. Secrets
    5. Auth headers
    6. URLs com senhas (antes de password genérico)
    7. Passwords (mais genérico)
    8. Dados pessoais (LGPD/GDPR)
    9. Dados financeiros
    10. IPs privados
    """

    # Constantes de configuração
    DEFAULT_CACHE_SIZE = 1000
    DEFAULT_VISIBLE_CHARS = 4

    # Padrões compilados para melhor performance (ORDEM IMPORTA!)
    _PATTERNS: Dict[str, Pattern] = {
        # Credenciais e Secrets (ordem importa - mais específicos primeiro)
        "jwt_token": re.compile(
            r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"
        ),
        "api_key": re.compile(r'(api[_-]?key[\s:="\']*)[\w\-]{6,}', re.IGNORECASE),
        "bearer_token": re.compile(r"(bearer[\s]+)[\w\-._]+", re.IGNORECASE),
        "secret": re.compile(
            r'(secret|secret_key)[\s:="\']*([\w\-]{8,})', re.IGNORECASE
        ),
        "auth_header": re.compile(
            r"(authorization[\s:]+)(basic|bearer)[\s]+[\w\-._=]+", re.IGNORECASE
        ),
        # URLs com credenciais (antes de password para não conflitar)
        "url_with_password": re.compile(
            r"(https?://[^:@\s]+):([^@\s]+)@", re.IGNORECASE
        ),
        "password": re.compile(
            r'(password|senha|pwd|pass)[\s:="\'\[]*([^\s,\]"\'}@]{3,})', re.IGNORECASE
        ),
        # Dados Pessoais (LGPD/GDPR)
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "cnpj": re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
        "cpf": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
        "rg": re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9Xx]\b"),
        "phone_br": re.compile(
            r"\b(?:\+55[\s]?)?\(?[1-9]{2}\)?[\s]?9[\s]?\d{4}-?\d{4}\b"
        ),
        # Dados Financeiros
        "credit_card": re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
        "cvv": re.compile(
            r'\b(cvv|cvc|security[\s]?code)[\s:="\']*([\d]{3,4})\b', re.IGNORECASE
        ),
        # Endereços IP (podem ser sensíveis em alguns contextos)
        "ipv4": re.compile(
            r"\b(?:10|127|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b"
        ),
    }

    @classmethod
    @lru_cache(maxsize=DEFAULT_CACHE_SIZE)
    def _filter_cached(cls, text: str) -> str:
        """
        Remove ou mascara dados sensíveis do texto (versão cacheada).
        Usa LRU cache para melhor performance e gerenciamento automático.

        Args:
            text: Texto a ser filtrado

        Returns:
            Texto com dados sensíveis substituídos por placeholders
        """
        filtered_text = text

        # Aplica cada padrão
        for pattern_name, pattern in cls._PATTERNS.items():
            if pattern_name == "password":
                # Preserva a palavra "password" mas remove o valor
                filtered_text = pattern.sub(r"\1[PASSWORD_REDACTED]", filtered_text)
            elif pattern_name == "secret":
                # Preserva a palavra "secret" mas remove o valor
                filtered_text = pattern.sub(r"\1[SECRET_REDACTED]", filtered_text)
            elif pattern_name == "cvv":
                # Preserva o label mas remove o CVV
                filtered_text = pattern.sub(r"\1[CVV_REDACTED]", filtered_text)
            elif pattern_name == "url_with_password":
                # Remove credenciais de URLs
                filtered_text = pattern.sub(
                    r"\1:[CREDENTIALS_REDACTED]@", filtered_text
                )
            elif pattern_name == "auth_header":
                # Preserva tipo de auth mas remove o token
                filtered_text = pattern.sub(r"\1\2 [TOKEN_REDACTED]", filtered_text)
            else:
                # Substituição completa para outros casos
                filtered_text = pattern.sub(
                    f"[{pattern_name.upper()}_REDACTED]", filtered_text
                )

        return filtered_text

    @classmethod
    def filter(cls, text: str) -> str:
        """
        Remove ou mascara dados sensíveis do texto.

        Args:
            text: Texto a ser filtrado

        Returns:
            Texto com dados sensíveis substituídos por placeholders

        Example:
            >>> text = "API Key: abc123xyz, email: user@example.com"
            >>> SensitiveDataFilter.filter(text)
            'API Key: [API_KEY_REDACTED], email: [EMAIL_REDACTED]'
        """
        if not text:
            return text

        return cls._filter_cached(text)

    @classmethod
    def clear_cache(cls) -> None:
        """Limpa o cache LRU de substituições."""
        cls._filter_cached.cache_clear()

    @classmethod
    def mask_partial(cls, text: str, visible_chars: int = DEFAULT_VISIBLE_CHARS) -> str:
        """
        Mascara parcialmente um texto, mantendo alguns caracteres visíveis.

        Args:
            text: Texto a ser mascarado
            visible_chars: Número de caracteres visíveis no final

        Returns:
            Texto mascarado

        Example:
            >>> SensitiveDataFilter.mask_partial("sk-1234567890abcdef", 4)
            '****cdef'
        """
        if len(text) <= visible_chars:
            return "*" * len(text)

        return "*" * (len(text) - visible_chars) + text[-visible_chars:]

    @classmethod
    def is_sensitive(cls, text: str) -> bool:
        """
        Verifica se o texto contém dados sensíveis.

        Args:
            text: Texto a ser verificado

        Returns:
            True se o texto contém dados sensíveis
        """
        if not text:
            return False

        for pattern in cls._PATTERNS.values():
            if pattern.search(text):
                return True

        return False
