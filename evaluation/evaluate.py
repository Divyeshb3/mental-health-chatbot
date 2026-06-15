import time
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hybrid_search import hybrid_search
from src.rag_pipeline import generate_response, build_prompt
from google import genai
from dotenv import load_dotenv

load_dotenv()

from groq import Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_groq(prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

# Load test dataset

with open("evaluation/test_dataset.json", "r") as f:
    test_data = json.load(f)

print(f"✅ Loaded {len(test_data)} test questions\n")

def generate_answer_for_eval(question, chunks):
    context = "\n".join(chunks)
    prompt = f"""You are a compassionate mental health support assistant.
Use ONLY the provided context to answer the question.
Never diagnose. Always recommend professional help.

Context:
{context}

Question: {question}
Answer:"""
    return call_groq(prompt)

# Evaluation functions using Gemini

def score_faithfulness(answer, chunks):
    context = "\n".join(chunks)
    prompt = f"""Rate how faithful this answer is to the given context.
Faithfulness means the answer only uses information from the context and does not add outside facts.

Context:
{context}

Answer:
{answer}

Give a score from 0.0 to 1.0 where:
1.0 = answer is completely based on the context
0.5 = answer partially uses context
0.0 = answer ignores the context completely

Reply with ONLY a number like 0.8 — nothing else."""
    try:
        result = call_groq(prompt)
        return float(result)
    except:
        return 0.5

def score_relevancy(question, answer):
    prompt = f"""Rate how relevant this answer is to the question.

Question: {question}
Answer: {answer}

Give a score from 0.0 to 1.0 where:
1.0 = answer directly and completely addresses the question
0.5 = answer is somewhat related but incomplete
0.0 = answer does not address the question at all

Reply with ONLY a number like 0.8 — nothing else."""
    try:
        result = call_groq(prompt)
        return float(result)
    except:
        return 0.5

def score_context_recall(question, chunks, ground_truth):
    context = "\n".join(chunks)
    prompt = f"""Rate how well the retrieved context covers the ground truth answer.

Question: {question}
Ground Truth: {ground_truth}
Retrieved Context: {context}

Give a score from 0.0 to 1.0 where:
1.0 = context contains all the information needed to answer correctly
0.5 = context contains some relevant information
0.0 = context is completely irrelevant

Reply with ONLY a number like 0.8 — nothing else."""
    try:
        result = call_groq(prompt)
        return float(result)
    except:
        return 0.5

# Run evaluation

faithfulness_scores = []
relevancy_scores = []
recall_scores = []

print("=" * 55)
print("Running Evaluation")
print("=" * 55 + "\n")

for i, item in enumerate(test_data):
    question = item["question"]
    ground_truth = item["ground_truth"]

    print(f"Q{i+1}: {question[:50]}...")

    # Get RAG answer
    chunks, sources, scores = hybrid_search(question, n_results=3)
    answer = generate_answer_for_eval(question, chunks)

    # Score it
    f_score = score_faithfulness(answer, chunks)
    r_score = score_relevancy(question, answer)
    c_score = score_context_recall(question, chunks, ground_truth)

    faithfulness_scores.append(f_score)
    relevancy_scores.append(r_score)
    recall_scores.append(c_score)

    print(f"  Faithfulness: {f_score} | Relevancy: {r_score} | Recall: {c_score}\n")
    print(f"  ⏳ Waiting before next question...")
    time.sleep(20)
    
# Final scores

avg_faithfulness = round(sum(faithfulness_scores) / len(faithfulness_scores), 4)
avg_relevancy = round(sum(relevancy_scores) / len(relevancy_scores), 4)
avg_recall = round(sum(recall_scores) / len(recall_scores), 4)
overall = round((avg_faithfulness + avg_relevancy + avg_recall) / 3, 4)

print("=" * 55)
print("Final Evaluation Results")
print("=" * 55)
print(f"\n📊 Faithfulness:      {avg_faithfulness}  (target: > 0.8)")
print(f"📊 Answer Relevancy:  {avg_relevancy}  (target: > 0.8)")
print(f"📊 Context Recall:    {avg_recall}  (target: > 0.7)")
print(f"\n⭐ Overall Score:     {overall}")

output = {
    "faithfulness": avg_faithfulness,
    "answer_relevancy": avg_relevancy,
    "context_recall": avg_recall,
    "overall": overall,
    "evaluation_method": "Gemini-based custom evaluation",
    "num_questions": len(test_data)
}

with open("evaluation/results.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\n✅ Results saved to evaluation/results.json")
print("=" * 55)