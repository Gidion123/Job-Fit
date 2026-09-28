"""Regression tests for deterministic job-data rules (cleaning, transformation, skills).

Cases come from real failure modes seen in the CP1 corpus and the JobSentinel observations.
Run: python3 -m pytest -q tests/
"""

from src.jobs.cleaning import clean_description, derive_posted_at, normalize_employment_type
from src.jobs.skills import extract_skills
from src.jobs.transform import education_levels, experience_bucket, extract_years, role_family, role_group, title_seniority


def test_wrong_role_titles_with_ai_are_not_target():
    for title in ["AI Content Creator", "Sales Engineer AI", "AI Trainer", "Solution QA Intern — AI-Powered Testing Prep",
                  "Digital Marketing AI Specialist", "Product Manager AI"]:
        assert role_group(role_family(title)) != "target", title


def test_target_titles_are_target():
    for title in ["Machine Learning Engineer", "LLM Engineer", "Junior Data Scientist", "AI Engineer - Video Analytic",
                  "Backend Engineer (AI Engineer)", "Lead Data Scientist (Analytics) - Digital Marketing"]:
        assert role_group(role_family(title)) == "target", title


def test_indonesian_staff_is_not_a_senior_level():
    assert title_seniority("Data Analyst Staff") == "unspecified"
    assert title_seniority("Staff Machine Learning Engineer") == "lead_plus"


def test_company_history_is_not_experience_requirement():
    assert extract_years("We have been operating for over 20 years.") == (None, None, None)
    assert extract_years("Minimum 3 years of experience in ML. The company was founded 10 years ago.")[:2] == (3, None)
    assert extract_years("Pengalaman minimal 1-2 tahun di bidang data")[:2] == (1, 2)


def test_unknown_experience_is_never_entry_level():
    assert experience_bucket(None, False) == "not_stated"
    assert experience_bucket(None, True) == "entry"
    assert experience_bucket(3, True) == "3-4y"


def test_posted_at_never_uses_retrieval_time_without_relative_text():
    assert derive_posted_at(None, None, "2026-09-26T01:00:00+00:00") == (None, "unknown")
    assert derive_posted_at(None, "4 hari yang lalu", "2026-09-26T01:00:00+00:00") == ("2026-09-22", "relative_text")
    assert derive_posted_at("2026-09-20T00:00:00Z", "6 days ago", None) == ("2026-09-20", "provider_structured")


def test_cleaning_masks_contacts_and_tracking_codes():
    text, rules = clean_description("Apply: hr@example.co.id / 081234567890 #J-18808-Ljbffr")
    assert "@" not in text and "0812" not in text and "#J-" not in text
    assert {"email_masked", "phone_masked", "aggregator_tracking_code"} <= set(rules)


def test_employment_type_bilingual():
    assert normalize_employment_type("Pekerjaan tetap") == "full_time"
    assert normalize_employment_type("Kontraktor") == "contract"
    assert normalize_employment_type("Magang") == "internship"
    assert normalize_employment_type(None) == "unknown"


def test_ambiguous_skill_names():
    skills = extract_skills("Our R&D team will go beyond. Required: Python, R, SQL and Golang; Postgres; k8s")
    assert {"python", "r", "sql", "golang", "postgresql", "kubernetes"} <= set(skills)
    assert "r" not in extract_skills("Join our R&D team")
    assert "golang" not in extract_skills("Go beyond expectations")


def test_years_uses_strictest_requirement():
    text = "Minimal 5 tahun di bidang ML/DS terapan dengan setidaknya 2 tahun pengalaman pada peran kepemimpinan."
    ymin, ymax, span = extract_years(text)
    assert ymin == 5 and "5 tahun" in span
    ymin, _, _ = extract_years("6+ years of professional experience, with at least 2 years in a technical lead role.")
    assert ymin == 6
    assert extract_years("Pengalaman 1-3 tahun sebagai data analyst.")[:2] == (1, 3)


def test_education_levels():
    assert education_levels("Minimal S1 Teknik Informatika, S2 lebih diutamakan") == ["bachelor", "master"]
    assert education_levels("Experience with D3.js dashboards; Scrum Master certified") == []
    assert education_levels("Bachelor\u2019s degree or Diploma in Computer Science") == ["diploma", "bachelor"]


def test_assistant_director_ai_is_administrative():
    assert role_family('Assistant Director (AI Specialist)') == 'business_product'


def test_experience_range_and_open_upper_bound():
    assert extract_years('0-2 years of experience in ML')[:2] == (0, 2)
    assert extract_years('Our 140+ years of experience')[:2] == (None, None)
    assert extract_years('5+ years experience in ML, 2-3 years experience leading')[:2] == (5, None)


def test_country_query_cannot_override_publisher_country():
    from src.jobs.transform import normalize_location
    loc = normalize_location('Los Angeles, CA, Amerika Serikat', 'US', 'id', 'indonesia')
    assert loc['country_code'] == 'US' and loc['location_conflict']
    assert normalize_location(None, None, 'id', 'indonesia')['country_code'] is None
    assert normalize_location('Bandung • melalui LinkedIn', None, 'sg', 'foreign')['country_code'] == 'ID'


def test_relative_date_uses_its_own_observation_and_valid_dates():
    assert derive_posted_at(None, '4 days ago', '2026-09-26T01:00:00Z')[0] == '2026-09-22'
    assert derive_posted_at(None, '4 days ago', '2026-09-25T01:00:00Z')[0] == '2026-09-21'
    assert derive_posted_at('invalid', '3 weeks ago', '2026-09-26T01:00:00Z') == ('2026-09-05', 'relative_text')
    assert derive_posted_at(None, 'starts in 3 days', '2026-09-26T01:00:00Z') == (None, 'unknown')
    assert derive_posted_at(None, '4 days ago', 'invalid') == (None, 'unknown')


def test_other_language_does_not_become_english():
    from src.jobs.cleaning import detect_language
    assert detect_language('開発経験機械学習日本語要件' * 15 + 'AI engineer and ML') == 'other_script'
    assert detect_language('') == 'unknown'
