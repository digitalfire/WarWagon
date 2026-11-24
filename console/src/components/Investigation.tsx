import { ArrowRight, Braces, Eye, FileSearch, Search, Terminal } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { Engagement } from '../domain/types';
import { useWorkspace } from '../state/workspace';
import { Empty, Panel, Pill, StatusIcon } from './ui';
export function Investigation({engagement}:{engagement:Engagement}) {
  const [query,setQuery]=useState('');
  const selectedId=useWorkspace(s=>s.taskId),selectTask=useWorkspace(s=>s.selectTask),selectEvidence=useWorkspace(s=>s.selectEvidence),selectHypothesis=useWorkspace(s=>s.selectHypothesis);
  const tasks=useMemo(()=>engagement.tasks.filter(t=>(t.title+' '+t.id+' '+t.owner).toLowerCase().includes(query.toLowerCase())),[engagement.tasks,query]);
  const task=engagement.tasks.find(t=>t.id===selectedId)||engagement.tasks[0];
  const evidence=task?.evidenceIds.map(id=>engagement.observations.find(e=>e.id===id)).filter(e=>e!==undefined)??[];
  if(!engagement.tasks.length)return <Empty title="No execution tasks" detail="This conceptual engagement is a draft. It has no real or simulated task history."/>;
  return <div className="ww-investigator">
    <Panel title="Investigation Task Tree" detail={engagement.tasks.length+' linked task records'}>
      <label className="ww-search"><Search size={15}/><input placeholder="Search tasks…" value={query} onChange={e=>setQuery(e.target.value)}/></label>
      <div className="ww-task-list">{tasks.map(t=><button key={t.id} className={'ww-task '+(task?.id===t.id?'selected':'')} onClick={()=>selectTask(t.id)}>
        <StatusIcon status={t.status}/><div><strong>{t.title}</strong><small>{t.id} · {t.owner}</small></div><span className="ww-small-tone">{t.status}</span></button>)}</div>
    </Panel>
    <Panel title="Agent Execution Inspector" detail={task?.owner||'No task selected'} action={task&&<Pill tone={task.status==='completed'?'good':task.status==='blocked'?'warn':'blue'}>{task.status}</Pill>}>
      {task?<div className="ww-inspector-content">
        <span className="ww-overline">{task.id} / {task.phase}</span><h3>{task.title}</h3><p>{task.detail}</p>
        <div className="ww-technical-block"><div><Terminal size={16}/> TOOL INVOCATION</div><code>{task.tool||'No invocation recorded'}</code><pre>{task.invocation||'Task is awaiting execution.'}</pre></div>
        <div className="ww-technical-block"><div><Braces size={16}/> OBSERVED RESULT</div><pre>{task.result||'No tool observation recorded.'}</pre></div>
        <div className="ww-inspector-actions">{task.hypothesisIds.map(id=><button key={id} className="ww-button ghost" onClick={()=>selectHypothesis(id)}>Hypothesis {id} <ArrowRight size={14}/></button>)}</div>
      </div>:<Empty title="Select a task" detail="Choose a task to see its tool invocation and evidence."/>}
    </Panel>
    <Panel title="Evidence Inspector" detail="Observations directly linked to the selected task">
      {evidence.length?evidence.map(ev=><article key={ev.id} className="ww-evidence-preview"><div className="ww-card-row"><span className="ww-overline">{ev.id} · {ev.timestamp}</span><Pill tone="blue">Observation</Pill></div><strong>{ev.title}</strong><code>{ev.source}</code><p>{ev.content}</p><button className="ww-inline-link" onClick={()=>selectEvidence(ev.id)}><Eye size={15}/> Open evidence <ArrowRight size={14}/></button></article>):<Empty title="No evidence yet" detail="This task has no stored observations. A hypothesis alone is not a verified result."/>}
      {task&&<div className="ww-technical-note"><FileSearch size={15}/> Tool output is illustrative. View real provenance-checked artifacts in the recorded inspector.</div>}
    </Panel>
  </div>;
}
