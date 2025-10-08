from openai import OpenAI


class ClientOpenAI:
    def get_client(self, api_key: str) -> OpenAI:
        client = OpenAI(api_key=api_key)
        return client
