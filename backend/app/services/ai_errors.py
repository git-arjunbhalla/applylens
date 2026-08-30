class AIError(Exception):
    """Base application error for AI provider operations."""


class AIConfigurationError(AIError):
    """Raised when provider settings are missing or invalid."""


class AIUnsupportedProviderError(AIError):
    """Raised when AI_PROVIDER is not implemented."""


class AITimeoutError(AIError):
    """Raised when the provider does not respond in time."""


class AIProviderError(AIError):
    """Raised when the provider/API request fails."""


class AIResponseError(AIError):
    """Raised when the provider response is empty, invalid, or unstructured."""
