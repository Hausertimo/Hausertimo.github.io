"""
Norm matching logic - uses LLM to check if norms apply to a product
Migrated from NormScout_Test/AICore
"""
import json
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from .openrouter import call_openrouter

logger = logging.getLogger(__name__)


def load_norms():
    """Load norms from JSON file"""
    norms_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "norms.json")
    with open(norms_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["norms"]


def check_norm_applies(product_description: str, norm: dict) -> dict:
    """
    Ask LLM if a norm applies to the product.
    Returns dict with: applies (bool), confidence (0-100), reasoning (str)
    """
    prompt = f"""You are an EU compliance expert. Analyze if this norm applies to the product.

PRODUCT: {product_description}

NORM: {norm['name']} ({norm['id']})
APPLIES TO: {norm['applies_to']}
DESCRIPTION: {norm['description']}

INSTRUCTIONS:
- Read the "APPLIES TO" field carefully and check if the product matches those criteria
- Pay close attention to voltage ranges, thresholds, and numeric values
- If the norm specifies a minimum voltage (e.g., ">75V DC"), the product voltage must be GREATER than that value
- Be precise with technical specifications
- Answer in this EXACT format:

APPLIES: yes/no
CONFIDENCE: 0-100
REASONING: brief explanation

Be critical, accurate, and precise with numbers."""

    messages = [{"role": "user", "content": prompt}]

    result = call_openrouter(
        messages,
        model="anthropic/claude-3.5-sonnet",
        temperature=0.3,
        max_tokens=200
    )

    if not result["success"]:
        logger.error(f"LLM call failed for norm {norm['id']}: {result.get('error')}")
        return {
            "norm_id": norm["id"],
            "norm_name": norm["name"],
            "applies": False,
            "confidence": 0,
            "reasoning": f"Error: {result.get('error')}"
        }

    # Parse response
    response = result["content"]
    lines = response.strip().split("\n")
    applies = "yes" in lines[0].lower() if lines else False
    confidence = 50  # default
    reasoning = ""

    # Find the reasoning line and capture everything after it
    reasoning_started = False
    reasoning_parts = []

    for i, line in enumerate(lines):
        if "CONFIDENCE:" in line.upper():
            try:
                confidence = int(''.join(filter(str.isdigit, line)))
            except:
                confidence = 50

        if "REASONING:" in line.upper():
            # Get text after "REASONING:" on the same line
            parts = line.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                reasoning_parts.append(parts[1].strip())
            reasoning_started = True
        elif reasoning_started and line.strip():
            # Continue capturing reasoning from following lines
            reasoning_parts.append(line.strip())

    reasoning = " ".join(reasoning_parts) if reasoning_parts else ""

    return {
        "norm_id": norm["id"],
        "norm_name": norm["name"],
        "applies": applies,
        "confidence": confidence,
        "reasoning": reasoning
    }


def match_norms(product_description: str, max_workers: int = 10, progress_callback=None) -> list:
    """
    Match all norms against a product description in parallel.
    Returns list of matching norms with confidence scores.

    Args:
        product_description: Description of the product
        max_workers: Maximum concurrent API calls
        progress_callback: Optional callback function(completed, total, norm_id) for progress updates

    Returns:
        List of matching norms sorted by confidence
    """
    norms = load_norms()
    results = []
    completed = 0

    logger.info(f"Checking {len(norms)} norms in parallel (max {max_workers} at a time)")

    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_norm = {
            executor.submit(check_norm_applies, product_description, norm): norm
            for norm in norms
        }

        # Process as they complete
        for future in as_completed(future_to_norm):
            completed += 1
            norm = future_to_norm[future]

            try:
                result = future.result()
                if result["applies"]:
                    results.append(result)
                logger.info(f"[{completed}/{len(norms)}] OK {norm['id']}")

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(completed, len(norms), norm['id'])

            except Exception as e:
                logger.error(f"[{completed}/{len(norms)}] ERROR {norm['id']} - {e}")
                if progress_callback:
                    progress_callback(completed, len(norms), norm['id'])

    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)

    logger.info(f"Found {len(results)} applicable norms")
    return results


def match_norms_streaming(product_description: str, max_workers: int = 10):
    """
    Match all norms against a product description in parallel, yielding progress events immediately.
    This is a generator that streams progress updates in real-time.

    Args:
        product_description: Description of the product
        max_workers: Maximum concurrent API calls

    Yields:
        Tuples of:
        - ('progress', completed, total, norm_id) for each completed norm
        - ('complete', results) when all norms are checked
    """
    norms = load_norms()
    results = []
    completed = 0
    total = len(norms)

    logger.info(f"Checking {total} norms in parallel (max {max_workers} at a time)")

    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_norm = {
            executor.submit(check_norm_applies, product_description, norm): norm
            for norm in norms
        }

        # Process as they complete and yield immediately
        for future in as_completed(future_to_norm):
            completed += 1
            norm = future_to_norm[future]

            try:
                result = future.result()
                if result["applies"]:
                    results.append(result)
                logger.info(f"[{completed}/{total}] OK {norm['id']}")

                # Yield progress immediately
                yield ('progress', completed, total, norm['id'])

            except Exception as e:
                logger.error(f"[{completed}/{total}] ERROR {norm['id']} - {e}")
                # Still yield progress even on error
                yield ('progress', completed, total, norm['id'])

    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)

    logger.info(f"Found {len(results)} applicable norms")

    # Yield final results
    yield ('complete', results)
