import re
from typing import List, Dict, Any, Optional, Tuple, Iterable
from ahocorasick import Automaton
from src.ingestion.utils import split_sentences, normalize_text, get_ngrams
from src.similarity_search.web_fetcher import fetch_full_text
from src.similarity_search import configs
from src.similarity_search.similarity_engine import semantic_similarity
import spacy
from spacy.tokens import Doc
import asyncio
import aiohttp
from aiohttp import ClientTimeout
import logging
from concurrent.futures import ThreadPoolExecutor
import time
import mimetypes
from functools import partial

logger = logging.getLogger(__name__)

# ============================================================
# Global executor + concurrency controls
# ============================================================
# Single global executor reused across the module (do not create ad-hoc)
GLOBAL_EXECUTOR = ThreadPoolExecutor(max_workers=8)  # tune as needed

# Semaphore to limit concurrent fetches across program
DEFAULT_FETCH_SEMAPHORE = asyncio.Semaphore(20)

# ============================================================
# Load spaCy once (synchronous loader). We'll run processing in executor.
# ============================================================
nlp = spacy.load("en_core_web_sm")

# ============================================================
# Utility async wrappers for CPU-bound functions
# ============================================================
async def run_in_executor(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    fn = partial(func, *args, **kwargs)
    return await loop.run_in_executor(GLOBAL_EXECUTOR, fn)

async def batch_spacy_process(texts: Iterable[str], batch_size: int = 64) -> List[Doc]:
    def _pipe(texts_slice):
        return list(nlp.pipe(texts_slice, batch_size=32))

    results = []
    texts = list(texts)
    for i in range(0, len(texts), batch_size):
        slice_texts = texts[i:i + batch_size]
        docs = await run_in_executor(_pipe, slice_texts)
        results.extend(docs)
    return results
    return results


async def async_semantic_similarity(a: str, b: str) -> float:
    return await run_in_executor(semantic_similarity, a, b)


# ============================================================
# NLP / Meaningfulness (batched)
# ============================================================
async def are_meaningful_sentences(sentences: List[str], batch_size: int = 64) -> List[bool]:
    results = [False] * len(sentences)
    if not sentences:
        return results

    docs = await batch_spacy_process(sentences, batch_size=batch_size)
    for i, doc in enumerate(docs):
        tokens = doc
        has_verb = any(tok.pos_ == "VERB" for tok in tokens)
        has_nsubj = any(tok.dep_ in {"nsubj", "nsubjpass"} for tok in tokens)
        results[i] = (len(sentences[i].split()) >= 3) and has_verb and has_nsubj
    return results


# ============================================================
# PDF Detection
# ============================================================
def is_pdf_url(url: str) -> bool:
    url = url.lower()
    if url.endswith(".pdf"):
        return True
    guessed = mimetypes.guess_type(url)[0]
    if guessed == "application/pdf":
        return True
    return False


# ============================================================
# Helper functions
# ============================================================
def build_aho_automaton(sentences: List[str]) -> Automaton:
    A = Automaton()
    for idx, sent in enumerate(sentences):
        if sent.strip():
            A.add_word(sent, (idx, sent))
    A.make_automaton()
    return A


def expand_exact_match(sentence: str, source_text: str, max_len: int = 500) -> str:
    sentence_norm = normalize_text(sentence)
    source_norm = normalize_text(source_text)
    if sentence_norm in source_norm:
        start_idx = source_norm.find(sentence_norm)
        end_idx = start_idx + len(sentence_norm)
        source_sents = split_sentences(source_text)
        for s in source_sents:
            s_norm = normalize_text(s)
            if sentence_norm in s_norm and len(s) > len(sentence):
                return s[:max_len]
        return source_text[start_idx:end_idx]
    return ""


def extract_best_snippet(sentence: str, source_text: str) -> str:
    snippet = expand_exact_match(sentence, source_text)
    if snippet:
        return snippet
    sentence_words = set(sentence.split())
    words = source_text.split()
    max_overlap, best_start, best_end = 0, 0, 0
    window_size = max(1, len(sentence_words))
    for i in range(0, max(0, len(words) - window_size + 1)):
        window_words = set(words[i:i + window_size])
        overlap = len(sentence_words & window_words)
        if overlap > max_overlap:
            max_overlap = overlap
            best_start, best_end = i, i + window_size
    return " ".join(words[best_start:best_end]) if max_overlap > 0 else source_text[:min(200, len(source_text))]



def idea_similarity_evidence(sentence: str) -> Dict[str, Any]:
    return {
        "sentence": sentence,
        "type": "idea_similarity",
        "source_text": "",
        "plagiarism_score": 0.3,
        "semantic_similarity": 0.0,
        "source_url": "",
        "highlights": [{"start": 0, "end": len(sentence), "type": "idea_similarity"}]
    }


# ============================================================
# Evidence Generators (patched)
# ============================================================
async def exact_match_evidence(sentences: List[str],
                               source_text: str,
                               source_url: str,
                               meaningful_flags: Optional[List[bool]] = None) -> List[Dict[str, Any]]:
    evidence = []
    source_sentences = split_sentences(source_text)
    source_text_norm = normalize_text(source_text)

    if meaningful_flags is None:
        meaningful_flags = await are_meaningful_sentences(sentences)

    tasks = []
    for idx, sent in enumerate(sentences):
        sent_norm = normalize_text(sent)
        if sent_norm in source_text_norm and meaningful_flags[idx]:
            start_idx = source_text_norm.find(sent_norm)
            end_idx = start_idx + len(sent_norm)
            snippet = source_text[start_idx:end_idx]
            tasks.append((idx, sent, snippet, source_url, "exact"))
        else:
            matched = False
            for i, src_sent in enumerate(source_sentences):
                if sent_norm in normalize_text(src_sent):
                    expanded = source_sentences[max(0, i - 1): min(len(source_sentences), i + 2)]
                    snippet = " ".join(expanded)
                    tasks.append((idx, sent, snippet, source_url, "exact"))
                    matched = True
                    break

    sem_tasks = [async_semantic_similarity(t[1], t[2]) for t in tasks]
    sem_scores = await asyncio.gather(*sem_tasks, return_exceptions=True)

    for (idx, sent, snippet, src_url, _typ), sem_score in zip(tasks, sem_scores):

        # --- PATCHED HERE ---
        if isinstance(sem_score, BaseException):
            logger.warning("semantic_similarity failed for %s: %s", src_url, sem_score)
            sem_score = 0.0
        else:
            sem_score = float(sem_score)
        # --------------------

        evidence.append({
            "sentence": sent,
            "type": "exact_match",
            "source_text": snippet,
            "plagiarism_score": 0.99,
            "semantic_similarity": round(sem_score, 2),
            "source_url": src_url,
            "highlights": [{"start": 0, "end": len(snippet), "type": "exact"}]
        })
    return evidence


async def paraphrase_match_evidence(sentences: List[str],
                                    source_text: str,
                                    source_url: str,
                                    skip_sents: set,
                                    meaningful_flags: Optional[List[bool]] = None) -> List[Dict[str, Any]]:
    evidence = []
    source_text_norm = normalize_text(source_text)

    if meaningful_flags is None:
        meaningful_flags = await are_meaningful_sentences(sentences)

    tasks = []
    for idx, sent in enumerate(sentences):
        if sent in skip_sents:
            continue
        if not meaningful_flags[idx]:
            continue

        sent_words = set(sent.split())
        src_words = source_text_norm.split()
        overlap = len(sent_words & set(src_words)) / max(len(sent_words), 1)

        if 0.4 <= overlap < 0.99:
            snippet = extract_best_snippet(sent, source_text_norm)
            tasks.append((sent, snippet, source_url))

    sem_tasks = [async_semantic_similarity(t[0], t[1]) for t in tasks]
    sem_scores = await asyncio.gather(*sem_tasks, return_exceptions=True)

    for (sent, snippet, src_url), sem_score in zip(tasks, sem_scores):

        # --- PATCHED HERE ---
        if isinstance(sem_score, BaseException):
            logger.warning("semantic_similarity failed for paraphrase: %s", sem_score)
            sem_score = 0.0
        else:
            sem_score = float(sem_score)
        # --------------------

        overlap = round(len(set(sent.split()) & set(normalize_text(snippet).split())) / max(len(sent.split()), 1), 2)

        evidence.append({
            "sentence": sent,
            "type": "paraphrased_match",
            "source_text": snippet,
            "plagiarism_score": overlap,
            "semantic_similarity": round(sem_score, 2),
            "source_url": src_url,
            "highlights": [{"start": 0, "end": len(snippet), "type": "paraphrase"}]
        })

    return evidence


# ============================================================
# Async scraping
# ============================================================
async def fetch_url_text(session: aiohttp.ClientSession, url: str, fetch_semaphore: asyncio.Semaphore) -> Tuple[str, Optional[str], bool]:
    if not configs.ALLOW_PDF_SCRAPING and is_pdf_url(url):
        logger.info("Skipping PDF: %s", url)
        return url, None, True

    async with fetch_semaphore:
        try:
            text = await run_in_executor(fetch_full_text, url)
            return url, text, False
        except Exception as e:
            logger.warning("Failed to fetch text from %s: %s", url, e)
            return url, None, False


class Fetcher:
    def __init__(self, concurrency: int = 20, timeout_seconds: int = 30):
        self._connector = aiohttp.TCPConnector(limit=concurrency)
        self._timeout = ClientTimeout(total=timeout_seconds)
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(concurrency)

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(connector=self._connector, timeout=self._timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.close()
            self._session = None
        await self._connector.close()

    @property
    def semaphore(self):
        return self._semaphore

    async def fetch_batch(self, urls: List[str]) -> List[Tuple[str, Optional[str], bool]]:
        session = self._session
        if session is None:
            raise RuntimeError("Fetcher session is not initialized.")
        tasks = [fetch_url_text(session, url, self._semaphore) for url in urls]
        results = await asyncio.gather(*tasks)
        return results


async def fetch_urls_in_batches_async(urls: List[str], batch_size: int = 20, concurrency: int = 20):
    results = []
    if not urls:
        return results

    async with Fetcher(concurrency=concurrency) as fetcher:
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            logger.info("Processing batch %d-%d", i + 1, i + len(batch))
            batch_results = await fetcher.fetch_batch(batch)
            results.extend(batch_results)
    return results


# ============================================================
# Main Evidence Generator
# ============================================================
async def generate_sentence_level_evidence_async(block: Dict[str, Any],
                                                 batch_size: int = 20,
                                                 concurrency: int = 20,
                                                 nlp_batch_size: int = 64):
    sentences = split_sentences(block.get("key_sentences", ""))
    if not sentences:
        return {"evidence": [], "skipped_pdf_urls": []}

    candidate_urls = [c.get("url") for c in block.get("candidates", []) if c.get("url")]
    url_results = {url: None for url in candidate_urls}
    skipped_pdfs = []

    fetched = await fetch_urls_in_batches_async(candidate_urls, batch_size=batch_size, concurrency=concurrency)
    for url, text, skipped_pdf in fetched:
        if skipped_pdf:
            skipped_pdfs.append(url)
        url_results[url] = text

    meaningful_flags = await are_meaningful_sentences(sentences, batch_size=nlp_batch_size)

    evidence_list: List[Dict[str, Any]] = []
    exact_matched = set()
    paraphrased_matched = set()

    for candidate in block.get("candidates", []):
        url = candidate.get("url")
        snippet = candidate.get("snippet", "")
        source_text = url_results.get(url) or snippet
        if not source_text:
            continue

        ex = await exact_match_evidence(sentences, source_text, url, meaningful_flags=meaningful_flags)
        evidence_list.extend(ex)
        exact_matched.update(ev["sentence"] for ev in ex)

        remaining = [s for s in sentences if s not in exact_matched]
        if remaining:
            idx_map = {s: i for i, s in enumerate(sentences)}
            remaining_flags = [meaningful_flags[idx_map[s]] for s in remaining]
            pr = await paraphrase_match_evidence(remaining, source_text, url, skip_sents=set(), meaningful_flags=remaining_flags)
            evidence_list.extend(pr)
            paraphrased_matched.update(ev["sentence"] for ev in pr)

    for s in sentences:
        if s not in exact_matched and s not in paraphrased_matched:
            evidence_list.append(idea_similarity_evidence(s))

    return {
        "evidence": evidence_list,
        "skipped_pdf_urls": skipped_pdfs
    }


# ============================================================
# Module 3 Processor
# ============================================================
async def process_module3(module2_json: Dict[str, Any], batch_size: int = 20, concurrency: int = 20, nlp_batch_size: int = 64):
    results = []
    doc_id = module2_json.get("doc_id", "unknown")
    blocks = module2_json.get("blocks", [])

    block_semaphore = asyncio.Semaphore(concurrency)

    async def _process_block_with_semaphore(block):
        async with block_semaphore:
            return await generate_sentence_level_evidence_async(block,
                                                               batch_size=batch_size,
                                                               concurrency=concurrency,
                                                               nlp_batch_size=nlp_batch_size)

    tasks = [asyncio.create_task(_process_block_with_semaphore(block)) for block in blocks]
    gathered = await asyncio.gather(*tasks)
    for block, res in zip(blocks, gathered):
        results.append({
            "block_id": block.get("block_id"),
            "evidence": res["evidence"],
            "skipped_pdf_urls": res["skipped_pdf_urls"]
        })

    return {"doc_id": doc_id, "results": results}
