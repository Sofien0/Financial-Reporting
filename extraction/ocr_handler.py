#!/usr/bin/env python3
"""
OCR Handler Module for ESG Report Processing
Handles Optical Character Recognition for image-based content in PDFs
"""

import logging
from typing import List, Dict, Optional, Tuple
import fitz  # PyMuPDF
import io
from PIL import Image
import numpy as np
import re

logger = logging.getLogger(__name__)

class OCRHandler:
    """OCR handler for processing image-based content in PDFs"""
    
    def __init__(self, use_tesseract: bool = True):
        """
        Initialize OCR handler
        
        Args:
            use_tesseract: Whether to use Tesseract OCR (requires installation)
        """
        self.logger = logging.getLogger(__name__)
        self.use_tesseract = use_tesseract
        
        # Try to import Tesseract
        try:
            import pytesseract
            self.tesseract = pytesseract
            self.logger.info("Tesseract OCR initialized successfully")
        except ImportError:
            self.tesseract = None
            self.use_tesseract = False
            self.logger.warning("Tesseract not available, OCR functionality limited")
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Extract images from PDF for OCR processing
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of image data with metadata
        """
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get image list
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    
                    # Get image data
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        # Convert to PIL Image
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Get image metadata
                        bbox = page.get_image_bbox(img)
                        
                        images.append({
                            'page_num': page_num + 1,
                            'image_index': img_index,
                            'image': pil_image,
                            'bbox': bbox,
                            'width': pil_image.width,
                            'height': pil_image.height,
                            'format': pil_image.format,
                            'mode': pil_image.mode
                        })
                    
                    pix = None  # Free memory
            
            doc.close()
            return images
            
        except Exception as e:
            self.logger.error(f"Error extracting images from PDF: {e}")
            return []
    
    def process_image_with_ocr(self, image_data: Dict) -> Dict:
        """
        Process image with OCR to extract text
        
        Args:
            image_data: Image data dictionary
            
        Returns:
            Dictionary with OCR results
        """
        try:
            image = image_data['image']
            
            if self.use_tesseract and self.tesseract:
                # Use Tesseract OCR
                ocr_text = self.tesseract.image_to_string(image)
                confidence = self._get_ocr_confidence(image)
                
                return {
                    'text': ocr_text.strip(),
                    'confidence': confidence,
                    'method': 'tesseract',
                    'bbox': image_data['bbox'],
                    'page_num': image_data['page_num'],
                    'image_index': image_data['image_index']
                }
            else:
                # Fallback: basic image analysis
                return self._basic_image_analysis(image_data)
                
        except Exception as e:
            self.logger.error(f"Error processing image with OCR: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'failed',
                'bbox': image_data.get('bbox', (0, 0, 0, 0)),
                'page_num': image_data.get('page_num', 0),
                'image_index': image_data.get('image_index', 0)
            }
    
    def _get_ocr_confidence(self, image) -> float:
        """
        Get OCR confidence score
        
        Args:
            image: PIL Image object
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            if self.tesseract:
                # Get OCR data with confidence
                data = self.tesseract.image_to_data(image, output_type=self.tesseract.Output.DICT)
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    return avg_confidence / 100.0  # Normalize to 0-1
                
            return 0.5  # Default confidence
            
        except Exception as e:
            self.logger.error(f"Error getting OCR confidence: {e}")
            return 0.5
    
    def _basic_image_analysis(self, image_data: Dict) -> Dict:
        """
        Basic image analysis when OCR is not available
        
        Args:
            image_data: Image data dictionary
            
        Returns:
            Dictionary with basic analysis results
        """
        try:
            image = image_data['image']
            
            # Convert to numpy array for analysis
            img_array = np.array(image)
            
            # Basic image properties
            height, width = img_array.shape[:2]
            aspect_ratio = width / height if height > 0 else 0
            
            # Analyze image characteristics
            is_likely_chart = self._is_likely_chart(img_array)
            is_likely_table = self._is_likely_table(img_array)
            
            return {
                'text': '',  # No text without OCR
                'confidence': 0.0,
                'method': 'basic_analysis',
                'bbox': image_data['bbox'],
                'page_num': image_data['page_num'],
                'image_index': image_data['image_index'],
                'image_properties': {
                    'width': width,
                    'height': height,
                    'aspect_ratio': aspect_ratio,
                    'is_likely_chart': is_likely_chart,
                    'is_likely_table': is_likely_table
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in basic image analysis: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'failed',
                'bbox': image_data.get('bbox', (0, 0, 0, 0)),
                'page_num': image_data.get('page_num', 0),
                'image_index': image_data.get('image_index', 0)
            }
    
    def _is_likely_chart(self, img_array: np.ndarray) -> bool:
        """
        Determine if image is likely a chart/graph
        
        Args:
            img_array: Image as numpy array
            
        Returns:
            True if likely a chart
        """
        try:
            # Simple heuristics for chart detection
            # Look for regular patterns, lines, and geometric shapes
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            # Edge detection (simple)
            edges = np.abs(np.diff(gray, axis=0)) + np.abs(np.diff(gray, axis=1))
            edge_density = np.mean(edges > 30)
            
            # Check for regular patterns
            horizontal_lines = np.sum(np.diff(gray, axis=1) > 50) / gray.size
            vertical_lines = np.sum(np.diff(gray, axis=0) > 50) / gray.size
            
            # Heuristic: charts often have moderate edge density and regular lines
            return (0.1 < edge_density < 0.3) and (horizontal_lines > 0.01 or vertical_lines > 0.01)
            
        except Exception:
            return False
    
    def _is_likely_table(self, img_array: np.ndarray) -> bool:
        """
        Determine if image is likely a table
        
        Args:
            img_array: Image as numpy array
            
        Returns:
            True if likely a table
        """
        try:
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            # Look for grid-like patterns
            horizontal_lines = np.sum(np.diff(gray, axis=1) > 50) / gray.size
            vertical_lines = np.sum(np.diff(gray, axis=0) > 50) / gray.size
            
            # Tables typically have both horizontal and vertical lines
            return horizontal_lines > 0.02 and vertical_lines > 0.02
            
        except Exception:
            return False
    
    def extract_kpi_from_ocr_text(self, ocr_text: str, context: str = "") -> List[Dict]:
        """
        Extract potential KPIs from OCR text
        
        Args:
            ocr_text: Text extracted via OCR
            context: Additional context
            
        Returns:
            List of potential KPI candidates
        """
        kpi_candidates = []
        
        try:
            # KPI patterns for OCR text
            kpi_patterns = [
                # Numbers with units
                r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(%|percent|tons?|tonnes?|kWh|MWh|GWh|tCO2e?|CO2e?|USD|EUR|GBP|employees?|people|incidents?|violations?)',
                # Ranges
                r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(%|tons?|kWh|USD)',
                # Percentages
                r'(\d+(?:\.\d+)?)\s*%',
                # Currency amounts
                r'(\$|€|£)\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
                # Emissions
                r'(\d+(?:\.\d+)?)\s*(tCO2e?|CO2e?|tons?\s*CO2)',
                # Energy
                r'(\d+(?:\.\d+)?)\s*(kWh|MWh|GWh)'
            ]
            
            full_text = f"{context} {ocr_text}"
            
            for pattern in kpi_patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    kpi_candidates.append({
                        'value': match.group(1),
                        'unit': match.group(2) if len(match.groups()) > 1 else '',
                        'full_match': match.group(0),
                        'context': full_text[max(0, match.start()-50):match.end()+50],
                        'pattern': pattern
                    })
            
            return kpi_candidates
            
        except Exception as e:
            self.logger.error(f"Error extracting KPIs from OCR text: {e}")
            return []
    
    def validate_ocr_result(self, ocr_result: Dict) -> bool:
        """
        Validate OCR result quality
        
        Args:
            ocr_result: OCR result dictionary
            
        Returns:
            True if result is valid
        """
        try:
            text = ocr_result.get('text', '')
            confidence = ocr_result.get('confidence', 0.0)
            
            # Basic validation criteria
            if not text.strip():
                return False
            
            if confidence < 0.3:  # Low confidence
                return False
            
            # Check for reasonable text length
            if len(text) < 5:
                return False
            
            # Check for excessive noise (too many special characters)
            special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s\.\,\-\+\%]', text)) / len(text)
            if special_char_ratio > 0.3:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating OCR result: {e}")
            return False 