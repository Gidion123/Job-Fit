"""D-065 proposal, offline only. Lower MATCH with traceable literal evidence rules.

G2 handles explicit lists of named tools only. It is not semantic entailment,
negation detection, duration verification or a claim that PARTIAL is always valid.
OR groups are evaluated per branch; alternative/example syntax is not split.
"""
import re
from copy import deepcopy

TOOLS=('SQL','PostgreSQL','Python','Excel','R','Git','Docker','FastAPI','Flask',
       'TensorFlow','PyTorch','pandas','scikit-learn','AWS','BigQuery','LangChain',
       'LlamaIndex','OpenAI','FAISS','Pinecone','Weaviate')

SKILL_HEADINGS={'skills','keahlian','technical skills','kemampuan','keterampilan','skills & tools',
    'tools','technical skills & tools','hard skills','skill'}
# Common CV section names, so a plain-text heading (PDF or DOCX upload, no Markdown
# marks) also ends the Skills section. Markdown headings behave exactly as before.
SECTION_HEADINGS=SKILL_HEADINGS|{'summary','ringkasan','profile','profil','about me','tentang saya',
    'experience','work experience','professional experience','pengalaman','pengalaman kerja',
    'education','pendidikan','projects','proyek','project','certifications','certification','sertifikasi',
    'courses','kursus','pelatihan','training','languages','bahasa','organizations','organisasi',
    'achievements','prestasi','awards','publications','publikasi','volunteering','references','referensi',
    'interests','minat'}


def _headings(cv_text):
    """(start, end, name) for Markdown headings and plain lines that are a known section name."""
    found=[]
    for m in re.finditer(r'(?m)^[ \t]*(#{1,6}[ \t]+)?([^\n]{1,60}?)[ \t]*:?[ \t]*$',cv_text):
        name=m.group(2).strip().strip('*_').strip().lower()
        if m.group(1) or name in SECTION_HEADINGS:
            found.append((m.start(),m.end(),name))
    return found


def skills_only(quote,cv_text):
    if not quote:return False
    headings=_headings(cv_text)
    ranges=[(end,headings[i+1][0] if i+1<len(headings) else len(cv_text))
        for i,(start,end,name) in enumerate(headings) if name in SKILL_HEADINGS]
    occurrences=list(re.finditer(re.escape(quote),cv_text))
    return bool(occurrences) and all(any(lo<=m.start() and m.end()<=hi for lo,hi in ranges) for m in occurrences)

def mentioned(term,text):return bool(re.search(r'(?<![\w])'+re.escape(term)+r'(?![\w])',text,re.I))

def named_conjunction(text):
    if re.search(r'\bor\b|\||\betc\b|\be\.g\.|\bsuch as\b',text,re.I):return []
    names='(?:'+'|'.join(re.escape(t) for t in sorted(TOOLS,key=len,reverse=True))+')'
    pattern=rf'(?<!\w)({names}(?:\s*(?:/|,|\band\b)\s*{names})+)(?!\w)'
    found=re.findall(pattern,text,re.I)
    return list(dict.fromkeys(t for segment in found for t in re.split(r'\s*(?:/|,|\band\b)\s*',segment,flags=re.I)))

def apply_guardrails(requirement,assessment,cv_text):
    """Return a copy and change receipts. Inputs and runtime defaults stay intact."""
    result=deepcopy(assessment);changes=[]
    targets=[(b,next(r['text'] for r in requirement['branches'] if r['branch_id']==b['branch_id']))
             for b in result.get('branches',[])] if result.get('branches') else [(result,requirement['text'])]
    for item,text in targets:
        if item.get('label')!='MATCH':continue
        quotes=item.get('cv_quotes',[]);flags=[]
        if quotes and all(skills_only(q,cv_text) for q in quotes):flags.append('skills_list_only')
        terms=named_conjunction(text)
        # A name listed only under Skills is not evidence of its use (D-035).
        supported='\n'.join(q for q in quotes if not skills_only(q,cv_text))
        covered=[t for t in terms if mentioned(t,supported)]
        if terms and 0<len(covered)<len(terms):flags.append('partial_item_coverage')
        if flags:
            item['label']='PARTIAL'
            changes.append({'unit_id':assessment['unit_id'],'branch_id':item.get('branch_id'),
                'before':'MATCH','after':'PARTIAL','flags':flags,'named_items':terms,'supported_items':covered})
    return result,changes
