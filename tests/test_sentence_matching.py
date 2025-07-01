import json
import re
from extractors.matcher.sentence_matcher import match_candidate_sentences

def is_valid_candidate(text):
    """
    Heuristic filter to skip junk sentences:
    - Remove values that are only years, dates, or nonsense
    - Remove sentences with empty/missing values
    """
    if not text or ":" not in text:
        return False

    label, value = map(str.strip, text.split(":", 1))
    
    # Discard if value is empty or placeholder
    if not value or value.lower() in {"n/a", "-", "na", "none"}:
        return False

    # Discard if value looks like a year
    if re.fullmatch(r"20\d{2}", value):
        return False

    # Discard if value is just numbers or garbage
    if re.fullmatch(r"[\d\s,\.%]+", value) and len(value) < 6:
        return False

    # Discard if label or value are too short
    if len(label) < 3 or len(value) < 2:
        return False

    return True

# Load extracted KPI entries
with open("data/processed/kpi_extraction.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Build candidate list from entries
candidates = []
for entry in data:
    company = entry.get("Company", "Unknown Company")
    year = entry.get("Year", "")
    for key, value in entry.items():
        if key in ["Company", "Year"]:
            continue
        sentence = f"{key}: {value}"
        if is_valid_candidate(sentence):
            candidates.append(sentence)

print(f"🔍 Loaded {len(candidates)} clean candidate sentences.")

# Run sentence transformer matching
matches = match_candidate_sentences(
    candidates=candidates,
    excel_path="data/esg kpis A+ critical.xlsx",  # Ground truth file
    lang="en",
    threshold=0.6  # As you tested earlier
)

# Save results
with open("data/processed/kpi_matches.json", "w", encoding="utf-8") as f:
    json.dump(matches, f, indent=2, ensure_ascii=False)

print(f"✅ Matching complete — {len(matches)} matched entries saved to data/processed/kpi_matches.json")
