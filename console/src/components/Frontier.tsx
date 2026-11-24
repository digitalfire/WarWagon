import { ArrowRight, BrainCircuit, GitCompareArrows, Lightbulb, SlidersHorizontal } from 'lucide-react';
import { useState } from 'react';
import type { Engagement } from '../domain/types';
import { useWorkspace } from '../state/workspace';
import { Empty, Panel, Pill, Progress } from './ui';
export function Frontier({engagement}:{engagement:Engagement}) {
  const selectedId=useWorkspace(s=>s.hypothesisId),selectHypothesis=useWorkspace(s=>s.selectHypothesis),selectEvidence=useWorkspace(s=>s.selectEvidence);
  const [preview,setPreview]=useState(false);
  const hypotheses=[...engagement.hypotheses].sort((a,b)=>b.priority-a.priority);
  const hypothesis=hypotheses.find(h=>h.id===selectedId)||hypotheses[0];
  return <div className="ww-two-columns">
    <Panel title="Opportunity Frontier" detail="Ranked questions, not automatically verified facts." action={<SlidersHorizontal size={17}/>}>
      {hypotheses.length?<div className="ww-frontier-list">{hypotheses.map(h=><button key={h.id} className={'ww-frontier-item '+(hypothesis.id===h.id?'selected':'')} onClick={()=>selectHypothesis(h.id)}><div className="ww-card-row"><span className="ww-overline">{h.id}</span><Pill tone={h.status==='resolved'?'good':h.status==='testing'?'warn':'muted'}>{h.status}</Pill></div><strong>{h.title}</strong><div className="ww-card-row"><small>Priority {h.priority}/100</small><small>Confidence: {h.confidence}</small></div><Progress value={h.priority}/></button>)}</div>:<Empty title="No hypotheses" detail="Reasoning frontier is empty until agent proposals are generated."/>}
    </Panel>
    <div className="ww-column-stack">
      <Panel title="Hypothesis Inspector" detail={hypothesis?'Current evidence and proposed next test':'No selected hypothesis'} action={<BrainCircuit size={18}/>}>
        {hypothesis?<div className="ww-inspector-content"><span className="ww-overline">{hypothesis.id} / {hypothesis.status}</span><h3>{hypothesis.title}</h3><p>{hypothesis.detail}</p><div className="ww-data-rows"><div><span>Priority</span><strong>{hypothesis.priority}/100</strong></div><div><span>Confidence</span><strong>{hypothesis.confidence}</strong></div><div><span>Next investigation</span><strong>{hypothesis.nextAction}</strong></div></div>
          <div className="ww-subheading">Supporting observations</div>{hypothesis.evidenceIds.map(id=><button className="ww-event-row" key={id} onClick={()=>selectEvidence(id)}><Lightbulb size={15}/><span>{engagement.observations.find(e=>e.id===id)?.title||id}</span><ArrowRight size={14}/></button>)}
        </div>:<Empty title="Nothing to inspect" detail="Agent hypotheses will appear here once recorded."/>}
      </Panel>
      <Panel title="Plan Diff Preview" detail="See tasking consequences before any operator-directed replan." action={<GitCompareArrows size={18}/>}>
        <button className="ww-button outline" onClick={()=>setPreview(v=>!v)}>{preview?'Hide proposed revision':'Preview a priority change'} <ArrowRight size={14}/></button>
        {preview&&<div className="ww-diff"><div className="ww-diff-old">− Continue broader route discovery without reprioritization</div><div className="ww-diff-new">+ Prioritize {hypothesis?.id||'current hypothesis'} independent verification</div><div className="ww-diff-new">+ Preserve previously collected observations and task history</div><p>This is a UI-only proposal. It does not replan or dispatch real agents.</p></div>}
      </Panel>
    </div>
  </div>;
}
