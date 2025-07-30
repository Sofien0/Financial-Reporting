# SASB KPI Generator

A comprehensive system for generating Key Performance Indicators (KPIs) from SASB (Sustainability Accounting Standards Board) topics using advanced LLM technology.

## 🎯 What This Does

This system takes your existing SASB topics (from `sasb_topics.csv`) and generates relevant, measurable KPIs for each topic using a hybrid approach combining:
- **Role-based prompting** (sustainability expert role)
- **Few-shot learning** (examples of good KPIs)
- **Advanced LLM** (Llama 3.1 70B model)

## 📁 Project Structure

```
Financial-Reporting/
├── config.py              # Easy-to-modify configuration
├── llm_client.py          # LLM communication module
├── prompt_manager.py      # Prompt construction and parsing
├── data_processor.py      # CSV handling and data management
├── main.py               # Main execution script
├── setup_ollama.py       # Ollama installation helper
├── requirements.txt      # Python dependencies
├── sasb_topics.csv       # Your existing topics data
└── README.md            # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Ollama (LLM)
```bash
python setup_ollama.py
```

### 3. Run KPI Generation
```bash
python main.py
```

## ⚙️ Configuration

All settings are easily modifiable in `config.py`:

### LLM Settings
```python
LLM_CONFIG = {
    "model": "llama3.1:70b",  # Change model here
    "temperature": 0.7,        # Creativity level (0.0-1.0)
    "max_tokens": 1000,        # Response length
}
```

### Prompt Settings
```python
PROMPT_CONFIG = {
    "kpis_per_topic": 5,       # Number of KPIs per topic
    "include_calculation": True,  # Include calculation methods
    "include_relevance": True,    # Include relevance explanations
}
```

### File Settings
```python
FILE_CONFIG = {
    "input_file": "sasb_topics.csv",
    "output_file": "sasb_kpis_generated.csv",
    "batch_size": 10           # Process in batches
}
```

## 📊 Output Format

The system generates a CSV file with the following columns:
- **Sector** - Industry sector
- **Subsector** - Industry subsector  
- **Topic Category** - SASB topic category
- **Disclosure Title** - Topic title
- **KPI Number** - Sequential KPI number
- **Metric Name** - Name of the KPI
- **Unit** - Unit of measurement
- **Description** - What the metric measures
- **Calculation** - How to calculate it
- **Relevance** - Why it matters

## 🔧 Customization

### Change Model
Edit `config.py`:
```python
LLM_CONFIG = {
    "model": "llama3.1:8b",  # Faster, less accurate
    # or
    "model": "llama3.1:70b", # Slower, more accurate
}
```

### Modify Prompts
Edit the prompt templates in `config.py`:
```python
PROMPT_TEMPLATES = {
    "role_description": "Your custom role description...",
    "few_shot_examples": "Your custom examples...",
    "main_prompt": "Your custom prompt template..."
}
```

### Adjust Batch Processing
```python
FILE_CONFIG = {
    "batch_size": 5,  # Smaller batches for slower processing
    # or
    "batch_size": 20, # Larger batches for faster processing
}
```

## 📈 Features

- ✅ **Resume Capability** - Continues from where it left off
- ✅ **Batch Processing** - Processes topics in manageable chunks
- ✅ **Error Handling** - Robust error recovery and logging
- ✅ **Progress Tracking** - Real-time progress updates
- ✅ **Quality Validation** - Validates generated KPIs
- ✅ **Flexible Configuration** - Easy parameter modification

## 🛠️ Troubleshooting

### Ollama Not Running
```bash
# Start Ollama service
ollama serve

# Check if running
ollama list
```

### Model Not Available
```bash
# Download the model
ollama pull llama3.1:70b

# Check available models
ollama list
```

### Memory Issues
If you encounter memory issues with 70B model:
1. Use the 8B model instead: `"model": "llama3.1:8b"`
2. Reduce batch size: `"batch_size": 5`
3. Close other applications to free RAM

## 📝 Logging

The system creates detailed logs in `kpi_generation.log`:
- Processing progress
- Error messages
- Performance statistics
- Generated KPI counts

## 🎯 Example Output

```
Sector,Subsector,Topic Category,Disclosure Title,KPI Number,Metric Name,Unit,Description,Calculation,Relevance
Consumer Goods,Apparel Accessories & Footwear,Product Quality & Safety,Management of Chemicals in Products,1,Chemical Compliance Rate,Percentage,Percentage of products meeting chemical safety standards,Compliant products / Total products × 100,Ensures regulatory compliance and reduces liability risks
Consumer Goods,Apparel Accessories & Footwear,Product Quality & Safety,Management of Chemicals in Products,2,Chemical Testing Frequency,Number per year,Number of chemical safety tests conducted annually,Sum of all chemical tests across product lines,Monitors product safety and maintains quality standards
```

## 🔄 Resume Processing

If the process is interrupted, simply run `python main.py` again. The system will:
- Detect already processed topics
- Skip them automatically
- Continue with remaining topics

## 📞 Support

For issues or questions:
1. Check the log file: `kpi_generation.log`
2. Verify Ollama is running: `ollama list`
3. Ensure your CSV file is properly formatted
4. Check available system memory (16GB+ recommended for 70B model)
