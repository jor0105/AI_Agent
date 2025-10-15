from openai import OpenAI


class ClientOpenAI:
    API_OPENAI_NAME = "OPENAI_API_KEY"

    @staticmethod
    def get_client(api_key: str) -> OpenAI:
        client = OpenAI(api_key=api_key)
        return client
