import json
import pandas as pd

# Load the extracted data
with open("data/processed/kpi_extraction.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)

# Export to Excel
df.to_excel("data/processed/kpi_extraction.xlsx", index=False)

# Optional: also export to CSV
df.to_csv("data/processed/kpi_extraction.csv", index=False)

print("✅ Export complete: Excel and CSV generated.")
