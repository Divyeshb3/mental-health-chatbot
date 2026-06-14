from hybrid_search import hybrid_search

# 20 test questions covering all your PDFs
TEST_QUESTIONS = [
    # Anxiety
    "What are the symptoms of anxiety?",
    "How does deep breathing help anxiety?",
    "What triggers anxiety?",
    "How to stop a panic attack?",
    "What is the difference between anxiety and panic?",

    # CBT
    "What is cognitive behavioural therapy?",
    "How do I challenge negative thoughts?",
    "What is the STOPP technique?",
    "What are safety behaviours in CBT?",
    "How does gradual exposure work?",

    # Mindfulness
    "What is mindfulness meditation?",
    "How do I start practising mindfulness?",
    "What is the body scan technique?",
    "How does mindfulness reduce stress?",
    "What is present moment awareness?",

    # Depression
    "What are signs of depression?",
    "How to deal with low mood?",
    "What self help techniques work for depression?",
    "How does activity scheduling help depression?",
    "What is behavioural activation?"
]

print("=" * 55)
print("Retrieval Quality Test — 20 Questions")
print("=" * 55)

passed = 0
failed = []

for i, question in enumerate(TEST_QUESTIONS):
    chunks, sources, scores = hybrid_search(question, n_results=3)

    # Check if retrieval returned anything meaningful
    top_score = scores[0] if scores else 0
    has_result = len(chunks) > 0 and top_score > 0.3

    status = "✅" if has_result else "❌"
    if has_result:
        passed += 1
    else:
        failed.append(question)

    print(f"{status} Q{i+1}: {question[:50]}")
    print(f"   Top score: {top_score} | Source: {sources[0] if sources else 'none'}\n")

print("=" * 55)
print(f"Results: {passed}/20 passed")
if failed:
    print(f"\nFailed questions:")
    for q in failed:
        print(f"  - {q}")
print("=" * 55)