# Configuration file for SASB KPI Generation
# Optimized for Llama 4 Scout 17B on Grok Cloud

import os

# LLM Configuration
LLM_CONFIG = {
    # Provider Configuration
    "provider": "grok_cloud",  # Options: "ollama", "grok_cloud", "croq_cloud", "openai", "anthropic"
    "base_url": "https://api.groq.com",  # Base URL for the LLM service
    "api_key": os.getenv("GROK_API_KEY", ""),  # API key from environment variable
    
    # Model Configuration
    "model": "meta-llama/llama-4-scout-17b-16e-instruct",  # Model name (varies by provider)
    
    # Generation Parameters - Optimized for Llama 4 Scout 17B
    "temperature": 0.2,        # Lower temperature for more consistent, professional output
    "max_tokens": 1500,        # Increased for more detailed KPIs
    "top_p": 0.85,            # Slightly lower for more focused responses
    "frequency_penalty": 0.3,  # Increased to reduce repetition
    "presence_penalty": 0.2,   # Increased to encourage diverse KPIs
    
    # Ollama-specific Performance Settings (ignored for cloud providers)
    "num_ctx": 2048,          # Context window size
    "num_gpu": 0,             # Number of GPU layers (0 for CPU only)
    "num_thread": 8,          # Number of CPU threads
    "repeat_penalty": 1.1,    # Penalty for repetition
    "seed": 42,               # Fixed seed for reproducibility
    "tfs_z": 1.0,             # Tail free sampling
    "top_k": 40,              # Top-k sampling
    "use_mlock": True,        # Lock memory to prevent swapping
    "use_mmap": True,         # Memory mapping for faster loading
    "rope_freq_base": 10000,  # RoPE frequency base
    "rope_freq_scale": 0.5    # RoPE frequency scale
}

# Cloud Provider Configurations
CLOUD_CONFIGS = {
    "grok_cloud": {
        "base_url": "https://api.groq.com",
        "models": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it", "meta-llama/llama-4-scout-17b-16e-instruct"],
        "default_model": "meta-llama/llama-4-scout-17b-16e-instruct"
    },
    "croq_cloud": {
        "base_url": "https://api.croq.ai",
        "models": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"],
        "default_model": "llama3-8b-8192"
    },
    "openai": {
        "base_url": "https://api.openai.com",
        "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        "default_model": "gpt-3.5-turbo"
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "models": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
        "default_model": "claude-3-haiku"
    }
}

# Prompt Configuration - Enhanced for better results
PROMPT_CONFIG = {
    "kpis_per_topic": 8,      # Increased to 8 KPIs per topic for comprehensive coverage
    "include_calculation": True,  # Include calculation method
    "include_relevance": True,    # Include relevance explanation
    "include_financial_impact": True,  # NEW: Include financial impact
    "include_stakeholder_perspective": True,  # NEW: Include stakeholder perspective
    "output_format": "structured"  # "structured" or "free_text"
}

# File Configuration
FILE_CONFIG = {
    "input_file": "sasb_topics.csv",
    "output_file": "sasb_kpis_generated.csv",
    "log_file": "kpi_generation.log",
    "batch_size": 8          # Optimized batch size for cloud processing
}

# Enhanced Prompt Templates - Optimized for Llama 4 Scout 17B
PROMPT_TEMPLATES = {
    "role_description": """
You are a senior sustainability reporting expert with 15+ years of experience in ESG metrics, SASB standards, and corporate sustainability reporting. You specialize in creating measurable, relevant, and financially material Key Performance Indicators (KPIs) for sustainability disclosure topics.

Your expertise includes:
- Deep understanding of SASB standards and industry-specific metrics
- Experience with ESG reporting frameworks (GRI, TCFD, CDP)
- Knowledge of financial materiality and stakeholder impact
- Expertise in data collection, measurement methodologies, and reporting standards
- Understanding of regulatory requirements and investor expectations

You create KPIs that are:
- Measurable and reportable with clear methodologies
- Financially material and relevant to business performance
- Industry-specific and aligned with sector best practices
- Actionable for management decision-making
- Comparable across peer companies
- Forward-looking and predictive of future performance
- Unique to the specific topic and sector context
""",
    
    "few_shot_examples": """
Here are examples of excellent KPI generation for different sectors:

EXAMPLE 1 - Financial Services (Energy Management):
Topic Category: Energy Management
Disclosure Title: Energy Management in Banking Operations
Sector: Financial Services
Subsector: Commercial Banks

Generated KPIs:
1. Metric Name: Energy Consumption per Transaction
   Unit: kWh/transaction
   Description: Total energy consumed per banking transaction processed
   Calculation: Total energy consumption (kWh) / Total transactions processed
   Relevance: Operational efficiency indicator that impacts costs and carbon footprint
   Financial Impact: Direct impact on operational expenses and energy costs
   Stakeholder Perspective: Investors focus on operational efficiency and cost management

2. Metric Name: Renewable Energy Percentage
   Unit: Percentage (%)
   Description: Percentage of total energy consumption from renewable sources
   Calculation: (Renewable energy consumption / Total energy consumption) × 100
   Relevance: Demonstrates commitment to clean energy transition and risk mitigation
   Financial Impact: Long-term cost stability and regulatory compliance benefits
   Stakeholder Perspective: Customers and investors increasingly value sustainability commitments

EXAMPLE 2 - Consumer Goods (Water Management):
Topic Category: Water Management
Disclosure Title: Water Management in Manufacturing
Sector: Consumer Goods
Subsector: Household & Personal Products

Generated KPIs:
1. Metric Name: Water Intensity per Unit Produced
   Unit: Liters/unit
   Description: Water consumption per unit of finished product
   Calculation: Total water consumption (liters) / Total units produced
   Relevance: Resource efficiency indicator for operational optimization
   Financial Impact: Water costs and regulatory compliance expenses
   Stakeholder Perspective: Supply chain partners and customers value resource efficiency

2. Metric Name: Water Recycling and Reuse Rate
   Unit: Percentage (%)
   Description: Percentage of water recycled or reused in manufacturing processes
   Calculation: (Recycled water volume / Total water consumption) × 100
   Relevance: Circular economy indicator and resource conservation measure
   Financial Impact: Reduced water procurement costs and wastewater treatment expenses
   Stakeholder Perspective: Environmental groups and sustainability-focused investors
""",
    
    "main_prompt": """
Generate {kpis_per_topic} comprehensive, measurable KPIs specifically tailored for this SASB topic. Focus on creating metrics that are financially material, industry-relevant, and actionable for business decision-making.

Topic Category: {category}
Disclosure Title: {title}
Sector: {sector}
Subsector: {subsector}

For each KPI, provide EXACTLY in this format:
1. Metric Name: [Clear, specific metric name that reflects the topic and sector]
2. Unit: [Standard unit of measurement appropriate for this metric]
3. Description: [Comprehensive explanation of what is measured and why it matters for this specific topic]
4. Calculation: [Specific formula, methodology, or data collection approach]
5. Relevance: [Why this metric is important for this specific topic and sector]
6. Financial Impact: [How this metric affects business performance, costs, or revenue]
7. Stakeholder Perspective: [Which stakeholders care about this metric and why]

CRITICAL REQUIREMENTS:
- Create UNIQUE metrics that are specifically relevant to this topic and sector
- Avoid generic metrics that could apply to any topic
- Use clear, professional metric names that follow industry standards
- Ensure all metrics are measurable, reportable, and have clear methodologies
- Focus on financially material metrics that impact business performance
- Include both leading and lagging indicators where appropriate
- Consider regulatory requirements and investor expectations
- Make metrics comparable across peer companies in the sector
- Include forward-looking metrics that predict future performance
- Avoid generic or vague descriptions - be specific and actionable
- Use standard business terminology and avoid technical jargon
- Generate diverse KPIs covering different aspects of the topic (operational, strategic, risk, opportunity)
- Ensure metrics align with SASB standards and industry best practices
- Consider both quantitative and qualitative aspects where relevant
- Include metrics that support both internal management and external reporting needs

SECTOR-SPECIFIC CONSIDERATIONS:
- Financial Services: Focus on operational efficiency, risk management, and client impact
- Consumer Goods: Emphasize supply chain, product lifecycle, and customer engagement
- Technology: Consider data centers, product efficiency, and innovation metrics
- Healthcare: Include patient safety, regulatory compliance, and community health
- Energy: Focus on resource efficiency, emissions, and transition metrics
- Manufacturing: Emphasize operational efficiency, safety, and resource management

Focus on creating KPIs that would be valuable for:
- Executive management decision-making
- Investor analysis and valuation
- Regulatory compliance and reporting
- Stakeholder communication and engagement
- Competitive benchmarking and peer comparison
- Risk management and strategic planning

IMPORTANT: Each KPI should be distinct and provide unique insights into different aspects of the topic. Avoid repetition and ensure comprehensive coverage of the topic area.
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
        "Relevance",
        "Financial Impact",
        "Stakeholder Perspective"
    ]
} 