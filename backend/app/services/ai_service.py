"""Lightweight AI helpers for MVP — replace with Cloud Vision / custom models in production."""

import io
import re
from dataclasses import dataclass

from PIL import Image

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SPAM_PATTERNS = [
    r"(?i)test{3,}",
    r"(?i)asdf+",
    r"(?i)http[s]?://",
    r"(?i)buy now",
    r"(?i)casino",
]


@dataclass
class ImageAnalysis:
    likely_aed: bool
    confidence: float
    reason: str


@dataclass
class SpamAnalysis:
    is_spam: bool
    score: float
    reason: str


class AIService:
    def analyze_image(self, content: bytes) -> ImageAnalysis:
        """
        Heuristic AED detection: red/green dominant regions + aspect ratio.
        Production: swap for Vertex AI / Cloud Vision custom model.
        """
        try:
            img = Image.open(io.BytesIO(content)).convert("RGB")
            img.thumbnail((256, 256))
            pixels = list(img.getdata())
            if not pixels:
                return ImageAnalysis(False, 0.0, "empty_image")

            red_score = 0
            green_score = 0
            for r, g, b in pixels:
                if r > 120 and g < 80 and b < 80:
                    red_score += 1
                if g > 100 and r < 100:
                    green_score += 1

            total = len(pixels)
            red_ratio = red_score / total
            green_ratio = green_score / total
            w, h = img.size
            aspect = w / h if h else 1

            confidence = min(1.0, red_ratio * 4 + green_ratio * 2)
            if 0.6 <= aspect <= 1.8:
                confidence += 0.1
            confidence = min(1.0, confidence)

            likely = confidence >= get_settings().min_aed_confidence
            reason = f"red={red_ratio:.3f},green={green_ratio:.3f},aspect={aspect:.2f}"
            logger.info("image_analysis", confidence=confidence, likely_aed=likely)
            return ImageAnalysis(likely, confidence, reason)
        except Exception as exc:
            logger.warning("image_analysis_failed", error=str(exc))
            return ImageAnalysis(False, 0.0, "parse_error")

    def check_spam(self, description: str | None, address: str | None) -> SpamAnalysis:
        text = " ".join(filter(None, [description, address]))
        if not text.strip():
            return SpamAnalysis(False, 0.0, "empty")

        score = 0.0
        for pattern in SPAM_PATTERNS:
            if re.search(pattern, text):
                score += 0.35

        if len(text) > 1500:
            score += 0.2

        score = min(1.0, score)
        return SpamAnalysis(score >= 0.5, score, "pattern_match" if score >= 0.5 else "ok")
