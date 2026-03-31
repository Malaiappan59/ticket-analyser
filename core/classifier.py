# ─────────────────────────────────────────────────────────────────────────────
# core/classifier.py  –  LLM + Keyword-based ticket classification engine
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import re
import time
import logging
from typing import Callable, Optional

import requests
import pandas as pd

from config.settings import CATEGORIES, OLLAMA_CONFIG

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Prompt template
# ─────────────────────────────────────────────────────────────────────────────
_CLASSIFY_PROMPT = """\
You are an expert IT infrastructure support-ticket classifier working for a \
large enterprise service desk.

Classify the ticket below into EXACTLY ONE of these categories:
CPU | Memory | Storage | Network | Hardware | Middleware | Application | \
Database | Security | OS | Monitoring | Others

Rules
-----
1. Reply with the category name ONLY – no explanation, no punctuation, \
   no extra words.
2. If the ticket clearly belongs to a specific category, use it.
3. If it spans multiple categories, choose the PRIMARY failing component.
4. Tickets about alerts/dashboards go to "Monitoring".
5. If nothing matches, use "Others".

Ticket
------
Type             : {ticket_type}
Short Description: {short_desc}
Description      : {description}

Category:"""


# ─────────────────────────────────────────────────────────────────────────────
# Ollama helpers
# ─────────────────────────────────────────────────────────────────────────────

def check_ollama_available(base_url: str = "") -> tuple[bool, str]:
    """
    Probe the Ollama server.

    Returns
    -------
    (True, message)  if Ollama is reachable
    (False, message) otherwise
    """
    url = (base_url or OLLAMA_CONFIG["base_url"]).rstrip("/")
    try:
        resp = requests.get(f"{url}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            msg = (
                f"Ollama running  ·  {len(models)} model(s) available: "
                + (", ".join(models) if models else "none pulled yet")
            )
            return True, msg
        return False, f"Ollama returned HTTP {resp.status_code}"
    except requests.ConnectionError:
        return False, "Ollama not reachable – run:  ollama serve"
    except requests.Timeout:
        return False, "Ollama connection timed out"
    except Exception as exc:  # noqa: BLE001
        return False, f"Unexpected error: {exc}"


def get_available_models(base_url: str = "") -> list[str]:
    """Return list of model names (tag stripped) available in Ollama."""
    url = (base_url or OLLAMA_CONFIG["base_url"]).rstrip("/")
    try:
        resp = requests.get(f"{url}/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m["name"].split(":")[0] for m in resp.json().get("models", [])]
    except Exception:  # noqa: BLE001
        pass
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Single-ticket classifiers
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_category(raw: str) -> str:
    """Map a raw LLM response string to a valid CATEGORIES key."""
    if not raw or not raw.strip():
        return "Others"

    cleaned = re.sub(r"[^a-zA-Z]", "", raw.strip().split()[0])
    if not cleaned:
        return "Others"

    valid = list(CATEGORIES.keys())

    # Exact match (case-insensitive)
    for cat in valid:
        if cat.lower() == cleaned.lower():
            return cat

    # Substring match (only if cleaned is at least 3 chars to avoid false matches)
    if len(cleaned) >= 3:
        for cat in valid:
            if cat.lower() in cleaned.lower() or cleaned.lower() in cat.lower():
                return cat

    return "Others"


def classify_with_llm(
    short_desc: str,
    description: str,
    ticket_type: str,
    model: str,
    base_url: str = "",
) -> str:
    """
    Call the Ollama /api/generate endpoint for one ticket.
    Falls back to keyword classification on any failure.
    """
    url = (base_url or OLLAMA_CONFIG["base_url"]).rstrip("/")
    prompt = _CLASSIFY_PROMPT.format(
        ticket_type=ticket_type or "N/A",
        short_desc=(short_desc or "N/A")[:300],
        description=(description or "N/A")[:600],
    )

    for attempt in range(OLLAMA_CONFIG["max_retries"]):
        try:
            resp = requests.post(
                f"{url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": OLLAMA_CONFIG["temperature"],
                        "num_predict": OLLAMA_CONFIG["num_predict"],
                        "top_p": 0.9,
                    },
                },
                timeout=OLLAMA_CONFIG["timeout"],
            )
            if resp.status_code == 200:
                raw = resp.json().get("response", "")
                return _normalise_category(raw)

            logger.warning("Ollama HTTP %s on attempt %d", resp.status_code, attempt + 1)

        except requests.Timeout:
            logger.warning("Ollama timeout on attempt %d", attempt + 1)
        except requests.ConnectionError:
            logger.warning("Ollama connection error on attempt %d", attempt + 1)
            break  # no point retrying a dead connection
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM error: %s", exc)
            break

    # Fallback
    return classify_with_keywords(short_desc, description)


def classify_with_keywords(short_desc: str, description: str) -> str:
    """
    Rule-based keyword classifier.
    Counts keyword hits per category; returns the winner.
    In case of tie the category appearing earlier in CATEGORIES wins.
    """
    text = f"{short_desc or ''} {description or ''}".lower()
    if not text.strip():
        return "Others"

    scores: dict[str, int] = {}
    for cat, keywords in CATEGORIES.items():
        if cat == "Others" or not keywords:
            continue
        score = sum(1 for kw in keywords if kw in text)
        if score:
            scores[cat] = score

    if scores:
        # Return highest-scoring; tie-break by category order
        return max(scores, key=lambda c: (scores[c], -list(CATEGORIES).index(c)))
    return "Others"


# ─────────────────────────────────────────────────────────────────────────────
# Batch classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_batch(
    tickets_df: pd.DataFrame,
    short_desc_col: Optional[str],
    desc_col: Optional[str],
    type_col: Optional[str],
    use_llm: bool = True,
    model: str = "",
    base_url: str = "",
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[str]:
    """
    Classify every row in *tickets_df* and return a list of category strings
    in the same row order.

    Parameters
    ----------
    tickets_df        : source DataFrame
    short_desc_col    : column name for short description (may be None)
    desc_col          : column name for full description (may be None)
    type_col          : column name for ticket type (may be None)
    use_llm           : use Ollama if True; keyword-only if False
    model             : Ollama model name
    base_url          : Ollama base URL override
    progress_callback : optional fn(current, total) for progress updates
    """
    model = model or OLLAMA_CONFIG["default_model"]
    categories: list[str] = []
    total = len(tickets_df)

    for idx, (_, row) in enumerate(tickets_df.iterrows()):
        sd = str(row[short_desc_col]) if short_desc_col and short_desc_col in row else ""
        dc = str(row[desc_col])       if desc_col       and desc_col       in row else ""
        tt = str(row[type_col])       if type_col        and type_col       in row else ""

        # Skip rows that are completely empty
        if not sd.strip() and not dc.strip():
            categories.append("Others")
        elif use_llm:
            cat = classify_with_llm(sd, dc, tt, model, base_url)
            categories.append(cat)
        else:
            categories.append(classify_with_keywords(sd, dc))

        if progress_callback:
            progress_callback(idx + 1, total)

        # Throttle LLM calls every 10 tickets to avoid server overload
        if use_llm and idx > 0 and idx % 10 == 0:
            time.sleep(0.05)

    return categories
