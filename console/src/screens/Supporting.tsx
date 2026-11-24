import { useState } from 'react';
import { Activity, ArrowRight, Bot, BrainCircuit, CheckCircle2, CircleAlert, Database, FileCheck, FlaskConical, KeyRound, Network, PlugZap, Server, ShieldCheck } from 'lucide-react';
import ReactECharts from 'echarts-for-react';
import { Panel, Pill } from '../components/ui';

export function ResearchLaboratory(){
  const [metric,setMetric]=useState('verification');
  const stats=[{name:'Single agent',verified:0,tokenCost:0},{name:'Hierarchical',verified:0,tokenCost:0},{name:'Fact-intent',verified:0,tokenCost:0},{name:'Hybrid',verified:0,tokenCost:0}];
  return <div className="ww-screen"><header className="ww-page-head"><div><span className="ww-overline">RESEARCH LABORATORY / EXPERIMENTS</span><h1>Measure intelligence, not scheduling</h1><p>Compare real model-driven planners against equivalent environments and budgets.</p></div><Pill tone="warn">Comparative dataset pending</Pill></header>
    <div className="ww-overview-grid">
      <Panel title="Strategy Comparison" detail="Only actual scored trials should appear on this chart.">
        <div className="ww-chart-controls"><label>Metric <select className="ww-input" value={metric} onChange={e=>setMetric(e.target.value)}><option value="verification">Verified discoveries</option><option value="tokens">Total model tokens</option></select></label></div>
        <ReactECharts style={{height:245}} option={{backgroundColor:'transparent',
          textStyle:{color:'#9fb0c5'},grid:{left:34,right:22,top:22,bottom:48},
          xAxis:{type:'category',data:stats.map(s=>s.name),axisLabel:{color:'#a4b6c9',rotate:0,fontSize:10},axisLine:{lineStyle:{color:'#2c4056'}}},
          yAxis:{type:'value',min:0,axisLabel:{color:'#a4b6c9',formatter:(v:number)=>v===0?'0':''},splitLine:{lineStyle:{color:'#1d2d3f'}}},
          series:[{type:'bar',data:stats.map(s=>metric==='tokens'?s.tokenCost:s.verified),itemStyle:{color:'#e7a84b',borderRadius:[5,5,0,0]}}],
          tooltip:{trigger:'axis'}}} notMerge/>
        <p className="ww-muted">All four strategies currently show zero **recorded comparable trials** in this UI. Zero is not a measured zero-vulnerability result.</p>
      </Panel>
      <Panel title="Experiment Design" detail="Versioned experimental controls">
        <div className="ww-data-rows"><div><span>Baseline</span><strong>Real tool-calling single agent</strong></div><div><span>Alternatives</span><strong>Hierarchy, fact-intent, hybrid</strong></div><div><span>Budget parity</span><strong>Required</strong></div><div><span>Held-out fixtures</span><strong>Required</strong></div><div><span>Scoring</span><strong>Independent evidence verification</strong></div><div><span>Current state</span><strong>Comparable runs not loaded</strong></div></div>
        <div className="ww-callout"><FlaskConical size={17}/> Source artifact reviews and CLI results remain accessible through the recorded-run inspector.</div>
        <a className="ww-button outline" href="./recorded-runs.html">Open real artifact viewer <ArrowRight size={15}/></a>
      </Panel>
    </div>
  </div>;
}
const arcRoles=['Agent Intelligence','Distributed Systems','Knowledge & Data','Offensive Security Research','Evaluation Science','Model & Inference','Developer Experience','Adversarial Reviewer','Research Skeptic'];
export function ArchitectureCouncil(){
  const [selected,setSelected]=useState(0);
  return <div className="ww-screen"><header className="ww-page-head"><div><span className="ww-overline">ARCHITECTURE REVIEW COUNCIL</span><h1>Challenge every assumption</h1><p>Independent model-review artifacts, recorded dissent and evidence-backed architecture decisions.</p></div><Pill tone="warn">Approval pending</Pill></header>
    <div className="ww-overview-grid">
      <Panel title="Council Seats" detail="Nine specialist review roles; role prompts alone are not independent consensus.">
        <div className="ww-role-grid">{arcRoles.map((name,i)=><button key={name} className={'ww-role-button '+(selected===i?'selected':'')} onClick={()=>setSelected(i)}><BrainCircuit size={16}/><span>{name}</span></button>)}</div>
      </Panel>
      <Panel title="Reviewer Inspector" detail="Scope and review evidence">
        <span className="ww-overline">ROLE / {String(selected+1).padStart(2,'0')}</span><h2>{arcRoles[selected]}</h2>
        <p>Reviewer output should include source proposal revision, model/provider identity, prompt hash, verdict, objections and proposed falsification experiments.</p>
        <div className="ww-callout"><CircleAlert size={17}/> This visual council roster is illustrative. Inspect original recorded reviews rather than assuming these roles have produced independent conclusions.</div>
        <a className="ww-button outline" href="./recorded-runs.html#arc">Open recorded ARC review <ArrowRight size={15}/></a>
      </Panel>
    </div>
    <Panel title="Decision Workflow" detail="Maintainer approval is separate from model commentary.">
      <div className="ww-review-gates">{['Frozen proposal','Isolated first passes','Adversarial challenge','Empirical experiment','Dissent synthesis','Maintainer decision'].map((item,i)=><div key={item}><span>{String(i+1).padStart(2,'0')}</span>{item}</div>)}</div>
    </Panel>
  </div>;
}
export function SystemIntegrations(){
  const rows=[{icon:Server,name:'Local Ollama',detail:'OpenAI-compatible inference endpoint',status:'Not connected to this UX'},
    {icon:Database,name:'Run artifact repository',detail:'Recorded JSON + provenance-checking inspector',status:'Available separately'},
    {icon:PlugZap,name:'Security tool adapters',detail:'Typed lab tool and future MCP plugins',status:'Backend integration pending'},
    {icon:KeyRound,name:'Access profiles',detail:'Guest/test-account configuration per engagement',status:'UI draft only'},
    {icon:Activity,name:'Engagement event stream',detail:'SSE or websocket live telemetry',status:'Not connected'},
    {icon:Network,name:'Shared knowledge graph',detail:'Observations, hypotheses, findings and provenance',status:'UI projection only'}];
  return <div className="ww-screen"><header className="ww-page-head"><div><span className="ww-overline">SYSTEM / PLATFORM INTEGRATIONS</span><h1>Models & Tools</h1><p>Component configuration and honest integration readiness.</p></div><Pill tone="warn">No live backend connection</Pill></header>
    <div className="ww-system-grid">{rows.map(row=><Panel key={row.name}><div className="ww-system-row"><row.icon size={24}/><div><h3>{row.name}</h3><p>{row.detail}</p><Pill tone={row.status==='Available separately'?'good':'muted'}>{row.status}</Pill></div></div></Panel>)}</div>
    <Panel title="Architecture contracts" detail="The frontend should use generated OpenAPI types rather than reading unverified model outputs as entities.">
      <div className="ww-action-list"><div><Bot size={17}/> Engagement → Objective → PlanRevision → Task → EventRecord</div><div><FileCheck size={17}/> Observation → EvidenceArtifact → FindingVerification</div><div><ShieldCheck size={17}/> Verifier-signed status separate from investigator hypothesis</div><div><CheckCircle2 size={17}/> Real data adapters replace fixtures without changing the screen components</div></div>
    </Panel>
  </div>;
}
