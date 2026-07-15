"""Image Provider - abstract base class (v2.0 plugin architecture)

Supports: jimeng, openai, future providers.
Configured via IMAGE_PROVIDER env var.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ImageResult:
    """Unified image generation result"""
    success: bool
    image_url: str = ""
    task_id: str = ""
    error: str = ""
    provider: str = ""


class BaseImageProvider(ABC):
    """Abstract image generation provider.

    All providers must implement generate().
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ImageResult:
        """Generate an image from a prompt.

        Args:
            prompt: Image description text
            **kwargs: Provider-specific options (size, style, etc.)

        Returns:
            ImageResult with success/error status
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. 'jimeng', 'openai')"""
        ...


def get_image_provider() -> BaseImageProvider:
    """Factory: returns configured image provider instance.

    Reads IMAGE_PROVIDER from settings.
    """
    from backend.config import settings

    provider_name = settings.IMAGE_PROVIDER.lower()

    if provider_name == "jimeng":
        from .jimeng import JimengProvider
        return JimengProvider()
    elif provider_name == "openai":
        # Future: OpenAI DALL-E provider
        raise NotImplementedError("OpenAI image provider not yet implemented")
    else:
        raise ValueError(f"Unknown image provider: {provider_name}")
