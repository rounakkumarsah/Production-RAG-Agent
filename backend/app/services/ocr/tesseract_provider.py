import pytesseract
from PIL import Image
from app.services.ocr.base import OCRProvider

class TesseractProvider(OCRProvider):
    def name(self) -> str:
        return "Tesseract"

    def extract_text(self, image: Image.Image) -> str:
        # Convert to RGB just in case it's RGBA or something else
        return pytesseract.image_to_string(image.convert("RGB")).strip()
