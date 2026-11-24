import { ArrowRight, ArrowUpRight, Bot, FileCheck2, Globe2, Plus, Radar, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { useWorkspace } from '../state/workspace';
import { Metric, Panel, Pill, Progress, StatusIcon } from '../components/ui';
import type { Engagement } from '../domain/types';
const statusTone=(status:Engagement['status'])=>status==='completed'?'good':status==='paused'?'warn':status==='running'?'blue':'muted';
const typeName=(type:Engagement['type'])=>({web:'Web application',api:'API & identity',cloud:'Cloud configuration'}[type]);
export function EngagementCard({engagement}:{engagement:Engagement}) {
  const open=useWorkspace(s=>s.openEngagement);
  const confirmed=engagement.findings.filter(f=>f.status==='verified').length;
  return <button className="ww-engagement-card" onClick={()=>open(engagement.id)}>
    <div className="ww-card-row"><span className="ww-overline">{engagement.id} · {typeName(engagement.type)}</span><Pill tone={statusTone(engagement.status)}>{engagement.status}</Pill></div>
    <h3>{engagement.name}</h3><p>{engagement.target}</p>
    <div className="ww-card-row"><span>{engagement.mode.toUpperCase()}</span><span>{confirmed} verified · {engagement.findings.length-confirmed} candidate</span></div>
    <Progress value={engagement.usedCalls} max={engagement.budget.modelCalls}/>
    <div className="ww-card-row"><small>{engagement.usedCalls}/{engagement.budget.modelCalls} calls</small><span className="ww-enter">Open workspace <ArrowRight size={14}/></span></div>
  </button>;
}
export function MissionControl({library=false}:{library?:boolean}) {
  const engagements=useWorkspace(s=>s.engagements),setPage=useWorkspace(s=>s.setPage);
  const [query,setQuery]=useState('');
  const visible=engagements.filter(e=>(e.name+' '+e.id+' '+e.type+' '+e.target).toLowerCase().includes(query.toLowerCase()));
  const verified=engagements.flatMap(e=>e.findings).filter(f=>f.status==='verified').length;
  const calls=engagements.reduce((n,e)=>n+e.usedCalls,0);
  return <div className="ww-screen">
    <header className="ww-page-head"><div><span className="ww-overline">WARWAGON / OPERATIONS</span><h1>{library?'Engagements':'Mission Control'}</h1><p>{library?'Select a mission or filter the engagement library.':'Direct investigations, inspect intelligence and review engagement outcomes.'}</p></div>
      <button className="ww-button primary" onClick={()=>setPage('new')}><Plus size={16}/> New Engagement</button></header>
    {!library&&<>
      <div className="ww-metrics">
        <Metric label="Sample engagements" value={engagements.length} detail="Illustrative, not live"/>
        <Metric label="Conceptual active" value={engagements.filter(e=>e.status==='running').length} detail="Simulated states"/>
        <Metric label="Sample verified findings" value={verified} detail="Not real assessment results"/>
        <Metric label="Sample model calls" value={calls} detail="Illustrative budget usage"/>
      </div>
      <div className="ww-overview-grid">
        <Panel title="Mission Intelligence" detail="Current example situation report">
          <div className="ww-sitrep"><Radar size={22}/><div><strong>Investigation priority: evidence-backed discovery</strong><p>Our primary web assessment has a candidate HTML output-encoding observation. Independent verification remains pending. API analysis is paused at a supervised gate.</p></div></div>
          <div className="ww-mini-actions"><button onClick={()=>useWorkspace.getState().openEngagement('ENG-LAB-001','investigation')}><Globe2 size={16}/> Web investigation</button><button onClick={()=>useWorkspace.getState().openEngagement('ENG-API-002','plan')}><ShieldCheck size={16}/> API review gate</button></div>
        </Panel>
        <Panel title="Intelligence & Governance" detail="Supporting workspaces">
          <div className="ww-action-list">
            <button onClick={()=>setPage('research')}><Radar size={18}/> Research Laboratory <ArrowUpRight size={15}/></button>
            <button onClick={()=>setPage('arc')}><FileCheck2 size={18}/> Architecture Review Council <ArrowUpRight size={15}/></button>
            <button onClick={()=>setPage('system')}><Bot size={18}/> Models & tool adapters <ArrowUpRight size={15}/></button>
            <a href="./recorded-runs.html"><FileCheck2 size={18}/> Actual recorded run artifacts <ArrowUpRight size={15}/></a>
          </div>
        </Panel>
      </div>
    </>}
    <div className="ww-section-head"><div><h2>{library?'Engagement Library':'Engagement Portfolio'}</h2><p>Three differentiated engagement experiences, with connected example evidence.</p></div>
      {library&&<input aria-label="Search engagements" className="ww-input" placeholder="Search engagements…" value={query} onChange={e=>setQuery(e.target.value)}/>}
    </div>
    <div className="ww-card-grid">{visible.map(engagement=><EngagementCard key={engagement.id} engagement={engagement}/>)}</div>
    {!visible.length&&<Panel><p>No engagements match that search.</p></Panel>}
    {!library&&<Panel title="Recent investigation events" detail="Events from the example missions">
      <div className="ww-event-list">{engagements.flatMap(e=>e.events.slice(0,2).map(event=>({engagement:e,event}))).map(({engagement,event})=><button key={engagement.id+event.id} onClick={()=>useWorkspace.getState().openEngagement(engagement.id,'investigation')} className="ww-event-row"><StatusIcon status={event.kind==='Verification'?'completed':'running'}/><div><strong>{event.title}</strong><small>{engagement.name} · {event.timestamp}</small></div><ArrowRight size={16}/></button>)}</div>
    </Panel>}
  </div>;
}
