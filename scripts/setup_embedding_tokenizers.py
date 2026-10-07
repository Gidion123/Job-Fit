"""Download tokenizer data only. No weights, model calls, or CV/JD transmission."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import hashlib
import json
import os
import httpx
from jobfit.config import REPO_ROOT


def main():
    cache = REPO_ROOT / 'reports/tokenizers'
    cache.mkdir(parents=True, exist_ok=True)
    pinned = json.loads((REPO_ROOT / 'config/tokenizers_v1.json').read_text())['qwen3-embedding-8b']
    path = cache / 'qwen3-embedding-8b-tokenizer.json'
    if not path.exists():
        response = httpx.get(pinned['url'], follow_redirects=True, timeout=60)
        response.raise_for_status()
        if hashlib.sha256(response.content).hexdigest() != pinned['sha256']:
            raise ValueError('tokenizer download hash mismatch')
        path.write_bytes(response.content)
    if hashlib.sha256(path.read_bytes()).hexdigest() != pinned['sha256']:
        raise ValueError('existing tokenizer hash mismatch; inspect without overwriting')
    os.environ['TIKTOKEN_CACHE_DIR'] = str(cache / 'tiktoken')
    import tiktoken
    tiktoken.get_encoding('cl100k_base')
    print('Pinned Qwen tokenizer and cl100k_base cache ready; no inference calls.')


if __name__ == '__main__':
    main()
