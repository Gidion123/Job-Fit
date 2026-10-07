"""Content/version-scoped cache; disk persistence is restricted to public corpus JDs."""
from pathlib import Path
from hashlib import sha256
import json, os, uuid

def content_hash(text: str) -> str:
    return sha256(text.encode()).hexdigest()

def cache_key(*, text: str, model: str, schema: str, prompt: str,
              preprocessing: str, guideline: str, scope: str, context: dict | None=None) -> str:
    return content_hash(json.dumps({'content':content_hash(text),'model':model,'schema':schema,
        'prompt':content_hash(prompt),'preprocessing':preprocessing,'guideline':guideline,
        'scope':scope,'context':context or {}},sort_keys=True,ensure_ascii=False))

class ExtractionCache:
    def __init__(self, directory: Path | None=None):
        self.directory=directory
        self._memory={}

    def get(self,key: str, *, scope: str) -> dict | None:
        self._validate_key(key)
        self._validate_scope(scope)
        if (scope,key) in self._memory: return json.loads(json.dumps(self._memory[(scope,key)]))
        if self.directory is not None and scope=='corpus_jd':
            p=self.directory/f'{key}.json'
            if p.exists():
                try:
                    row=json.loads(p.read_text())
                    if (isinstance(row,dict) and row.get('scope')=='corpus_jd'
                            and row.get('key')==key and isinstance(row.get('value'),dict)
                            and content_hash(json.dumps(row['value'],sort_keys=True))==row.get('value_hash')):
                        return row['value']
                except (ValueError,KeyError,TypeError): pass
        return None

    def put(self,key: str,value: dict, *, scope: str) -> None:
        self._validate_key(key)
        self._validate_scope(scope)
        if not isinstance(value,dict): raise ValueError('cache value must be a record')
        value=json.loads(json.dumps(value))
        if self.directory is not None and scope=='corpus_jd':
            self.directory.mkdir(parents=True,exist_ok=True)
            record={'key':key,'scope':scope,'value':value,'value_hash':content_hash(json.dumps(value,sort_keys=True))}
            tmp=self.directory/f'{key}.{uuid.uuid4().hex}.tmp'
            with tmp.open('x') as f:
                json.dump(record,f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
            os.replace(tmp,self.directory/f'{key}.json')
        self._memory[(scope,key)]=value

    @staticmethod
    def _validate_scope(scope):
        if scope not in {'corpus_jd','session_jd','session_evidence'}: raise ValueError('invalid cache scope')

    @staticmethod
    def _validate_key(key):
        if len(key)!=64 or any(c not in '0123456789abcdef' for c in key): raise ValueError('invalid cache key')
