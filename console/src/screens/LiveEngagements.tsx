import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, ArrowRight, BrainCircuit, CircleAlert, FileCheck2, HardDrive, Network, Radio, RefreshCw, ShieldCheck, Terminal } from 'lucide-react';
import { getLedgerCatalog, type LedgerEvent } from '../api/live';
import { useLedgerFeed } from '../api/useLedgerFeed';
import { Empty, Metric, Panel, Pill } from '../components/ui';

function text(value:unknown):string{
  if(value===null||value===undefined)return 'Not recorded';
  return typeof value==='string'?value:JSON.stringify(value,null,2);
}
function highlight(kind:string):'good'|'warn'|'blue'|'muted' {
  if(kind==='run.failed'||kind==='engagement.failed')return 'warn';
  if(kind==='tool.observation'||kind==='model.response')return 'blue';
  if(kind==='engagement.completed')return 'good';
  return 'muted';
}
function EventDetail({event}:{event:LedgerEvent}){
  const payload=event.payload;
  return <div className="ww-inspector-content" data-testid="event-inspector">
    <div className="ww-card-row"><span className="ww-overline">EVENT #{event.sequence} · {event.kind}</span><Pill tone={highlight(event.kind)}>{event.origin}</Pill></div>
    <div className="ww-data-rows"><div><span>Event ID</span><strong>{event.eventId}</strong></div><div><span>Recorded at</span><strong>{event.occurredAt}</strong></div><div><span>Engagement</span><strong>{event.engagementId}</strong></div><div><span>Schema revision</span><strong>{event.schemaVersion}</strong></div></div>
    {event.kind==='tool.invocation'&&<div className="ww-technical-block"><div><Terminal size={15}/> MODEL-SELECTED TOOL</div><code>{text(payload.tool)}</code><pre>{text(payload.arguments)}</pre><small>Tool call ID: {text(payload.toolCallId)}</small></div>}
    {event.kind==='tool.observation'&&<div className="ww-technical-block"><div><Activity size={15}/> ACTUAL TOOL OBSERVATION</div><pre>{text(payload.result)}</pre><small>Tool: {text(payload.tool)} · Call: {text(payload.toolCallId)}</small></div>}
    {event.kind==='model.response'&&<div className="ww-technical-block"><div><BrainCircuit size={15}/> MODEL CALL METADATA</div><pre>{text(payload.usage)}</pre><small>Model: {text(payload.model)} · Tool calls: {text(payload.toolCallCount)}</small></div>}
    {event.kind==='agent.discovery.heuristic'&&<div className="ww-callout"><CircleAlert size={18}/> Lab-specific evidence-matching heuristic, not independent confirmation of a real-world security vulnerability. Scorer credit: {text(payload.credited)}</div>}
    {event.kind==='fixture.oracle.result'&&<div className="ww-callout"><ShieldCheck size={18}/> This only establishes the training fixture's known weakness; it does not credit the agent with discovering it.</div>}
    <div className="ww-technical-block"><div><HardDrive size={15}/> DURABLE EVENT PAYLOAD</div><pre>{text(payload)}</pre></div>
    <div><span className="ww-overline">SHA-256 / RECORDED PAYLOAD</span><p className="ww-digest">{event.payloadSha256}</p></div>
  </div>;
}

export function LiveEngagements(){
  const catalog=useQuery({queryKey:['ledger-engagement-catalog'],queryFn:getLedgerCatalog,
    refetchInterval:10000,retry:1,refetchOnWindowFocus:false});
  const [selected,setSelected]=useState<string|null>(null);
  const [eventSequence,setEventSequence]=useState<number|null>(null);
  useEffect(()=>{
    const items=catalog.data?.engagements??[];
    if(!selected&&items.length)setSelected(items[0].id);
  },[catalog.data,selected]);
  const {detail,events,status,error}=useLedgerFeed(selected);
  const engagement=catalog.data?.engagements.find(e=>e.id===selected)??detail.data?.engagement;
  const observed=events.filter(e=>e.kind==='tool.observation');
  const models=events.filter(e=>e.kind==='model.response');
  const toolCalls=events.filter(e=>e.kind==='tool.invocation');
  const focused=events.find(e=>e.sequence===eventSequence)??events.at(-1);
  const terminal=events.findLast(e=>e.kind==='engagement.completed'||e.kind==='engagement.failed'||e.kind==='engagement.canceled');
  return <div className="ww-screen">
    <header className="ww-page-head"><div><span className="ww-overline">WARWAGON / PERSISTED ENGAGEMENT EXECUTION</span><h1>Live Engagement Events</h1>
      <p>Observe real local-lab model calls, tool execution and durable evidence as the agent runs.</p></div>
      <Pill tone={error||detail.error||catalog.error?'warn':status==='connected'?'good':'muted'}>
        {error?'Event integrity error':catalog.error?'Gateway offline':status==='connected'?'SSE connected':status==='reconnecting'?'Reconnecting':status==='connecting'?'Connecting':status==='unavailable'?'Stream unavailable':'Awaiting selection'}
      </Pill>
    </header>
    <div className="ww-callout"><CircleAlert size={17}/> This workspace reads stored local-agent events. It does not start security assessments. Lab oracle and agent-discovery heuristic results are NOT independently verified vulnerability findings. The three concept engagements remain in their own preview workspace.</div>
    {catalog.error&&<Panel title="Engagement API unavailable" detail="No sample data will be substituted for persisted execution records."><p className="ww-muted">Start the API from the repository root: <code>python -m warwagon.console_api --port 8765</code></p>
      <button className="ww-button outline" onClick={()=>void catalog.refetch()}><RefreshCw size={15}/> Retry</button></Panel>}
    {catalog.isLoading&&<Panel><p className="ww-muted">Loading persisted engagement catalog…</p></Panel>}
    {catalog.data&&<div className="ww-two-columns">
      <Panel title="Recorded Engagements" detail="Only engagements actually persisted to the local SQLite ledger appear here.">
        {catalog.data.engagements.map(item=><button className={'ww-frontier-item '+(selected===item.id?'selected':'')} key={item.id} onClick={()=>{setSelected(item.id);setEventSequence(null);}}>
          <div className="ww-card-row"><span className="ww-overline">{item.id.slice(0,23)}</span><Pill tone={item.state==='failed'?'warn':item.state==='completed'?'good':'blue'}>{item.state}</Pill></div>
          <strong>{item.title}</strong><small>{item.target}</small><small>{item.model??'Model unspecified'}</small>
        </button>)}
        {!catalog.data.engagements.length&&<Empty title="No persisted engagements" detail="Start a bounded local model run with python -m warwagon.live_lab --model YOUR_MODEL."/>}
      </Panel>
      <Panel title="Execution Snapshot" detail={engagement?'Stored agent event stream':'Select an engagement'}>
        {engagement?<div className="ww-inspector-content"><span className="ww-overline">ENGAGEMENT / {engagement.id}</span><h3>{engagement.title}</h3><p>{engagement.target}</p>
          <div className="ww-metrics ww-inline-metrics"><Metric label="Model turns" value={models.length}/><Metric label="Tool invocations" value={toolCalls.length}/><Metric label="Observations" value={observed.length}/><Metric label="Events loaded" value={events.length}/></div>
          <div className="ww-data-rows"><div><span>Model</span><strong>{engagement.model??'Unknown'}</strong></div><div><span>Lifecycle</span><strong>{terminal?.kind.replace('engagement.','')??engagement.state}</strong></div><div><span>Transport</span><strong>{status==='connected'?'Stream connected':status}</strong></div></div>
          {detail.data?.hasMore&&<p className="ww-muted">Initial snapshot is limited to 1,000 events. Stream continues from the last loaded cursor.</p>}
          {detail.error&&<p className="ww-muted" role="alert">Could not load this engagement's stored events. {String(detail.error)}</p>}
          <button className="ww-button outline" onClick={()=>void catalog.refetch()}><RefreshCw size={15}/> Refresh catalog</button>
        </div>:<Empty title="Nothing selected" detail="Select a persisted run to inspect its event history."/>}
      </Panel>
    </div>}
    {selected&&<div className="ww-two-columns">
      <Panel title="Actual Execution Timeline" detail={events.length+' stored records · global sequence order'} action={<Radio size={18}/>}>
        <div className="ww-task-list" data-testid="live-event-timeline">{events.map(event=><button key={event.sequence} onClick={()=>setEventSequence(event.sequence)} className={'ww-task '+(focused?.sequence===event.sequence?'selected':'')}>
          <Activity size={15}/><div><strong>{event.kind}</strong><small>#{event.sequence} · {event.occurredAt} · {event.origin}</small></div><ArrowRight size={15}/></button>)}</div>
        {!events.length&&<Empty title="No recorded events" detail="Waiting for the agent event producer or restored ledger history."/>}
      </Panel>
      <Panel title="Task & Evidence Inspector" detail="Actual run information only; task hierarchy is not yet emitted by the single-agent runtime.">
        {focused?<EventDetail event={focused}/>:<Empty title="Select a recorded event" detail="Tool arguments, results and provenance will appear here."/>}
      </Panel>
    </div>}
    <Panel title="Agent Execution Controls" detail="Read-only observation. Launch and worker management are CLI/backend responsibilities.">
      <div className="ww-action-list"><div><Terminal size={16}/> Explicit local model run: <code>python -m warwagon.live_lab --model YOUR_INSTALLED_MODEL</code></div>
        <div><Network size={16}/> SSE resumes from persisted sequence, deduplicates events and retains snapshots across server reconnection.</div>
        <div><FileCheck2 size={16}/> Findings must be independently verified. The existing lab's heuristic result remains a separate event.</div></div>
    </Panel>
  </div>;
}
