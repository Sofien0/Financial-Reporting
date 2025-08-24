# Financial-Reporting
This project implements a complete **ESG (Environmental, Social, and Governance) document intelligence system**. It extracts KPIs and themes from ESG reports, scores and merges them, and answers natural language questions through a **Retrieval-Augmented Generation (RAG) pipeline** powered by FAISS, Sentence Transformers, and a local LLM (Mistral via Ollama).

It was developed as part of an internship to demonstrate how ESG disclosures can be transformed into structured data, benchmarked, and made explorable through an AI assistant.

---

## 🚀 Overview

The system is organized around **two complementary methods** for ESG KPI discovery:

- **Method 1 – KPI Extraction:**  
  Regex-based extraction of ESG KPIs (e.g., water, waste, GHG emissions), followed by thematic tagging. This produces a structured table of measurable indicators.

- **Method 2 – Topic-to-KPI Generation:**  
  BERTopic is used to extract ESG themes from company reports by subsector. From these themes, new candidate KPIs are generated, scored for redundancy, and merged with Method 1 outputs.

Both methods are scored and merged into benchmark tables. The unified outputs are then made queryable through a **RAG system**:

- ESG reports are parsed and chunked.
- Chunks are embedded with `sentence-transformers/all-MiniLM-L6-v2` and indexed in FAISS.
- Queries are embedded, the most relevant chunks are retrieved, and a local Mistral LLM (via Ollama) generates grounded answers.
- Answers cite company name, sector, year, page, and source path, ensuring transparency.

At the end of a Q&A session, users can export the results in **PDF, DOCX, or PPTX** with professional formatting.

---

## 📂 Project Structure

- `data/raw/` – Original ESG reports organized by sector → subsector → company.  
- `data/processed/` – Processed text, parsed subsector-level corpora, FAISS index, metadata, generated KPIs, redundancy scores, merged tables.  
- `data/outputs/` – Deliverables (visualizations, exports, validation reports, RAG sessions).  
- `extractors/` – Core pipeline modules:
  - `kpi_extractor.py` – Method 1 KPI extraction.
  - `topic_extractor_bertopic.py` – Method 2 topic modeling.
  - `topic_to_kpi_generator.py` – Generate KPIs from themes.
  - `redundancy_scorer.py` / `method2_redundancy_scorer.py` – Scoring modules.
  - `merge_kpi_scores.py` / `structured_kpi_table_builder.py` – Combine outputs.
  - `question_answering_rag.py` – Interactive ESG RAG interface.
  - `rag_exporter.py` – Export chat sessions to PDF/DOCX/PPTX.
  - `visualizer.py` – KPI coverage and trend visualizations.
  - `matcher/` – Sentence transformer matcher for KPI-to-reference alignment.
- `scrapers/` – Agents used in the very beginning for automated SASB PDF retrieval.  
- `tools/` – Helper scripts (e.g., grouping parsed text by subsector).  
- `tests/` – Unit tests for search and sentence matching.  
- `main.py` – ⚠️ Legacy script used only for initial PDF downloads. Not needed for current workflow, but preserved for reproducibility.

---


🧑‍💻 Usage
Running the ESG RAG Assistant

python -m extractors.question_answering_rag

You’ll see:

💬 ESG RAG Chat Interface (powered by Mistral via Ollama)
Type your ESG question below. Type 'exit' to quit.

Example:

🧠 You: what steps are being taken to lessen water waste?
🤖 Answer:
Aarti Industries Ltd recycles 44% of its water, operates ZLD facilities at 11 of 16 sites,
recovers 50% of steam condensate, and treats effluents before discharge.
(Resource_Transformation/Chemicals/Aarti_Industries_Ltd__2023-2024.pdf, Page 56)

Exporting a Session

After typing exit, you are prompted:

📤 Do you want to export this session? (no / pdf / docx / pptx):

    PDF → Formal report style, blue highlights, bullet-points.

    DOCX → Editable report with styled headings and bullet-points.

    PPTX → Presentation deck with one slide per Q&A, light blue theme, readable fonts.

Files are saved in data/outputs/.
📊 Deliverables

    KPI Extraction (Method 1): Regex + tagging.

    Topic-to-KPI (Method 2): BERTopic themes → KPI generation.

    Scoring: Redundancy scoring across both methods.

    Merged Benchmark: Structured KPI tables combining methods.

    RAG Assistant: Interactive ESG Q&A with metadata citations.

    Exporter: Session export in PDF/DOCX/PPTX with professional formatting.

    Visualizations: KPI coverage heatmaps, sector trends, waste metrics.

    Sample Questions: Curated ESG queries stored in data/processed/generated_questions.csv.

⚠️ Notes on Legacy Components

    main.py – Initial SASB PDF scraper. Not needed unless new raw reports must be fetched.

    topic_extractor_tfidf.py – Early experiment with TF-IDF topic extraction, replaced by BERTopic.

    advanced dynamic extractors – Tested but discarded due to noise and false positives. Regex + semantic matching proved more robust.

These are preserved for reproducibility but not part of the active pipeline.
