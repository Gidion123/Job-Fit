from jobfit.search.pools import pool_rows


def rankings(n=6):
    return {str(i): [{'job_id': f'{i}-{j}'} for j in range(10)] for i in range(n)}


def test_top_five_over_cap_blocks_instead_of_dropping():
    rs = rankings()
    titles = {r['job_id']: r['job_id'] for rows in rs.values() for r in rows}
    rows, info = pool_rows('CV1', rs, titles, set())
    assert info['mandatory_new_top5'] == 30 and info['selection_blocked']
    assert info['selected_new'] == 0
    assert all(r['gold_review'] == 'pending_decision' for r in rows)


def test_gold_exclusion_and_deterministic_selection():
    rs = rankings(2)
    titles = {r['job_id']: r['job_id'] for rows in rs.values() for r in rows}
    first, info = pool_rows('CV1', rs, titles, {'0-0'}, limit=12)
    assert info['selected_new'] == 12 and not info['selection_blocked']
    assert next(r for r in first if r['job_id'] == '0-0')['gold_review'] == 'no'
    assert first == pool_rows('CV1', rs, titles, {'0-0'}, limit=12)[0]
    assert all(r['gold_review'] == 'yes' for r in first
               if r['in_top5_any'] == 'yes' and r['already_gold'] == 'no')
