import os

from dotenv import load_dotenv


class EnvironmentConfig:
    @staticmethod
    def get_api_key(key: str) -> str:
        load_dotenv()
        api_key = os.getenv(key)
        if not api_key:
            raise EnvironmentError(f"Environment variable {key} not found")
        return api_key
