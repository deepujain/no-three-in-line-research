"""Synthetic receipt-association checks; never loads actual inputs or geometry."""
from copy import deepcopy
from research import two_row_suffix75_actual_authority_adapter as a
report={'elapsed_seconds':7.0}
job={'argv':[str(a.ROOT/'.venv/bin/python'),'research/two_row_suffix75.py','--seconds','25','--output-dir','data/two-row-suffix75-v1','--source-pins',a.MANIFEST],'status':'completed','sources_unchanged':True,'source_manifest_sha256':a.EXPECTED[a.MANIFEST],'elapsed_seconds':8.0,'gate':{'returncode':0,'seconds_limit':30,'rss_limit_mib':256,'peak_sampled_rss_kib':100000,'rss_samples':3,'cleanup_samples':1,'gate_status':'exited','cleanup_status':'clean','cleanup_error':None,'monitor_error':None,'trigger_gate_status':None,'elapsed_seconds':7.5}}
a.clean_receipt(report,job)
for key,value in [('returncode',1),('cleanup_status','failed'),('trigger_gate_status','timeout'),('peak_sampled_rss_kib',262145),('rss_samples',0),('elapsed_seconds',30)]:
    changed=deepcopy(job);changed['gate'][key]=value
    try:a.clean_receipt(report,changed)
    except ValueError:pass
    else:raise AssertionError(key)
for key,value in [('status','failed'),('sources_unchanged',False),('source_manifest_sha256','0'*64)]:
    changed=deepcopy(job);changed[key]=value
    try:a.clean_receipt(report,changed)
    except ValueError:pass
    else:raise AssertionError(key)
print('PASS synthetic clean_receipt: 1 clean and 9 invalid guard/receipt cases; no actual input read')
