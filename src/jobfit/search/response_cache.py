"""Durable API receipts for offline embedding builds, without input text.

SQLite commits a whole response before PostgreSQL writes. A database write
failure can therefore resume without paying for the same returned vectors.
There is no distributed exactly-once guarantee if the process dies between
the provider response and this receipt commit.
"""
import json
import sqlite3
from jobfit.search.embeddings import validate_vector


class ResponseCache:
    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute('PRAGMA synchronous=FULL')
        self.conn.execute('CREATE TABLE IF NOT EXISTS receipts ('
                          'profile_id TEXT, document_id TEXT, source_hash TEXT, input_hash TEXT, '
                          'vector_json TEXT NOT NULL, PRIMARY KEY(profile_id,document_id,source_hash,input_hash))')
        self.conn.commit()

    @staticmethod
    def key(spec, doc):
        return spec.profile_id, doc.document_id, doc.source_hash, doc.input_hash

    def get(self, spec, doc):
        row = self.conn.execute('SELECT vector_json FROM receipts WHERE profile_id=? '
                                'AND document_id=? AND source_hash=? AND input_hash=?',
                                self.key(spec,doc)).fetchone()
        if row is None:
            return None
        vector = json.loads(row[0])
        validate_vector(vector, spec.dimensions)
        return vector

    def save_batch(self, spec, pairs):
        with self.conn:
            for doc, vector in pairs:
                validate_vector(vector, spec.dimensions)
                self.conn.execute('INSERT OR IGNORE INTO receipts VALUES (?,?,?,?,?)',
                                  (*self.key(spec,doc), json.dumps(vector)))

    def close(self):
        self.conn.close()
