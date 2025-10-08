from dotenv import load_dotenv
import os

class EnvironmentConfig:    
    def get_api_key(self, key: str) -> str:
        load_dotenv()
        api_key = os.getenv(key)
        if not api_key:
            raise EnvironmentError(f"Environment variable {key} not found")
        return api_key
