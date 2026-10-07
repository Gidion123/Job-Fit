from types import SimpleNamespace

from scripts.run_cp23_model_sweep import CANDIDATES, SweepAdapter, stages


def test_four_fixed_development_pairs():
    s = stages()
    assert {(x['cv_id'], x['job_id']) for x in s} == {('CV1', 'F00332'), ('CV1', 'F00036'),
                                                     ('CV2', 'F00815'), ('CV2', 'F00018')}


def test_all_requested_models_are_candidates():
    assert {'gpt-6-luna', 'deepseek-flash', 'gpt-6-sol', 'claude-haiku-4.5', 'gemini-3.5-flash-lite',
            'deepseek-v4-pro', 'claude-sonnet-5.5', 'gemini-3.8-flash', 'gemini-3.1-pro',
            'claude-opus-5.5'} == set(CANDIDATES)


def test_adapter_uses_metadata_rules_only_for_listed_models():
    sent = []

    class Fake:
        chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: sent.append(kw)))

    rules = {'m/no-temp': {'temperature_supported': False, 'min_output_limit': 32000},
             'm/ok': {'temperature_supported': True, 'min_output_limit': None}}
    a = SweepAdapter(Fake(), rules)
    a.create(model='m/no-temp', temperature=0.0, max_tokens=60000, messages=[])
    a.create(model='m/ok', temperature=0.0, max_tokens=60000, messages=[])
    a.create(model='m/unknown', temperature=0.0, max_tokens=60000, messages=[])
    assert 'temperature' not in sent[0] and sent[0]['max_tokens'] == 32000
    assert sent[1]['temperature'] == 0.0 and sent[1]['max_tokens'] == 60000
    assert sent[2]['temperature'] == 0.0


def test_probe_classifies_workspace_budget_and_redacts_keys():
    from scripts.probe_openrouter_access import classify, redact
    msg = 'Workspace lifetime budget of $5.00 exceeded. Contact your org admin.'
    assert classify(msg, 403) == 'account_or_workspace_budget'
    assert classify('Input flagged by moderation', 403) == 'moderation'
    assert classify('No endpoints found', 404) == 'route_or_model_not_found'
    assert 'sk-or-v1-abcdefghijk' not in redact('bad key sk-or-v1-abcdefghijk here')


def test_403_stops_the_sweep_and_recovery_only_redoes_403_pairs():
    from scripts.run_cp23_model_sweep import CONT2_TASKS, STOP_ERRORS
    assert 'PermissionDeniedError' in STOP_ERRORS
    assert ('gemini-3.1-pro', 'CV2', 'F00018') in CONT2_TASKS
    assert sum(t[0] == 'claude-opus-5.5' for t in CONT2_TASKS) == 4


def test_probe_does_not_reenter_the_ledger_lock():
    from scripts.probe_openrouter_access import probe

    class Client:
        def chat_structured(self, *a, **k):
            raise AssertionError('would deadlock: nested ledger.exclusive()')

        def _chat_attempt(self, model, messages, output_model, task, max_tokens, temperature):
            assert max_tokens == 64 and task == 'access_probe'
            return output_model(reply='OK')

    assert probe(Client(), 'm') == {'model': 'm', 'ok': True, 'reply_ok': True}
