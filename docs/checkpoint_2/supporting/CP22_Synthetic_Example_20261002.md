# Synthetic development example: CV1 PDF + pasted J1

2 October 2026. Model-produced diagnostic report, not gold and not a held-out evaluation. The latest run reused the validated two-column CV1 PDF parse from run `_04`. Original synthetic sources and workbook labels are unchanged.

## Three separate result axes

- **Evidence coverage:** 91.67%, **provisional**: (5 MATCH + 0.5 × 1 PARTIAL) / 6 extracted required units.
- **Constraints:** experience and location UNKNOWN. No user location was confirmed; the JD experience condition is not an unambiguous mandatory gate.
- **Information:** the structured/unstructured-data unit and architecture/engineering grouping still need interpretation review. This changes the denominator compared with approved pilot labels. Do not present the percentage as verified matching quality.

Approved pilot score v1 is 92.86% over seven required technical units. This discrepancy is recorded for development error analysis; the model result does not overwrite it. The 0.75-year duration in the JSON is a whole-employment upper bound across internship/teaching, not 0.75 years of verified Data Science employment.

## Per-unit model output

| ID | Requirement | Importance | Model assessment | CV source quote |
| --- | --- | --- | --- | --- |
| U01 | 1-2 years of professional experience in Data Science fields; fresh graduates welcome | unknown | PARTIAL | **Data Analyst Intern**, PT Contoh Retail Nusantara, Jakarta · Februari<br>2026 - Mei 2026 (4 bulan) |
| U02 | Experience using Python to manipulate data and draw insights from large data sets | required | MATCH | Membersihkan dan menggabungkan data transaksi 1,2 juta baris<br>dengan Python (pandas) dan SQL (PostgreSQL). |
| U03 | Experience using SQL to manipulate data and draw insights from large data sets | required | MATCH | Membersihkan dan menggabungkan data transaksi 1,2 juta baris<br>dengan Python (pandas) dan SQL (PostgreSQL). |
| U04 | Mathematical skills, including real-world advantages/drawbacks | required | PARTIAL | S1 Statistika**, Universitas Negeri Contoh, Jakarta · Agustus 2022 -<br>Agustus 2026; Mata kuliah terkait: Analisis Regresi, Data Mining, Statistika Bayesian,<br>Basis Data |
| U05 | Statistical skills, including real-world advantages/drawbacks | required | MATCH | S1 Statistika**, Universitas Negeri Contoh, Jakarta · Agustus 2022 -<br>Agustus 2026; Melakukan analisis cohort retensi pelanggan dan mempresentasikan<br>hasilnya ke manajer divisi. |
| U06 | Machine Learning skills, including real-world advantages/drawbacks | required | MATCH | Membangun model regresi logistik dan random forest dengan<br>scikit-learn; F1-score 0,78 pada data uji.; Mengumpulkan 5.000 ulasan berbahasa Indonesia dan<br>mengklasifikasikan sentimen dengan TF-IDF dan Naive Bayes. |
| U07 | Knowledge and/or experience in working with structured and/or unstructured data sets | unknown | failed | No quote: unresolved check |
| U08 | Knowledge and/or experience in Data Architecture and Engineering | preferred | failed | No quote: unresolved check |
| U09 | Google Cloud Platform | preferred | NO_MATCH | No evidence quoted |
| U10 | Familiarity with Data Visualization Tools | required | MATCH | Membuat dashboard penjualan mingguan di Looker Studio untuk tim<br>marketing. |
| U11 | Google Data Studio | preferred | MATCH | Membuat dashboard penjualan mingguan di Looker Studio untuk tim<br>marketing. |
| U12 | Problem-solving skills | required | NO_MATCH | No evidence quoted |
| U13 | Structured thinking | required | NO_MATCH | No evidence quoted |
| U14 | Scientific approach | required | NO_MATCH | No evidence quoted |
| U15 | Ability to work with minimal supervision | required | NO_MATCH | No evidence quoted |
| U16 | Ability to keep supervisors informed | required | NO_MATCH | No evidence quoted |
| U17 | Ability to work well in a team environment | required | NO_MATCH | No evidence quoted |
| U18 | Ability to communicate in clear and concise terms | required | MATCH | Melakukan analisis cohort retensi pelanggan dan mempresentasikan<br>hasilnya ke manajer divisi. |
| U19 | Willing to learn new skills | required | NO_MATCH | No evidence quoted |
| U20 | Able to learn new skills independently | required | NO_MATCH | No evidence quoted |
| U21 | Ability to take initiative | required | NO_MATCH | No evidence quoted |

## Provenance

- Source: CV1 synthetic two-column PDF and development pilot F00022; reference date 30 September 2026.
- Configured baseline: `deepseek/deepseek-v4.1-flash`, low reasoning, 16,000 output-token allowance; JD prompt v1.1; guideline v1.2.
- Latest run: 2 new calls, US$0.023168232. CV parsing cost is recorded in the earlier run, not billed again.
- Full machine-readable report: [run 06](../../../evals/results/cp22_live_cv1_j1_20261002_06.json).
- Implementation, failure history and remaining limitations: [pipeline report](CP22_Pipeline_Implementation_20261002.md).
