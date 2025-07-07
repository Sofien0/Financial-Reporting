import re

def clean_sentence(sentence):
    """
    Keep sentences that include at least:
    - one digit
    - a colon separating KPI name and value
    - a meaningful value
    """
    sentence = sentence.strip()
    if not sentence or ":" not in sentence:
        return ""

    # Remove stray control characters, normalize spaces
    sentence = re.sub(r"[^\x20-\x7E]", "", sentence)
    sentence = re.sub(r"\s+", " ", sentence)

    # Keep only if it contains some digits
    if not re.search(r"\d", sentence):
        return ""

    # Basic check: sentence should contain pattern like "KPI: value"
    kpi_part, _, value_part = sentence.partition(":")
    if not kpi_part.strip() or not value_part.strip():
        return ""

    return sentence
