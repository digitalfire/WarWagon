import { useState } from 'react';
import { Activity, ArrowRight, Bot, BrainCircuit, CheckCircle2, ChevronRight, Clock3, FileSearch, FileText, GitCompare, Layers3, Network, ShieldCheck, SlidersHorizontal, Terminal, Zap } from 'lucide-react';
import * as Tabs from '@radix-ui/react-tabs';
import type { Engagement, WorkspaceTab } from '../domain/types';
import { useWorkspace } from '../state/workspace';
import { Empty, Metric, Panel, Pill, Progress, StatusIcon } from '../components/ui';
import { Investigation } from '../components/Investigation';
import { Frontier } from '../components/Frontier';
import { IntelligenceGraph } from '../components/IntelligenceGraph';
import { Verification } from '../components/Verification';

const sections:{id:WorkspaceTab;label:string;icon:typeof Activity}[]=[
 {id:'overview',label:'Overview',icon:Layers3},{id:'investigation',label:'Investigation',icon:Terminal},
 {id:'plan',label:'Mission Plan',icon:GitCompare},{id:'frontier',label:'Reasoning Frontier',icon:BrainCircuit},
 {id:'graph',label:'Intelligence Graph',icon:Network},{id:'agents',label:'Agent Command',icon:Bot},
 {id:'findings',label:'Findings',icon:ShieldCheck},{id:'verification',label:'Verification',icon:CheckCircle2},
 {id:'evidence',label:'Evidence',icon:FileSearch},{id:'report',label:'Report',icon:FileText},
 {id:'settings',label:'Settings',icon:SlidersHorizontal},
];
function Summary({engagement}:{engagement:Engagement}) {
  const setTab=useWorkspace(s=>s.setTab),selectTask=useWorkspace(s=>s.selectTask);
  return <div className="ww-screen">
    <div className="ww-overview-grid">
      <Panel title="Current Mission Intelligence" detail="Illustrative coordinator situation report" action={<BrainCircuit size={20}/>}>
        <div className="ww-sitrep"><Zap size={22}/><div><strong>{engagement.status==='completed'?'Example investigation completed':engagement.status==='paused'?'Awaiting operator review':'Active investigative questions'}</strong><p>{engagement.objective}</p></div></div>
        <div className="ww-mini-actions"><button onClick={()=>setTab('frontier')}>View reasoning frontier <ArrowRight size={14}/></button><button onClick={()=>setTab('verification')}>Finding verification <ArrowRight size={14}/></button></div>
      </Panel>
      <Panel title="Immediate priorities" detail="Tasks drawn from the example plan">
        {engagement.tasks.length?engagement.tasks.filter(t=>t.status!=='completed').slice(0,4).map(t=><button key={t.id} className="ww-event-row" onClick={()=>selectTask(t.id)}><StatusIcon status={t.status}/><div><strong>{t.title}</strong><small>{t.owner} · {t.status}</small></div><ChevronRight size={16}/></button>):<Empty title="No tasks yet" detail="This is a draft briefing; no execution has been scheduled."/>}
      </Panel>
    </div>
    <Panel title="Engagement Activity" detail="Sample event history. Select an event to inspect the linked task.">
      <EventList engagement={engagement}/>
    </Panel>
  </div>;
}
function EventList({engagement}:{engagement:Engagement}) {
  const selectTask=useWorkspace(s=>s.selectTask),selectEvidence=useWorkspace(s=>s.selectEvidence);
  return <div className="ww-event-list">{engagement.events.map(event=><button className="ww-event-row" key={event.id} onClick={()=>event.evidenceId?selectEvidence(event.evidenceId):event.taskId?selectTask(event.taskId):undefined}>
    <Activity size={16}/><div><strong>{event.title}</strong><small>{event.timestamp} · {event.kind}</small><p>{event.detail}</p></div>{(event.taskId||event.evidenceId)&&<ChevronRight size={16}/>}</button>)}
    {!engagement.events.length&&<Empty title="No events" detail="Drafts do not have an execution history."/>}
  </div>;
}
function Plan({engagement}:{engagement:Engagement}){
  const selectTask=useWorkspace(s=>s.selectTask);
  const done=engagement.tasks.filter(t=>t.status==='completed').length;
  return <div className="ww-screen"><Panel title="Mission Plan" detail={engagement.tasks.length+' planned tasks · '+done+' completed'}>
    <div className="ww-steps-list">{engagement.tasks.map((t,i)=><button className="ww-plan-row" key={t.id} onClick={()=>selectTask(t.id)}><span className="ww-step-number">{String(i+1).padStart(2,'0')}</span><StatusIcon status={t.status}/><div><strong>{t.title}</strong><p>{t.detail}</p><small>{t.phase} · {t.owner}</small></div><Pill tone={t.status==='completed'?'good':t.status==='blocked'?'warn':'muted'}>{t.status}</Pill><ChevronRight size={17}/></button>)}
      {!engagement.tasks.length&&<Empty title="No task graph" detail="This engagement is only a conceptual briefing; it has not been launched."/>}</div></Panel></div>;
}
function Agents({engagement}:{engagement:Engagement}){
  const selectTask=useWorkspace(s=>s.selectTask);
  const [selected,setSelected]=useState<string|null>(null);
  const agent=engagement.agents.find(a=>a.id===selected)||engagement.agents[0];
  return <div className="ww-two-columns"><Panel title="Agent Fleet" detail="Logical specialist roles. These are not concurrently running model processes.">
    <div className="ww-agent-grid">{engagement.agents.map(a=><button className={'ww-agent-card '+(a.id===agent?.id?'selected':'')} key={a.id} onClick={()=>setSelected(a.id)}><Bot size={20}/><strong>{a.name}</strong><small>{a.specialty}</small><Pill tone={a.state==='Queued'?'muted':'blue'}>{a.state}</Pill></button>)}</div>
    {!engagement.agents.length&&<Empty title="No assigned agents" detail="No agent processes are active for a draft."/>}
  </Panel><Panel title="Agent Inspector" detail="Assignment, inference configuration and task link">
    {agent?<div className="ww-inspector-content"><span className="ww-overline">{agent.id}</span><h3>{agent.name}</h3><p>{agent.specialty}</p><div className="ww-data-rows"><div><span>State</span><strong>{agent.state}</strong></div><div><span>Model</span><strong>{agent.model}</strong></div><div><span>Model calls</span><strong>{agent.calls} (sample)</strong></div></div>{agent.taskId&&<button className="ww-button outline" onClick={()=>selectTask(agent.taskId!)}>Open assigned task <ArrowRight size={15}/></button>}</div>:<Empty title="No agent selected" detail="An assignment will appear when the backend supports agent tasking."/>}
  </Panel></div>;
}
function Findings({engagement}:{engagement:Engagement}){
  const selectFinding=useWorkspace(s=>s.selectFinding);
  return <Panel title="Finding Register" detail="Verification status is separate from model confidence.">
    {engagement.findings.map(f=><button key={f.id} className="ww-finding-option" onClick={()=>selectFinding(f.id)}><div><span className="ww-overline">{f.id} · {f.severity.toUpperCase()}</span><strong>{f.title}</strong><p>{f.summary}</p></div><Pill tone={f.status==='verified'?'good':f.status==='candidate'?'warn':'muted'}>{f.status}</Pill><ChevronRight size={16}/></button>)}
    {!engagement.findings.length&&<Empty title="No candidate findings" detail="No findings have been imported or generated."/>}
  </Panel>;
}
function Evidence({engagement}:{engagement:Engagement}){
  const selectedId=useWorkspace(s=>s.evidenceId),selectEvidence=useWorkspace(s=>s.selectEvidence),selectTask=useWorkspace(s=>s.selectTask);
  const observation=engagement.observations.find(e=>e.id===selectedId)||engagement.observations[0];
  return <div className="ww-two-columns">
    <Panel title="Evidence Artifacts" detail="Every observation is linked to a task and source.">
      {engagement.observations.map(e=><button className={'ww-event-row '+(e.id===observation?.id?'selected':'')} key={e.id} onClick={()=>selectEvidence(e.id)}><FileSearch size={17}/><div><strong>{e.title}</strong><small>{e.id} · {e.source}</small></div><ChevronRight size={16}/></button>)}
      {!engagement.observations.length&&<Empty title="No evidence" detail="An unstarted draft has no observable evidence."/>}
    </Panel>
    <Panel title="Observation Inspector" detail="Illustrative source content; actual artifacts have separate digest verification.">
      {observation?<div className="ww-inspector-content"><span className="ww-overline">{observation.id} · {observation.timestamp}</span><h3>{observation.title}</h3><div className="ww-technical-block"><div>ORIGIN</div><code>{observation.source}</code><pre>{observation.content}</pre></div><button className="ww-button outline" onClick={()=>selectTask(observation.taskId)}>Inspect originating task <ArrowRight size={16}/></button><div className="ww-callout">These illustrative sample observations do not have cryptographically verified provenance. <a href="./recorded-runs.html">Open actual recorded artifacts ↗</a></div></div>:<Empty title="Select an observation" detail="No evidence artifact is available."/>}
    </Panel>
  </div>;
}
function Report({engagement}:{engagement:Engagement}){
  const verified=engagement.findings.filter(f=>f.status==='verified');
  const inconclusive=engagement.findings.filter(f=>f.status!=='verified');
  return <div className="ww-screen"><Panel title="Assessment Report — Concept Preview" detail="This is a generated presentation of fixture data, not an actual security assessment.">
    <div className="ww-report-intro"><FileText size={27}/><div><h2>{engagement.name}</h2><p>{engagement.objective}</p><span>{engagement.target}</span></div></div>
    <div className="ww-metrics"><Metric label="Verified (example)" value={verified.length}/><Metric label="Candidates / unresolved" value={inconclusive.length}/><Metric label="Recorded tasks" value={engagement.tasks.length}/><Metric label="Evidence objects" value={engagement.observations.length}/></div>
    <h3>Finding summary</h3><div className="ww-report-findings">{engagement.findings.map(f=><div key={f.id}><strong>{f.title}</strong><Pill tone={f.status==='verified'?'good':'warn'}>{f.status}</Pill><p>{f.impact}</p></div>)}</div>
    <h3>Remaining work</h3><p>{engagement.tasks.filter(t=>t.status!=='completed').length} incomplete example tasks. This report should never be interpreted as a complete assessment of the referenced target.</p>
  </Panel></div>;
}
function Settings({engagement}:{engagement:Engagement}){
  return <Panel title="Engagement Configuration" detail="These proposed resource ceilings are not actively enforced by the frontend.">
    <div className="ww-data-rows"><div><span>Target</span><strong>{engagement.target}</strong></div><div><span>Mode</span><strong>{engagement.mode}</strong></div><div><span>Access</span><strong>{engagement.access}</strong></div><div><span>Perspective</span><strong>{engagement.perspective}</strong></div><div><span>Time</span><strong>{engagement.budget.minutes} minutes</strong></div><div><span>Model calls</span><strong>{engagement.budget.modelCalls}</strong></div><div><span>Tokens</span><strong>{engagement.budget.tokens.toLocaleString()}</strong></div><div><span>Workers</span><strong>{engagement.budget.workers}</strong></div><div><span>HTTP request ceiling</span><strong>{engagement.budget.httpRps}/sec</strong></div></div>
  </Panel>;
}
function OperatorCommand({engagement}:{engagement:Engagement}){
  const mode=useWorkspace(s=>s.operatorMode),setMode=useWorkspace(s=>s.setOperatorMode),add=useWorkspace(s=>s.addOperatorNote);
  const notes=useWorkspace(s=>s.operatorNotes.filter(n=>n.engagementId===engagement.id));
  const [message,setMessage]=useState('');
  return <Panel title="Operator Command Channel" detail="Ask, direct and command are distinct intentions. This preview does not dispatch backend actions.">
    <div className="ww-segmented">{(['ask','direct','command'] as const).map(value=><button key={value} className={mode===value?'active':''} onClick={()=>setMode(value)}>{value}</button>)}</div>
    <p className="ww-muted">{mode==='ask'?'Ask why an agent made a decision, without changing its work.':mode==='direct'?'Propose a mission-priority change and inspect the plan impact.':'Propose a pause, resume or checkpoint instruction.'}</p>
    <label className="sr-only" htmlFor="operator-text">Operator instruction</label><textarea id="operator-text" className="ww-input" value={message} rows={3} onChange={e=>setMessage(e.target.value)} placeholder={mode==='ask'?'Why prioritize this investigation?':mode==='direct'?'Prioritize verification before discovery…':'Checkpoint and pause the engagement…'}/>
    <div className="ww-card-row"><small>Local preview notes only · no active agent channel</small><button className="ww-button primary" disabled={!message.trim()} onClick={()=>{add(message.trim());setMessage('');}}>Preview {mode} <ArrowRight size={14}/></button></div>
    {notes.slice(0,2).map(note=><div className="ww-operator-note" key={note.id}><span className="ww-overline">{note.kind} · {note.createdAt}</span><p>{note.content}</p><small>Recorded as a local preview. No live plan revision or execution action was made.</small></div>)}
  </Panel>;
}
export function EngagementWorkspace(){
  const engagement=useWorkspace(s=>s.engagements.find(e=>e.id===s.engagementId)??s.engagements[0]);
  const tab=useWorkspace(s=>s.tab),setTab=useWorkspace(s=>s.setTab),setPage=useWorkspace(s=>s.setPage);
  const verified=engagement.findings.filter(f=>f.status==='verified').length;
  return <div className="ww-screen">
    <header className="ww-page-head"><div><span className="ww-overline">ENGAGEMENT / {engagement.id}</span><h1>{engagement.name}</h1><p>{engagement.target} · {engagement.mode} · {engagement.perspective} · {engagement.access}</p></div>
      <div className="ww-page-actions"><Pill tone={engagement.status==='completed'?'good':engagement.status==='paused'?'warn':engagement.status==='running'?'blue':'muted'}>{engagement.status==='draft'?'Draft (not launched)':'Simulated '+engagement.status}</Pill>
        <button className="ww-button ghost" onClick={()=>setPage('engagements')}><ArrowRight size={14}/> All engagements</button></div></header>
    <div className="ww-metrics"><Metric label="Elapsed (sample)" value={engagement.elapsedMinutes+'m'} detail={'of '+engagement.budget.minutes+'m'}/><Metric label="Model calls (sample)" value={engagement.usedCalls} detail={'of '+engagement.budget.modelCalls}/><Metric label="Tokens (sample)" value={engagement.usedTokens.toLocaleString()} detail={'of '+engagement.budget.tokens.toLocaleString()}/><Metric label="Verified (illustrative)" value={verified} detail={engagement.findings.length-verified+' candidates / others'}/></div>
    <div className="ww-budget-strip"><div><Clock3 size={15}/> Model budget <b>{engagement.usedCalls} / {engagement.budget.modelCalls} calls</b></div><Progress value={engagement.usedCalls} max={engagement.budget.modelCalls}/></div>
    <Tabs.Root value={tab} onValueChange={v=>setTab(v as WorkspaceTab)}>
      <Tabs.List className="ww-tabs" aria-label="Engagement workspaces">{sections.map(s=><Tabs.Trigger key={s.id} className="ww-tab" value={s.id}><s.icon size={15}/>{s.label}</Tabs.Trigger>)}</Tabs.List>
      <div className="ww-tab-body">
        <Tabs.Content value="overview"><Summary engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="investigation"><Investigation engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="plan"><Plan engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="frontier"><Frontier engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="graph"><IntelligenceGraph engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="agents"><Agents engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="findings"><Findings engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="verification"><Verification engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="evidence"><Evidence engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="report"><Report engagement={engagement}/></Tabs.Content>
        <Tabs.Content value="settings"><Settings engagement={engagement}/></Tabs.Content>
      </div>
    </Tabs.Root>
    <OperatorCommand engagement={engagement}/>
  </div>;
}
