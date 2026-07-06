import numpy as np
from PIL import Image
from app.services.ocr.base import OCRProvider

class PaddleOCRProvider(OCRProvider):
    def __init__(self):
        # We lazily import PaddleOCR so the backend doesn't crash if it's missing during init
        try:
            from paddleocr import PaddleOCR
            # use_angle_cls=True to rotate images automatically
            # lang='en' as a default, though could be configurable
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        except ImportError:
            self.ocr = None

    def name(self) -> str:
        return "PaddleOCR"

    def extract_text(self, image: Image.Image) -> str:
        if not self.ocr:
            raise RuntimeError("PaddleOCR is not installed or failed to initialize.")
        
        # Convert PIL Image to cv2 format (numpy array)
        img_arr = np.array(image.convert('RGB'))
        # RGB to BGR for PaddleOCR (though usually it handles RGB fine)
        img_arr = img_arr[:, :, ::-1].copy()

        result = self.ocr.ocr(img_arr, cls=True)
        if not result or not result[0]:
            return ""

        # result is a list of lines, each line is [coords, (text, confidence)]
        extracted_lines = []
        for line in result[0]:
            if line and len(line) >= 2:
                text = line[1][0]
                extracted_lines.append(text)
                
        return "\n".join(extracted_lines)
