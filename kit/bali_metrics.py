
import json, collections, datetime as dt, io, contextlib, statistics, re
from zoneinfo import ZoneInfo
ET=ZoneInfo('America/New_York'); UTC=dt.timezone.utc
BALI='user_c0wPSKtEPsqkIh08OnjiGaj6XHeFBjGSp2jyVxAggDl'
SEQ='seq_0XX3twr6enX8SbfMZILA8x'  # Welcome Series - Bali Test
# Oct 21, 2026 (Sheila): Welcome Series sign-ups are split between Bali, Jose and Jordan K. A setter's list = leads whose
# "Initial Contact User" field is that setter (what the Close smart views filter on). LIST holds those lead ids while a
# setter is selected (use_setter in bali_show.py); None counts every sign-up (the old Bali-only behavior).
ICU_FIELD='cf_C6fOIXKxCBrG5PhlmEhcO6Rzu20G8XV6aA7wnADkH3P'
LIST=None
# Oct 28, 2026 (Sheila): the Welcome Series card counts no Abandoned Typeform leads (they have their own card). EXCLUDE
# holds the setter's Abandoned Typeform leads ("Incomplete Typeform User" is the setter) while a setter is selected;
# load() drops them from every call, text, meeting and sign-up, so every number on the card leaves them out. None
# keeps every lead (bali_abandoned.py runs that way). Not LIST: Initial Contact User only reaches back to mid October.
AB_USER_FIELD='cf_qiVzsFQUYHM2vmDeUg0mbfIrWgvU3ZJmhujqNtWiAhJ'
EXCLUDE=None
def list_leads(uid, field=ICU_FIELD):
    """Lead ids whose user field `field` (default Initial Contact User) is uid (Close data search, read only)."""
    q={"query":{"type":"and","queries":[{"type":"object_type","object_type":"lead"},
        {"type":"field_condition","field":{"type":"custom_field","custom_field_id":field},
         "condition":{"type":"reference","reference_type":"user_or_group","object_ids":[uid]}}]},
       "_fields":{"lead":["id"]},"_limit":200}
    ids=[];cur=None
    while True:
        b=dict(q)
        if cur: b['cursor']=cur
        r,e=_q(proxy_execute,'POST','/data/search/','close',body=b)
        if e: raise Exception(str(e)[:300])
        body=r.get('data') if isinstance(r.get('data'),dict) else r
        ids+=[x['id'] for x in body.get('data') or []]; cur=body.get('cursor')
        if not cur: break
    return set(ids)
REAL_SEC=180  # calls with no Close outcome: a real conversation lasts 3+ minutes (or led to a booking)
REAL_MIN_SEC=60  # outcome-tagged calls must last 60+ seconds (Sheila, Oct 5)
REAL_TAGS=('conversation: set to closer','conversation: call back later','disqualified')
def is_real_call(c, booked=frozenset()):
    """Real conversation (Sheila, Oct 5, 2026): a call of 60+ sec tagged Set to closer, Call back later or Disqualified,
    or tagged Set to self when a meeting was actually booked (booked = leads with a closer call or self-set that day).
    Calls with no Close outcome keep the old rule: a pickup of 3+ min, or one that led to a booking."""
    d=c.get('duration') or 0
    on=OUTCOMES.get(c.get('outcome_id') or '')
    if on:
        if BAD_NUM.search((c.get('note') or '').lower()): return False
        if on.startswith(REAL_TAGS): return d>=REAL_MIN_SEC
        if on.startswith('conversation: set to self'): return d>=REAL_MIN_SEC and c['lead_id'] in booked
        return False
    return c['_k']=='talk' and (d>=REAL_SEC or c['lead_id'] in booked)
# Closers (Sheila, Oct 5, 2026): Adam Larkins, VeJohn Heinemann, Omar Kaddoura, Nick Vaughan, Owen Henderson,
# Jordan Zadrozny (Jay Z), Julien Breteau, Harry Whyte, Kevin Manuel, Daniel Jenkins, Solomon House, Oliver English, Tyler Johnson
CLOSERS={'user_6MNsV5izSPoZXcJP2YIpFugEBfZ4vFHSvKEpcwDqdGw','user_bWKARGZE8EbHRdVAwb1X7PKedIgSpk36pQqCNedoFux','user_KljJRbJ4KU5gr2vYuVcQOXr2fwDrBRWF77rHsqIvmTP','user_e5ftkzIEvfPsrJiQL5iDkECWGn6zvgVRNNPP7736d75','user_6WoeSFWodzS6EVPUlyUiEv1pplLvDiUokB28Cr72tSO','user_6MGs8qirvfVYunzojwPX9vxrGjYIxwW5caVU40i0V5l','user_eE1A7LS7qtadfjtL4lWfnts3x6RBYBToJNRb5pT1Z23','user_f3vkQZe4xJvRsPV9L6cU1UOHk7nwxStq94aMqJYLqzm','user_pjOhfDFMYSNFDKwgLEMHYOP1a9h8HjfwjSWekJnhx7j','user_2AigaoH78jJdTRUkOZYx4GGiefiBWKiRtR9m9T9LbTA','user_FscBL0yyfYEgqQWD8ZBxvNkyrVfmIl2D6dKuLP2TPoi','user_GTts5Wcmueh0bn5bIMYXgF2TuvZ9qwKXu1kk9s0oLaT','user_G5MW8qwDBNVPFYs9zFGoGUt834xgUxqbHSnCMD8t19U'}
def other_rep_call(o):
    """A call by someone other than Bali that takes the closer-call credit away from him. 0-second 'external'
    records are integration duplicates, not real calls (Oct 6: one logged under David Martin a minute into Bali's
    call hid Mike Mosel's Oct 5 closer call)."""
    return o.get('user_id')!=BALI and o.get('call_method')!='external' and (o.get('duration') or 0)>0
def _q(fn,*a,**k):
    with contextlib.redirect_stdout(io.StringIO()): return fn(*a,**k)
def get_all(ep,params,maxn=20000,stop=None):
    out=[];skip=0
    while True:
        p=dict(params);p['_skip']=skip;p.setdefault('_limit',100)
        r,e=_q(proxy_execute,'GET',ep,'close',query_params=p)
        if e: raise Exception(str(e)[:300])
        body=r.get('data')
        if isinstance(body,dict): items=body.get('data',[]); more=body.get('has_more')
        else: items=body or []; more=len(items)==p['_limit']
        out+=items; skip+=len(items)
        if stop and items and stop(items[-1]): break
        if not more or not items or len(out)>=maxn: break
    return out
def pt(s):
    s=s.replace('Z','+00:00')
    t=dt.datetime.fromisoformat(s)
    if t.tzinfo is None: t=t.replace(tzinfo=UTC)
    return t
def etd(t): return t.astimezone(ET).date()
def day_bounds(d):
    a=dt.datetime(d.year,d.month,d.day,tzinfo=ET); return a, a+dt.timedelta(days=1)
def note_code(n):
    n=(n or '').strip().lower()
    if not n: return None
    if re.search(r'\bvm\b|voicemail|left vm|left msg', n): return 'vm'
    if re.search(r'\bscr(een(er)?)?\b', n): return 'screen'
    if re.search(r'\b(talk|conv|set-?c|set-?s|set to|booked)\b', n): return 'talk'
    if re.match(r'^(called )?(na|no answer)\b', n) or 'called 2x' in n: return 'na'
    if 'wrong number' in n: return 'na'
    return 'note'
OUTCOMES={}
NO_VM_OUTCOME=re.compile(r'no (vm|voice ?mail) option')   # Close outcome 'No answer - no VM option', added by Sheila Oct 5
BAD_NUM=re.compile(r'wrong (number|#|num)|invalid (number|#|num)|not in service|disconnected|bad number|no longer in service')
def load_outcomes():
    try:
        for o in get_all('/outcome/',{}): OUTCOMES[o['id']]=(o.get('name') or '').lower()
    except Exception: pass
def classify(c):
    """'talk' = picked up (talked to a real person). Screeners and voicemails are not pickups."""
    on=OUTCOMES.get(c.get('outcome_id') or '')
    if on:
        if on.startswith('conversation'): return 'talk'
        if on.startswith('disqualified') or on.startswith('do not contact'):
            # he talked to the person and DQ'd them (Sheila, Oct 5). Wrong/invalid numbers and 0-second records stay out.
            if BAD_NUM.search((c.get('note') or '').lower()) or not (c.get('duration') or 0): return 'miss'
            return 'talk'
        if 'voicemail' in on: return 'vm'
        if 'screener' in on: return 'talk' if 'got through' in on else 'screen'
        # a voicemail drop or a VM note means he left one, whatever 'no answer' outcome he picked (Sheila, Oct 5)
        if c.get('disposition')=='vm-left': return 'vm'
        if NO_VM_OUTCOME.search(on): return 'miss'   # 'No answer - no VM option': a note like 'no vm' is not a voicemail
        if note_code(c.get('note'))=='vm': return 'vm'
        return 'miss'
    code=note_code(c.get('note'))
    if c.get('disposition')=='vm-left' or code=='vm': return 'vm'
    if code=='screen': return 'screen'
    if code=='talk': return 'talk'
    if code=='na': return 'miss'
    if (c.get('duration') or 0)>=45: return 'talk'
    return 'miss'
# Voicemail KPI (Sheila, Oct 5): some no-pickups never give Bali a chance to leave a voicemail
# (they hang up or decline, or the call never reaches a mailbox). Those people are left out of the voicemail KPI.
NO_VM_SEC=15   # a 'No answer / hung up' call this short ended before any voicemail beep
NOVM_NOTE=re.compile(r"reject|declin|(doesn.?t|didn.?t|does not|did not|won.?t|not) go through|not in service|no longer in service|disconnected|invalid|wrong (number|#|num)|mailbox (is )?full|vm (is )?full|no (voice ?mail|vm)|can.?t leave|couldn.?t leave")
def no_vm_option(c):
    """True when this call gave Bali no chance to leave a voicemail."""
    if c['_k'] in ('vm','talk','screen'): return False
    if c.get('disposition') in ('busy','blocked','no-answer','failed','error','canceled'): return True   # never reached a mailbox
    on=OUTCOMES.get(c.get('outcome_id') or '','')
    if NO_VM_OUTCOME.search(on): return True   # Bali's own call: 'No answer - no VM option' (from Oct 5), any length
    if 'automated' in on: return True   # 'No answer - automated system'
    if NOVM_NOTE.search((c.get('note') or '').lower()): return True
    if 'hung up' in on and (c.get('duration') or 0)<=NO_VM_SEC: return True
    return False
# Text KPI (Sheila, Oct 8): a number that can't take a call or a text is left out of the text count:
# Close blocked the call (disposition 'blocked'), or Bali's note says wrong/invalid number, not in service or disconnected.
def bad_number(c):
    return c.get('disposition')=='blocked' or bool(BAD_NUM.search((c.get('note') or '').lower()))
# Callbacks (Sheila, Oct 13): an inbound call Bali answered counts as a pickup for closer calls, self-sets and closes
# (a lead who calls back after his voicemail and gets booked). It is NOT a dial: dials, people dialed, pickup and
# connect rates and the follow-up KPIs still count only his outbound calls.
def inbound_talk(c):
    """An inbound call from a lead that Bali answered and talked on."""
    if c.get('direction')!='inbound' or c.get('call_method')=='external' or not c.get('lead_id'): return False
    if c.get('disposition') not in (None,'','answered'): return False
    return classify(c)=='talk' or (c.get('duration') or 0)>=45
def load(D, back=16):
    start=day_bounds(D-dt.timedelta(days=back))[0]; end=day_bounds(D)[1]
    su=start.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'); eu=end.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    if not OUTCOMES: load_outcomes()
    allc=get_all('/activity/call/',{'user_id':BALI,'date_created__gte':su,'date_created__lt':eu})
    calls=[c for c in allc if c.get('direction')=='outbound' and c.get('call_method')!='external' and c.get('lead_id')]
    for c in calls: c['_t']=pt(c['date_created']); c['_k']=classify(c)
    inbound=[c for c in allc if inbound_talk(c)]   # callbacks he answered (Oct 13)
    for c in inbound: c['_t']=pt(c['date_created']); c['_k']='talk'; c['_in']=True
    subs=get_all('/sequence_subscription/',{'sequence_id':SEQ},stop=lambda x: pt(x['date_created'])<start-dt.timedelta(days=3))
    enr={}
    for s in subs:
        t=pt(s['date_created'])
        if s['lead_id'] not in enr or t<enr[s['lead_id']]: enr[s['lead_id']]=t
    if LIST is not None: enr={l:x for l,x in enr.items() if l in LIST}   # only sign-ups on the setter's list (Oct 21)
    sms=get_all('/activity/sms/',{'user_id':BALI,'date_created__gte':su,'date_created__lt':eu})
    sms=[s for s in sms if s.get('direction')=='outbound' and s.get('status') in ('sent','delivered','scheduled','outbox','inbox') ]
    for s in sms: s['_t']=pt(s['date_created'])
    ms=get_all('/activity/meeting/',{'date_created__gte':(day_bounds(D-dt.timedelta(days=back))[0]).astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),'date_created__lt':eu})
    for m in ms: m['_t']=pt(m['date_created'])
    # Do Not Contact (Sheila, Oct 8): leads set to a Do Not Contact status by anyone, with the first time it was set
    dnc={}
    for x in get_all('/activity/status_change/lead/',{'date_created__gte':su,'date_created__lt':eu}):
        if 'do not contact' in (x.get('new_status_label') or '').lower() and x.get('lead_id'):
            t=pt(x['date_created'])
            if x['lead_id'] not in dnc or t<dnc[x['lead_id']]: dnc[x['lead_id']]=t
    if EXCLUDE:   # Oct 28 (Sheila): Abandoned Typeform leads count only on their own card
        keep=lambda x: x.get('lead_id') not in EXCLUDE
        calls=[c for c in calls if keep(c)]; inbound=[c for c in inbound if keep(c)]
        sms=[s for s in sms if keep(s)]; ms=[m for m in ms if keep(m)]; enr={l:x for l,x in enr.items() if l not in EXCLUDE}
    return dict(calls=calls,enr=enr,sms=sms,meetings=ms,dnc=dnc,inbound=inbound)
def first_calls(calls):
    f={}
    for c in sorted(calls,key=lambda c:c['_t']):
        f.setdefault(c['lead_id'],c)
    return f
def _byl(calls):
    byl=collections.defaultdict(list)
    for c in sorted(calls,key=lambda c:c['_t']): byl[c['lead_id']].append(c)
    return byl
def _bookings(D,data,byl):
    """Closer calls and self-sets created on D after a Bali pickup within 24h (rules unchanged from round one).
    From Oct 13 a callback Bali answered (data['inbound']) counts as a pickup here too."""
    a,b=day_bounds(D)
    inb=_byl(data.get('inbound',[]))
    talks=lambda l: sorted([c for c in byl.get(l,[]) if c['_k']=='talk']+inb.get(l,[]),key=lambda c:c['_t'])
    bl=set(byl)|set(inb)
    live=[x for x in data['meetings'] if x.get('lead_id') in bl and not (x.get('title') or '').lower().startswith('canceled')]
    closer=set(); selfset=set(); names=[]
    for x in live:
        if not (a<=x['_t']<b): continue
        lcs=[c for c in talks(x['lead_id']) if c['_t']<=x['_t'] and (x['_t']-c['_t'])<=dt.timedelta(hours=24)]
        if not lcs: continue
        if x.get('user_id')==BALI: selfset.add(x['lead_id']); continue
        if x.get('user_id') not in CLOSERS: continue
        # Oct 8, 2026 (Sheila): an earlier Bali-owned meeting (set to self, two-step) no longer blocks the closer-call credit
        oc=_q(get_all,'/activity/call/',{'lead_id':x['lead_id']})
        # Oct 8, 2026 (Sheila): a lead who booked a meeting on their own before Bali's first real call is not Bali's set
        mine=[pt(o['date_created']) for o in oc if o.get('user_id')==BALI and o.get('call_method')!='external'
              and (o.get('direction')=='outbound' or inbound_talk(o))]
        lm=_q(get_all,'/activity/meeting/',{'lead_id':x['lead_id']})
        if mine and any(pt(y['date_created'])<min(mine) for y in lm if not (y.get('title') or '').lower().startswith('canceled')): continue
        if any(other_rep_call(o) and lcs[-1]['_t']<pt(o['date_created'])<x['_t'] for o in oc): continue
        if x['lead_id'] not in closer: names.append((x.get('title') or '').split(' and ')[0])
        closer.add(x['lead_id'])
    return closer, selfset-closer, names
def day_metrics(D, data, earliest_first=None, with_bookings=True):
    a,b=day_bounds(D)
    calls=data['calls']; byl=_byl(calls)
    dc=[c for c in calls if a<=c['_t']<b]
    m={'date':D.isoformat()}
    m['dials']=len(dc); m['people_dialed']=len({c['lead_id'] for c in dc})
    if not dc:
        m['dialed']=False; return m
    m['dialed']=True
    t0=min(c['_t'] for c in dc); t1=max(c['_t'] for c in dc)
    m['first_call']=t0.astimezone(ET).strftime('%-I:%M%p').lower(); m['last_call']=t1.astimezone(ET).strftime('%-I:%M%p').lower()
    new=[l for l,t in data['enr'].items() if a<=t<b]
    m['new_leads']=len(new)
    inh=[l for l in new if t0<=data['enr'][l]<=t1]
    waits=[]; w15=0; called_new=0
    for l in new:
        cs=[c for c in byl.get(l,[]) if c['_t']>=data['enr'][l]-dt.timedelta(minutes=1) and c['_t']<b]
        if cs: called_new+=1
    for l in inh:
        cs=[c for c in byl.get(l,[]) if c['_t']>=data['enr'][l]-dt.timedelta(minutes=1)]
        if cs:
            w=(cs[0]['_t']-data['enr'][l]).total_seconds()/60; waits.append(max(w,0))
            if w<=15: w15+=1
    m['new_in_hours']=len(inh); m['within15']=w15; m['in_hours_called']=len(waits)
    m['median_wait_min']=round(statistics.median(waits)) if waits else None
    m['new_called_same_day']=called_new
    lo=day_bounds(D-dt.timedelta(days=2))[0]
    m['backlog']=sum(1 for l,t in data['enr'].items() if lo<=t<b and not any(c['_t']<b for c in byl.get(l,[])))
    # pickups (talked to a real person) and real conversations (3+ min or booked)
    talk={c['lead_id'] for c in dc if c['_k']=='talk'}
    m['pickups']=len(talk); m['conversations']=len(talk)  # 'conversations' kept as an alias of pickups for old readers
    m['conv_from_notes']=sum(1 for c in dc if c['_k']=='talk' and note_code(c.get('note'))=='talk')
    long_={c['lead_id'] for c in dc if is_real_call(c)}
    if with_bookings:
        closer,selfs,names=_bookings(D,data,byl)
        m['closer_calls']=len(closer); m['self_sets']=len(selfs); m['closer_names']=names
        m['real_conversations']=len({c['lead_id'] for c in dc if is_real_call(c,closer|selfs)})
    else:
        m['real_conversations']=len(long_)
    # follow-up cohort: first-ever call on D, not a pickup on D
    fc=first_calls(calls)
    coh=[l for l,c in fc.items() if a<=c['_t']<b and (earliest_first is None or c['_t']>=earliest_first) and l not in talk]
    dnc=data.get('dnc',{})   # Oct 8 (Sheila): leads set to Do Not Contact by the end of D are left out of all follow-up counts
    m['dnc_left_out']=sum(1 for l in coh if l in dnc and dnc[l]<b)
    coh=[l for l in coh if not (l in dnc and dnc[l]<b)]
    smsl=collections.defaultdict(list)
    for s in data['sms']: smsl[s['lead_id']].append(s['_t'])
    vm=tx=t2=dd=vp=tp=0
    for l in coh:
        cs=[c for c in byl[l] if a<=c['_t']<b]
        if any(c['_k']=='vm' for c in cs): vm+=1
        if any(not no_vm_option(c) for c in cs): vp+=1   # at least one call that day where he could leave a voicemail
        bad=any(bad_number(c) for c in cs)   # blocked or invalid number: no text possible (Oct 8)
        if not bad: tp+=1
        if not bad and any(a<=t<b for t in smsl.get(l,[])): tx+=1
        if any((c['_t']-cs[0]['_t'])>=dt.timedelta(minutes=60) for c in cs[1:]): t2+=1
        if any(0<(cs[i+1]['_t']-cs[i]['_t']).total_seconds()<=180 for i in range(len(cs)-1)): dd+=1
    m['missed_first']=len(coh); m['vm_possible']=vp; m['vm_left']=vm; m['text_sent']=tx; m['text_possible']=tp; m['try2_same_day']=t2; m['double_dial']=dd
    prevdays=sorted({etd(c['_t']) for c in calls if etd(c['_t'])<D})
    if prevdays:
        P=prevdays[-1]; pa,pb=day_bounds(P)
        ptalk={c['lead_id'] for c in calls if pa<=c['_t']<pb and c['_k']=='talk'}
        pco=[l for l,c in fc.items() if pa<=c['_t']<pb and l not in ptalk and (earliest_first is None or c['_t']>=earliest_first)]
        pco=[l for l in pco if not (l in dnc and dnc[l]<b)]   # Do Not Contact by the end of D: no third try owed (Oct 8)
        m['prev_day']=P.isoformat(); m['prev_missed']=len(pco)
        m['try3_next_day']=sum(1 for l in pco if any(a<=c['_t']<b for c in byl[l]))
    us=[c for c in dc if (c.get('local_phone') or '').startswith('+1') and not (c.get('local_phone') or '').startswith('+1807')]
    m['us_number_calls']=len(us); m['power_dialer_calls']=sum(1 for c in dc if c.get('call_method')=='power')
    m['texts_total']=sum(1 for s in data['sms'] if a<=s['_t']<b)
    return m
def _speed(D,data,byl):
    a,b=day_bounds(D); dc=[c for c in data['calls'] if a<=c['_t']<b]
    if not dc: return []
    t0=min(c['_t'] for c in dc); t1=max(c['_t'] for c in dc); out=[]
    for l,e in data['enr'].items():
        if not (a<=e<b and t0<=e<=t1): continue
        cs=[c for c in byl.get(l,[]) if c['_t']>=e-dt.timedelta(minutes=1) and c['_t']<b]
        if not cs: out.append(dict(w=None,pick=False,real=False)); continue
        out.append(dict(w=max((cs[0]['_t']-e).total_seconds()/60,0), pick=cs[0]['_k']=='talk',
                        real=any(is_real_call(c) for c in cs)))
    return out
def _bucket(w):
    if w is None: return 'none'
    return 'le15' if w<=15 else 'm15_60' if w<=60 else 'h1_3' if w<=180 else 'h3p'
def run(D, trend_days=7):
    """Daily scorecard metrics for dialing day D (v2: new-lead funnel)."""
    data=load(D, back=16); m=day_metrics(D,data)
    if not m.get('dialed'): return m
    a,b=day_bounds(D); calls=data['calls']; byl=_byl(calls)
    dc=[c for c in calls if a<=c['_t']<b]; dialed={c['lead_id'] for c in dc}
    fc=first_calls(calls)
    new={l for l,t in data['enr'].items() if a<=t<b}
    prevdays=sorted({etd(c['_t']) for c in calls if etd(c['_t'])<D})
    if prevdays:
        P=prevdays[-1]; pa,pb=day_bounds(P)
        ptalk={c['lead_id'] for c in calls if pa<=c['_t']<pb and c['_k']=='talk'}
        due={l for l,c in fc.items() if pa<=c['_t']<pb and l not in ptalk}-new
    else: due=set()
    lo=day_bounds(D-dt.timedelta(days=3))[0]
    back={l for l,t in data['enr'].items() if lo<=t<a and not any(c['_t']<a for c in byl.get(l,[]))}-new-due
    other=dialed-new-due-back
    closer,selfs,_=_bookings(D,data,byl); booked=closer|selfs
    pick={c['lead_id'] for c in dc if c['_k']=='talk'}
    real={c['lead_id'] for c in dc if is_real_call(c,booked)}
    G=dict(new=new,due=due,backlog=back,other=other); F={}
    for k,s in G.items():
        F[k]=dict(list=len(s),dialed=len(s&dialed),dials=sum(1 for c in dc if c['lead_id'] in s),picked=len(s&pick),real=len(s&real),
                  closer=len(s&closer),self=len(s&selfs))
    m['funnel']=F; m['funnel_total']={x:sum(F[k][x] for k in F) for x in F['new']}
    smsl=collections.defaultdict(list)
    for s in data['sms']: smsl[s['lead_id']].append(s['_t'])
    def touches(leads):
        r=collections.Counter()
        for l in leads:
            pc=[c for c in byl[l] if a<=c['_t']<b and c['_k']=='talk'][0]
            pr=[c for c in byl[l] if c['_t']<pc['_t']]; ps=[t for t in smsl.get(l,[]) if t<pc['_t']]
            if not pr and not ps: r['first_dial']+=1; continue
            r['after_more']+=1; r['with_prior_dials']+=bool(pr); r['with_vm']+=any(c['_k']=='vm' for c in pr); r['with_text']+=bool(ps)
        return {k:r.get(k,0) for k in ['first_dial','after_more','with_prior_dials','with_vm','with_text']}
    m['touch_new']=touches(pick&new); m['touch']=touches(pick)
    sp=_speed(D,data,byl); bk=collections.Counter(_bucket(x['w']) for x in sp)
    m['speed']=dict(n=len(sp),**{k:bk.get(k,0) for k in ['le15','m15_60','h1_3','h3p','none']})
    lo2=day_bounds(D-dt.timedelta(days=2))[0]
    never=sum(1 for l,t in data['enr'].items() if lo2<=t<b and not any(c['_t']<b for c in byl.get(l,[])))
    m['carry']=dict(never_called=never,owed_followups=len(due-dialed),total=never+len(due-dialed))
    hrs=list(range(9,24))
    ch=collections.Counter(c['_t'].astimezone(ET).hour for c in dc)
    sh=collections.Counter(data['enr'][l].astimezone(ET).hour for l in new)
    m['hours']=[dict(h=h,calls=ch.get(h,0),signups=sh.get(h,0)) for h in hrs]
    ts=sorted(c['_t'] for c in dc); batches=[[ts[0],ts[0],1]]
    for t in ts[1:]:
        if (t-batches[-1][1])>=dt.timedelta(minutes=30): batches.append([t,t,1])
        else: batches[-1][1]=t; batches[-1][2]+=1
    f=lambda t:t.astimezone(ET).strftime('%-I:%M%p').lower()
    m['batches']=[dict(start=f(x[0]),end=f(x[1]),calls=x[2]) for x in batches]
    lo14=day_bounds(D-dt.timedelta(days=13))[0]
    e14=[t.astimezone(ET) for t in data['enr'].values() if lo14<=t<b and t.astimezone(ET).weekday()<5]
    h14=collections.Counter(t.hour for t in e14)
    best=max(range(9,22),key=lambda h:h14.get(h,0)+h14.get(h+1,0))
    m['block']=dict(start_hour=best,signups=h14.get(best,0)+h14.get(best+1,0),signups_total=len(e14),
                    calls_in_block=sum(1 for c in dc if best<=c['_t'].astimezone(ET).hour<best+2),
                    hist24=[h14.get(h,0) for h in range(24)],weekdays=len({t.date() for t in e14}) or 1)
    cnt=collections.Counter(etd(c['_t']) for c in calls)
    days=sorted(d for d,n in cnt.items() if n>=20 and d<=D)[-trend_days:]
    agg={'fast':[0,0,0],'slow':[0,0,0]}; tr=[]
    for d in days:
        for x in _speed(d,data,byl):
            if x['w'] is None: continue
            g='fast' if x['w']<=15 else 'slow'; agg[g][0]+=1; agg[g][1]+=x['pick']; agg[g][2]+=x['real']
        y=day_metrics(d,data,with_bookings=False)
        tr.append({k:y.get(k) for k in ['date','new_in_hours','within15','missed_first','vm_possible','vm_left','try2_same_day','people_dialed','pickups','real_conversations']})
    m['speed7']={g:dict(n=v[0],picked=v[1],real=v[2]) for g,v in agg.items()}; m['speed7']['days']=len(days)
    m['trend']=tr
    return m
def week(start, end):
    """Sum day_metrics over dialing days start..end (dates, inclusive). Used by the weekly leadership report."""
    data=load(end, back=(end-start).days+11)
    days=[start+dt.timedelta(days=i) for i in range((end-start).days+1)]
    keys=['dials','people_dialed','new_leads','new_in_hours','within15','pickups','conversations','real_conversations','closer_calls','self_sets','missed_first','vm_possible','vm_left','text_possible','text_sent','try2_same_day','double_dial','prev_missed','try3_next_day','us_number_calls','power_dialer_calls','texts_total','conv_from_notes']
    tot=collections.Counter(); per=[]; names=[]
    coded=0; allc=0
    for d in days:
        x=day_metrics(d,data)
        if not x.get('dialed'): continue
        per.append({k:x.get(k) for k in ['date','dials','people_dialed','within15','new_in_hours','pickups','real_conversations','closer_calls','self_sets','missed_first','vm_possible','vm_left','text_possible','text_sent','try2_same_day','us_number_calls','power_dialer_calls','median_wait_min']})
        for k in keys: tot[k]+=x.get(k) or 0
        names+=x.get('closer_names',[])
        a,b=day_bounds(d)
        for c in data['calls']:
            if a<=c['_t']<b:
                allc+=1
                if c.get('outcome_id') or note_code(c.get('note')) in ('vm','na','screen','talk'): coded+=1
    out=dict(tot); out['days']=per; out['closer_names']=names; out['calls_coded']=coded; out['calls_total']=allc
    return out
