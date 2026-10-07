"""Evaluation-only cache for approved synthetic development queries CV1/CV2.

Not a production CV storage path. Contains vectors and hashes, never CV text.
"""
from dataclasses import asdict
import json
import os
import tempfile
from jobfit.search.embeddings import sha256, validate_vector


class SyntheticQueryCache:
    def __init__(self, directory):
        self.directory = directory

    def path(self, spec, doc):
        if doc.document_id not in {'CV1', 'CV2'}:
            raise ValueError('development query cache only permits CV1/CV2')
        key = sha256('|'.join((doc.document_id, spec.profile_id, doc.source_hash, doc.input_hash)))
        return self.directory / (key + '.json')

    def contains(self, spec, doc):
        if not self.path(spec, doc).exists():
            return False
        self.get(spec, doc)
        return True

    def get(self, spec, doc):
        row = json.loads(self.path(spec, doc).read_text())
        if row['profile_id'] != spec.profile_id or row['input_hash'] != doc.input_hash or row['source_hash'] != doc.source_hash:
            raise ValueError('query cache provenance mismatch')
        validate_vector(row['vector'], spec.dimensions)
        return row['vector']

    def save_batch(self, spec, pairs):
        self.directory.mkdir(parents=True, exist_ok=True)
        for doc, vector in pairs:
            validate_vector(vector, spec.dimensions)
            if self.contains(spec, doc):
                continue
            # Never publish half-written JSON. Durable API receipts can recover a
            # failed cache write without making the final path unreadable.
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', dir=self.directory,
                                                 prefix='.query-', delete=False) as f:
                    temporary = f.name
                    json.dump(dict(profile_id=spec.profile_id, profile_spec=asdict(spec),
                                   source_hash=doc.source_hash, input_hash=doc.input_hash,
                                   vector=vector), f)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temporary, self.path(spec, doc))
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
