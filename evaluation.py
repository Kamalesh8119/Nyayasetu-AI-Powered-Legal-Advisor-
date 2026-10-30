import requests
import time

# 🔗 API endpoint
URL = "http://127.0.0.1:8001/chat"

# 🧪 Test dataset
# keywords = must-have terms (true positives for recall)
# negative_keywords = terms that should NOT appear (false positives for precision)
test_cases = [

    # 🔹 CRIMINAL LAW (CrPC + BNS)
    {
        "question": "What is the difference between cognizable and non-cognizable offences under CrPC?",
        "keywords": ["cognizable", "non-cognizable", "CrPC", "arrest", "police"],
        "negative_keywords": ["GST", "company", "divorce"],
        "category": "Criminal Law"
    },
    {
        "question": "Explain the procedure for arrest without warrant under CrPC.",
        "keywords": ["arrest", "without warrant", "CrPC", "police", "cognizable"],
        "negative_keywords": ["GST", "contract", "trademark"],
        "category": "Criminal Law"
    },

    # 🔹 EVIDENCE LAW
    {
        "question": "What is the meaning of 'relevant facts' under the Indian Evidence Act?",
        "keywords": ["relevant", "facts", "Evidence Act", "fact in issue", "connection"],
        "negative_keywords": ["GST", "company", "divorce"],
        "category": "Evidence Law"
    },
    {
        "question": "What is the difference between proved, disproved, and not proved?",
        "keywords": ["proved", "disproved", "not proved", "Evidence Act"],
        "negative_keywords": ["GST", "FIR", "company"],
        "category": "Evidence Law"
    },

    # 🔹 CIVIL PROCEDURE (CPC)
    {
        "question": "What is a decree under the Code of Civil Procedure?",
        "keywords": ["decree", "CPC", "judgment", "civil court"],
        "negative_keywords": ["GST", "criminal", "bail"],
        "category": "Civil Law"
    },
    {
        "question": "What is the difference between decree and order in CPC?",
        "keywords": ["decree", "order", "CPC", "civil"],
        "negative_keywords": ["GST", "FIR", "company"],
        "category": "Civil Law"
    },

    # 🔹 CONSTITUTIONAL LAW
    {
        "question": "What does Article 14 of the Constitution provide?",
        "keywords": ["Article 14", "equality", "law", "equal protection"],
        "negative_keywords": ["GST", "company", "contract"],
        "category": "Constitutional Law"
    },
    {
        "question": "What is the significance of the Preamble of the Constitution?",
        "keywords": ["preamble", "justice", "liberty", "equality", "sovereign"],
        "negative_keywords": ["GST", "FIR", "company"],
        "category": "Constitutional Law"
    },

    # 🔹 FAMILY LAW (HMA + Divorce Act)
    {
        "question": "What are the essential conditions for a valid Hindu marriage?",
        "keywords": ["conditions", "Hindu marriage", "ceremony", "valid"],
        "negative_keywords": ["GST", "company", "bail"],
        "category": "Family Law"
    },
    {
        "question": "Under what conditions can a divorce petition be filed under the Divorce Act?",
        "keywords": ["divorce", "petition", "court", "grounds"],
        "negative_keywords": ["GST", "company", "FIR"],
        "category": "Family Law"
    },

    # 🔹 COMMERCIAL LAW (NI Act)
    {
        "question": "What is a promissory note under the Negotiable Instruments Act?",
        "keywords": ["promissory note", "instrument", "payment", "NI Act"],
        "negative_keywords": ["GST", "divorce", "criminal"],
        "category": "Commercial Law"
    },
    {
        "question": "What is the difference between cheque and bill of exchange?",
        "keywords": ["cheque", "bill of exchange", "banker", "NI Act"],
        "negative_keywords": ["GST", "FIR", "company"],
        "category": "Commercial Law"
    },

    # 🔹 MOTOR VEHICLES ACT
    {
        "question": "What is the definition of a motor vehicle under the Motor Vehicles Act?",
        "keywords": ["motor vehicle", "definition", "vehicle", "Act"],
        "negative_keywords": ["GST", "divorce", "contract"],
        "category": "Motor Vehicles Law"
    },
    {
        "question": "What is meant by a driving licence under the Motor Vehicles Act?",
        "keywords": ["driving licence", "authority", "motor vehicle", "permit"],
        "negative_keywords": ["GST", "FIR", "company"],
        "category": "Motor Vehicles Law"
    },

    # 🔥 HARD — CROSS LAW
    {
        "question": "How does CrPC define a bailable offence and how is it treated differently from non-bailable offence?",
        "keywords": ["bailable", "non-bailable", "CrPC", "offence", "arrest"],
        "negative_keywords": ["GST", "company", "divorce"],
        "category": "Criminal Law"
    },

    # 🔥 HARD — INTERPRETATION
    {
        "question": "Explain the concept of 'fact in issue' with reference to Evidence Act.",
        "keywords": ["fact in issue", "Evidence Act", "relevant", "fact"],
        "negative_keywords": ["GST", "company", "contract"],
        "category": "Evidence Law"
    }
]

def compute_metrics(answer: str, keywords: list, negative_keywords: list):
    """
    Precision  = relevant terms present / all terms present (penalizes off-topic answers)
    Recall     = relevant terms found / total relevant terms expected
    F1         = harmonic mean of precision and recall
    """
    answer_lower = answer.lower()

    true_positives  = sum(1 for kw in keywords if kw.lower() in answer_lower)
    false_negatives = len(keywords) - true_positives
    false_positives = sum(1 for nkw in negative_keywords if nkw.lower() in answer_lower)

    # Recall: how many expected keywords did we catch?
    recall = true_positives / len(keywords) if keywords else 0.0

    # Precision: of all signals (TP + FP), how many were correct?
    denominator = true_positives + false_positives
    precision = true_positives / denominator if denominator > 0 else 1.0

    # F1
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return round(precision, 3), round(recall, 3), round(f1, 3), true_positives, false_positives, false_negatives


def call_with_retry(question: str, max_retries: int = 5, base_delay: float = 15.0) -> tuple[str, float]:
    """
    POST to /chat and retry on 429s with exponential backoff.
    Returns (answer_text, total_latency_seconds).
    """
    total_latency = 0.0
    for attempt in range(max_retries):
        start = time.time()
        response = requests.post(URL, json={"message": question, "user_id": "evaluation"}, timeout=120)
        elapsed = round(time.time() - start, 2)
        total_latency += elapsed

        answer = response.json().get("response", "") if response.status_code == 200 else ""

        # Detect 429 buried in the response body (FastAPI forwards LLM errors as 200)
        is_rate_limited = (
            response.status_code == 429
            or "rate limit" in answer.lower()
            or "rate_limited" in answer.lower()
            or "429" in answer
        )

        if is_rate_limited and attempt < max_retries - 1:
            wait = base_delay * (2 ** attempt)   # 15s → 30s → 60s → 120s
            print(f"    ⏳ Rate limited on attempt {attempt+1}. Waiting {wait:.0f}s before retry...")
            time.sleep(wait)
            continue

        return answer, total_latency

    return answer, total_latency   # return last attempt regardless


def evaluate():
    total = len(test_cases)
    passed = 0
    total_time = 0

    # Aggregate counters for corpus-level P/R/F1
    total_tp = total_fp = total_fn = 0

    category_stats = {}

    print("🚀 Starting NyayaSetu Evaluation...\n")
    print("=" * 70)

    for i, case in enumerate(test_cases):
        question          = case["question"]
        keywords          = case["keywords"]
        negative_keywords = case["negative_keywords"]
        category          = case["category"]

        try:
            if i > 0:
                print(f"    ⏸  Waiting 10s before next question...")
                time.sleep(10)  # baseline gap — reduces chance of hitting limit at all

            answer, latency = call_with_retry(question)
            total_time += latency

            precision, recall, f1, tp, fp, fn = compute_metrics(answer, keywords, negative_keywords)

            total_tp += tp
            total_fp += fp
            total_fn += fn

            passed_flag = f1 >= 0.5
            if passed_flag:
                passed += 1
                result_icon = " PASS"
            else:
                result_icon = " FAIL"

            # Track per-category
            if category not in category_stats:
                category_stats[category] = {"pass": 0, "total": 0}
            category_stats[category]["total"] += 1
            if passed_flag:
                category_stats[category]["pass"] += 1

            print(f"\nQ{i+1} [{category}] {result_icon}")
            print(f"  Question  : {question}")
            print(f"  Response  : {answer[:160]}...")
            print(f"  Precision : {precision:.2f}  |  Recall : {recall:.2f}  |  F1 : {f1:.2f}")
            print(f"  TP={tp}  FP={fp}  FN={fn}  |  Latency: {latency}s")

        except Exception as e:
            print(f"\nQ{i+1}  ERROR: {e}")

    # ── Corpus-level metrics ──────────────────────────────────────────────
    corpus_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    corpus_recall    = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    corpus_f1        = (2 * corpus_precision * corpus_recall) / (corpus_precision + corpus_recall) \
                       if (corpus_precision + corpus_recall) > 0 else 0

    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    print(f"  Total Questions  : {total}")
    print(f"  Passed (F1≥0.5)  : {passed} / {total}  ({round(passed/total*100, 1)}%)")
    print(f"  Avg Latency      : {round(total_time/total, 2)}s")
    print(f"\n  Corpus Precision : {corpus_precision:.3f}")
    print(f"  Corpus Recall    : {corpus_recall:.3f}")
    print(f"  Corpus F1        : {corpus_f1:.3f}")

    print("\n📂 Results by Category:")
    for cat, stats in category_stats.items():
        pct = round(stats["pass"] / stats["total"] * 100)
        bar = "█" * stats["pass"] + "░" * (stats["total"] - stats["pass"])
        print(f"  {cat:<20} {bar}  {stats['pass']}/{stats['total']} ({pct}%)")

    print("=" * 70)


if __name__ == "__main__":
    evaluate()