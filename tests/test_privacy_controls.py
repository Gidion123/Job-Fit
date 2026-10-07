from dataclasses import replace
from datetime import date
from types import SimpleNamespace
import pytest
from jobfit.privacy.masking import mask_local
from jobfit.session.store import SessionStore, SessionHandle, SessionDenied
from jobfit.privacy.boundary import embed_session_cv, parse_session_cv, match_session_cv

@pytest.fixture
def state():
    now=[0.0]
    store=SessionStore(clock=lambda:now[0])
    user=store.create()
    preview=mask_local('Rina Example\nPython SQL\nrina@example.com',reviewed_identifiers={'name':('Rina Example',)})
    lease=store.set_preview(user,preview)
    return store,user,preview,lease,now

@pytest.mark.parametrize('source',[
    'Nama: Rina Example\nSummary: Python SQL\nFooter rina@example.com +62 812-3456-7890',
    'Summary Python SQL. Contact rina@example.com. Rina Example. NIK: 3276012345678901',
    'Sidebar Rina Example\nLinkedIn: https://linkedin.com/in/rina-example\nGitHub github.com/rina-example\nPython SQL 2025 - 2026 F1 0.78',
])
def test_full_text_identifiers_masked_professional_content_preserved(source):
    out=mask_local(source,reviewed_identifiers={'name':('Rina Example',)})
    assert 'Rina Example' not in out.text and 'rina@example.com' not in out.text
    assert '+62 812' not in out.text and '3276012345678901' not in out.text
    assert 'linkedin.com' not in out.text and 'github.com/rina-example' not in out.text
    assert 'Python SQL' in out.text
    assert 'Rina' not in repr(out)


def test_numbers_dates_repositories_and_pending_location_policy():
    raw='Jakarta · PT Example · Universitas Example\nPython SQL 2025 - 2026 F1 0.78\ngithub.com/person/project'
    assert mask_local(raw).text==raw
    with pytest.raises(ValueError):mask_local(' ')
    with pytest.raises(ValueError):mask_local(raw,reviewed_identifiers={'employer':('PT Example',)})


def test_no_transmission_without_exact_consent(state):
    store,user,preview,lease,_=state;calls=[]
    with pytest.raises(SessionDenied):store.dispatch(user,lease,lambda text:calls.append(text))
    with pytest.raises(SessionDenied):store.consent(user,exact_digest='wrong',affirmative=True)
    with pytest.raises(SessionDenied):store.consent(user,exact_digest=preview.digest,affirmative=False)
    assert calls==[]
    lease=store.consent(user,exact_digest=preview.digest,affirmative=True)
    store.dispatch(user,lease,lambda text:calls.append(text))
    assert calls==[preview.text]


def test_edits_invalidate_results_consent_and_inflight_token(state):
    store,user,preview,lease,_=state
    lease=store.consent(user,exact_digest=preview.digest,affirmative=True)
    store.put(user,lease,'parsed',{'value':'private'})
    replacement=mask_local(preview.text+'\nR')
    newer=store.set_preview(user,replacement)
    with pytest.raises(SessionDenied):store.read(user,lease,'parsed')
    with pytest.raises(SessionDenied):store.dispatch(user,newer,lambda text:text)
    newer=store.consent(user,exact_digest=replacement.digest,affirmative=True)
    with pytest.raises(KeyError):store.read(user,newer,'parsed')


def test_ownership_is_checked_on_read_write_delete_and_heartbeat(state):
    store,user,preview,lease,_=state
    lease=store.consent(user,exact_digest=preview.digest,affirmative=True)
    other=store.create(); swapped=SessionHandle(user.session_id,other.credential)
    for action in [lambda:store.read(swapped,lease,'key'),lambda:store.put(swapped,lease,'key','bad'),
                   lambda:store.delete(swapped),lambda:store.heartbeat(swapped)]:
        with pytest.raises(SessionDenied):action()
    store.put(user,lease,'key',{'values':[]});copy=store.read(user,lease,'key');copy['values'].append('bad')
    assert store.read(user,lease,'key')=={'values':[]}


def test_delete_during_call_discards_late_response(state):
    store,user,preview,lease,_=state
    lease=store.consent(user,exact_digest=preview.digest,affirmative=True)
    def provider(text):store.delete(user);return 'late private response'
    with pytest.raises(SessionDenied):store.dispatch(user,lease,provider)
    assert user.session_id not in store._states
    with pytest.raises(SessionDenied):store.put(user,lease,'result','late')


def test_disconnect_deadline_and_periodic_sweep(state):
    store,user,preview,lease,now=state
    now[0]=119;assert store.preview(user)[0]==preview.text
    now[0]=120;assert store.sweep()==1
    with pytest.raises(SessionDenied):store.preview(user)


def test_heartbeats_do_not_extend_idle_or_absolute_lifetime():
    now=[0.];store=SessionStore(clock=lambda:now[0],disconnect_seconds=120,idle_seconds=150,absolute_seconds=300)
    user=store.create();now[0]=100;store.heartbeat(user);now[0]=150
    with pytest.raises(SessionDenied):store.heartbeat(user)
    now[0]=0;user=store.create()
    for t in [100,200,299]:now[0]=t;store.heartbeat(user,user_activity=True)
    now[0]=300
    with pytest.raises(SessionDenied):store.preview(user)


def test_changed_preview_while_call_is_running_discards_response(state):
    store,user,preview,lease,_=state;lease=store.consent(user,exact_digest=preview.digest,affirmative=True)
    def provider(text):store.set_preview(user,mask_local(text+'\nNew text'));return 'stale'
    with pytest.raises(SessionDenied):store.dispatch(user,lease,provider)


def test_both_provider_boundaries_use_exact_preview_and_real_path_stays_blocked(state,monkeypatch):
    store,user,preview,lease,_=state;calls=[]
    client=SimpleNamespace(embed=lambda texts,**kw:calls.extend(texts))
    with pytest.raises(SessionDenied):embed_session_cv(store,user,lease,client=client,model='fake',is_synthetic=True)
    lease=store.consent(user,exact_digest=preview.digest,affirmative=True)
    embed_session_cv(store,user,lease,client=client,model='fake',is_synthetic=True)
    monkeypatch.setattr('jobfit.privacy.boundary.parse_cv',lambda text,**kw:calls.append(text.text))
    parse_session_cv(store,user,lease,client=client,model='fake',analysis_date=date(2026,9,30),is_synthetic=True)
    assert calls==[preview.text,preview.text]
    for action in [lambda:embed_session_cv(store,user,lease,client=client,model='fake',is_synthetic=False),
                   lambda:parse_session_cv(store,user,lease,client=client,model='fake',analysis_date=date(2026,9,30),is_synthetic=False)]:
        with pytest.raises(ValueError,match='disabled'):action()
    assert len(calls)==2


def test_masked_matching_rejects_stale_source(state,monkeypatch):
    store,user,preview,lease,_=state;lease=store.consent(user,exact_digest=preview.digest,affirmative=True)
    monkeypatch.setattr('jobfit.privacy.boundary.match_evidence',lambda *a,**kw:'accepted')
    cv=SimpleNamespace(profile=SimpleNamespace(is_synthetic=True,raw_text=preview.text))
    assert match_session_cv(store,user,lease,cv=cv,extraction=None,client=None,model='fake')=='accepted'
    cv.profile.raw_text='raw original text'
    with pytest.raises(ValueError):match_session_cv(store,user,lease,cv=cv,extraction=None,client=None,model='fake')

@pytest.mark.parametrize('timeout',[0,-1,float('nan'),float('inf'),True])
def test_invalid_timeout_rejected(timeout):
    with pytest.raises(ValueError):SessionStore(disconnect_seconds=timeout)
