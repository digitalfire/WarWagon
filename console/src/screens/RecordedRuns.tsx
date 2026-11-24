import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Activity, ArrowRight, CheckCircle2, CircleAlert, FileCheck2, FlaskConical, Hash, Radio, ShieldCheck, Terminal } from 'lucide-react';
import type { RecordedEvent, RecordedRunSummary } from '../api/recorded';
import { getRecordedRun, getRecordedRuns } from '../api/recorded';
import { Empty, Metric, Panel, Pill } from '../components/ui';
function EventCard({event}:{event:RecordedEvent}){
  return <article className="ww-evidence-preview">
    <div className="ww-card-row"><span className="ww-overline">{event.id} / {event.kind.replace('_',' ')}</span><Pill tone={event.kind==='verification'?(event.verification?.verified?'good':'warn'):'blue'}>{event.kind==='verification'?(event.verification?.verified?'Supported':'Rejected'):event.kind}</Pill></div>
    <strong>{event.summary}</strong>
    {event.kind==='tool_call'&&<div className="ww-technical-block"><div><Terminal size={14}/> MODEL-SELECTED TOOL</div><code>{event.tool?.function.name}</code><pre>{event.tool?.function.arguments}</pre><small>Model tokens: {event.usage?.total_tokens??'Not reported'}</small></div>}
    {event.kind==='observation'&&<div className="ww-technical-block"><div><Activity size={14}/> REAL HTTP OBSERVATION</div><code>{event.observation?.method} {event.observation?.url}</code><pre>HTTP {event.observation?.status_code} · {event.observation?.total_seconds}s · redirects {event.observation?.redirects_followed}</pre><small>SHA-256: {event.sha256}</small></div>}
    {event.kind==='claim'&&<div className="ww-technical-block"><div><FileCheck2 size={14}/> MODEL CLAIM</div><pre>Claimed status: {event.claim?.status_code}\nObservation hash: {event.claim?.observation_sha256}</pre><small>Model tokens: {event.usage?.total_tokens??'Not reported'}</small></div>}
    {event.kind==='verification'&&<div className="ww-technical-block"><div><ShieldCheck size={14}/> VERIFIER RESULT</div><pre>{event.verification?.claim_source} claim: {event.verification?.verified?'Supported':'Rejected'}{event.verification?.reason?' · '+event.verification.reason:''}</pre><small>Expectation SHA-256: {event.verification?.expectation_sha256}</small></div>}
  </article>;
}
export function RecordedRuns(){
  const [selected,setSelected]=useState<RecordedRunSummary['id']>('confirmation');
  const [replayed,setReplayed]=useState<RecordedEvent[]>([]);
  const [replayState,setReplayState]=useState<'idle'|'playing'|'complete'|'error'>('idle');
  const [startReplay,setStartReplay]=useState(0);
  useEffect(()=>{
    if(!startReplay)return;
    setReplayed([]);setReplayState('playing');
    const source=new EventSource('/api/v1/runs/'+encodeURIComponent(selected)+'/events');
    source.addEventListener('record',event=>{
      try{setReplayed(records=>[...records,JSON.parse((event as MessageEvent).data) as RecordedEvent]);}
      catch{source.close();setReplayState('error');}
    });
    source.addEventListener('replay_complete',()=>{source.close();setReplayState('complete');});
    source.onerror=()=>{source.close();setReplayState('error');};
    return ()=>source.close();
  },[selected,startReplay]);
  const {data:catalog,isLoading,error,refetch}=useQuery({queryKey:['recorded-runs'],queryFn:getRecordedRuns,retry:1});
  const {data:detail,isLoading:detailLoading,error:detailError}=useQuery({
    queryKey:['recorded-run',selected],queryFn:()=>getRecordedRun(selected),enabled:!!catalog?.runs.find(r=>r.id===selected),retry:1});
  const current=catalog?.runs.find(r=>r.id===selected);
  return <div className="ww-screen">
    <header className="ww-page-head"><div><span className="ww-overline">WARWAGON / ACTUAL RECORDED MODEL EVIDENCE</span><h1>Recorded Run Workspace</h1><p>Real model/tool traces and independent verifier results, loaded through the local read-only API.</p></div><Pill tone={error?'warn':catalog?'good':'muted'}>{error?'Gateway offline':catalog?'Recorded data':'Connecting'}</Pill></header>
    <div className="ww-callout"><CircleAlert size={18}/> These records are real local service-health observation experiments, <b>not penetration tests or confirmed security vulnerabilities</b>. Events are historical replay. No agent is currently running on this page.</div>
    {error&&<Panel title="Recorded artifact gateway unavailable"><p className="ww-muted">Start the local read-only API: <code>python -m warwagon.console_api --port 8765</code> from the repository root. No synthetic data will be substituted.</p><button className="ww-button outline" onClick={()=>void refetch()}>Retry connection <ArrowRight size={15}/></button></Panel>}
    {isLoading&&<Panel><p className="ww-muted">Loading validated recorded artifacts…</p></Panel>}
    {catalog&&<div className="ww-two-columns">
      <Panel title="Recorded run catalog" detail={catalog.runs.length+' digest-checked saved experiment(s)'}>
        <div className="ww-frontier-list">{catalog.runs.map(run=><button className={'ww-frontier-item '+(run.id===selected?'selected':'')} key={run.id} onClick={()=>setSelected(run.id)}>
          <div className="ww-card-row"><span className="ww-overline">{run.id.toUpperCase()} / {run.observedAt}</span><Pill tone="blue">Recorded</Pill></div>
          <strong>{run.model}</strong><small>{run.target} · HTTP {run.observedStatus}</small><small>{run.modelCalls} model invocations · {run.tokens??'unknown'} tokens</small>
        </button>)}</div>
        <div className="ww-technical-note"><Hash size={14}/> Source SHA-256 values verified against the exact stored artifact bytes before the API returned them.</div>
      </Panel>
      <Panel title="Run summary" detail="Recorded model claim verification, not an application finding">
        {current&&<div className="ww-inspector-content">
          <div className="ww-metrics ww-inline-metrics"><Metric label="Model calls" value={current.modelCalls}/><Metric label="Total tokens" value={current.tokens??'Unavailable'}/></div>
          <div className="ww-data-rows"><div><span>Observed HTTP status</span><strong>{current.observedStatus}</strong></div><div><span>Model claim</span><strong>{current.modelVerdict}</strong></div><div><span>Model</span><strong>{current.model}</strong></div></div>
          <span className="ww-overline">RUN ARTIFACT SHA-256</span><code className="ww-digest">{current.traceSha256}</code>
        </div>}
      </Panel>
    </div>}
    {detailLoading&&<Panel><p className="ww-muted">Loading run provenance and recorded events…</p></Panel>}
    {detailError&&<Panel><p className="ww-muted">The selected recorded artifact could not be validated or loaded.</p></Panel>}
    {detail&&<div className="ww-two-columns">
      <Panel title="Recorded execution history" detail="Tool → observation → claim → verification (ordered from original artifact)">
        <div className="ww-replay-toolbar"><button className="ww-button outline" onClick={()=>setStartReplay(n=>n+1)}>Replay recorded events</button><span role="status" className="ww-muted">{replayState==="playing"?"Playing historical records":replayState==="complete"?"Historical replay complete":replayState==="error"?"Replay unavailable":"Historical data; not live"}</span><span className="ww-muted">{replayState==="idle"?"":replayed.length+" events"}</span></div>
        <div className="ww-recorded-events">{(replayState==="idle"?detail.events:replayed).map(event=><EventCard key={event.id} event={event}/>)}</div>
      </Panel>
      <Panel title="Evidence Verification" detail="Model verdict and negative-control verdict are distinct">
        {detail.verifications.map((v,i)=><div className="ww-comparison-card" key={i}>
          <div className="ww-card-row"><span className="ww-overline">{v.claim_source.toUpperCase()} CLAIM</span>{v.verified?<CheckCircle2 className="good-text" size={16}/>:<CircleAlert className="warn-text" size={16}/>}</div>
          <strong>{v.verified?'Verified model status claim':'Rejected supplied negative control'}</strong>
          <p>{v.reason??'Verifier accepted the recorded status claim based on the matching fixture expectation.'}</p>
          <small>Trace SHA-256: {v.trace_sha256}</small>
        </div>)}
        <div className="ww-callout"><FlaskConical size={17}/> The verifier established that the model's observed **HTTP status** matches the benign fixture expectation. This says nothing about finding a vulnerability.</div>
        <a className="ww-button outline" href="./recorded-runs.html">Open original raw JSON inspector <ArrowRight size={16}/></a>
      </Panel>
    </div>}
    {catalog&&!catalog.runs.length&&<Empty title="No recorded runs" detail="Add validated artifacts to the configured read-only gateway."/>}
    <Panel title="Event delivery contract" detail="Recorded replay, not live execution">
      <div className="ww-action-list"><div><Radio size={17}/> The API exposes <code>/api/v1/runs/{selected}/events</code> as finite SSE playback with stable event IDs.</div><div><ShieldCheck size={17}/> No background assessment, model inference, task scheduling or live event delivery is implied.</div></div>
    </Panel>
  </div>;
}
