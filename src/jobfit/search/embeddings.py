"""Versioned preparation and resumable batches. No labels or test CVs."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import yaml
from jobfit.config import REPO_ROOT


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class EmbeddingSpec:
    model: str
    dimensions: int
    preprocessing_version: str
    max_input_tokens: int
    tokenizer: str
    tokenizer_revision: str

    @property
    def profile_id(self):
        return sha256(json.dumps(asdict(self), sort_keys=True))


def load_specs(models_file=REPO_ROOT / 'config/models_v1.yaml'):
    models = yaml.safe_load(Path(models_file).read_text())['embeddings']
    retrieval = yaml.safe_load((REPO_ROOT / 'config/retrieval_v1.yaml').read_text())
    tokenizers = json.loads((REPO_ROOT / 'config/tokenizers_v1.json').read_text())
    return [EmbeddingSpec(m['id'], m['dimensions'], retrieval['preprocessing_version'],
                          m['max_input_tokens'], m['tokenizer'],
                          tokenizers[m['tokenizer']]['sha256'] if m['tokenizer'] in tokenizers
                          else 'cl100k_base-v1') for m in models.values()]


class ModelTokenizer:
    def __init__(self, spec):
        cache = REPO_ROOT / 'reports/tokenizers'
        if spec.tokenizer == 'cl100k_base':
            import tiktoken
            os.environ['TIKTOKEN_CACHE_DIR'] = str(cache / 'tiktoken')
            self.encoder = tiktoken.get_encoding('cl100k_base')
            self.is_openai = True
        else:
            from tokenizers import Tokenizer
            path = cache / 'qwen3-embedding-8b-tokenizer.json'
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != spec.tokenizer_revision:
                raise ValueError('missing or changed Qwen tokenizer; run setup_embedding_tokenizers.py')
            self.encoder = Tokenizer.from_file(str(path))
            self.encoder.no_truncation()
            self.is_openai = False

    def encode(self, text):
        if self.is_openai:
            return self.encoder.encode(text, disallowed_special=())
        return self.encoder.encode(text, add_special_tokens=False).ids


@dataclass(frozen=True)
class PreparedText:
    document_id: str
    source_hash: str
    input_hash: str
    text: str
    original_tokens: int
    input_tokens: int
    truncated: bool


def prepare(document_id, text, spec, tokenizer, source_hash=None):
    text = text.replace('\r\n', '\n').replace('\r', '\n').strip()
    if not text:
        raise ValueError('empty embedding input')
    original_tokens = len(tokenizer.encode(text))
    original_hash = source_hash or sha256(text)
    if original_tokens > spec.max_input_tokens:
        # Keep a literal source prefix: no invented replacement characters from
        # decoding an incomplete token. Exact token check after the search.
        low, high = 0, len(text)
        while low < high:
            mid = (low + high + 1) // 2
            if len(tokenizer.encode(text[:mid])) <= spec.max_input_tokens:
                low = mid
            else:
                high = mid - 1
        text = text[:low]
    count = len(tokenizer.encode(text))
    if not text.strip() or count > spec.max_input_tokens:
        raise ValueError('invalid truncated input')
    return PreparedText(document_id, original_hash, sha256(text), text,
                        original_tokens, count, count < original_tokens)


def job_text(job):
    return (job.get('normalized_title') or job['title']).strip() + '\n\n' + job['description_clean'].strip()


def cv_body(path):
    """Comments are administration, not semantic input or system date controls."""
    return re.sub(r'<!--.*?-->', '', Path(path).read_text(), flags=re.S).strip()


def validate_vector(vector, dimensions):
    if len(vector) != dimensions or not all(math.isfinite(x) for x in vector) or not any(vector):
        raise ValueError('invalid embedding vector')


def batches(documents, size=16, max_tokens=64000):
    if size < 1 or max_tokens < 1:
        raise ValueError('invalid batch limits')
    batch, count = [], 0
    for doc in documents:
        if doc.input_tokens > max_tokens:
            raise ValueError('single input exceeds batch token limit')
        if batch and (len(batch) >= size or count + doc.input_tokens > max_tokens):
            yield batch
            batch, count = [], 0
        batch.append(doc)
        count += doc.input_tokens
    if batch:
        yield batch


def build(documents, spec, client, store, batch_size=16, max_batch_tokens=64000, progress=None,
          response_cache=None):
    """Stop at first failure; resume skips committed exact-profile inputs."""
    missing = [d for d in documents if not store.contains(spec, d)]
    result = dict(documents=len(documents), cached=len(documents)-len(missing),
                  succeeded=0, failed=0, not_attempted=len(missing),
                  truncated=sum(d.truncated for d in documents), recovered=0, api_inputs=0, error_type=None)
    for batch in batches(missing, batch_size, max_batch_tokens):
        try:
            recovered = {d.document_id: response_cache.get(spec,d) for d in batch} if response_cache else {}
            needed = [d for d in batch if recovered.get(d.document_id) is None]
            if needed:
                fresh = client.embed([d.text for d in needed], model=spec.model, dimensions=spec.dimensions)
                if len(fresh) != len(needed):
                    raise ValueError('incomplete embedding batch')
                for vector in fresh:
                    validate_vector(vector, spec.dimensions)
                if response_cache:
                    response_cache.save_batch(spec, list(zip(needed,fresh)))
                result['api_inputs'] += len(needed)
                recovered.update({d.document_id:v for d,v in zip(needed,fresh)})
            result['recovered'] += len(batch) - len(needed)
            vectors = [recovered[d.document_id] for d in batch]
            if len(vectors) != len(batch):
                raise ValueError('incomplete embedding batch')
            for vector in vectors:
                validate_vector(vector, spec.dimensions)
            store.save_batch(spec, list(zip(batch, vectors)))
        except Exception as exc:
            result['failed'] += len(batch)
            result['not_attempted'] -= len(batch)
            result['error_type'] = type(exc).__name__
            if progress:
                progress(dict(result))
            return result
        result['succeeded'] += len(batch)
        result['not_attempted'] -= len(batch)
        if progress:
            progress(dict(result))
    return result
