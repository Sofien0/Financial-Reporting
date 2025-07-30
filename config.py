# Configuration file for SASB KPI Generation
# Easy to modify parameters

# LLM Configuration
LLM_CONFIG = {
    "model": "llama3.1:8b",  # Better instruction following model
    "temperature": 0.3,        # Lower temperature for more consistent quality
    "max_tokens": 1000,        # Maximum response length
    "top_p": 0.9,             # Nucleus sampling
    "frequency_penalty": 0.1,  # Reduce repetition
    "presence_penalty": 0.1    # Encourage new content
}

# Prompt Configuration
PROMPT_CONFIG = {
    "kpis_per_topic": 5,       # Number of KPIs to generate per topic
    "include_calculation": True,  # Include calculation method
    "include_relevance": True,    # Include relevance explanation
    "output_format": "structured"  # "structured" or "free_text"
}

# File Configuration
FILE_CONFIG = {
    "input_file": "sasb_topics.csv",
    "output_file": "sasb_kpis_generated.csv",
    "log_file": "kpi_generation.log",
    "batch_size": 10           # Process topics in batches
}

# Prompt Templates
PROMPT_TEMPLATES = {
    "role_description": """
You are a sustainability reporting expert with deep knowledge of SASB standards, ESG metrics, and corporate sustainability reporting. You specialize in creating measurable, relevant, and industry-appropriate Key Performance Indicators (KPIs) for sustainability disclosure topics.
""",
    
    "few_shot_examples": """
Here are examples of good KPI generation:

EXAMPLE 1:
Topic Category: Energy Management
Disclosure Title: Energy Management in Manufacturing
Sector: Consumer Goods
Subsector: Building Products & Furnishings

Generated KPIs:
1. Metric Name: Total Energy Consumption
   Unit: MWh/year
   Description: Total energy consumed across all manufacturing facilities
   Calculation: Sum of electricity, natural gas, and other fuel consumption
   Relevance: Direct impact on operational costs and carbon footprint

2. Metric Name: Energy Intensity
   Unit: MWh/unit produced
   Description: Energy consumption per unit of production
   Calculation: Total energy consumption / Total units produced
   Relevance: Efficiency indicator for operational optimization

EXAMPLE 2:
Topic Category: Water Management
Disclosure Title: Water Management
Sector: Consumer Goods
Subsector: Household & Personal Products

Generated KPIs:
1. Metric Name: Total Water Consumption
   Unit: m³/year
   Description: Total water used in manufacturing operations
   Calculation: Sum of water intake from all sources
   Relevance: Resource efficiency and cost management

2. Metric Name: Water Recycling Rate
   Unit: Percentage (%)
   Description: Percentage of water recycled or reused
   Calculation: (Recycled water volume / Total water consumption) × 100
   Relevance: Circular economy and resource conservation
""",
    
    "main_prompt": """
Generate {kpis_per_topic} specific, measurable KPIs for this SASB topic:

Topic Category: {category}
Disclosure Title: {title}
Sector: {sector}
Subsector: {subsector}

For each KPI, provide EXACTLY in this format:
1. Metric Name: [Clear, specific metric name without bold or special formatting]
2. Unit: [Standard unit of measurement]
3. Description: [Brief explanation of what is measured]
4. Calculation: [Specific formula or method to calculate]
5. Relevance: [Why this metric matters for this topic]

Requirements:
- Use clear, professional metric names
- Ensure all metrics are measurable and reportable
- Focus on industry-specific and financially material metrics
- Avoid generic or vague descriptions
- Use standard business terminology
- Do not use bold formatting or special characters
- Keep metric names concise but descriptive
"""
}

# Output Format Configuration
OUTPUT_FORMAT = {
    "columns": [
        "Sector",
        "Subsector", 
        "Topic Category",
        "Disclosure Title",
        "KPI Number",
        "Metric Name",
        "Unit",
        "Description",
        "Calculation",
        "Relevance"
    ]
} 