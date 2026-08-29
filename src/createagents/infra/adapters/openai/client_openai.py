from openai import AsyncOpenAI


class ClientOpenAI:
    """Client for interacting with the OpenAI API."""

    API_OPENAI_NAME = 'OPENAI_API_KEY'

    @staticmethod
    def get_client(
        api_key: str, timeout: float, max_retries: int
    ) -> AsyncOpenAI:
        """Create and return an OpenAI client instance.

        Args:
            api_key: The OpenAI API key.
            timeout: Per-request timeout in seconds.
            max_retries: How many times the SDK retries a failed request.

        Returns:
            AsyncOpenAI: The configured OpenAI client.

        """
        return AsyncOpenAI(
            api_key=api_key, timeout=timeout, max_retries=max_retries
        )
