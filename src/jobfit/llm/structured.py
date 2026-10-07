"""One validation repair, shared by all CP2.2 stages; no transport retries here."""
from __future__ import annotations
import json
from typing import Callable, Protocol, TypeVar
from pydantic import BaseModel, ValidationError
from jobfit.llm.client import TruncatedStructuredResponse

T = TypeVar('T', bound=BaseModel)
STRUCTURED_MAX_TOKENS = 16000
REPAIR_CONTEXT_MAX_BYTES = 16000

def schema_error_codes(exc: ValidationError, output_model: type[BaseModel]) -> list[dict]:
    """Schema-owned field paths and error kinds only; no model inputs or messages."""
    names=set()
    def collect(node):
        if isinstance(node,dict):
            names.update(node.get('properties',{}))
            for value in node.values(): collect(value)
        elif isinstance(node,list):
            for value in node:collect(value)
    collect(output_model.model_json_schema())
    return [{'type':e['type'],'path':[p if isinstance(p,int) or p in names else '<field>' for p in e['loc']]}
            for e in exc.errors(include_input=False,include_context=False,include_url=False)[:12]]

class StructuredClient(Protocol):
    def chat_structured(self, model: str, messages: list[dict], output_model: type[T],
                        task: str, max_tokens: int = 2000, temperature: float = 0.0) -> T: ...

class StageFailure(RuntimeError):
    """Safe status without provider exception text or source data."""
    def __init__(self, stage: str, code: str, attempts: int):
        self.stage, self.code, self.attempts = stage, code, attempts
        super().__init__(f'{stage}: {code} ({attempts} attempt(s))')

def validated_call(client: StructuredClient, *, model: str, prompt: str, payload: dict,
                   output_model: type[T], task: str, validate: Callable[[T], None],
                   max_tokens: int = STRUCTURED_MAX_TOKENS,
                   model_output_limit: int | None = None) -> tuple[T, int]:
    messages = [{'role':'system','content':prompt},
                {'role':'user','content':json.dumps({'untrusted_document_data':payload},ensure_ascii=False)}]
    calls=0
    repairs=0
    continued=False
    current_limit=max_tokens
    call_kind='initial'
    while True:
        out = None
        try:
            calls+=1
            ledger_task=task if call_kind=='initial' else f'{task}_{call_kind}'
            out = client.chat_structured(model, messages, output_model, ledger_task, max_tokens=current_limit)
            out = output_model.model_validate(out)
            validate(out)
            return out, calls
        except ValueError as exc:
            if isinstance(exc,TruncatedStructuredResponse) and model_output_limit is not None:
                next_limit=min(model_output_limit,current_limit*2)
                if not continued and next_limit>current_limit:
                    continued=True
                    current_limit=next_limit
                    call_kind='length_continuation'
                    # The incomplete response is not trusted or reused. This is
                    # a single fresh completion, separate from validation repair.
                    messages.append({'role':'user','content':'The previous structured response ended at its output limit. Return one fresh complete result with the same source and rules. This is the only length continuation.'})
                    continue
                raise StageFailure(task,'truncated',calls) from None
            # Only fixed, application-owned codes enter diagnostics or repair instructions.
            safe_codes = {'invalid_source_quote', 'missing_source_quote', 'evidence_section_mismatch',
                'employment_must_be_experience', 'duplicate_fact_id', 'no_sections_or_evidence',
                'job_identity_mismatch', 'assessment_coverage', 'branch_coverage',
                'empty_extraction_despite_requirement_section',
                'qualification_inventory_incomplete', 'qualification_inventory_unsupported_mapping',
                'group_label_must_be_resolved_by_scorer', 'unresolved_unit_needs_review',
                'qualified_MATCH_needs_bounded_duration', 'unbounded_required_duration_needs_clarification'}
            code = str(exc) if str(exc) in safe_codes else 'invalid_structured_output_or_source'
            schema_issues = schema_error_codes(exc,output_model) if isinstance(exc,ValidationError) else []
            if schema_issues: code='schema_validation'
            if type(exc).__name__ in {'IncompleteStructuredResponse', 'UnexpectedResponseModel'}:
                code = type(exc).__name__
            if repairs>=1: raise StageFailure(task,code,calls) from None
            repairs+=1
            call_kind='validation_repair'
            # No model-returned instructions, source fragments or exception contents promoted to system text.
            if isinstance(out, BaseModel):
                prior = out.model_dump_json()
                if len(prior.encode('utf-8')) <= REPAIR_CONTEXT_MAX_BYTES:
                    messages.append({'role':'assistant','content':prior})
            messages.append({'role':'user','content':f'The previous response failed validation ({code}). Return a fresh complete result. Verify IDs, required fields, exact source substrings and dates. Preserve literal newlines in quotes. Do not invent missing facts. This is the only repair attempt.'})
            if schema_issues:
                messages[-1]['content']+=' Schema errors (field paths only): '+json.dumps(schema_issues)
        except Exception as exc:
            raise StageFailure(task,type(exc).__name__,calls) from None
