import pytest
from unittest.mock import patch, MagicMock
from utils import preprocess_text_for_ai, extract_pdf_content


# 1. Test Text Preprocessing 
def test_preprocess_text_truncation():
    long_text = "word " * 100000 
    processed = preprocess_text_for_ai(long_text, max_tokens=100) 
    assert len(processed) < len(long_text)
    assert "word" in processed

def test_preprocess_removes_double_spaces():
    text = "This  has   double    spaces."
    processed = preprocess_text_for_ai(text)
    assert "  " not in processed
    assert " " in processed

# 2. Test PDF Extraction (Mocked) - Standard Mode
@patch('utils.update_terminal_log') 
@patch('utils.fitz')                 
def test_extract_pdf_content_success(mock_fitz, mock_log): 
    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_doc.metadata = {'title': 'Test Paper', 'author': 'Test Author', 'creationDate': 'D:20240101'}
    
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Sample PDF Content for testing."
    
    mock_doc.__iter__.return_value = iter([mock_page])
    mock_fitz.open.return_value = mock_doc

    # Test with OCR disabled (default)
    text, title, author, year = extract_pdf_content(b"fake_pdf_bytes")
    
    assert "Sample PDF Content" in text
    assert title == "Test Paper"
    assert author == "Test Author"
    mock_doc.close.assert_called_once()

# 3. Test PDF Extraction - OCR Mode Enabled (PyTesseract)
@patch('utils.pytesseract') 
@patch('utils.update_terminal_log')
@patch('utils.fitz')
def test_extract_pdf_content_with_ocr(mock_fitz, mock_log, mock_pytesseract):
    # Setup Mock Doc
    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_doc.metadata = {'title': 'OCR Paper', 'author': 'A', 'creationDate': 'D:2024'}
    
    # Setup Mock Page with an image
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Normal Text"
    mock_page.get_images.return_value = [[1]] # Simulate 1 image found
    
    mock_doc.__iter__.return_value = iter([mock_page])
    mock_fitz.open.return_value = mock_doc
    
    # Mock image extraction
    mock_doc.extract_image.return_value = {"image": b"img_bytes"}
    
    # Mock pytesseract return value
    # We mock the function call directly: pytesseract.image_to_string(...)
    mock_pytesseract.image_to_string.return_value = "OCR Result"
    
    # Mock PIL Image.open
    with patch('utils.Image.open') as mock_img_open:
        mock_img_open.return_value = MagicMock()
        
        # Run with OCR Enabled
        text, title, author, year = extract_pdf_content(b"fake_pdf_bytes", enable_ocr=True)
        
        # Verify pytesseract.image_to_string was called
        mock_pytesseract.image_to_string.assert_called_once()
        
        # Verify text contains both normal and OCR text
        assert "Normal Text" in text
        assert "OCR Result" in text