import { useState } from 'react';
import { ArrowLeft, ArrowRight, CheckCircle2, FileText, FlaskConical, Globe, KeyRound, Shield, ShieldCheck } from 'lucide-react';
import type { Engagement, EngagementType, OperatingMode, AccessType, EngagementBudget } from '../domain/types';
import { useWorkspace } from '../state/workspace';
import { Panel, Pill } from '../components/ui';

const types:{id:EngagementType;name:string;detail:string;icon:typeof Globe}[]=[
 {id:'web',name:'Web Application',detail:'Browser surfaces, HTTP behavior, forms and API endpoints',icon:Globe},
 {id:'api',name:'API & Identity',detail:'Endpoint coverage, authorization policies and access comparison',icon:KeyRound},
 {id:'cloud',name:'Cloud Configuration',detail:'Sandbox resource inventory, IAM policy and effective access',icon:ShieldCheck},
];
const steps=['Engagement Type','Objective & Scope','Operating Limits','Mission Briefing'];
const defaultBudget:EngagementBudget={minutes:60,modelCalls:60,tokens:120000,workers:2,httpRps:30};
export function NewEngagement(){
  const create=useWorkspace(s=>s.createDraft);
  const [step,setStep]=useState(0);
  const [type,setType]=useState<EngagementType>('web');
  const [title,setTitle]=useState('New local application review');
  const [target,setTarget]=useState('http://127.0.0.1:3000');
  const [objective,setObjective]=useState('Assess my local web application for security weaknesses; independently verify findings and prioritize next investigations.');
  const [access,setAccess]=useState<AccessType>('both');
  const [mode,setMode]=useState<OperatingMode>('autonomous');
  const [budget,setBudget]=useState(defaultBudget);
  const [confirmed,setConfirmed]=useState(false);
  const valid=!!title.trim()&&!!target.trim()&&!!objective.trim();
  const changeBudget=(field:keyof EngagementBudget,value:number)=>setBudget(v=>({...v,[field]:Math.max(1,value||1)}));
  const createDraft=()=>{
    if(!confirmed||!valid)return;
    const id='DRAFT-'+crypto.randomUUID().slice(0,8).toUpperCase();
    const engagement:Engagement={id,name:title.trim(),type,target:target.trim(),objective:objective.trim(),access,mode,
      status:'draft',perspective:'blackbox',priority:'balanced',budget,elapsedMinutes:0,usedCalls:0,usedTokens:0,
      tasks:[],observations:[],hypotheses:[],findings:[],agents:[],events:[],lastUpdated:new Date().toISOString().slice(0,10),source:'illustrative'};
    create(engagement);
  };
  return <div className="ww-screen">
    <header className="ww-page-head"><div><span className="ww-overline">ENGAGEMENT BUILDER</span><h1>Develop a mission</h1><p>Describe the outcome. WarWagon will eventually compile goals into versioned plans and agent tasking.</p></div><Pill tone="warn">Conceptual draft only</Pill></header>
    <div className="ww-steps">{steps.map((name,i)=><div key={name} className={i===step?'selected':i<step?'done':''}><span>{i<step?<CheckCircle2 size={16}/>:String(i+1).padStart(2,'0')}</span>{name}</div>)}</div>
    {step===0&&<Panel title="Choose engagement type" detail="One common command experience with specialized investigator tools.">
      <div className="ww-type-grid">{types.map(x=><button key={x.id} onClick={()=>{setType(x.id);if(x.id==='cloud')setTarget('sandbox-policy-export.json');else if(x.id==='api')setTarget('http://127.0.0.1:8080/api');else setTarget('http://127.0.0.1:3000');}} className={'ww-type-card '+(type===x.id?'selected':'')}><x.icon size={25}/><strong>{x.name}</strong><span>{x.detail}</span></button>)}</div>
    </Panel>}
    {step===1&&<div className="ww-overview-grid">
      <Panel title="Operator's intent" detail="State the desired outcome, not individual tool commands.">
        <label className="ww-field">Mission name<input className="ww-input" value={title} onChange={e=>setTitle(e.target.value)} maxLength={100}/></label>
        <label className="ww-field">Primary target or dataset<input className="ww-input" value={target} onChange={e=>setTarget(e.target.value)} maxLength={300}/></label>
        <label className="ww-field">Objective<textarea className="ww-input" value={objective} onChange={e=>setObjective(e.target.value)} rows={5}/></label>
      </Panel>
      <Panel title="Assessment context" detail="Access and operating mode affect the proposed work plan.">
        <label className="ww-field">Access profile<select className="ww-input" value={access} onChange={e=>setAccess(e.target.value as AccessType)}><option value="guest">Unauthenticated</option><option value="authenticated">Test account</option><option value="both">Both guest and authenticated</option></select></label>
        <label className="ww-field">Autonomy<select className="ww-input" value={mode} onChange={e=>setMode(e.target.value as OperatingMode)}><option value="autonomous">Autonomous</option><option value="supervised">Supervised</option><option value="guided">Guided</option></select></label>
        <div className="ww-callout"><Shield size={18}/> This creates a local UX draft only. It does not test target connectivity or execute assessment tasks.</div>
      </Panel>
    </div>}
    {step===2&&<Panel title="Resource ceilings" detail="Maximum allowed engagement resources in the proposed briefing.">
      <div className="ww-form-grid">{([
        ['minutes','Maximum minutes'],['modelCalls','Model invocations'],['tokens','Aggregate tokens'],['workers','Concurrent workers'],['httpRps','HTTP requests / second'],
      ] as [keyof EngagementBudget,string][]).map(([key,label])=><label className="ww-field" key={key}>{label}<input type="number" min={1} className="ww-input" value={budget[key]} onChange={e=>changeBudget(key,Number(e.target.value))}/></label>)}</div>
      <div className="ww-callout"><FlaskConical size={18}/> Runtime budget enforcement requires the engagement API. This preview only stores the proposed limits.</div>
    </Panel>}
    {step===3&&<div className="ww-overview-grid">
      <Panel title="Mission briefing" detail="A proposed operating plan, not an executed assessment.">
        <div className="ww-brief"><span className="ww-overline">ENGAGEMENT OBJECTIVE</span><h2>{title}</h2><p>{objective}</p>
          <dl><dt>Type</dt><dd>{types.find(x=>x.id===type)?.name}</dd><dt>Target</dt><dd>{target}</dd><dt>Access</dt><dd>{access}</dd><dt>Operating mode</dt><dd>{mode}</dd><dt>Resource ceiling</dt><dd>{budget.minutes} minutes · {budget.modelCalls} calls · {budget.tokens.toLocaleString()} tokens</dd></dl></div>
        <label className="ww-confirm"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/> I confirm this conceptual scope and understand that this saves a draft, not a live engagement.</label>
      </Panel>
      <Panel title="Proposed investigation phases" detail="The coordinator will later generate task-level plans from real observations.">
        <ol className="ww-phase-list"><li>Establish target baseline and available access.</li><li>Map observable routes, services or resources.</li><li>Develop ranked, falsifiable hypotheses.</li><li>Collect controlled investigation evidence.</li><li>Independently verify candidate findings.</li><li>Assess impact, replan and report.</li></ol>
        <div className="ww-callout"><FileText size={18}/> Drafts contain no verified observations, findings or actual agent telemetry.</div>
      </Panel>
    </div>}
    <footer className="ww-wizard-actions"><button className="ww-button ghost" disabled={step===0} onClick={()=>setStep(v=>Math.max(0,v-1))}><ArrowLeft size={16}/> Back</button>
      {step<3?<button className="ww-button primary" onClick={()=>setStep(v=>Math.min(3,v+1))} disabled={step===1&&!valid}>Continue <ArrowRight size={16}/></button>:<button className="ww-button primary" onClick={createDraft} disabled={!confirmed||!valid}>Save concept briefing <ArrowRight size={16}/></button>}
    </footer>
  </div>;
}
