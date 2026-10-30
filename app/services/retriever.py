import re
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.models.embedding import EmbeddingModel
from app.services.vector_store import client
from app.utils.config import COLLECTION_NAME

embedder = EmbeddingModel()


LAW_BOOST        = 1.5  
KEYWORD_BOOST    = 0.5  
FETCH_MULTIPLIER = 2    


LAW_KEYWORDS = {
    "constitution": [
        ("right to life", 4), ("personal liberty", 4), ("fundamental right", 4),
        ("pardon", 4), ("self incrimination", 4), ("witness against himself", 4),
        ("compelled to be a witness", 4), ("forced to be a witness", 4),
        ("double jeopardy", 4), ("right to privacy", 4), ("right to education", 4),
        ("right to equality", 3), ("freedom of speech", 3), ("directive principles", 3),
        ("president power", 3), ("article", 2), ("constitution", 2),
        ("preamble", 1), ("amendment", 1), ("citizenship", 1),
    ],
    "bns": [
        ("murder", 4), ("cheating", 4), ("theft", 4), ("rape", 4),
        ("sedition", 4), ("culpable homicide", 4), ("false promise of marriage", 4),
        ("minor death penalty", 3), ("robbery", 3), ("fraud", 3),
        ("indian penal code", 3), ("ipc", 3), ("bns", 3),
        ("crime", 2), ("punishment", 2), ("criminal offense", 2),
        ("criminal", 1), ("offense", 1),
    ],
    # BNSS replaced the CrPC, so general criminal-procedure queries default to it.
    # "bnss" also contains "bns", so it needs a higher weight to win over BNS
    "bnss": [
        ("bnss", 8), ("nagarik suraksha", 8), ("bharatiya nagarik", 8),
        ("anticipatory bail", 4), ("arrested without warrant", 4),
        ("arrest without warrant", 4), ("zero fir", 4), ("e-fir", 4),
        ("electronic fir", 4), ("trial in absentia", 4), ("police custody", 4),
        ("judicial custody", 4), ("remand", 4), ("bail", 3),
        ("arrest", 3), ("fir", 3), ("warrant", 3), ("proclaimed offender", 3),
        ("audio-video electronic", 3), ("trial", 2), ("investigation", 2),
        ("videography", 2), ("forensic", 2), ("police", 1), ("procedure", 1),
    ],
    # Only when the user asks for the old code by name
    "crpc": [
        ("crpc", 8), ("cr.p.c", 8), ("code of criminal procedure", 8),
        ("criminal procedure code", 8),
    ],
    "cpc": [
        ("civil suit", 4), ("injunction", 3), ("decree", 3),
        ("appeal", 2), ("plaint", 2), ("civil", 1),
    ],
    # data/ida.json is the Indian Divorce Act, 1869 (not the Industrial Disputes Act)
    "ida": [
        ("divorce act", 4), ("dissolution of marriage", 4), ("judicial separation", 4),
        ("restitution of conjugal rights", 4), ("nullity of marriage", 4),
        ("alimony", 4), ("divorce", 3), ("maintenance", 2), ("custody", 2),
        ("separation", 2), ("husband", 1), ("wife", 1),
    ],
    "mva": [
        ("speed limit", 4), ("maximum speed", 4), ("drunk driving", 4),
        ("highway speed", 4), ("traffic violation", 3), ("license", 2),
        ("traffic", 2), ("vehicle", 2), ("accident", 2), ("highway", 2), ("road", 1),
    ],
    "iea": [
        ("evidence act", 4), ("admissible", 4), ("admissibility", 4),
        ("confession", 3), ("burden of proof", 4), ("dying declaration", 4),
        ("evidence", 2), ("witness", 1),
    ],
    "nia": [
        ("cheque bounce", 4), ("cheque bounces", 4), ("bounced cheque", 4), ("dishonour of cheque", 4),
        ("negotiable instrument", 4), ("promissory note", 4), ("bill of exchange", 4),
        ("cheque", 3),
    ],
}

# Prefix added to query when no specific rewrite matches.
LAW_PREFIXES = {
    "constitution": "Indian constitution fundamental rights article: ",
    "bns":          "Indian penal law BNS offense definition section: ",
    "bnss":         "Bharatiya Nagarik Suraksha Sanhita BNSS criminal procedure section: ",
    "crpc":         "Indian criminal procedure code CrPC section: ",
    "cpc":          "Indian civil procedure code section: ",
    "ida":          "Indian divorce act section: ",
    "mva":          "Indian motor vehicles act section: ",
    "iea":          "Indian evidence act section: ",
    "nia":          "Indian negotiable instruments act section: ",
}

# Exact phrase → enriched search query rewrites.
# Sorted longest-first at runtime so the most specific phrase matches first.
PHRASE_REWRITES = {
    # Constitution
    "compelled to be a witness":        "Article 20 self incrimination accused compelled witness against himself constitution fundamental right",
    "forced to be a witness":           "Article 20 self incrimination accused compelled witness against himself constitution fundamental right",
    "witness against himself":          "Article 20 self incrimination accused compelled witness against himself constitution fundamental right",
    "self-incrimination":               "Article 20 self incrimination accused compelled witness constitution",
    "double jeopardy":                  "Article 20 double jeopardy convicted prosecuted same offense constitution protection",
    "right to life":                    "Article 21 right to life personal liberty no person deprived constitution",
    "right to privacy":                 "Article 21 right to privacy personal liberty constitution",
    "right to education":               "Article 21A free compulsory education children constitution",
    "pardon a death sentence":          "Article 72 president power grant pardon reprieve respite death sentence constitution",
    "power to pardon":                  "Article 72 president power grant pardon reprieve respite death sentence constitution",
    "pardon":                           "Article 72 president power grant pardon reprieve respite death sentence constitution",
    # BNS
    "false promise of marriage":        "section 69 sexual intercourse deceitful means false promise marriage consent BNS",
    "consensual physical relationship": "section 69 sexual intercourse deceitful means false promise marriage consent BNS",
    "dies during a strike":             "section 103 murder culpable homicide death group acts punishment BNS",
    "minor death penalty":              "section 103 section 27 minor child age offender punishment death sentence BNS",
    "minor be given death":             "section 103 section 27 minor child age offender punishment death sentence BNS",
    "sedition":                         "section 152 acts endangering sovereignty integrity unity india punishment BNS",
    "murder":                           "section 103 murder culpable homicide death punishment imprisonment life BNS",
    "cheating":                         "section 318 cheating deceives dishonestly induces wrongful gain loss offense BNS",
    "theft":                            "section 303 theft dishonestly takes moveable property without consent BNS",
    "robbery":                          "section 309 robbery theft extortion punishment rigorous imprisonment ten years fine BNS",
    "dacoity":                          "section 310 dacoity five or more persons conjointly commit robbery punishment imprisonment life BNS",
    "theft in a house":                 "section 305 theft in a dwelling house building tent vessel place of worship punishment imprisonment seven years BNS",
    "theft in house":                   "section 305 theft in a dwelling house building tent vessel place of worship punishment imprisonment seven years BNS",
    "theft in a dwelling":              "section 305 theft in a dwelling house building tent vessel place of worship punishment imprisonment seven years BNS",
    "house theft":                      "section 305 theft in a dwelling house building tent vessel place of worship punishment imprisonment seven years BNS",
    "house burglary":                   "section 305 theft in a dwelling house building tent vessel place of worship punishment imprisonment seven years BNS",
    "committed in a house":             "section 305 theft in a dwelling house building tent vessel place of worship punishment imprisonment seven years BNS",
    "stolen from a house":              "section 305 theft in a dwelling house building tent vessel place of worship punishment imprisonment seven years BNS",
    "stolen from my house":             "section 305 theft in a dwelling house building tent vessel place of worship punishment imprisonment seven years BNS",
    "happens in a house":               "section 305 theft in a dwelling house building tent vessel place of worship punishment imprisonment seven years BNS",
    # BNSS
    "anticipatory bail":                "section 482 anticipatory bail apprehension arrest non-bailable offence direction high court court of session BNSS",
    "arrested without warrant":         "section 35 police may arrest without warrant order magistrate cognizable offence BNSS",
    "arrest without warrant":           "section 35 police may arrest without warrant order magistrate cognizable offence BNSS",
    "zero fir":                         "section 173 information cognizable offence irrespective of area where offence committed orally electronic communication police station BNSS",
    "police custody":                   "section 187 procedure when investigation cannot be completed in twenty-four hours custody magistrate fifteen days BNSS",
    # IDA (Indian Divorce Act, 1869)
    "mutual consent":                   "section 10A dissolution of marriage by mutual consent divorce act IDA",
    "grounds for divorce":              "section 10 grounds for dissolution of marriage divorce act IDA",
    "permanent alimony":                "section 37 power to order permanent alimony divorce act IDA",
    # MVA
    "maximum speed limit":              "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    "speed limit on highways":          "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    "speed limit":                      "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    "maximum speed":                    "section 112 maximum speed limit vehicle highway road motor vehicles act MVA",
    # NIA
    "cheque bounce":                    "section 138 dishonour of cheque for insufficiency of funds in the account punishment negotiable instruments act NIA",
    "cheque bounced":                   "section 138 dishonour of cheque for insufficiency of funds in the account punishment negotiable instruments act NIA",
    "cheque bounces":                   "section 138 dishonour of cheque for insufficiency of funds in the account punishment negotiable instruments act NIA",
    "bounced cheque":                   "section 138 dishonour of cheque for insufficiency of funds in the account punishment negotiable instruments act NIA",
    "dishonour of cheque":              "section 138 dishonour of cheque for insufficiency of funds in the account punishment negotiable instruments act NIA",
    "dishonoured cheque":               "section 138 dishonour of cheque for insufficiency of funds in the account punishment negotiable instruments act NIA",
}


# The BNS (2023) replaced the IPC with new section numbers; users still cite IPC.
IPC_TO_BNS = {
    "34": "3", "120b": "61", "124a": "152", "299": "100", "300": "101",
    "302": "103", "304": "105", "304a": "106", "304b": "80", "307": "109",
    "323": "115", "324": "118", "326": "118", "354": "74", "363": "137",
    "375": "63", "376": "64", "378": "303", "379": "303", "380": "305",
    "392": "309", "415": "318", "420": "318", "498a": "85", "499": "356",
    "500": "356", "503": "351", "506": "351",
}

IPC_CITATION = re.compile(
    r"\bipc\s*(?:section|sec\.?|s\.?)?\s*(\d+[a-z]?)\b"
    r"|\b(?:section|sec\.?)\s*(\d+[a-z]?)\s*(?:of\s+)?(?:the\s+)?(?:ipc|indian penal code)\b"
)


# ── Step 0: Translate IPC section citations to their BNS equivalents ──────────
def translate_ipc_citations(query: str) -> str:
    """Rewrite e.g. "ipc section 302" to "bns section 103" so the search (and the
    section-id rerank bonus) targets the current BNS provision, not an unrelated
    section that happens to share the old IPC number."""
    def repl(m):
        bns = IPC_TO_BNS.get(m.group(1) or m.group(2))
        return f"bns section {bns}" if bns else m.group(0)
    return IPC_CITATION.sub(repl, query)


# ── Step 1: Detect which law the query is about ────────────────────────────────
def detect_law_type(query: str) -> str | None:
    """Score each law by how many of its keywords appear in the query.
    Returns the best-matching law name, or None if nothing matched."""
    scores = {law: 0 for law in LAW_KEYWORDS}

    for law, keywords in LAW_KEYWORDS.items():
        for phrase, weight in keywords:
            if phrase in query:
                scores[law] += weight

    best_law  = max(scores, key=scores.get)
    best_score = scores[best_law]

    return best_law if best_score > 0 else None


LOOSE_PATTERNS = {
    phrase: re.compile(r"\b" + r"\b(?:\s+\S+){0,2}?\s+\b".join(map(re.escape, phrase.split())) + r"\b")
    for phrase in PHRASE_REWRITES
}


# ── Step 2: Build an enriched search query ─────────────────────────────────────
def build_enriched_query(query: str, law_type: str | None) -> str:
    """Try to match a specific phrase rewrite first (longest match wins).
    Fall back to prepending a law-specific prefix to the original query."""

    # Sort rewrites by phrase length so longer/more-specific phrases match first
    sorted_rewrites = sorted(PHRASE_REWRITES.items(), key=lambda x: len(x[0]), reverse=True)

    for phrase, rewrite in sorted_rewrites:
        if phrase in query:
            return rewrite

    # Looser pass: same words in order with up to two extra words between them,
    # e.g. "arrest me without a warrant" -> "arrest without warrant"
    for phrase, rewrite in sorted_rewrites:
        if LOOSE_PATTERNS[phrase].search(query):
            return rewrite

    # No specific rewrite found — use law prefix + original query
    prefix = LAW_PREFIXES.get(law_type, "Indian law: ")
    return f"{prefix}{query}"


# ── Step 3: Fetch results using both enriched and original query ───────────────
def fetch_results(original_query: str, enriched_query: str, fetch_limit: int,
                  law_type: str | None = None) -> list:
    """Embed both queries, run vector search for each, then merge results.
    When a law is detected, also search within that law only, so its sections are
    always candidates. When the same chunk appears more than once, keep the higher score."""

    vec_enriched = embedder.encode([f"query: {enriched_query}"])[0]
    vec_original = embedder.encode([f"query: {original_query}"])[0]

    hits_enriched = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vec_enriched,
        limit=fetch_limit,
    ).points

    hits_original = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vec_original,
        limit=fetch_limit // 2,
    ).points

    hits_law = []
    if law_type:
        hits_law = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vec_enriched,
            query_filter=Filter(must=[FieldCondition(key="type", match=MatchValue(value=law_type))]),
            limit=fetch_limit,
        ).points

    # Deduplicate: for each unique chunk keep only the highest score
    best = {}
    for hit in hits_enriched + hits_original + hits_law:
        key = (hit.payload.get("id"), hit.payload.get("text", "")[:50])
        if key not in best or hit.score > best[key].score:
            best[key] = hit

    return list(best.values())


# ── Step 4: Boost scores for chunks whose title overlaps with the query ────────
def rerank_by_keywords(results: list, query: str, enriched_query: str = "",
                       law_type: str | None = None) -> list:
    """Give a small score bonus when query words appear in the chunk title, and
    when a phrase rewrite names the chunk's section in the detected law."""
    enriched_query = enriched_query.lower()
    query_words = set(query.split())

    for hit in results:
        title       = (hit.payload.get("title") or "").lower()
        title_words = set(title.split())
        overlap     = len(query_words & title_words)

        # Once a law is detected, title matches from other acts shouldn't outrank it
        # (BNSS sections have no titles, so they could never compete on this)
        in_law = not law_type or hit.payload.get("type") == law_type
        if overlap > 0 and in_law:
            hit.score += KEYWORD_BOOST * overlap

        # Extra bonus if the chunk's id is mentioned directly in the query
        chunk_id = (hit.payload.get("id") or "").lower()
        if chunk_id in query:
            hit.score += KEYWORD_BOOST * 2
        elif (law_type and hit.payload.get("type") == law_type and chunk_id
              and re.search(rf"\b{re.escape(chunk_id)}\b", enriched_query)):
            hit.score += KEYWORD_BOOST * 2

    return results


# ── Main entry point ───────────────────────────────────────────────────────────
def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Full retrieval pipeline:
    1. Detect law type
    2. Build enriched query
    3. Dual vector search + merge
    4. Boost chunks matching the detected law
    5. Keyword rerank
    6. Return top_k results
    """
    query = translate_ipc_citations(query.lower().strip())

    law_type       = detect_law_type(query)
    enriched_query = build_enriched_query(query, law_type)


    results = fetch_results(query, enriched_query, fetch_limit=top_k * FETCH_MULTIPLIER,
                            law_type=law_type)

    # BNSS superseded the CrPC: unless the user named the CrPC, don't cite it
    if law_type == "bnss":
        results = [hit for hit in results if hit.payload.get("type") != "crpc"]

    # Boost chunks that belong to the detected law
    if law_type:
        for hit in results:
            if hit.payload.get("type") == law_type:
                hit.score *= LAW_BOOST

    results = rerank_by_keywords(results, query, enriched_query, law_type)
    results = sorted(results, key=lambda x: x.score, reverse=True)[:top_k]

    return [
        {
            "type":  hit.payload["type"],
            "id":    hit.payload["id"],
            "title": hit.payload["title"],
            "text":  hit.payload["text"],
            "score": hit.score,
        }
        for hit in results
    ]