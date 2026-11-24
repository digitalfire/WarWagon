import { ArrowRight, GitCompare, ShieldCheck, ShieldQuestion } from 'lucide-react';
import type { Engagement, Finding } from '../domain/types';
import { useWorkspace } from '../state/workspace';
import { Empty, Panel, Pill } from './ui';
const tone=(s:Finding['status'])=>s==='verified'?'good':s==='rejected'?'bad':s==='candidate'?'warn':'muted';
export function Verification({engagement}:{engagement:Engagement}) {
  const selectedId=useWorkspace(s=>s.findingId),selectFinding=useWorkspace(s=>s.selectFinding),selectEvidence=useWorkspace(s=>s.selectEvidence);
  const finding=engagement.findings.find(f=>f.id===selectedId)||engagement.findings[0];
  const original=engagement.observations.find(e=>e.id===finding?.originalEvidenceId);
  const independently=engagement.observations.find(e=>e.id===finding?.verificationEvidenceId);
  const counter=engagement.observations.find(e=>e.id===finding?.counterEvidenceId);
  if(!finding)return <Empty title="No findings" detail="This draft has no candidate or verified findings. No model confidence is presented as evidence."/>;
  return <div className="ww-screen">
    <div className="ww-finding-selector">{engagement.findings.map(f=><button key={f.id} className={'ww-finding-option '+(f.id===finding.id?'selected':'')} onClick={()=>selectFinding(f.id)}><div><span className="ww-overline">{f.id} · {f.severity}</span><strong>{f.title}</strong></div><Pill tone={tone(f.status)}>{f.status}</Pill></button>)}</div>
    <Panel title="Finding Verification Studio" detail="Recorded claim, supporting observation and independent check must remain distinct." action={<Pill tone={tone(finding.status)}>{finding.status}</Pill>}>
      <div className="ww-claim"><span className="ww-overline">{finding.id} · INVESTIGATION CLAIM</span><h3>{finding.title}</h3><p>{finding.summary}</p></div>
      <div className="ww-evidence-compare">
        <div className="ww-comparison-card"><div className="ww-card-row"><span className="ww-overline">ORIGINAL OBSERVATION</span><ShieldQuestion size={16}/></div>{original?<><strong>{original.title}</strong><code>{original.source}</code><p>{original.content}</p><button className="ww-inline-link" onClick={()=>selectEvidence(original.id)}>Open {original.id} <ArrowRight size={14}/></button></>:<p>No original evidence recorded.</p>}</div>
        <div className="ww-comparison-card"><div className="ww-card-row"><span className="ww-overline">INDEPENDENT VERIFICATION</span><ShieldCheck size={16}/></div>{independently?<><strong>{independently.title}</strong><code>{independently.source}</code><p>{independently.content}</p><button className="ww-inline-link" onClick={()=>selectEvidence(independently.id)}>Open {independently.id} <ArrowRight size={14}/></button></>:<><strong>Verification pending</strong><p>No independent reproduction artifact is attached. This must remain a candidate, regardless of the agent's confidence.</p></>}</div>
      </div>
      {counter&&<div className="ww-callout"><GitCompare size={17}/> Counter-evidence: {counter.content}</div>}
      <div className="ww-impact"><strong>Impact rationale</strong><p>{finding.impact}</p><small>All items shown here are illustrative demo records, not actual assessment findings.</small></div>
    </Panel>
  </div>;
}
