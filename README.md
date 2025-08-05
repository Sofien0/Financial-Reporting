# SASB KPI Generator

A comprehensive AI-powered tool for generating Key Performance Indicators (KPIs) based on SASB (Sustainability Accounting Standards Board) topics. This project consists of two main components:

1. **SASB Topics Scraper** - Extracts SASB disclosure topics from the official website
2. **KPI Generator** - Uses advanced language models to create comprehensive, sector-specific KPIs

## 🚀 Features

### SASB Topics Scraper
- **Automated Data Extraction**: Scrapes all SASB disclosure topics from the official website
- **Comprehensive Coverage**: Extracts 448 topics across all sectors and subsectors
- **Structured Output**: Generates clean CSV with sector, subsector, topic category, and disclosure title
- **Error Handling**: Robust scraping with retry logic and error recovery

### KPI Generator
- **AI-Powered Generation**: Uses Grok Cloud's Llama 4 Scout 17B model for high-quality KPI generation
- **Sector-Specific KPIs**: Generates relevant KPIs for different industries and sectors
- **Comprehensive Coverage**: 8 KPIs per topic with detailed metrics including:
  - Metric Name
  - Unit of Measurement
  - Description
  - Calculation Methodology
  - Relevance
  - Financial Impact
  - Stakeholder Perspective
- **Batch Processing**: Efficient processing of multiple topics
- **Real-time Saving**: Immediate saving of generated KPIs to CSV
- **Error Handling**: Robust error handling and retry logic
- **Progress Tracking**: Real-time progress monitoring

## 📋 Requirements

- Python 3.8+
- Grok Cloud API key
- Required Python packages (see `requirements.txt`)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Financial-Reporting
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key**:
   - Edit `src/sasb_kpi_generator/config.py`
   - Replace the `api_key` in `LLM_CONFIG` with your Grok Cloud API key
   - Or set environment variable: `export GROK_API_KEY="your_api_key"`

## 📁 Project Structure

```
Financial-Reporting/
├── src/
│   └── sasb_kpi_generator/
│       ├── __init__.py
│       ├── main.py              # Main KPI generation script
│       ├── config.py            # Configuration settings
│       ├── llm_client.py        # LLM client for API interactions
│       ├── prompt_manager.py    # Prompt engineering and parsing
│       └── data_processor.py    # Data handling and CSV operations
├── scripts/
│   ├── scrape_sasb_topics.py    # SASB topics scraper
│   └── run_scraper.py          # Scraper runner script
├── data/
│   ├── sasb_topics.csv         # Input SASB topics (448 topics)
│   └── sasb_kpis_generated.csv # Output generated KPIs
├── docs/                       # Documentation
├── run.py                      # Main execution script
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## 🎯 Usage

### Step 1: Scrape SASB Topics

First, extract the SASB disclosure topics from the official website:

   ```bash
# Option 1: Run the scraper directly
python scripts/scrape_sasb_topics.py

# Option 2: Use the runner script
python scripts/run_scraper.py
```

This will:
- Scrape all SASB disclosure topics from the official website
- Extract sector, subsector, topic category, and disclosure title
- Save the data to `data/sasb_topics.csv`
- Generate 448 topics across all sectors

### Step 2: Generate KPIs

Once you have the SASB topics, generate comprehensive KPIs:

```bash
# Option 1: Run the main script directly
python src/sasb_kpi_generator/main.py

# Option 2: Use the runner script (recommended)
python run.py
```

This will:
- Load the SASB topics from `data/sasb_topics.csv`
- Generate 8 KPIs per topic using the AI model
- Save results to `data/sasb_kpis_generated.csv`
- Provide real-time progress updates

### Configuration Options

Edit `src/sasb_kpi_generator/config.py` to customize:

- **KPI Count**: Number of KPIs per topic (default: 8)
- **Batch Size**: Processing batch size (default: 8)
- **Model Parameters**: Temperature, max tokens, etc.
- **Output Format**: CSV structure and fields

### Output

The tool generates a CSV file (`data/sasb_kpis_generated.csv`) containing:

| Column | Description |
|--------|-------------|
| Sector | Industry sector |
| Subsector | Industry subsector |
| Topic Category | SASB topic category |
| Disclosure Title | Specific disclosure topic |
| KPI Number | Sequential KPI number |
| Metric Name | KPI metric name |
| Unit | Unit of measurement |
| Description | Detailed description |
| Calculation | Calculation methodology |
| Relevance | Why this KPI matters |
| Financial Impact | Business impact |
| Stakeholder Perspective | Stakeholder relevance |

## 🔧 Configuration

### LLM Settings

```python
LLM_CONFIG = {
    "provider": "grok_cloud",
    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "temperature": 0.2,
    "max_tokens": 1500,
    # ... other settings
}
```

### Prompt Configuration

```python
PROMPT_CONFIG = {
    "kpis_per_topic": 8,
    "include_financial_impact": True,
    "include_stakeholder_perspective": True,
    # ... other settings
}
```

## 📊 Performance

- **Scraping Speed**: ~50 topics/minute
- **Processing Speed**: ~30 topics/minute
- **KPI Generation Rate**: ~21 KPIs/minute
- **Average Response Time**: 4.17 seconds per topic
- **Success Rate**: High quality parsing and generation

## 🔒 Rate Limits

- **Grok Cloud Free Tier**: 500,000 tokens per day
- **Recommended**: Upgrade to paid tier for larger datasets
- **Handling**: System gracefully handles rate limits with retry logic

## 📈 Example Output

Generated KPIs include high-quality metrics such as:

**Financial Services:**
- ESG Integration Rate in Investment Portfolio
- Climate-Related Investment Exposure
- Sustainable Investment Ratio

**Consumer Goods:**
- Hazardous Substance Reduction Rate
- Chemical Disclosure Rate
- Sustainable Material Sourcing Rate

**Technology:**
- Trade Reporting Accuracy Rate
- Market Data Latency
- Order Book Depth

## 🛡️ Error Handling

- **API Failures**: Automatic retry with exponential backoff
- **Rate Limits**: Graceful handling with wait times
- **Parsing Errors**: Robust parsing with fallback methods
- **Data Validation**: Quality checks for generated KPIs
- **Scraping Errors**: Retry logic for network issues

## 🔄 Resuming Generation

The system saves progress in real-time. If interrupted:

1. Check `data/sasb_kpis_generated.csv` for completed topics
2. The system will skip already processed topics
3. Resume with `python run.py`

## 📝 Logging

Comprehensive logging includes:
- Progress tracking
- Error details
- Performance metrics
- Generation statistics
- Scraping progress


**Note**: This tool is designed for sustainability reporting professionals and ESG practitioners. Generated KPIs should be reviewed and validated before use in official reporting.
