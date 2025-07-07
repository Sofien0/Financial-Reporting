#!/usr/bin/env python3
"""
Main KPI Extractor Module for ESG Report Processing
Orchestrates the extraction process using PDF parser, HTML parser, and OCR handler
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set
from pathlib import Path
import logging
import re
from dataclasses import dataclass
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import unicodedata
import os
from datetime import datetime

# Import local modules
from pdf_parser import PDFParser
from html_parser import HTMLParser
from ocr_handler import OCRHandler

logger = logging.getLogger(__name__)

@dataclass
class KPIResult:
    """Data class for KPI extraction results"""
    metric_name: str
    value: str
    unit: str
    year: str
    page_number: str
    company: str
    confidence: float
    source_section: str
    extraction_method: str
    context: str
    coordinates: Optional[Tuple[float, float, float, float]] = None
    validation_status: str = "pending"
    timestamp: str = None

class KPIExtractor:
    """Main KPI extractor with layout awareness and multilingual support"""
    
    def __init__(self, kpi_csv_path: str, output_dir: str = "data/processed"):
        """
        Initialize KPI extractor
        
        Args:
            kpi_csv_path: Path to CSV file containing KPI definitions
            output_dir: Directory to save processed results
        """
        self.kpi_csv_path = kpi_csv_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.pdf_parser = PDFParser()
        self.html_parser = HTMLParser()
        self.ocr_handler = OCRHandler()
        
        # Load KPI definitions
        self.kpi_definitions = self._load_kpi_definitions()
        
        # Initialize semantic model
        self.sentence_model = None
        self._initialize_semantic_model()
        
        # Unit validation patterns
        self.unit_patterns = self._initialize_unit_patterns()
        
        # SASB metric codes pattern
        self.sasb_code_pattern = re.compile(r'[A-Z]{2}-[A-Z]{2}-\d{3}[a-z]?\.?\d*')
        
        logger.info(f"KPI Extractor initialized with {len(self.kpi_definitions)} KPI definitions")
    
    def _load_kpi_definitions(self) -> List[Dict]:
        """Load KPI definitions from CSV file with enhanced metadata"""
        try:
            df = pd.read_csv(self.kpi_csv_path, sep=';')
            
            kpi_definitions = []
            for _, row in df.iterrows():
                # Extract expected units from KPI name and topic
                expected_units = self._extract_expected_units(row['kpi_name'], row.get('topic', ''))
                
                kpi_definitions.append({
                    'metric_name': row['kpi_name'],
                    'metric_name_fr': row.get('kpi_name_fr', ''),
                    'topic': row.get('topic', ''),
                    'topic_fr': row.get('topic_fr', ''),
                    'category': row.get('source', ''),
                    'priority': row.get('score', 'C - Low'),
                    'expected_units': expected_units,
                    'keywords': self._extract_keywords(row['kpi_name']),
                    'keywords_fr': self._extract_keywords(row.get('kpi_name_fr', '')),
                    'variations': self._generate_variations(row['kpi_name']),
                    'value_ranges': self._get_value_ranges(row['kpi_name'])
                })
            
            return kpi_definitions
            
        except Exception as e:
            logger.error(f"Error loading KPI definitions: {e}")
            return []
    
    def _extract_expected_units(self, kpi_name: str, topic: str) -> Set[str]:
        """Extract expected units from KPI name and topic"""
        units = set()
        
        # Common unit patterns
        unit_patterns = {
            'emissions': {'tons', 'tonnes', 'tCO2e', 'tCO2', 'CO2e', 'metric tons', 'kg', 'g'},
            'energy': {'kWh', 'MWh', 'GWh', 'TJ', 'GJ', 'BTU'},
            'water': {'m3', 'litres', 'gallons', 'cubic meters', 'L', 'gal'},
            'percentage': {'%', 'percent', 'percentage'},
            'currency': {'USD', 'EUR', 'GBP', 'CAD', '$', '€', '£'},
            'people': {'employees', 'people', 'workers', 'personnel'},
            'incidents': {'incidents', 'breaches', 'violations', 'cases'},
            'time': {'days', 'hours', 'minutes', 'years'}
        }
        
        text_lower = (kpi_name + ' ' + topic).lower()
        
        for category, unit_set in unit_patterns.items():
            if any(keyword in text_lower for keyword in category.split()):
                units.update(unit_set)
        
        return units
    
    def _get_value_ranges(self, kpi_name: str) -> Dict[str, Tuple[float, float]]:
        """Get expected value ranges for different KPI types"""
        ranges = {
            'emissions': (0, 1000000),  # 0 to 1M tons
            'energy': (0, 1000000),     # 0 to 1M kWh
            'water': (0, 1000000),      # 0 to 1M m3
            'percentage': (0, 100),     # 0-100%
            'currency': (0, 1000000000), # 0 to 1B currency
            'people': (0, 1000000),     # 0 to 1M people
            'temperature': (-50, 100),  # -50 to 100°C
            'time': (0, 10000)          # 0 to 10K days
        }
        
        text_lower = kpi_name.lower()
        
        if any(word in text_lower for word in ['emission', 'ghg', 'co2', 'carbon']):
            return {'emissions': ranges['emissions']}
        elif any(word in text_lower for word in ['energy', 'kwh', 'mwh', 'power']):
            return {'energy': ranges['energy']}
        elif any(word in text_lower for word in ['water', 'wastewater', 'consumption']):
            return {'water': ranges['water']}
        elif any(word in text_lower for word in ['rate', 'percentage', 'percent', '%']):
            return {'percentage': ranges['percentage']}
        elif any(word in text_lower for word in ['cost', 'expense', 'revenue', 'usd', 'eur']):
            return {'currency': ranges['currency']}
        elif any(word in text_lower for word in ['employee', 'worker', 'people', 'personnel']):
            return {'people': ranges['people']}
        elif any(word in text_lower for word in ['temperature', '°c', 'celsius']):
            return {'temperature': ranges['temperature']}
        elif any(word in text_lower for word in ['day', 'hour', 'time', 'duration']):
            return {'time': ranges['time']}
        
        return {}
    
    def _initialize_unit_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize regex patterns for unit extraction"""
        return {
            'emissions': re.compile(r'\b(tons?|tonnes?|tCO2e?|CO2e?|metric\s+tons?|kg|g)\b', re.IGNORECASE),
            'energy': re.compile(r'\b(kWh|MWh|GWh|TJ|GJ|BTU)\b', re.IGNORECASE),
            'water': re.compile(r'\b(m3?|litres?|gallons?|cubic\s+meters?|L|gal)\b', re.IGNORECASE),
            'percentage': re.compile(r'\b(%|percent|percentage)\b', re.IGNORECASE),
            'currency': re.compile(r'\b(USD|EUR|GBP|CAD|\$|€|£)\b', re.IGNORECASE),
            'people': re.compile(r'\b(employees?|people|workers?|personnel)\b', re.IGNORECASE),
            'time': re.compile(r'\b(days?|hours?|minutes?|years?)\b', re.IGNORECASE)
        }
    
    def _extract_keywords(self, metric_name: str) -> List[str]:
        """Extract keywords from metric name"""
        # Remove common words and extract key terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'rate', 'total', 'number', 'percentage', 'per', 'per', 'de', 'la', 'le', 'les', 'du', 'des'
        }
        
        # Normalize unicode characters
        normalized = unicodedata.normalize('NFD', metric_name.lower())
        words = re.findall(r'\b\w+\b', normalized)
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _generate_variations(self, metric_name: str) -> List[str]:
        """Generate variations of the metric name for better matching"""
        variations = [metric_name]
        
        # Common variations
        if 'emissions' in metric_name.lower():
            variations.extend([
                metric_name.replace('Emissions', 'emissions'),
                metric_name.replace('Emissions', 'emission'),
                metric_name.replace('GHG', 'greenhouse gas'),
                metric_name.replace('greenhouse gas', 'GHG')
            ])
        
        if 'rate' in metric_name.lower():
            variations.extend([
                metric_name.replace('Rate', 'rate'),
                metric_name.replace('Rate', 'ratio'),
                metric_name.replace('Rate', 'percentage')
            ])
        
        if 'total' in metric_name.lower():
            variations.extend([
                metric_name.replace('Total', 'total'),
                metric_name.replace('Total', 'overall'),
                metric_name.replace('Total', 'sum')
            ])
        
        return list(set(variations))  # Remove duplicates
    
    def _initialize_semantic_model(self):
        """Initialize sentence transformer for semantic similarity"""
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Semantic model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing semantic model: {e}")
    
    def extract_kpis_from_pdf(self, pdf_path: str, company_name: str, year: str) -> List[KPIResult]:
        """
        Extract KPIs from PDF using multiple extraction methods
        
        Args:
            pdf_path: Path to PDF file
            company_name: Name of the company
            year: Year of the report
            
        Returns:
            List of extracted KPI results
        """
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Method 1: Extract from text blocks
                text_blocks = self.pdf_parser.extract_text_blocks_with_coordinates(page)
                text_results = self._extract_kpis_from_text_blocks(
                    text_blocks, company_name, year, page_num + 1
                )
                results.extend(text_results)
                
                # Method 2: Extract from tables
                tables = self.pdf_parser.extract_tables(page)
                table_results = self._extract_kpis_from_tables(
                    tables, company_name, year, page_num + 1
                )
                results.extend(table_results)
                
                # Method 3: Extract from images using OCR
                images = self.ocr_handler.extract_images_from_pdf(pdf_path)
                for img_data in images:
                    if img_data['page_num'] == page_num + 1:
                        ocr_result = self.ocr_handler.process_image_with_ocr(img_data)
                        if self.ocr_handler.validate_ocr_result(ocr_result):
                            ocr_kpis = self.ocr_handler.extract_kpi_from_ocr_text(
                                ocr_result['text'], f"Page {page_num + 1}"
                            )
                            for kpi in ocr_kpis:
                                results.append(KPIResult(
                                    metric_name="OCR_Extracted",
                                    value=kpi['value'],
                                    unit=kpi['unit'],
                                    year=year,
                                    page_number=str(page_num + 1),
                                    company=company_name,
                                    confidence=ocr_result['confidence'],
                                    source_section="Image/Chart",
                                    extraction_method="OCR",
                                    context=kpi['context'],
                                    coordinates=ocr_result['bbox']
                                ))
            
            doc.close()
            
            # Post-process results
            results = self._postprocess_results(results)
            
            logger.info(f"Extracted {len(results)} KPI results from PDF: {pdf_path}")
            return results
            
        except Exception as e:
            logger.error(f"Error extracting KPIs from PDF {pdf_path}: {e}")
            return []
    
    def _extract_kpis_from_text_blocks(self, text_blocks: List[Dict], company_name: str, year: str, page_num: int) -> List[KPIResult]:
        """Extract KPIs from text blocks with layout awareness"""
        results = []
        
        for block in text_blocks:
            text = block['text']
            bbox = block['bbox']
            
            # Method 1: SASB code matching
            sasb_codes = self.sasb_code_pattern.findall(text)
            if sasb_codes:
                sasb_results = self._extract_kpis_by_sasb_codes(text, sasb_codes, company_name, year, page_num, bbox)
                results.extend(sasb_results)
            
            # Method 2: Semantic matching
            semantic_results = self._semantic_kpi_matching(text, company_name, year, page_num, bbox)
            results.extend(semantic_results)
            
            # Method 3: Keyword matching
            keyword_results = self._keyword_kpi_matching(text, company_name, year, page_num, bbox)
            results.extend(keyword_results)
        
        return results
    
    def _extract_kpis_by_sasb_codes(self, text: str, sasb_codes: List[str], company_name: str, year: str, page_num: int, bbox: Tuple) -> List[KPIResult]:
        """Extract KPIs using SASB metric codes"""
        results = []
        
        for code in sasb_codes:
            kpi_def = self._find_kpi_by_sasb_code(code)
            if kpi_def:
                value_data = self._extract_value_near_code(text, code, kpi_def)
                if value_data:
                    results.append(KPIResult(
                        metric_name=kpi_def['metric_name'],
                        value=value_data['value'],
                        unit=value_data['unit'],
                        year=year,
                        page_number=str(page_num),
                        company=company_name,
                        confidence=0.9,  # High confidence for SASB codes
                        source_section=self._identify_source_section(text),
                        extraction_method="SASB_Code",
                        context=text,
                        coordinates=bbox
                    ))
        
        return results
    
    def _find_kpi_by_sasb_code(self, sasb_code: str) -> Optional[Dict]:
        """Find KPI definition by SASB code"""
        # This would need to be implemented based on your SASB code mapping
        # For now, return None
        return None
    
    def _extract_value_near_code(self, text: str, code: str, kpi_def: Dict) -> Optional[Dict]:
        """Extract value near a SASB code"""
        try:
            # Look for numbers near the code
            code_pos = text.find(code)
            if code_pos == -1:
                return None
            
            # Search for numbers in the vicinity
            start = max(0, code_pos - 100)
            end = min(len(text), code_pos + 100)
            vicinity = text[start:end]
            
            # Find numbers with units
            number_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(%|tons?|kWh|USD|EUR|GBP|employees?|people)?'
            matches = re.findall(number_pattern, vicinity)
            
            if matches:
                value, unit = matches[0]
                return {
                    'value': value,
                    'unit': unit if unit else ''
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting value near code: {e}")
            return None
    
    def _semantic_kpi_matching(self, text: str, company_name: str, year: str, page_num: int, bbox: Tuple, threshold: float = 0.6) -> List[KPIResult]:
        """Extract KPIs using semantic similarity"""
        results = []
        
        if not self.sentence_model:
            return results
        
        try:
            # Encode the text
            text_embedding = self.sentence_model.encode([text])
            
            for kpi_def in self.kpi_definitions:
                # Encode KPI variations
                kpi_texts = [kpi_def['metric_name']] + kpi_def['variations']
                kpi_embeddings = self.sentence_model.encode(kpi_texts)
                
                # Calculate similarities
                similarities = cosine_similarity(text_embedding, kpi_embeddings)[0]
                max_similarity = max(similarities)
                
                if max_similarity >= threshold:
                    # Extract value
                    value_data = self._extract_value_with_validation(text, kpi_def)
                    if value_data:
                        results.append(KPIResult(
                            metric_name=kpi_def['metric_name'],
                            value=value_data['value'],
                            unit=value_data['unit'],
                            year=year,
                            page_number=str(page_num),
                            company=company_name,
                            confidence=max_similarity,
                            source_section=self._identify_source_section(text),
                            extraction_method="Semantic",
                            context=text,
                            coordinates=bbox
                        ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic KPI matching: {e}")
            return results
    
    def _keyword_kpi_matching(self, text: str, company_name: str, year: str, page_num: int, bbox: Tuple) -> List[KPIResult]:
        """Extract KPIs using keyword matching"""
        results = []
        
        for kpi_def in self.kpi_definitions:
            # Check if any keywords match
            text_lower = text.lower()
            keyword_matches = sum(1 for keyword in kpi_def['keywords'] if keyword.lower() in text_lower)
            
            if keyword_matches >= 2:  # At least 2 keywords must match
                # Extract value
                value_data = self._extract_value_with_validation(text, kpi_def)
                if value_data:
                    confidence = min(0.8, keyword_matches * 0.2)  # Cap at 0.8
                    results.append(KPIResult(
                        metric_name=kpi_def['metric_name'],
                        value=value_data['value'],
                        unit=value_data['unit'],
                        year=year,
                        page_number=str(page_num),
                        company=company_name,
                        confidence=confidence,
                        source_section=self._identify_source_section(text),
                        extraction_method="Keyword",
                        context=text,
                        coordinates=bbox
                    ))
        
        return results
    
    def _extract_value_with_validation(self, text: str, kpi_def: Dict) -> Optional[Dict]:
        """Extract and validate value from text"""
        try:
            # Look for numbers with units
            for unit_type, pattern in self.unit_patterns.items():
                matches = pattern.findall(text)
                if matches:
                    # Find the number before the unit
                    for match in matches:
                        # Look for number before the unit
                        before_unit = text[:text.find(match)].strip()
                        number_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*$', before_unit)
                        
                        if number_match:
                            value = number_match.group(1)
                            if self._validate_value(value, match, kpi_def):
                                return {
                                    'value': value,
                                    'unit': match
                                }
            
            # Look for percentages
            percent_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
            if percent_matches:
                value = percent_matches[0]
                if self._validate_value(value, '%', kpi_def):
                    return {
                        'value': value,
                        'unit': '%'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting value with validation: {e}")
            return None
    
    def _validate_value(self, value: str, unit: str, kpi_def: Dict) -> bool:
        """Validate extracted value"""
        try:
            # Convert value to float
            value_float = float(value.replace(',', ''))
            
            # Check against expected ranges
            for range_type, (min_val, max_val) in kpi_def['value_ranges'].items():
                if min_val <= value_float <= max_val:
                    return True
            
            # If no specific range, do basic validation
            if value_float >= 0 and value_float < 1e12:  # Reasonable range
                return True
            
            return False
            
        except (ValueError, TypeError):
            return False
    
    def _identify_source_section(self, text: str) -> str:
        """Identify the source section from text"""
        text_lower = text.lower()
        
        section_keywords = {
            'environmental': ['environment', 'emissions', 'carbon', 'energy', 'water', 'waste'],
            'social': ['social', 'employee', 'community', 'human rights', 'labor'],
            'governance': ['governance', 'board', 'ethics', 'compliance', 'risk'],
            'financial': ['financial', 'revenue', 'profit', 'cost', 'investment']
        }
        
        for section, keywords in section_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return section.title()
        
        return "General"
    
    def _extract_kpis_from_tables(self, tables: List[Dict], company_name: str, year: str, page_num: int) -> List[KPIResult]:
        """Extract KPIs from tables"""
        results = []
        
        for table in tables:
            table_text = table['text']
            bbox = table['bbox']
            
            # Process table text similar to regular text
            table_results = self._extract_kpis_from_text_blocks(
                [{'text': table_text, 'bbox': bbox}], company_name, year, page_num
            )
            
            # Mark as table extraction
            for result in table_results:
                result.extraction_method = "Table_" + result.extraction_method
                result.source_section = "Table"
            
            results.extend(table_results)
        
        return results
    
    def _postprocess_results(self, results: List[KPIResult]) -> List[KPIResult]:
        """Post-process and validate results"""
        # Add timestamps
        timestamp = datetime.now().isoformat()
        for result in results:
            result.timestamp = timestamp
        
        # Validate results
        results = self._validate_results(results)
        
        # Deduplicate results
        results = self._deduplicate_results(results)
        
        return results
    
    def _validate_results(self, results: List[KPIResult]) -> List[KPIResult]:
        """Validate and filter results"""
        valid_results = []
        
        for result in results:
            if self._additional_validation(result):
                result.validation_status = "validated"
                valid_results.append(result)
            else:
                result.validation_status = "rejected"
        
        return valid_results
    
    def _additional_validation(self, result: KPIResult) -> bool:
        """Additional validation rules"""
        try:
            # Check if value is numeric
            value_clean = result.value.replace(',', '').replace('%', '')
            float(value_clean)
            
            # Check confidence threshold
            if result.confidence < 0.3:
                return False
            
            # Check for reasonable text length
            if len(result.context) < 10:
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def _deduplicate_results(self, results: List[KPIResult]) -> List[KPIResult]:
        """Remove duplicate results"""
        seen = set()
        unique_results = []
        
        for result in results:
            # Create a unique key
            key = (result.metric_name, result.value, result.unit, result.company, result.year)
            
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
    
    def process_all_pdfs(self, data_folder: str) -> List[KPIResult]:
        """
        Process all PDFs in the data folder
        
        Args:
            data_folder: Path to folder containing PDFs
            
        Returns:
            List of all extracted KPI results
        """
        all_results = []
        data_path = Path(data_folder)
        
        # Find all PDF files recursively
        pdf_files = list(data_path.rglob("*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_path in pdf_files:
            try:
                # Extract company name and year from file path
                company_name, year = self._extract_company_and_year(str(pdf_path))
                
                # Extract KPIs from PDF
                results = self.extract_kpis_from_pdf(str(pdf_path), company_name, year)
                
                all_results.extend(results)
                
                logger.info(f"Extracted {len(results)} KPIs from {pdf_path}")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                continue
        
        return all_results
    
    def _extract_company_and_year(self, pdf_path: str) -> Tuple[str, str]:
        """Extract company name and year from PDF file path"""
        try:
            # Try to extract year from filename
            year_match = re.search(r'(\d{4})', pdf_path)
            year = year_match.group(1) if year_match else "Unknown"
            
            # Extract company name from filename
            filename = Path(pdf_path).stem
            company_name = filename.split('_')[0] if '_' in filename else filename
            
            # If company name is too generic, try to get it from folder structure
            if len(company_name) < 3:
                path_parts = Path(pdf_path).parts
                for part in reversed(path_parts[:-1]):
                    if len(part) > 3 and not part.isdigit():
                        company_name = part
                        break
            
            return company_name, year
            
        except Exception as e:
            logger.error(f"Error extracting company and year from {pdf_path}: {e}")
            return "Unknown", "Unknown"
    
    def save_results_to_csv(self, results: List[KPIResult], output_filename: str = None):
        """
        Save results to CSV file
        
        Args:
            results: List of KPI results
            output_filename: Optional custom filename
        """
        try:
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"kpi_extraction_results_{timestamp}.csv"
            
            output_path = self.output_dir / output_filename
            
            # Convert results to DataFrame
            data = []
            for result in results:
                data.append({
                    'metric_name': result.metric_name,
                    'value': result.value,
                    'unit': result.unit,
                    'year': result.year,
                    'page_number': result.page_number,
                    'company': result.company,
                    'confidence': result.confidence,
                    'source_section': result.source_section,
                    'extraction_method': result.extraction_method,
                    'context': result.context,
                    'validation_status': result.validation_status,
                    'timestamp': result.timestamp
                })
            
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            
            logger.info(f"Results saved to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error saving results to CSV: {e}")
            return None
    
    def append_to_master_csv(self, results: List[KPIResult]):
        """
        Append results to master CSV file
        
        Args:
            results: List of KPI results to append
        """
        try:
            master_csv_path = self.output_dir / "master_kpi_extraction.csv"
            
            # Convert results to DataFrame
            data = []
            for result in results:
                data.append({
                    'metric_name': result.metric_name,
                    'value': result.value,
                    'unit': result.unit,
                    'year': result.year,
                    'page_number': result.page_number,
                    'company': result.company,
                    'confidence': result.confidence,
                    'source_section': result.source_section,
                    'extraction_method': result.extraction_method,
                    'context': result.context,
                    'validation_status': result.validation_status,
                    'timestamp': result.timestamp
                })
            
            new_df = pd.DataFrame(data)
            
            if master_csv_path.exists():
                # Append to existing file
                existing_df = pd.read_csv(master_csv_path)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_csv(master_csv_path, index=False)
                logger.info(f"Appended {len(results)} results to master CSV")
            else:
                # Create new file
                new_df.to_csv(master_csv_path, index=False)
                logger.info(f"Created master CSV with {len(results)} results")
            
            return str(master_csv_path)
            
        except Exception as e:
            logger.error(f"Error appending to master CSV: {e}")
            return None 