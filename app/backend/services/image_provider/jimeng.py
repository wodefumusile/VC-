"""Jimeng (即梦) AI image provider — via ByteDance Volcano Ark API"""

import time
import json
import requests
from loguru import logger
from backend.config import settings
from .base import BaseImageProvider, ImageResult


class JimengProvider(BaseImageProvider):
    """即梦 AI 图片生成 Provider.

    Uses ByteDance Volcano Engine Ark API (OpenAI-compatible image endpoint).
    """

    def __init__(self):
        self.api_key = settings.IMAGE_API_KEY
        self.base_url = settings.IMAGE_BASE_URL.rstrip("/")
        self.model = settings.IMAGE_MODEL
        logger.info("JimengProvider init | model={}", self.model)

    @property
    def name(self) -> str:
        return "jimeng"

    def generate(self, prompt: str, size: str = "1024x1024", **kwargs) -> ImageResult:
        """Generate image via Jimeng/Volcano Ark API.

        Args:
            prompt: Image description (Chinese or English)
            size: Image dimensions (default 1024x1024)

        Returns:
            ImageResult with image_url or error
        """
        if not self.api_key:
            return ImageResult(
                success=False,
                error="IMAGE_API_KEY not configured",
                provider=self.name,
            )

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # Volcano Ark image generation API (OpenAI-compatible)
            payload = {
                "model": self.model,
                "prompt": prompt,
                "n": 1,
                "size": size,
                "response_format": "url",
            }

            logger.info("Jimeng generate | prompt={}...", prompt[:60])

            resp = requests.post(
                f"{self.base_url}/images/generations",
                headers=headers,
                json=payload,
                timeout=120,
            )

            if resp.status_code == 200:
                data = resp.json()
                image_url = ""
                task_id = ""

                # Extract image URL from response
                if "data" in data and len(data["data"]) > 0:
                    image_url = data["data"][0].get("url", "")
                if "id" in data:
                    task_id = data["id"]

                if image_url:
                    logger.success("Jimeng generated | url={}...", image_url[:50])
                    return ImageResult(
                        success=True,
                        image_url=image_url,
                        task_id=task_id,
                        provider=self.name,
                    )

            # Handle errors
            error_msg = f"HTTP {resp.status_code}"
            try:
                err_data = resp.json()
                if "error" in err_data:
                    error_msg = err_data["error"].get("message", error_msg)
            except:
                error_msg = resp.text[:200]

            logger.error("Jimeng failed: {}", error_msg)
            return ImageResult(
                success=False,
                error=error_msg,
                provider=self.name,
            )

        except requests.Timeout:
            return ImageResult(
                success=False,
                error="Image generation timeout (>120s)",
                provider=self.name,
            )
        except Exception as e:
            logger.exception("Jimeng exception")
            return ImageResult(
                success=False,
                error=str(e),
                provider=self.name,
            )
