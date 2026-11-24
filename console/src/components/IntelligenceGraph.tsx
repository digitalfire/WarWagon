import { Background, Controls, ReactFlow, type Edge, type Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useMemo } from 'react';
import type { Engagement } from '../domain/types';
import { useWorkspace } from '../state/workspace';
import { Panel } from './ui';
export function IntelligenceGraph({engagement}:{engagement:Engagement}) {
  const selectHypothesis=useWorkspace(s=>s.selectHypothesis),selectFinding=useWorkspace(s=>s.selectFinding),selectEvidence=useWorkspace(s=>s.selectEvidence);
  const graph=useMemo(()=>{
    const nodes:Node[]=[{id:'asset',position:{x:300,y:0},data:{label:engagement.target},style:{background:'#223a51',color:'#e8f1fa',border:'1px solid #5ebcdd',borderRadius:10,width:225}}];
    const edges:Edge[]=[];
    engagement.tasks.slice(0,5).forEach((task,i)=>{
      nodes.push({id:'task:'+task.id,position:{x:i*228,y:115},data:{label:task.title},style:{background:'#19283a',color:'#d9e5f0',border:'1px solid #405c75',borderRadius:9,width:200}});
      edges.push({id:'asset-'+task.id,source:'asset',target:'task:'+task.id,animated:task.status==='running'});
    });
    engagement.hypotheses.forEach((hypothesis,i)=>{
      nodes.push({id:'hypothesis:'+hypothesis.id,position:{x:i*250+100,y:255},data:{label:hypothesis.title},style:{background:'#352c23',color:'#f5ddb8',border:'1px solid #c38d4a',borderRadius:9,width:220}});
      const task=engagement.tasks.find(t=>t.hypothesisIds.includes(hypothesis.id));
      if(task)edges.push({id:'h-'+hypothesis.id,source:'task:'+task.id,target:'hypothesis:'+hypothesis.id});
    });
    engagement.findings.forEach((finding,i)=>{
      nodes.push({id:'finding:'+finding.id,position:{x:i*270+185,y:390},data:{label:finding.title},style:{background:'#25392f',color:'#d9f2e4',border:'1px solid #59b88e',borderRadius:9,width:230}});
      const hypothesis=engagement.hypotheses.find(h=>h.evidenceIds.includes(finding.originalEvidenceId));
      if(hypothesis)edges.push({id:'f-'+finding.id,source:'hypothesis:'+hypothesis.id,target:'finding:'+finding.id});
    });
    return {nodes,edges};
  },[engagement]);
  return <Panel title="Investigation Knowledge Graph" detail="Click a hypothesis or finding to inspect its evidence. This graph is a projection of the illustrative engagement data." className="ww-graph-panel">
    <div className="ww-flow"><ReactFlow nodes={graph.nodes} edges={graph.edges} fitView minZoom={0.25} maxZoom={1.8} nodesDraggable={false} nodesConnectable={false}
      onNodeClick={(_,node)=>{if(node.id.startsWith('hypothesis:'))selectHypothesis(node.id.slice(11));else if(node.id.startsWith('finding:'))selectFinding(node.id.slice(8));else if(node.id.startsWith('evidence:'))selectEvidence(node.id.slice(9));}}
      proOptions={{hideAttribution:true}}><Background color="#29384a" gap={22}/><Controls/></ReactFlow></div>
    <div className="ww-legend"><span>● Asset / tasks</span><span className="warn-text">● Hypotheses</span><span className="good-text">● Findings</span></div>
  </Panel>;
}
