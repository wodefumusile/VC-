"""Image Handler — post-generation image processing.

- Detect image count in article
- Auto-assign first image as cover
- WeChat-compatible img tag injection
- Missing image detection
"""

import re
from loguru import logger


class ImageHandler:
    """Process and inject images into article HTML."""

    @staticmethod
    def inject_images(content_html: str, image_records: list[dict]) -> str:
        """Inject generated images into article HTML.

        Args:
            content_html: Article HTML content
            image_records: List of image records from DB
                [{position:0, image_url:"...", type:"cover"}, ...]

        Returns:
            HTML with injected img tags
        """
        if not image_records:
            logger.info("No images to inject")
            return content_html

        covers = [r for r in image_records if r.get("type") == "cover" and r.get("image_url")]
        illustrations = [r for r in image_records if r.get("type") == "illustration" and r.get("image_url")]

        # Inject cover at the very beginning (after title in formatter)
        html = content_html

        # Inject illustrations at paragraph boundaries
        if illustrations:
            # Find H2 headings or paragraph breaks to insert images
            paras = list(re.finditer(r"(</section>)\s*(<section)", html))
            step = max(1, len(paras) // (len(illustrations) + 1))

            offset = 0
            for i, img in enumerate(illustrations):
                pos = (i + 1) * step
                if pos < len(paras):
                    insert_point = paras[pos].end() + offset
                    img_html = ImageHandler._build_img_tag(img["image_url"], img.get("position", i + 1))
                    html = html[:insert_point] + img_html + html[insert_point:]
                    offset += len(img_html)

        return html

    @staticmethod
    def _build_img_tag(image_url: str, position: int = 1) -> str:
        """Build WeChat-compatible image HTML.

        Uses section+img pattern for ProseMirror compatibility.
        """
        return (
            f'<section style="text-align:center;margin:16px 0">'
            f'<img src="{image_url}" '
            f'style="max-width:100%;border-radius:8px;display:block;margin:0 auto" '
            f'alt="图{position}">'
            f'</section>'
        )

    @staticmethod
    def count_images(content_html: str) -> int:
        """Count existing <img> tags in content."""
        return len(re.findall(r"<img[^>]*>", content_html))

    @staticmethod
    def has_cover(image_records: list[dict]) -> bool:
        """Check if any image is marked as cover."""
        return any(r.get("type") == "cover" and r.get("image_url") for r in image_records)

    @staticmethod
    def get_cover_url(image_records: list[dict]) -> str:
        """Get the first cover image URL."""
        for r in image_records:
            if r.get("type") == "cover" and r.get("image_url"):
                return r["image_url"]
        return ""

    @staticmethod
    def check_missing_images(image_records: list[dict]) -> list[dict]:
        """Return images that failed to generate."""
        return [r for r in image_records if r.get("status") == "failed"]


image_handler = ImageHandler()
