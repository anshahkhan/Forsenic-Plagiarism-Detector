from perplexity import Perplexity
import logging
from typing import List, Dict
import json

logger = logging.getLogger(__name__)

client = Perplexity()

def call_llm_for_metadata(urls: List[str]) -> Dict[str, Dict]:
    """
    Calls Perplexity LLM (sonar) to get structured metadata for a list of URLs.
    Returns a dictionary mapping each URL to its metadata (author, publication_date, document_type, citation)
    """
    if not urls:
        return {}

    # Prepare the prompt
    prompt = (
        "Provide metadata for the following URLs. For each URL, return "
        "author, publication_date, document_type, and citation.\n\n"
        + "\n".join(urls)
    )

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="sonar",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "metadata": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "url": {"type": "string"},
                                        "author": {"type": "string"},
                                        "publication_date": {"type": "string"},
                                        "document_type": {"type": "string"},
                                        "citation": {"type": "string"}
                                    },
                                    "required": ["url", "author", "publication_date", "document_type", "citation"]
                                }
                            }
                        },
                        "required": ["metadata"]
                    }
                }
            }
        )
        # The SDK may return structured content as a dict/list or a JSON string; parse robustly
        result = completion.choices[0].message.content

        # Normalize result into a Python object
        try:
            if isinstance(result, str):
                parsed = json.loads(result)
            else:
                parsed = result
        except Exception:
            # fallback: attempt to coerce to JSON from string representation
            try:
                parsed = json.loads(str(result))
            except Exception:
                parsed = {}

        # Extract metadata list whether parsed is a dict with "metadata" or a raw list
        if isinstance(parsed, dict):
            metadata_list = parsed.get("metadata", [])
        elif isinstance(parsed, list):
            metadata_list = parsed
        else:
            metadata_list = []

        metadata_map = {}
        for item in metadata_list:
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if not isinstance(url, str):
                continue
            metadata_map[url] = {
                "author": item.get("author", "Unknown"),
                "publication_date": item.get("publication_date", "Unknown"),
                "document_type": item.get("document_type", "Unknown"),
                "citation": item.get("citation", f"Citation for {url}")
            }
        return metadata_map

    except Exception as e:
        logger.error("Failed to call Perplexity LLM for metadata: %s", e)
        # Return defaults if LLM call fails
        return {url: {
                    "author": "Unknown",
                    "publication_date": "Unknown",
                    "document_type": "Unknown",
                    "citation": f"Citation for {url}"
                } for url in urls}