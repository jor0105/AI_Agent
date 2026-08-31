from typing import Final

OPENAI_MODEL_NANO: Final[str] = 'gpt-5-nano'
OPENAI_MODEL_MINI: Final[str] = 'gpt-5-mini'

OLLAMA_MODEL_LFM: Final[str] = 'lfm2.5:2.6b'
OLLAMA_MODEL_PHI: Final[str] = 'phi4-mini:latest'
OLLAMA_MODEL_GRANITE: Final[str] = 'granite4:latest'

OLLAMA_TEST_MODELS: tuple[str, ...] = (
    OLLAMA_MODEL_LFM,
    OLLAMA_MODEL_PHI,
    OLLAMA_MODEL_GRANITE,
)
