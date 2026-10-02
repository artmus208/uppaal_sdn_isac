"""In-memory negative controls for the offline audit; no native execution."""
import copy,json
from pathlib import Path
import audit

original=audit.read
controls=[]
for label,target,mutate in [
 ('registry_verdict','results.json',lambda v:v['queries'][0].update(verdict='satisfied')),
 ('formula_identity','results.json',lambda v:v['queries'][0].update(formula='A[] true')),
 ('query_hash_identity','results.json',lambda v:v['queries'][0].update(query_hash='0'*64)),
 ('model_hash_identity','results.json',lambda v:v['queries'][0].update(model_hash='0'*64)),
 ('raw_attempt_status','result.json',lambda v:v.update(status='success',verdict='satisfied')),
]:
    def altered(path,label=label,target=target,mutate=mutate):
        value=original(path)
        if Path(path).name==target:
            value=copy.deepcopy(value);mutate(value)
        return value
    audit.read=altered
    try:audit.audit()
    except ValueError as error:controls.append({'control':label,'detected':True,'diagnostic':str(error)})
    else:raise RuntimeError('Undetected tamper: '+label)
    finally:audit.read=original
print(json.dumps({'audit_negative_controls':'ok','controls':controls,'new_verifier_executions':0},indent=2))
