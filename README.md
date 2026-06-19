# 🧠 Mental Health Support Chatbot

A RAG-based mental health support chatbot built with Gemini 2.5 Flash, ChromaDB, and FastAPI. The chatbot provides empathetic responses grounded in clinical mental health literature, with built-in crisis detection and safety guardrails.

> ⚠️ **Disclaimer:** This chatbot is not a substitute for professional mental health care. If you are in crisis, please contact iCall at 9152987821 or Vandrevala Foundation at 1860-2662-345 (24/7).

---

## 🌐 Live Demo

- **Frontend:** https://mental-health-chatbot-sooty.vercel.app
- **Backend API:** https://mindcare-ai-backend-4wgx.onrender.com
- **API Docs:** https://mindcare-ai-backend-4wgx.onrender.com/docs

## 📊 Evaluation Scores

Evaluated using a Groq LLaMA 3.3 70B judge across 10 standardized mental health questions:

| Metric | Score | Target |
|---|---|---|
| Faithfulness | 0.81 | > 0.80 |
| Answer Relevancy | 0.88 | > 0.80 |
| Context Recall | 0.81 | > 0.70 |
| **Overall** | **0.83** | **> 0.80** |

> Independent LLM evaluation used to avoid self-evaluation bias.

---

## 🏗️ Architecture

```
User → Crisis Detection → Query Rewriting → Hybrid Search
     → ChromaDB → Prompt Builder → Gemini 2.5 Flash → Response
```

See [architecture.md](./architecture.md) for detailed flow diagrams.

---

## ✨ Features

- **RAG Pipeline** — answers grounded in 8 clinical PDFs, 330+ document chunksdocument chunks
- **Hybrid Search** — combines semantic similarity (70%) and BM25 keyword search (30%)
- **Crisis Detection** — intercepts harmful messages and returns emergency helplines before RAG runs
- **Query Rewriting** — rewrites vague follow-up questions using conversation history for better retrieval
- **Conversation Memory** — maintains last 5 exchanges as context
- **Source Citations** — every response includes which document it came from
- **FastAPI Backend** — REST API with Pydantic validation, rate limiting, and request logging
- **Fault Tolerant Embedding** — resumes from checkpoint if embedding pipeline fails

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Gemini 2.5 Flash |
| Embeddings | Gemini Embedding 001 |
| Vector Database | ChromaDB |
| Keyword Search | BM25 (rank-bm25) |
| Backend | FastAPI + Uvicorn |
| Evaluation | Groq LLaMA 3.3 70B (cross-model judge) |
| PDF Processing | pdfplumber |

---

## 📚 Knowledge Base

| Document | Topics Covered |
|---|---|
| CBT Workshop Booklet | CBT techniques, thought challenging, STOPP |
| Anxiety Management Package | Anxiety symptoms, panic attacks, coping strategies |
| Beginner's Guide to Mindfulness | Mindfulness practices, meditation, present moment |
| Psychological Self-Help Interventions | Depression, Step-by-Step program, stress |
| Mindfulness & Depression Guide | MBCT, mindfulness for depression specifically |
| WHO Preventing Suicide | Crisis support, warning signs, risk factors |
| Stress Management Guide | Stress reduction, relaxation techniques |

---

## 🔒 Safety Design

Safety was a first-class concern in this project:

1. **Crisis Detection** — keyword and pattern matching scans every message before RAG runs. Crisis messages immediately return emergency helplines without LLM involvement.
2. **No Diagnosis** — system prompt explicitly prohibits any diagnostic language.
3. **Professional Referral** — every response includes a reminder to seek professional help.
4. **Source Grounding** — faithfulness evaluation ensures answers stick to retrieved content.
5. **Disclaimer** — prominent disclaimer displayed on every response.

---

## 📁 Project Structure

```
mental-health-chatbot/
├── data/                      # Knowledge base documents
├── evaluation/
│   ├── evaluate.py            # Custom LLM-based evaluation
│   ├── test_dataset.json      # 10 standardized test questions
│   └── results.json           # Evaluation scores
├── src/
│   ├── main.py                # FastAPI application
│   ├── rag_pipeline.py        # Core RAG logic
│   ├── hybrid_search.py       # BM25 + semantic search
│   ├── retrieval_tester.py    # 20-question retrieval test
│   ├── pdf_loader.py          # PDF + TXT document loader
│   └── embed_and_store_v2.py  # Embedding pipeline
├── .env.example               # Environment variables template
├── architecture.md            # System architecture diagrams
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Run

### 1. Clone and install

```bash
git clone https://github.com/Divyeshb3/mental-health-chatbot
cd mental-health-chatbot
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Add your GEMINI_API_KEY and GROQ_API_KEY
```

### 3. Build the knowledge base

```bash
python src/embed_and_store_v2.py
```

### 4. Run the API

```bash
uvicorn src.main:app --reload
```

### 5. Test at

```
http://127.0.0.1:8000/docs
```

---

## 📈 Evaluation

Run the evaluation pipeline:

```bash
python evaluation/evaluate.py
```

Results are saved to `evaluation/results.json`.

---

## 🔑 Key Design Decisions

**Why hybrid search?**
Pure semantic search misses exact clinical terms like "STOPP" or "psychoeducation". BM25 keyword search catches these. Combining both (70/30 split) improved context recall from 0.75 to 0.81.

**Why cross-model evaluation?**
Using Gemini to evaluate Gemini-generated answers introduces self-evaluation bias — the model tends to agree with its own outputs. Using Groq LLaMA 3.3 70B as an independent judge gives more reliable scores.

**Why query rewriting?**
Vague follow-up questions like "Can you explain that?" have no semantic meaning on their own. Rewriting them using conversation history before embedding significantly improved multi-turn conversation quality.

**Why crisis detection before RAG?**
Speed and reliability. Crisis responses must be immediate and must not depend on retrieval quality. Routing crisis messages directly to hardcoded helpline information guarantees a safe response regardless of what is in the knowledge base.

---

## 📞 Crisis Resources

If you or someone you know is in crisis:

- **iCall:** 9152987821 (Mon–Sat, 8am–10pm)
- **Vandrevala Foundation:** 1860-2662-345 (24/7)

---

*Built as a portfolio project to demonstrate RAG pipeline design, safety engineering, and LLM evaluation.*