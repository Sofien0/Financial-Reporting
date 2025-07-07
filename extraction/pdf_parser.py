#!/usr/bin/env python3
"""
PDF Parser Module for ESG Report Processing
Handles PDF text extraction with layout awareness and coordinate tracking
"""

import fitz  # PyMuPDF
import logging
from typing import List, Dict, Tuple, Optional
import re

logger = logging.getLogger(__name__)

class PDFParser:
    """PDF parser with layout awareness for ESG report processing"""
    
    def __init__(self):
        """Initialize PDF parser"""
        self.logger = logging.getLogger(__name__)
    
    def extract_text_blocks_with_coordinates(self, page) -> List[Dict]:
        """
        Extract text blocks with coordinates and metadata from a PDF page
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            List of text blocks with coordinates and metadata
        """
        text_blocks = []
        
        try:
            # Get text blocks with detailed information
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:  # Text block
                    block_text = ""
                    block_bbox = block.get("bbox", (0, 0, 0, 0))
                    
                    # Extract text from lines
                    for line in block["lines"]:
                        for span in line["spans"]:
                            block_text += span["text"] + " "
                    
                    block_text = block_text.strip()
                    
                    if block_text:
                        # Calculate average font size
                        avg_font_size = self._get_avg_font_size(block)
                        
                        # Determine if it's a header
                        is_header = self._is_header_block(block)
                        
                        text_blocks.append({
                            'text': block_text,
                            'bbox': block_bbox,
                            'font_size': avg_font_size,
                            'is_header': is_header,
                            'block_type': 'text'
                        })
            
            return text_blocks
            
        except Exception as e:
            self.logger.error(f"Error extracting text blocks: {e}")
            return []
    
    def _get_avg_font_size(self, block) -> float:
        """Calculate average font size for a text block"""
        font_sizes = []
        
        try:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font_sizes.append(span.get("size", 12))
            
            return sum(font_sizes) / len(font_sizes) if font_sizes else 12.0
            
        except Exception:
            return 12.0
    
    def _is_header_block(self, block) -> bool:
        """Determine if a text block is a header based on font size and content"""
        try:
            # Check font size (headers are usually larger)
            avg_font_size = self._get_avg_font_size(block)
            
            # Check text content for header patterns
            text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text += span.get("text", "")
            
            # Header patterns
            header_patterns = [
                r'^\d+\.\s+[A-Z]',  # Numbered sections
                r'^[A-Z][A-Z\s]{2,}$',  # ALL CAPS text
                r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',  # Title Case
                r'^Chapter\s+\d+',
                r'^Section\s+\d+',
                r'^Table\s+\d+',
                r'^Figure\s+\d+'
            ]
            
            is_large_font = avg_font_size > 14
            matches_pattern = any(re.match(pattern, text.strip()) for pattern in header_patterns)
            
            return is_large_font or matches_pattern
            
        except Exception:
            return False
    
    def extract_tables(self, page) -> List[Dict]:
        """
        Extract tables from PDF page
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            List of table data
        """
        tables = []
        
        try:
            # Extract tables using PyMuPDF
            table_data = page.find_tables()
            
            for table in table_data:
                table_text = ""
                table_bbox = table.bbox
                
                # Convert table to text
                for row in table.extract():
                    for cell in row:
                        if cell:
                            table_text += str(cell) + " "
                    table_text += "\n"
                
                if table_text.strip():
                    tables.append({
                        'text': table_text.strip(),
                        'bbox': table_bbox,
                        'block_type': 'table',
                        'rows': len(table.extract()),
                        'columns': len(table.extract()[0]) if table.extract() else 0
                    })
            
            return tables
            
        except Exception as e:
            self.logger.error(f"Error extracting tables: {e}")
            return []
    
    def extract_images_with_text(self, page) -> List[Dict]:
        """
        Extract images and their associated text
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            List of image data with text
        """
        images = []
        
        try:
            # Get image blocks
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                bbox = page.get_image_bbox(img)
                
                # Get text near the image
                nearby_text = self._extract_text_near_bbox(page, bbox)
                
                images.append({
                    'image_index': img_index,
                    'bbox': bbox,
                    'nearby_text': nearby_text,
                    'block_type': 'image'
                })
            
            return images
            
        except Exception as e:
            self.logger.error(f"Error extracting images: {e}")
            return []
    
    def _extract_text_near_bbox(self, page, bbox: Tuple[float, float, float, float], 
                               margin: float = 50.0) -> str:
        """
        Extract text near a bounding box
        
        Args:
            page: PyMuPDF page object
            bbox: Bounding box (x0, y0, x1, y1)
            margin: Margin around bbox to search for text
            
        Returns:
            Text found near the bounding box
        """
        try:
            # Expand bbox with margin
            expanded_bbox = (
                bbox[0] - margin,
                bbox[1] - margin,
                bbox[2] + margin,
                bbox[3] + margin
            )
            
            # Extract text from the expanded area
            text = page.get_text("text", clip=expanded_bbox)
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting text near bbox: {e}")
            return ""
    
    def get_page_metadata(self, page) -> Dict:
        """
        Get page metadata
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            Dictionary with page metadata
        """
        try:
            return {
                'page_number': page.number + 1,
                'width': page.rect.width,
                'height': page.rect.height,
                'rotation': page.rotation,
                'media_box': page.mediabox,
                'crop_box': page.cropbox
            }
        except Exception as e:
            self.logger.error(f"Error getting page metadata: {e}")
            return {} 