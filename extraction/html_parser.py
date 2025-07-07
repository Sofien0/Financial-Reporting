#!/usr/bin/env python3
"""
HTML Parser Module for ESG Report Processing
Handles HTML content extraction and parsing for web-based reports
"""

import logging
from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class HTMLParser:
    """HTML parser for ESG report processing"""
    
    def __init__(self):
        """Initialize HTML parser"""
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def parse_html_content(self, html_content: str) -> Dict:
        """
        Parse HTML content and extract structured data
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Dictionary with parsed content and metadata
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            text_content = self._extract_text_content(soup)
            
            # Extract tables
            tables = self._extract_tables(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup)
            
            return {
                'text_content': text_content,
                'tables': tables,
                'metadata': metadata,
                'soup': soup
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML content: {e}")
            return {}
    
    def _extract_text_content(self, soup) -> List[Dict]:
        """Extract text content from HTML with structure"""
        text_blocks = []
        
        try:
            # Extract headings
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                text_blocks.append({
                    'type': 'heading',
                    'level': int(heading.name[1]),
                    'text': heading.get_text(strip=True),
                    'tag': heading.name
                })
            
            # Extract paragraphs
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 10:  # Filter out short text
                    text_blocks.append({
                        'type': 'paragraph',
                        'text': text,
                        'tag': 'p'
                    })
            
            # Extract list items
            lists = soup.find_all(['ul', 'ol'])
            for lst in lists:
                items = lst.find_all('li')
                for item in items:
                    text = item.get_text(strip=True)
                    if text:
                        text_blocks.append({
                            'type': 'list_item',
                            'text': text,
                            'tag': 'li',
                            'list_type': lst.name
                        })
            
            return text_blocks
            
        except Exception as e:
            self.logger.error(f"Error extracting text content: {e}")
            return []
    
    def _extract_tables(self, soup) -> List[Dict]:
        """Extract tables from HTML"""
        tables = []
        
        try:
            table_elements = soup.find_all('table')
            
            for table in table_elements:
                table_data = {
                    'headers': [],
                    'rows': [],
                    'caption': '',
                    'id': table.get('id', ''),
                    'class': table.get('class', [])
                }
                
                # Extract caption
                caption = table.find('caption')
                if caption:
                    table_data['caption'] = caption.get_text(strip=True)
                
                # Extract headers
                thead = table.find('thead')
                if thead:
                    header_row = thead.find('tr')
                    if header_row:
                        headers = header_row.find_all(['th', 'td'])
                        table_data['headers'] = [h.get_text(strip=True) for h in headers]
                
                # Extract rows
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                else:
                    rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        table_data['rows'].append(row_data)
                
                if table_data['rows']:
                    tables.append(table_data)
            
            return tables
            
        except Exception as e:
            self.logger.error(f"Error extracting tables: {e}")
            return []
    
    def _extract_metadata(self, soup) -> Dict:
        """Extract metadata from HTML"""
        metadata = {}
        
        try:
            # Extract title
            title = soup.find('title')
            if title:
                metadata['title'] = title.get_text(strip=True)
            
            # Extract meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name', meta.get('property', ''))
                content = meta.get('content', '')
                if name and content:
                    metadata[name] = content
            
            # Extract structured data (JSON-LD)
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    metadata['structured_data'] = data
                except:
                    pass
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata: {e}")
            return {}
    
    def fetch_url_content(self, url: str) -> Optional[str]:
        """
        Fetch content from URL
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error fetching URL {url}: {e}")
            return None
    
    def extract_kpi_candidates(self, text_content: List[Dict]) -> List[Dict]:
        """
        Extract potential KPI candidates from text content
        
        Args:
            text_content: List of text blocks
            
        Returns:
            List of potential KPI candidates
        """
        kpi_candidates = []
        
        try:
            # KPI patterns
            kpi_patterns = [
                r'(\d+(?:\.\d+)?)\s*(%|percent|tons?|tonnes?|kWh|MWh|GWh|tCO2e?|CO2e?|USD|EUR|GBP|employees?|people)',
                r'(emissions?|energy|water|waste|renewable|sustainable|carbon|ghg|esg)',
                r'(rate|ratio|percentage|total|number|amount|volume)',
                r'(compliance|certification|audit|inspection|violation)'
            ]
            
            for block in text_content:
                if block['type'] in ['paragraph', 'list_item']:
                    text = block['text']
                    
                    # Look for KPI patterns
                    for pattern in kpi_patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            kpi_candidates.append({
                                'text': match.group(0),
                                'context': text,
                                'block_type': block['type'],
                                'pattern': pattern
                            })
            
            return kpi_candidates
            
        except Exception as e:
            self.logger.error(f"Error extracting KPI candidates: {e}")
            return []
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters but keep important ones
            text = re.sub(r'[^\w\s\.\,\-\+\%\$\€\£\°\()]', '', text)
            
            # Normalize unicode
            import unicodedata
            text = unicodedata.normalize('NFD', text)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {e}")
            return text 