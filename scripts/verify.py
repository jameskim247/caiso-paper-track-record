#!/usr/bin/env python3
"""Public PTP-compatible table checks; no orders, alpha, or source network calls."""
import argparse
import base64
import csv
from datetime import date,datetime,timedelta,timezone,time
import hashlib
import io
import json
import math
from pathlib import Path
import re
import ssl
import statistics as st
import subprocess
import tempfile
from zoneinfo import ZoneInfo

START='2024-01-01'
FIRST_BID='2026-10-10'
LAST_BID='2027-09-29'
FOLDERS={'FX':'data/fx','F_BROAD':'data/f-broad'}
NAMES=('daily.csv','weekly.csv','monthly.csv','summary.csv','source_anchor.json','publication.json')
DAILY='date,signal_date,status,pnl,gross_pnl,cumulative_pnl,pnl_drawdown,placed_mw,awarded_mw,fill_rate,pending_awarded_mw,decision_proof_id,settlement_proof_id,source_proof_id,proof_id'.split(',')
PERIOD='period_start,period_end,status,calendar_days,settled_days,placed_mw,awarded_mw,pending_awarded_mw,fill_rate,pnl,mean_day_pnl,worst_day_pnl,proof_id'.split(',')
SUMMARY='basis,start_date,end_date,calendar_days,settled_days,placed_mw,awarded_mw,pending_awarded_mw,fill_rate,total_pnl,gross_pnl,costs,mean_day_pnl,median_day_pnl,daily_pnl_stdev,annualized_pnl_mean_to_stdev,worst_day_pnl,pnl_es10,max_pnl_drawdown,annualized_zero_target_sortino,winning_day_fraction,profit_factor,best_day_fraction_of_total_pnl,top_five_days_fraction_of_total_pnl,ex_top_five_days_count,ex_top_five_total_pnl,ex_top_five_annualized_pnl_mean_to_stdev,latest_settled_date,proof_id'.split(',')
STRINGS={'date','signal_date','status','basis','start_date','end_date','period_start','period_end','latest_settled_date'}
INTEGERS={'calendar_days','settled_days','ex_top_five_days_count'}
LA=ZoneInfo('America/Los_Angeles')
CA_SHA='2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438'
SIGNER_SHA='8bfb0305bb64e2571ca507552ef3245cb1c2fee8728e0ff8689225081ea13467'
HEX=re.compile('[0-9a-f]{64}\\Z')

def check(value,message):
    if not value:raise ValueError(message)
def digest(body):return hashlib.sha256(body).hexdigest()
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def proved(row):return {**row,'proof_id':digest(encoded(row))}
def csv_bytes(rows,fields):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader();writer.writerows(rows);return stream.getvalue().encode()
def read_rows(body,fields):
    reader=csv.DictReader(io.StringIO(body.decode()))
    check(reader.fieldnames==fields,'column/order mismatch')
    rows=[]
    for raw in reader:
        check(set(raw)==set(fields) and all(isinstance(v,str) for v in raw.values()),'malformed row')
        row={k:(v if not v or k in STRINGS or k.endswith('_id') else int(v) if k in INTEGERS else float(v)) for k,v in raw.items()}
        check(all(not isinstance(v,float) or math.isfinite(v) for v in row.values()),'nonfinite value')
        proof=row.pop('proof_id');check(digest(encoded(row))==proof,'row proof mismatch')
        rows.append({**row,'proof_id':proof})
    return rows
def sum_known(rows,key,digits=6):
    values=[r[key] for r in rows if r[key]!='']
    return round(math.fsum(values),digits) if values else ''
def totals(rows):
    placed=sum_known(rows,'placed_mw');awarded=sum_known(rows,'awarded_mw')
    complete=all(r['placed_mw']!='' and r['awarded_mw']!='' for r in rows)
    return dict(calendar_days=len(rows),settled_days=sum(r['status']=='settled' for r in rows),
        placed_mw=placed,awarded_mw=awarded,pending_awarded_mw=sum_known(rows,'pending_awarded_mw'),
        fill_rate=round(awarded/placed,6) if complete and placed else 0. if complete else '')
def ratio(values):
    sd=st.stdev(values) if len(values)>1 else 0
    return round(st.mean(values)/sd*math.sqrt(365),6) if sd else ''
def summary(basis,rows):
    good=[r for r in rows if r['status']=='settled'];pnl=[r['pnl'] for r in good]
    value=dict(basis=basis,start_date=rows[0]['date'],end_date=rows[-1]['date'],**totals(rows))
    value.update({k:'' for k in SUMMARY[9:-1]})
    if not good:return proved(value)
    total=math.fsum(pnl);gross=math.fsum(r['gross_pnl'] for r in good)
    equity=peak=drawdown=0.
    for p in pnl:equity+=p;peak=max(peak,equity);drawdown=min(drawdown,equity-peak)
    ex=sorted(pnl,reverse=True)[5:];losses=-math.fsum(v for v in pnl if v<0)
    downside=math.sqrt(st.mean(min(v,0)**2 for v in pnl))
    value.update(total_pnl=round(total,4),gross_pnl=round(gross,4),costs=round(gross-total,4),
       mean_day_pnl=round(st.mean(pnl),6),median_day_pnl=round(st.median(pnl),4),
       daily_pnl_stdev=round(st.stdev(pnl),6) if len(pnl)>1 else '',annualized_pnl_mean_to_stdev=ratio(pnl),
       worst_day_pnl=min(pnl),pnl_es10=round(st.mean(sorted(pnl)[:math.ceil(len(pnl)/10)]),6),
       max_pnl_drawdown=round(drawdown,4),annualized_zero_target_sortino=round(st.mean(pnl)/downside*math.sqrt(365),6) if downside else '',
       winning_day_fraction=round(sum(v>0 for v in pnl)/len(pnl),6),
       profit_factor=round(math.fsum(v for v in pnl if v>0)/losses,6) if losses else '',
       best_day_fraction_of_total_pnl=round(max(pnl)/total,6) if total else '',
       top_five_days_fraction_of_total_pnl=round(math.fsum(sorted(pnl,reverse=True)[:5])/total,6) if total else '',
       ex_top_five_days_count=len(ex),ex_top_five_total_pnl=round(math.fsum(ex),4),
       ex_top_five_annualized_pnl_mean_to_stdev=ratio(ex) if ex else '',latest_settled_date=good[-1]['date'])
    return proved(value)
def tables(daily):
    result={'daily.csv':daily}
    for name in ['weekly.csv','monthly.csv']:
        groups={}
        for row in daily:
            d=date.fromisoformat(row['date']);key=d-timedelta(days=d.weekday()) if name=='weekly.csv' else d.replace(day=1)
            groups.setdefault(key,[]).append(row)
        periods=[]
        for rows in groups.values():
            good=[r for r in rows if r['status']=='settled'];p=[r['pnl'] for r in good]
            periods.append(proved(dict(period_start=rows[0]['date'],period_end=rows[-1]['date'],
                status='settled' if len(good)==len(rows) else 'prices_pending',**totals(rows),
                pnl=round(math.fsum(p),4) if p else '',mean_day_pnl=round(st.mean(p),6) if p else '',worst_day_pnl=min(p) if p else '')))
        result[name]=periods
    start,end=daily[0]['date'],daily[-1]['date'];ranges=[('full_displayed_history',start,end)]
    for year in range(int(start[:4]),int(end[:4])+1):
        ranges.append((str(year)+('_to_date' if str(year)==end[:4] and end[5:]!='12-31' else ''),max(start,f'{year}-01-01'),min(end,f'{year}-12-31')))
    y=end[:4]
    for suffix,first,last in [('_h1',y+'-01-01',y+'-06-30'),('_h2_to_date',y+'-07-01',end)]:
        if last>=first and end>=first:ranges.append((y+suffix,max(start,first),min(end,last)))
    result['summary.csv']=[summary(label,part) for label,lo,hi in ranges if (part:=[r for r in daily if lo<=r['date']<=hi])]
    return result

def verify_tokens(identity):
    proofs=identity['decision_proofs'];certs=identity['timestamp_certificates'];count=0;timely=0
    check(set(certs)=={'freetsa_cacert.pem','freetsa_tsa.crt'},'certificate inventory mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        for name,value in certs.items():(root/name).write_bytes(base64.b64decode(value,validate=True))
        check(digest((root/'freetsa_cacert.pem').read_bytes())==CA_SHA,'CA pin mismatch')
        check(digest((root/'freetsa_tsa.crt').read_bytes())==SIGNER_SHA,'signer pin mismatch')
        seen=set()
        allowed={'bid_day','operating_day','decision_sha256','signal','admissible','published_pt','deadline_pt','independent_timestamp','evidence_basis','token_time_pt','token_authority','token_sha256','token','first_exported_utc'}
        for proof in proofs:
            check(set(proof)==allowed,'decision-proof field inventory mismatch')
            day=proof['bid_day'];check(day not in seen and FIRST_BID<=day<=LAST_BID,'decision date mismatch');seen.add(day)
            check(proof['operating_day']==str(date.fromisoformat(day)+timedelta(days=1)) and proof['signal']=='6b72eba552ec','decision identity mismatch')
            deadline=datetime.combine(date.fromisoformat(day),time(9,55),LA)
            check(datetime.fromisoformat(proof['deadline_pt'])==deadline,'cutoff mismatch')
            check(HEX.fullmatch(proof['decision_sha256']) is not None,'invalid decision digest')
            if not proof['token']:
                check(not proof['independent_timestamp'],'missing timestamp token');continue
            token=base64.b64decode(proof['token'],validate=True);check(digest(token)==proof['token_sha256'],'timestamp hash mismatch')
            target=root/'token.tsr';target.write_bytes(token)
            if proof['token_authority']=='freetsa':trust=['-CAfile',str(root/'freetsa_cacert.pem'),'-untrusted',str(root/'freetsa_tsa.crt')]
            else:
                check(proof['token_authority']=='digicert','unknown timestamp authority')
                ca=root/'system-ca.pem';ca.write_text(''.join(ssl.DER_cert_to_PEM_cert(c) for c in ssl.create_default_context().get_ca_certs(binary_form=True)))
                trust=['-CAfile',str(ca)]
            result=subprocess.run(['openssl','ts','-verify','-digest',proof['decision_sha256'],'-in',str(target),*trust],capture_output=True,text=True)
            check(result.returncode==0,'timestamp signature/imprint mismatch')
            body=subprocess.run(['openssl','ts','-reply','-in',str(target),'-text'],capture_output=True,text=True,check=True).stdout
            match=re.search(r'^Time stamp: (.+)$',body,re.M);check(match is not None,'timestamp time missing')
            stamp=datetime.strptime(re.sub(r'\.\d+','',match.group(1).replace(' GMT','')),'%b %d %H:%M:%S %Y').replace(tzinfo=timezone.utc)
            check(stamp==datetime.fromisoformat(proof['token_time_pt']),'signed time differs')
            check(proof['independent_timestamp']==(stamp<=deadline),'timestamp timeliness mismatch')
            if proof['evidence_basis']=='on_time_independent':check(proof['admissible'] and stamp<=deadline,'unsupported on-time claim')
            count+=1;timely+=stamp<=deadline
    return count,timely

def verify(root,now=None,require_current=False):
    root=Path(root);now=now or datetime.now(LA)
    if now.tzinfo is None:raise ValueError('aware clock required')
    now=now.astimezone(LA)
    identity=json.loads((root/'proof/private_anchor.json').read_bytes())
    check(set(identity)=={'schema','record_start','record_end','series_ids','captured_utc','canonical_record_start','canonical_record_end',
        'canonical_record_set_sha256','registry_sha256','generation','paper_projection','timestamp_certificates','decision_proofs',
        'financial_truth_independently_verified','records_sha256'},'identity field inventory mismatch')
    check(identity['schema']=='caiso-paper-projection-v1' and identity['record_start']==START and identity['series_ids']==list(FOLDERS),'identity mismatch')
    check(identity['paper_projection']==dict(schema='caiso-paper-projection-v1',record_start=START,folders=FOLDERS,quantity_multiplier=1)
          and identity['financial_truth_independently_verified'] is False,'unsupported projection or financial claim')
    manifest=(root/'proof/records.sha256').read_bytes();check(digest(manifest)==identity['records_sha256'],'manifest anchor mismatch')
    expected={'.gitattributes','README.md','STATUS.md','scripts/verify.py',*(folder+'/'+n for folder in FOLDERS.values() for n in NAMES)}
    entries=[line.split('  ',1) for line in manifest.decode().splitlines()]
    check(len(entries)==len(expected) and {r[1] for r in entries}==expected,'manifest inventory mismatch')
    for hashvalue,name in entries:
        check(HEX.fullmatch(hashvalue) is not None and digest((root/name).read_bytes())==hashvalue,'file hash mismatch: '+name)
    allowed=expected|{'proof/private_anchor.json','proof/records.sha256','.gitignore','.github/workflows/verify.yml'}
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ['.git','__pycache__']) and not p.name.endswith('.pyc')}
    check(actual==allowed,'public file inventory mismatch')
    count,timely=verify_tokens(identity);proofs={p['bid_day']:p for p in identity['decision_proofs']}
    daily_by_book={};observations={}
    for book,folder in FOLDERS.items():
        anchor=json.loads((root/folder/'source_anchor.json').read_bytes());receipt=json.loads((root/folder/'publication.json').read_bytes())
        check(set(anchor)=={'schema','book','record_start','record_end','source_package_sha256','source_frozen_specification_sha256',
            'quantity_multiplier','public_cost_per_awarded_mwh','modeled_uplift_by_date','historical_evidence','history_end',
            'prospective_first_operating_day','source_files_sha256','files_sha256','assumptions','historical_strict_price_tie_days',
            'template_repository','template_commit'},'source-anchor field inventory mismatch')
        check(set(receipt)=={'checked_through','missing_result_days','record_end','record_start','source_package_sha256','state','status'},'publication field inventory mismatch')
        check(set(anchor['source_files_sha256'])=={'baseline_daily.csv','exposure.csv','baseline_verification.json','g3_U2.npz',
            'G5F_U2_test_orders.npz','rc_tier1_central.csv','cb_awards_hourly.csv'} and
            all(isinstance(v,str) and HEX.fullmatch(v) for v in anchor['source_files_sha256'].values()),'source-file digest inventory mismatch')
        check(anchor['schema']=='caiso-paper-anchor-v1' and anchor['book']==book and anchor['record_start']==START and anchor['quantity_multiplier']==1,'source identity mismatch')
        check(anchor['public_cost_per_awarded_mwh']==.5 and anchor['record_end']==identity['record_end'],'source cost/window mismatch')
        check(HEX.fullmatch(anchor['source_package_sha256']) and anchor['source_package_sha256']==receipt['source_package_sha256'],'source package mismatch')
        check(anchor['source_frozen_specification_sha256']=='d8a1e16f28227a723128184f26a785eccdcfb762f76545136ac9edb4e67add00','frozen programme changed')
        check(anchor['history_end']=='2026-09-30' and anchor['prospective_first_operating_day']=='2026-10-11' and anchor['historical_evidence']=='retrospective_legacy_research_not_A4','historical evidence mislabeled')
        data={name:read_rows((root/folder/name).read_bytes(),DAILY if name=='daily.csv' else SUMMARY if name=='summary.csv' else PERIOD) for name in NAMES if name.endswith('.csv')}
        check(anchor['files_sha256']=={name:digest((root/folder/name).read_bytes()) for name in data},'table hashes differ')
        daily=data['daily.csv'];first=date.fromisoformat(START);end=date.fromisoformat(identity['record_end'])
        check(set(anchor['modeled_uplift_by_date'])=={r['date'] for r in daily if r['status']=='settled'} and
            all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in anchor['modeled_uplift_by_date'].values()),'modeled-cost inventory mismatch')
        check([r['date'] for r in daily]==[str(first+timedelta(days=i)) for i in range((end-first).days+1)],'calendar mismatch')
        check(end<=now.date()-timedelta(days=1),'future financial date')
        equity=peak=0.
        for row in daily:
            check(row['signal_date']==str(date.fromisoformat(row['date'])-timedelta(days=1)),'signal date mismatch')
            check(row['status'] in ['settled','source_missing','prices_pending','execution_pending','timing_failed','cost_pending'],'unknown status')
            for key in ['decision_proof_id','settlement_proof_id','source_proof_id']:
                check(row[key]=='' or HEX.fullmatch(row[key]) is not None,'invalid source hash')
            for key in ['placed_mw','awarded_mw','pending_awarded_mw']:check(row[key]=='' or row[key]>=0,'negative volume')
            if row['status']=='settled':
                check(all(row[k]!='' for k in ['pnl','gross_pnl','placed_mw','awarded_mw','fill_rate','pending_awarded_mw']),'missing scored value')
                check(0<=row['pending_awarded_mw']<=row['awarded_mw']<=row['placed_mw']+1e-6,'exposure bounds')
                uplift=anchor['modeled_uplift_by_date'][row['date']]
                check(abs(row['pnl']-(row['gross_pnl']-.5*row['awarded_mw']-uplift))<.001,'cost equation mismatch')
                equity+=row['pnl'];peak=max(peak,equity)
                check(abs(row['cumulative_pnl']-equity)<.001 and abs(row['pnl_drawdown']-(equity-peak))<.001,'equity/drawdown mismatch')
                check(abs(row['fill_rate']-(row['awarded_mw']/row['placed_mw'] if row['placed_mw'] else 0))<=1e-6,'fill-rate mismatch')
                if row['date']>='2026-10-11':
                    p=proofs.get(row['signal_date']);check(p is not None and p['evidence_basis']=='on_time_independent','unsealed prospective row')
                    check(row['decision_proof_id']==p['decision_sha256'],'decision binding changed')
            else:
                check(all(row[k]=='' for k in ['pnl','gross_pnl','cumulative_pnl','pnl_drawdown','awarded_mw','fill_rate','pending_awarded_mw']),'pending value replaced by zero')
            if '2026-10-01'<=row['date']<='2026-10-10':check(row['status']=='source_missing','unproven historical gap filled')
        recomputed=tables(daily)
        check(all(data[n]==recomputed[n] for n in ['weekly.csv','monthly.csv','summary.csv']),'aggregate arithmetic mismatch')
        check(receipt['record_start']==START and receipt['record_end']==identity['record_end'],'publication range mismatch')
        missing=sum(r['status']!='settled' for r in daily)
        check(receipt['missing_result_days']==missing,'missing count mismatch')
        daily_by_book[book]={r['date']:r for r in daily};observations[book]=dict(calendar_days=len(daily),settled_days=len(daily)-missing,missing_days=missing)
    issues=[];coverage_issues=[]
    if require_current:
        local_time=now.time().replace(tzinfo=None)
        required_bid=min(now.date() if local_time>=time(9,55) else now.date()-timedelta(days=1),date.fromisoformat(LAST_BID))
        if required_bid>=date.fromisoformat(FIRST_BID):
            proof=proofs.get(str(required_bid))
            if proof is None or not proof['admissible'] or not proof['independent_timestamp']:issues.append('COMMITMENT_COVERAGE_STALE')
        expected=min(now.date()-timedelta(days=1 if local_time>=time(10,45) else 2),date(2027,9,30))
        for book,rows in daily_by_book.items():
            if expected>=date(2026,10,11):
                status=rows.get(str(expected),{}).get('status')
                if status=='execution_pending':coverage_issues.append('UNRESOLVED_EXECUTION:'+book+':'+str(expected))
                elif status!='settled':issues.append('MATURE_SCORING_PENDING:'+book)
        report_day=min(now.date() if local_time>=time(10,45) else now.date()-timedelta(days=1),date(2027,10,1))
        if datetime.fromisoformat(identity['captured_utc'])<datetime.combine(report_day,time(10,35),LA):issues.append('REPORT_STATUS_STALE')
    return dict(ok=not issues,verified_timestamp_tokens=count,independent_before_cutoff=timely,books=observations,
                financial_truth_independently_verified=False,freshness=dict(ok=not issues,issues=issues),coverage_issues=coverage_issues)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--require-current',action='store_true')
    parser.add_argument('--timezone',default='America/Los_Angeles',choices=['America/Los_Angeles'])
    parser.add_argument('--not-before',default='10:45',choices=['10:45'])
    args=parser.parse_args()
    try:
        result=verify(Path(__file__).resolve().parents[1],require_current=args.require_current)
    except (ValueError,KeyError,TypeError,OSError,csv.Error,subprocess.SubprocessError) as exc:result=dict(ok=False,errors=[str(exc)])
    print(json.dumps(result));return int(not result['ok'])
if __name__=='__main__':raise SystemExit(main())
