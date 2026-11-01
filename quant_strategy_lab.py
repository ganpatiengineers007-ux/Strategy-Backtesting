#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quant Strategy Lab: 10 independent research strategies; Python 3.10+, stdlib only.
CSV schema: timestamp,symbol,open,high,low,close,volume plus strategy-specific fields.
No live trading, credentials, or order placement. Results are research screens only.
"""
from __future__ import annotations
import argparse, csv, json, math, statistics, sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

BASE = ('timestamp','symbol','open','high','low','close','volume')
REQ = {
'S01':('bid_depth','ask_depth','aggr_buy_volume','aggr_sell_volume'),
'S02':('pair_symbol','pair_close'),
'S03':('venue','venue_timestamp','sweep_flag'),
'S04':('trade_sign','trade_volume'),
'S05':('event_type','order_id','order_price','order_qty'),
'S06':(), 'S07':(), 'S08':(),
'S09':('event_type','order_id','order_price','order_qty','trade_price','trade_qty'),
'S10':()
}
NAMES = {
'S01':'Order-book imbalance + cumulative delta divergence',
'S02':'Cross-sectional pairs / rolling spread',
'S03':'Cross-venue latency + liquidity-sweep reversal',
'S04':'Absorption + VPIN/Kyle impact proxies',
'S05':'Spoofing / layering event detector',
'S06':'Volume Profile POC / VAH / VAL',
'S07':'Four-phase multi-feature reversal model',
'S08':'Fair Value Gap / institutional imbalance',
'S09':'Iceberg replenishment detector',
'S10':'Session-open ignition'
}
CAPITAL=1_000_000.0; RISK=0.005; COST_BPS=4.0; MIN_TRADES=30

def num(x, default=None):
    try:
        v=float(x); return v if math.isfinite(v) else default
    except (TypeError,ValueError): return default

def dt(x): return datetime.fromisoformat(x.strip().replace('Z','+00:00'))
@dataclass
class Bar:
    timestamp: datetime; symbol: str; open: float; high: float; low: float; close: float; volume: float; x: dict
@dataclass
class Trade:
    strategy:str; symbol:str; entry_time:str; exit_time:str; side:str; entry:float; exit:float; qty:float; gross:float; costs:float; net:float; reason:str
@dataclass
class Sig:
    side:int=0; stop:float=0.; target:float=0.; reason:str='no signal'

def load_file(path):
    out=[]
    with open(path,newline='',encoding='utf-8-sig') as f:
        rd=csv.DictReader(f); missing=[k for k in BASE if k not in (rd.fieldnames or [])]
        if missing: raise ValueError('Missing base columns: '+', '.join(missing))
        for n,row in enumerate(rd,2):
            try:
                t=dt(row['timestamp']); s=row['symbol'].strip(); vals=[num(row[k]) for k in ('open','high','low','close','volume')]
                if not s or any(v is None for v in vals): raise ValueError('invalid symbol/OHLCV')
                o,h,l,c,v=vals
                if min(o,h,l,c)<=0 or v<0 or h<max(o,l,c) or l>min(o,h,c): raise ValueError('invalid OHLC range')
                out.append(Bar(t,s,o,h,l,c,v,row))
            except Exception as e: raise ValueError(f'CSV row {n}: {e}')
    return sorted(out,key=lambda b:(b.symbol,b.timestamp))

def groups(bars):
    d={}
    for b in bars:d.setdefault(b.symbol,[]).append(b)
    return d

def atr(r,n=14):
    if len(r)<n+1:return None
    z=[]
    for p,b in zip(r[-n-1:-1],r[-n:]):z.append(max(b.high-b.low,abs(b.high-p.close),abs(b.low-p.close)))
    return sum(z)/len(z)
def avg(v,n): return sum(v[-n:])/n if len(v)>=n else None
def profile(r,n=50,bins=24):
    q=r[-n:]; lo=min(b.low for b in q); hi=max(b.high for b in q)
    if hi<=lo:return None
    w=(hi-lo)/bins; vol=[0.]*bins
    for b in q:vol[min(bins-1,max(0,int((b.close-lo)/w)))]+=b.volume
    poc=max(range(bins),key=lambda i:vol[i]); chosen={poc}; total=sum(vol); acc=vol[poc]; l=poc-1; rr=poc+1
    while acc<.70*total and (l>=0 or rr<bins):
        lv=vol[l] if l>=0 else -1; rv=vol[rr] if rr<bins else -1
        if rv>lv:chosen.add(rr);acc+=max(0,rv);rr+=1
        else:chosen.add(l);acc+=max(0,lv);l-=1
    return lo+(poc+.5)*w,lo+(max(chosen)+1)*w,lo+min(chosen)*w

def schema_missing(code,bars):
    have={k for b in bars for k,v in b.x.items() if v not in ('',None)}
    return [k for k in REQ[code] if k not in have]

class Strategy:
    code=''
    def signal(self,r,i): return Sig()
class S01(Strategy):
    code='S01'
    def signal(self,r,i):
        b=r[i];a=atr(r[:i+1]); bd=num(b.x.get('bid_depth'));ad=num(b.x.get('ask_depth'));bu=num(b.x.get('aggr_buy_volume'));se=num(b.x.get('aggr_sell_volume'))
        if not a or None in (bd,ad,bu,se) or bd+ad<=0:return Sig(reason='L2 fields/ATR unavailable')
        obi=(bd-ad)/(bd+ad); delta=bu-se
        old=sum((num(x.x.get('aggr_buy_volume'),0)-num(x.x.get('aggr_sell_volume'),0)) for x in r[max(0,i-5):i])
        if obi>.25 and delta>0 and old<0:return Sig(1,b.close-1.5*a,b.close+2.5*a,'positive OBI + delta turn')
        if obi<-.25 and delta<0 and old>0:return Sig(-1,b.close+1.5*a,b.close-2.5*a,'negative OBI + delta turn')
        return Sig(reason='OBI/delta gate not met')
class S02(Strategy):
    code='S02'
    def signal(self,r,i):
        b=r[i];p=num(b.x.get('pair_close'));a=atr(r[:i+1])
        if not p or not a:return Sig(reason='pair history/ATR unavailable')
        hist=[math.log(x.close)-math.log(num(x.x['pair_close'])) for x in r[max(0,i-60):i] if num(x.x.get('pair_close'),0)>0]
        if len(hist)<30:return Sig(reason='need 30 prior paired observations')
        sd=statistics.stdev(hist);z=(math.log(b.close)-math.log(p)-statistics.mean(hist))/sd if sd>1e-12 else 0
        if z>2:return Sig(-1,b.close+1.5*a,b.close-2*a,f'spread z={z:.2f}; single-leg proxy')
        if z< -2:return Sig(1,b.close-1.5*a,b.close+2*a,f'spread z={z:.2f}; single-leg proxy')
        return Sig(reason=f'z={z:.2f}')
class S03(Strategy):
    code='S03'
    def signal(self,r,i):
        b=r[i];a=atr(r[:i+1])
        if not a or b.x.get('sweep_flag','').lower() not in ('1','true','yes','sweep'):return Sig(reason='no confirmed sweep')
        try:lat=abs((b.timestamp-dt(b.x['venue_timestamp'])).total_seconds())
        except Exception:return Sig(reason='venue timestamp missing/invalid')
        if lat>2:return Sig(reason='latency > 2 seconds')
        if b.close>b.open:return Sig(1,b.close-1.2*a,b.close+2*a,'sweep bullish reclaim')
        if b.close<b.open:return Sig(-1,b.close+1.2*a,b.close-2*a,'sweep bearish rejection')
        return Sig()
class S04(Strategy):
    code='S04'
    def signal(self,r,i):
        b=r[i];a=atr(r[:i+1]);sg=num(b.x.get('trade_sign'));tv=num(b.x.get('trade_volume'));base=avg([x.volume for x in r[max(0,i-20):i]],20)
        if not a or sg is None or tv is None or not base:return Sig(reason='trade prints/volume baseline unavailable')
        # Heuristic absorption proxy; not a true bucketed VPIN or calibrated Kyle lambda.
        if tv>1.5*base and abs(b.close-b.open)<.25*a:
            if sg>0:return Sig(1,b.close-1.3*a,b.close+2*a,'buy-flow absorption proxy')
            if sg<0:return Sig(-1,b.close+1.3*a,b.close-2*a,'sell-flow absorption proxy')
        return Sig(reason='absorption proxy not met')
class S05(Strategy):
    code='S05'
    def signal(self,r,i):
        b=r[i];a=atr(r[:i+1])
        if not a:return Sig()
        ev={}
        for x in r[max(0,i-20):i+1]:
            oid=x.x.get('order_id');typ=(x.x.get('event_type') or '').lower()
            if not oid:continue
            q=ev.setdefault(oid,[0,0]);q[0]+=typ in ('add','new','submit');q[1]+=typ in ('cancel','delete')
        suspicious=sum(1 for adds,cancels in ev.values() if adds and cancels>=adds)
        if suspicious>=3 and b.close>b.open:return Sig(-1,b.close+1.5*a,b.close-2*a,'layering/cancel cluster heuristic')
        if suspicious>=3 and b.close<b.open:return Sig(1,b.close-1.5*a,b.close+2*a,'layering/cancel cluster heuristic')
        return Sig(reason='no suspicious event cluster')
class S06(Strategy):
    code='S06'
    def signal(self,r,i):
        b=r[i];a=atr(r[:i+1])
        if not a or i<50:return Sig(reason='profile history unavailable')
        vp=profile(r[:i],50);poc,vah,val=vp;vavg=avg([x.volume for x in r[i-20:i]],20)
        if b.close>vah and vavg and b.volume>vavg:return Sig(1,b.close-1.5*a,b.close+2.5*a,'value-area upside acceptance')
        if b.close<val and vavg and b.volume>vavg:return Sig(-1,b.close+1.5*a,b.close-2.5*a,'value-area downside acceptance')
        if b.low<=val and b.close>val:return Sig(1,b.close-1.2*a,poc,'VAL rejection')
        if b.high>=vah and b.close<vah:return Sig(-1,b.close+1.2*a,poc,'VAH rejection')
        return Sig(reason=f'POC={poc:.4f}, VAH={vah:.4f}, VAL={val:.4f}')
class S07(Strategy):
    code='S07'
    def signal(self,r,i):
        b=r[i];a=atr(r[:i+1])
        if not a or i<35:return Sig(reason='feature history unavailable')
        vr=b.volume/(avg([x.volume for x in r[i-20:i]],20) or b.volume);trend=(b.close-r[i-5].close)/a;rev=-(b.close-b.open)/a
        score=1.2*rev-.35*trend+.25*(vr-1)
        gates=(abs(rev)>.25,vr>1.1,abs(trend)<2.5,abs(score)>.45)
        if all(gates) and score>0:return Sig(1,b.close-1.5*a,b.close+2.5*a,f'four gates; score={score:.3f}')
        if all(gates) and score<0:return Sig(-1,b.close+1.5*a,b.close-2.5*a,f'four gates; score={score:.3f}')
        return Sig(reason=f'gate rejected; score={score:.3f}')
class S08(Strategy):
    code='S08'
    def signal(self,r,i):
        b=r[i];a=atr(r[:i+1])
        if not a or i<2:return Sig()
        x,m=r[i-2],r[i-1]
        if x.high<b.low and m.close>m.open:return Sig(1,b.close-1.5*a,b.close+2.5*a,'bullish three-bar FVG')
        if x.low>b.high and m.close<m.open:return Sig(-1,b.close+1.5*a,b.close-2.5*a,'bearish three-bar FVG')
        return Sig(reason='no three-bar gap')
class S09(Strategy):
    code='S09'
    def signal(self,r,i):
        b=r[i];a=atr(r[:i+1])
        if not a:return Sig()
        book={}
        for x in r[max(0,i-30):i+1]:
            px=num(x.x.get('order_price'));typ=(x.x.get('event_type') or '').lower()
            if px is None:continue
            z=book.setdefault(round(px,2),[0,0]);z[0]+=typ in ('trade','fill','execution');z[1]+=typ in ('add','refresh','replenish')
        hit=any(t>=3 and adds>=2 for t,adds in book.values())
        if hit and b.close>b.open:return Sig(1,b.close-1.3*a,b.close+2*a,'iceberg replenishment proxy')
        if hit and b.close<b.open:return Sig(-1,b.close+1.3*a,b.close-2*a,'iceberg replenishment proxy')
        return Sig(reason='no replenishment cluster')
class S10(Strategy):
    code='S10'
    def signal(self,r,i):
        b=r[i];a=atr(r[:i+1])
        if not a:return Sig()
        minute=b.timestamp.hour*60+b.timestamp.minute
        # Generic opening windows in the timestamp's own timezone; configure per exchange before use.
        opening=any(abs(minute-m)<=10 for m in (0,480,810,870))
        vavg=avg([x.volume for x in r[max(0,i-20):i]],20)
        if not opening or not vavg or b.volume<1.8*vavg:return Sig(reason='session/volume gate not met')
        if b.close>b.open and b.close-b.open>.5*a:return Sig(1,b.close-1.5*a,b.close+3*a,'session bullish ignition')
        if b.close<b.open and b.open-b.close>.5*a:return Sig(-1,b.close+1.5*a,b.close-3*a,'session bearish ignition')
        return Sig()

CLASSES={c.code:c for c in (S01,S02,S03,S04,S05,S06,S07,S08,S09,S10)}
def size(eq,entry,stop):
    d=abs(entry-stop)
    return min(eq*RISK/d,eq/entry) if d>0 and entry>0 else 0
def metrics(ts,initial,equity,maxdd):
    p=[t.net for t in ts];w=[x for x in p if x>0];l=[x for x in p if x<0];gw=sum(w);gl=abs(sum(l));sd=statistics.stdev(p) if len(p)>1 else 0
    run=best=0
    for x in p:run=run+1 if x<0 else 0;best=max(best,run)
    return {'initial_capital':round(initial,2),'ending_equity':round(equity,2),'net_profit':round(equity-initial,2),'return_pct':round((equity/initial-1)*100,3),'win_rate_pct':round(100*len(w)/len(p),2) if p else 0,'profit_factor':round(gw/gl,3) if gl else ('Infinity' if gw else 0),'expectancy_per_trade':round(sum(p)/len(p),2) if p else 0,'avg_win':round(statistics.mean(w),2) if w else 0,'avg_loss':round(abs(statistics.mean(l)),2) if l else 0,'max_drawdown_pct':round(maxdd*100,3),'trade_sharpe_proxy':round(statistics.mean(p)/sd*math.sqrt(len(p)),3) if sd else 0,'max_consecutive_losses':best}
def run(code,bars,initial):
    missing=schema_missing(code,bars)
    if missing:return {'strategy':code,'name':NAMES[code],'status':'BLOCKED','reason':'required fields missing: '+', '.join(missing),'trades':0,'metrics':{},'trade_records':[]}
    strat=CLASSES[code]();ts=[];eq=initial;peak=eq;maxdd=0
    for sym,r in groups(bars).items():
        pos=None
        for i in range(35,len(r)):
            b=r[i]
            if pos:
                side=pos['side'];exitp=reason=None
                # Conservative OHLC assumption: stop takes precedence if stop and target touched in same bar.
                if side==1 and b.low<=pos['stop']:exitp=pos['stop'];reason='STOP'
                elif side==-1 and b.high>=pos['stop']:exitp=pos['stop'];reason='STOP'
                elif side==1 and b.high>=pos['target']:exitp=pos['target'];reason='TARGET'
                elif side==-1 and b.low<=pos['target']:exitp=pos['target'];reason='TARGET'
                elif i==len(r)-1:exitp=b.close;reason='END_OF_DATA'
                if exitp is not None:
                    gross=(exitp-pos['entry'])*pos['qty']*side;cost=(pos['entry']+exitp)*pos['qty']*COST_BPS/10000;net=gross-cost;eq+=net
                    ts.append(Trade(code,sym,pos['time'],b.timestamp.isoformat(),'LONG' if side==1 else 'SHORT',pos['entry'],exitp,pos['qty'],gross,cost,net,reason));pos=None
            if pos is None:
                s=strat.signal(r,i)
                if s.side and s.stop>0 and s.target>0:
                    q=size(eq,b.close,s.stop)
                    if q>0:pos={'side':s.side,'entry':b.close,'stop':s.stop,'target':s.target,'qty':q,'time':b.timestamp.isoformat()}
            peak=max(peak,eq);maxdd=max(maxdd,(peak-eq)/peak if peak else 0)
    m=metrics(ts,initial,eq,maxdd);status='PASS' if len(ts)>=MIN_TRADES and isinstance(m['profit_factor'],(int,float)) and m['profit_factor']>1 and m['net_profit']>0 else 'FAIL'
    return {'strategy':code,'name':NAMES[code],'status':status,'reason':'Preliminary in-sample screen only; not production approval.','trades':len(ts),'metrics':m,'trade_records':[asdict(t) for t in ts]}
def main():
    ap=argparse.ArgumentParser(description='Standalone 10-strategy Quant Lab (CSV research only)')
    ap.add_argument('--list',action='store_true');ap.add_argument('--strategy',default='all',help='S01..S10, comma-separated, or all');ap.add_argument('--data',default='data',help='CSV file or directory');ap.add_argument('--capital',type=float,default=CAPITAL);ap.add_argument('--report-dir',default='reports');ap.add_argument('--validate',action='store_true')
    a=ap.parse_args()
    if a.list:
        for k in CLASSES:print(k,NAMES[k],'| optional fields:',', '.join(REQ[k]) or 'OHLCV only')
        return 0
    p=Path(a.data);files=sorted(p.glob('*.csv')) if p.is_dir() else [p]
    if not files:print('BLOCKED: no CSV files found');return 2
    bars=[]
    for f in files:bars.extend(load_file(f))
    bars.sort(key=lambda b:(b.symbol,b.timestamp));dups=sum(1 for sym,r in groups(bars).items() for x,y in zip(r,r[1:]) if x.timestamp==y.timestamp)
    audit={'rows':len(bars),'symbols':sorted(groups(bars)),'start':min(x.timestamp for x in bars).isoformat(),'end':max(x.timestamp for x in bars).isoformat(),'duplicate_adjacent_timestamps':dups,'data_quality':'PASS' if dups==0 else 'WARN'}
    print('DATA AUDIT:',json.dumps(audit,ensure_ascii=False))
    if a.validate:return 0 if dups==0 else 2
    codes=list(CLASSES) if a.strategy.lower()=='all' else [x.strip().upper() for x in a.strategy.split(',')]
    if any(x not in CLASSES for x in codes):print('Unknown strategy code');return 2
    results=[]
    for c in codes:
        z=run(c,bars,a.capital);results.append(z);print(f"{c} {z['status']} trades={z['trades']} {z['reason']}")
        if z['metrics']:print(json.dumps(z['metrics'],ensure_ascii=False))
    out=Path(a.report_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'quant_lab_report.json').write_text(json.dumps({'data_audit':audit,'results':results,'approval':'No live approval. Require walk-forward, untouched out-of-sample, realistic market-specific fees/slippage, parameter stability and independent review.'},indent=2,ensure_ascii=False,default=str),encoding='utf-8')
    with (out/'strategy_summary.csv').open('w',newline='',encoding='utf-8') as f:
        cols=['strategy','name','status','trades','net_profit','return_pct','win_rate_pct','profit_factor','max_drawdown_pct','reason'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for z in results:
            m=z['metrics'];w.writerow({k:(z.get(k,'') if k in z else m.get(k,'')) for k in cols})
    for z in results:(out/f"{z['strategy']}_trades.json").write_text(json.dumps(z['trade_records'],indent=2,ensure_ascii=False),encoding='utf-8')
    print('Reports:',out.resolve());print('NOTE: PASS/FAIL is only an in-sample screen. No strategy is certified profitable or ready for live deployment.')
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:print('Cancelled',file=sys.stderr);raise SystemExit(130)
    except Exception as e:print('ERROR:',e,file=sys.stderr);raise SystemExit(1)
