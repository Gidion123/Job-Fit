"""One semantic repair of a nonterminal result, within existing stage/cost limits.

Never reopen terminal probes or discard the first output. Structural repair and
semantic repair share the same two-attempt stage allowance.
"""
from jobfit.llm.closure_probe import ClosureProbeSession

class SemanticRepairSession(ClosureProbeSession):
    def begin_repair(self,receipt,extension_sha256):
        d=self.data
        if d['status']!='awaiting_semantic_check':raise ValueError('Only an unchecked nonterminal result may be repaired')
        last=d['results'][-1];job=last['job_id']
        if receipt.get('result_sha256')!=last['result_sha256'] or receipt.get('job_id')!=job:raise ValueError('Repair must name exact output')
        if not receipt.get('corrections') or not extension_sha256:raise ValueError('Versioned source-backed correction required')
        if d.get('stage_attempts',{}).get(job,0)!=1 or d.get('semantic_repairs',{}).get(job):raise ValueError('Stage already consumed its repair')
        self.check_budget(0)
        d.setdefault('prior_stage_results',[]).append(dict(last))
        d.setdefault('semantic_repairs',{})[job]={'receipt':receipt,'extension_sha256':extension_sha256,'used':True}
        d.update(status='running',active_job=job)
        self.save()

    def finish_repair(self,result):
        d=self.data
        if d['status']!='running' or result['job_id']!=d['active_job'] or not d.get('semantic_repairs',{}).get(result['job_id']):raise ValueError('No active semantic repair')
        if d.get('stage_attempts',{}).get(result['job_id'],0)>2:raise ValueError('Stage limit violated')
        d['results'][-1]=result
        d['status']='awaiting_semantic_check' if result['status']=='done' else 'stopped_process_failure'
        self.save()
