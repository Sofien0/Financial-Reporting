from sentence_transformers import SentenceTransformer, util
from extractors.matcher.kpi_reference_loader import load_kpi_targets, encode_kpis

def match_candidate_sentences(candidates, excel_path, lang="en", threshold=0.75):
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Load and encode KPI targets
    kpi_labels = load_kpi_targets(excel_path, lang=lang)
    kpi_embeddings = encode_kpis(kpi_labels, model)

    # Encode the candidate sentences
    candidate_embeddings = model.encode(candidates, convert_to_tensor=True)

    # Perform cosine similarity matching
    matches = []
    for i, candidate in enumerate(candidates):
        similarities = util.cos_sim(candidate_embeddings[i], kpi_embeddings)[0]
        best_score = similarities.max().item()
        best_idx = similarities.argmax().item()

        if best_score >= threshold:
            matches.append({
                "candidate": candidate,
                "matched_kpi": kpi_labels[best_idx],
                "score": round(best_score, 4)
            })
        else:
            print(f"⚠️ No match: '{candidate}' → best score = {round(best_score, 4)}")

    return matches