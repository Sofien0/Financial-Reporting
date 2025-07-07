#!/usr/bin/env python3
"""
Main Script for ESG KPI Extraction
Runs the complete extraction pipeline on PDF reports
"""

import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime
from kpi_extractor import KPIExtractor

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'extraction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function to run KPI extraction"""
    parser = argparse.ArgumentParser(description='ESG KPI Extraction Tool')
    
    parser.add_argument(
        '--kpi-definitions',
        type=str,
        default='esg kpis.csv',
        help='Path to KPI definitions CSV file'
    )
    
    parser.add_argument(
        '--data-folder',
        type=str,
        default='../data/reports',
        help='Path to folder containing PDF reports'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='../data/processed',
        help='Output directory for processed results'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    parser.add_argument(
        '--append-master',
        action='store_true',
        help='Append results to master CSV file'
    )
    
    parser.add_argument(
        '--single-pdf',
        type=str,
        help='Process a single PDF file instead of all PDFs in folder'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting ESG KPI Extraction Process")
    logger.info(f"KPI Definitions: {args.kpi_definitions}")
    logger.info(f"Data Folder: {args.data_folder}")
    logger.info(f"Output Directory: {args.output_dir}")
    
    try:
        # Initialize KPI extractor
        extractor = KPIExtractor(
            kpi_csv_path=args.kpi_definitions,
            output_dir=args.output_dir
        )
        
        if args.single_pdf:
            # Process single PDF
            logger.info(f"Processing single PDF: {args.single_pdf}")
            
            # Extract company name and year
            company_name, year = extractor._extract_company_and_year(args.single_pdf)
            
            # Extract KPIs
            results = extractor.extract_kpis_from_pdf(args.single_pdf, company_name, year)
            
            logger.info(f"Extracted {len(results)} KPIs from {args.single_pdf}")
            
        else:
            # Process all PDFs in folder
            logger.info(f"Processing all PDFs in folder: {args.data_folder}")
            results = extractor.process_all_pdfs(args.data_folder)
            
            logger.info(f"Total extracted KPIs: {len(results)}")
        
        if results:
            # Save results
            if args.append_master:
                output_path = extractor.append_to_master_csv(results)
                logger.info(f"Results appended to master CSV: {output_path}")
            else:
                output_path = extractor.save_results_to_csv(results)
                logger.info(f"Results saved to: {output_path}")
            
            # Print summary
            print("\n" + "="*50)
            print("EXTRACTION SUMMARY")
            print("="*50)
            print(f"Total KPIs extracted: {len(results)}")
            print(f"Companies processed: {len(set(r.company for r in results))}")
            print(f"Years covered: {sorted(set(r.year for r in results))}")
            print(f"Extraction methods used: {set(r.extraction_method for r in results)}")
            print(f"Average confidence: {sum(r.confidence for r in results) / len(results):.3f}")
            print("="*50)
            
        else:
            logger.warning("No KPIs were extracted")
            
    except Exception as e:
        logger.error(f"Error in main extraction process: {e}")
        sys.exit(1)
    
    logger.info("ESG KPI Extraction Process completed")

if __name__ == "__main__":
    main() 