"""Offline scripted responses. Never use to claim model accuracy or live inference."""
from copy import deepcopy
import json, re

class FixtureClient:
    def __init__(self, responses):
        self.responses=list(responses);self.calls=[]

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0.0):
        self.calls.append({'model':model,'messages':deepcopy(messages),'task':task})
        if not self.responses: raise AssertionError('unplanned fake call')
        response=self.responses.pop(0)
        if isinstance(response,Exception):raise response
        data=json.loads(messages[1]['content'])['untrusted_document_data']
        if callable(response):response=response(data)
        return output_model.model_validate(deepcopy(response))

def cv1_response(text):
    """Manually scoped response adapter for the approved CV1 source, including PDF line wraps.

    This is NOT a CV parser or semantic oracle. Facts and employment spans are fixed
    to CV1 for plumbing/quote tests, independent of every JD and test CV.
    """
    mapping={'Ringkasan':'Summary','Pendidikan':'Education','Pengalaman':'Experience',
             'Proyek':'Projects','Keahlian':'Skills','Sertifikasi':'Certifications','Bahasa':'Other'}
    hits=list(re.finditer(r'^## (.+)$',text,re.M));sections=[]
    for i,m in enumerate(hits):
        sections.append({'section':mapping[m[1]],'text':text[m.end():hits[i+1].start() if i+1<len(hits) else len(text)].strip()})
    experience=next(s['text'] for s in sections if s['section']=='Experience')
    start=experience.index('**Data Analyst Intern**');second=experience.index('**Asisten Praktikum Analisis Regresi**')
    work=[{'title':'Data Analyst Intern','organization':'PT Contoh Retail Nusantara','source_quote':experience[start:second].strip(),
           'start_text':'Februari 2026','end_text':'Mei 2026','is_present':False},
          {'title':'Asisten Praktikum Analisis Regresi','organization':'Universitas Negeri Contoh','source_quote':experience[second:].strip(),
           'start_text':'Februari 2025','end_text':'Juni 2025','is_present':False}]
    for entry in work:
        for field in ['start_text','end_text']:
            # Preserve the upload's exact whitespace, including wrapped month/year.
            pattern=r'\s+'.join(re.escape(t) for t in entry[field].split())
            entry[field]=re.search(pattern,entry['source_quote'])[0]
    return {'language':'id','sections':sections,'employment':work,'skills_list':['Python','SQL','R','Looker Studio','Excel','Git'],
            'evidence':[{'fact_id':f'f{i+1}','section':s['section'],'quote':s['text']} for i,s in enumerate(sections)],
            'location_quote':'Jakarta Selatan, Indonesia'}

def simple_jd_response(payload):
    return {'job_id':payload['job_id'],'units':[{'unit_id':'python','text':'Python','importance':'required','field':'skill_tool','source_quotes':['Python']},
        {'unit_id':'git','text':'Git','importance':'required','field':'skill_tool','source_quotes':['Git']}]}

def simple_evidence_response(payload):
    text=payload['cv_text']
    # Existing CV1 work activity, preserving whichever line wrapping the upload contains.
    m=re.search(r'- Membersihkan dan menggabungkan.*?PostgreSQL\)\.',text,re.S)
    return {'assessments':[{'unit_id':'python','label':'MATCH','cv_quotes':[m[0]]},
                           {'unit_id':'git','label':'PARTIAL','cv_quotes':['Git']}]}
