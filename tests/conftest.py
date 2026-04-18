import sys
from unittest.mock import MagicMock

# Mock PaddleOCR and PaddlePaddle globally so tests don't crash on import
sys.modules['paddleocr'] = MagicMock()
sys.modules['paddlepaddle'] = MagicMock()