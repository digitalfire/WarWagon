import type { Engagement, EngagementType, Agent, Task, Observation, Hypothesis, Finding, EventRecord } from '../domain/types';
const budget = { minutes: 60, modelCalls: 60, tokens: 120000, workers: 2, httpRps: 30 };

const webTasks: Task[] = [
  {id:'T-001',title:'Application baseline',phase:'Discovery',status:'completed',owner:'Application Mapper',
    detail:'Record the entry page, HTTP response headers and visible navigation.',tool:'lab_http_get',
    invocation:'GET /',result:'HTTP/1.1 200 OK · text/html',evidenceIds:['EV-001'],hypothesisIds:[]},
  {id:'T-002',title:'Map /search behavior',phase:'Discovery',status:'completed',owner:'Application Mapper',
    detail:'Inspect user-controllable query parameters and response contexts.',tool:'lab_http_get',
    invocation:'GET /search?q=sample',result:'HTTP/1.1 200 OK · echoed query parameter',evidenceIds:['EV-002'],hypothesisIds:['H-001']},
  {id:'T-003',title:'Evaluate reflected markup',phase:'Investigation',status:'running',owner:'Security Investigator',
    detail:'Determine whether supplied text is encoded in the HTML response context.',tool:'lab_http_get',
    invocation:'GET /search?q=%3Cb%3EWW_MARKER%3C%2Fb%3E',result:'HTTP 200 · marker reflected into HTML',
    evidenceIds:['EV-003'],hypothesisIds:['H-001']},
  {id:'T-004',title:'Independent reproduction',phase:'Verification',status:'queued',owner:'Evidence Verifier',
    detail:'Check the candidate using a separate safe-control comparison.',evidenceIds:[],hypothesisIds:['H-001']},
  {id:'T-005',title:'Guest versus test-user access',phase:'Access',status:'running',owner:'Access Specialist',
    detail:'Compare permitted views and session behavior under both access contexts.',tool:'session_compare',
    invocation:'Compare documented session contexts',result:'Comparison pending',evidenceIds:['EV-004'],hypothesisIds:['H-002']},
];
const webEvidence: Observation[] = [
  {id:'EV-001',title:'Application baseline',source:'GET / · HTTP 200',content:'Content-Type: text/html; discovered navigation to /search and /profile',taskId:'T-001',timestamp:'14:17:05'},
  {id:'EV-002',title:'Search parameter observed',source:'GET /search?q=sample',content:'HTTP 200 · Search results include user-provided query text',taskId:'T-002',timestamp:'14:21:09'},
  {id:'EV-003',title:'Markup reflection observation',source:'GET /search?q=%3Cb%3EWW_MARKER%3C%2Fb%3E',content:'HTTP 200 · HTML source includes <b>WW_MARKER</b> in a reflected query result',taskId:'T-003',timestamp:'14:22:41'},
  {id:'EV-004',title:'Access context comparison started',source:'session_compare',content:'Two access contexts identified; results not yet verified',taskId:'T-005',timestamp:'14:23:10'},
];
const webHypotheses: Hypothesis[] = [
 {id:'H-001',title:'Unencoded reflected HTML in /search',detail:'Observed reflection may permit unintended markup interpretation.',priority:92,confidence:'Medium',status:'testing',evidenceIds:['EV-002','EV-003'],nextAction:'Run independent reproduction with an encoded control.'},
 {id:'H-002',title:'Guest/test-user access discrepancy',detail:'Permission differences may expose protected routes.',priority:76,confidence:'Low',status:'open',evidenceIds:['EV-004'],nextAction:'Compare corresponding resources with each session.'},
 {id:'H-003',title:'HTTP response-header hardening',detail:'Review baseline security headers and distinguish exposure from impact.',priority:44,confidence:'Low',status:'open',evidenceIds:['EV-001'],nextAction:'Inspect baseline headers before filing a finding.'},
];
const webFindings: Finding[] = [
 {id:'F-001',title:'Potential reflected HTML output encoding weakness',severity:'medium',status:'candidate',
 summary:'Search parameter content was observed in an HTML response; independent reproduction is pending.',
 impact:'If confirmed, markup injection could affect page presentation or script execution depending on the context and browser defenses.',
 originalEvidenceId:'EV-003'},
];
const webAgents: Agent[] = [
 {id:'A-001',name:'Mission Coordinator',specialty:'Planning and prioritization',state:'Coordinating',model:'Reasoning model · illustrative',calls:9},
 {id:'A-002',name:'Application Mapper',specialty:'Route and surface discovery',state:'Working',model:'Tool model · illustrative',taskId:'T-002',calls:11},
 {id:'A-003',name:'Security Investigator',specialty:'Hypothesis testing',state:'Working',model:'Tool model · illustrative',taskId:'T-003',calls:7},
 {id:'A-004',name:'Evidence Verifier',specialty:'Independent reproduction',state:'Queued',model:'Verifier model · illustrative',taskId:'T-004',calls:0},
];
const webEvents: EventRecord[] = [
 {id:'E-005',timestamp:'14:23:18',kind:'Verification',title:'Independent verification requested',detail:'Candidate F-001 queued for separate evidence assessment.',taskId:'T-004'},
 {id:'E-004',timestamp:'14:22:41',kind:'Hypothesis',title:'Reflected HTML investigated',detail:'A safe markup marker appeared in the response; confirmation pending.',taskId:'T-003',evidenceId:'EV-003'},
 {id:'E-003',timestamp:'14:21:09',kind:'Observation',title:'Search response captured',detail:'Baseline search parameter behavior recorded.',taskId:'T-002',evidenceId:'EV-002'},
 {id:'E-002',timestamp:'14:19:32',kind:'Task',title:'Access comparison scheduled',detail:'Guest versus authenticated visibility selected for review.',taskId:'T-005'},
 {id:'E-001',timestamp:'14:17:05',kind:'Plan',title:'Initial engagement plan created',detail:'Discovery, access comparison and evidence verification identified.'},
];

const apiTasks: Task[] = [
 {id:'T-A1',title:'Inventory documented API endpoints',phase:'Discovery',status:'completed',owner:'API Mapper',detail:'Review sample OpenAPI description and request collection.',tool:'openapi_read',invocation:'GET /openapi.json',result:'12 example endpoints listed',evidenceIds:['EV-A1'],hypothesisIds:[]},
 {id:'T-A2',title:'Role-access comparison',phase:'Access',status:'completed',owner:'Authorization Analyst',detail:'Compare normal and privileged test-account access.',tool:'role_matrix',invocation:'GET /api/projects/42 as two test roles',result:'Role mismatch in illustrative response',evidenceIds:['EV-A2'],hypothesisIds:['H-A1']},
 {id:'T-A3',title:'Independent permission check',phase:'Verification',status:'blocked',owner:'Verifier',detail:'Await supervised authorization for next test action.',evidenceIds:[],hypothesisIds:['H-A1']},
];
const apiEvidence: Observation[] = [
 {id:'EV-A1',title:'API collection',source:'GET /openapi.json',content:'Twelve API routes in example collection; 3 require privileged roles',taskId:'T-A1',timestamp:'10:12:02'},
 {id:'EV-A2',title:'Role matrix discrepancy',source:'GET /api/projects/42',content:'A lower-privilege role received a response inconsistent with the example role policy',taskId:'T-A2',timestamp:'10:24:45'},
];
const apiHypotheses: Hypothesis[]=[
 {id:'H-A1',title:'Project resource authorization gap',detail:'Illustrative lower-privilege response differs from expected role policy.',priority:94,confidence:'Medium',status:'testing',evidenceIds:['EV-A2'],nextAction:'Request supervised verification using the prepared test identities.'},
 {id:'H-A2',title:'Token audience validation',detail:'Check token scope and audience enforcement in the sample API.',priority:63,confidence:'Low',status:'open',evidenceIds:['EV-A1'],nextAction:'Review documented token flows.'},
];
const apiFindings: Finding[]=[
 {id:'F-A1',title:'Possible project-level authorization mismatch',severity:'high',status:'candidate',
 summary:'A sample API response may violate the configured test-role policy; verification is blocked.',
 impact:'If confirmed, access to another project could expose protected information.',
 originalEvidenceId:'EV-A2'},
];
const apiEvents:EventRecord[]=[
 {id:'E-A3',timestamp:'10:27:50',kind:'Review gate',title:'Supervised checkpoint required',detail:'Permission verification paused for operator review.',taskId:'T-A3'},
 {id:'E-A2',timestamp:'10:24:45',kind:'Hypothesis',title:'Role mismatch proposed',detail:'Compare policy with observed access behavior.',taskId:'T-A2',evidenceId:'EV-A2'},
 {id:'E-A1',timestamp:'10:12:02',kind:'Observation',title:'API inventory generated',detail:'Sample OpenAPI collection mapped.',taskId:'T-A1',evidenceId:'EV-A1'},
];
const cloudTasks:Task[]=[
 {id:'T-C1',title:'Inventory identity principals',phase:'Discovery',status:'completed',owner:'Cloud Analyst',detail:'Inspect supplied sandbox IAM inventory.',tool:'policy_inventory',invocation:'Read sandbox policy export',result:'Example principals and resources indexed',evidenceIds:['EV-C1'],hypothesisIds:[]},
 {id:'T-C2',title:'Evaluate effective access',phase:'Analysis',status:'completed',owner:'IAM Specialist',detail:'Analyze policy allow/deny semantics on controlled configuration.',tool:'policy_evaluator',invocation:'Evaluate example role permissions',result:'Broad resource access detected',evidenceIds:['EV-C2'],hypothesisIds:['H-C1']},
 {id:'T-C3',title:'Validate excess permission',phase:'Verification',status:'completed',owner:'Verifier',detail:'Recheck effective permissions against controlled policy data.',tool:'policy_evaluator',invocation:'Independent policy evaluation',result:'Illustrative broad scope confirmed',evidenceIds:['EV-C3'],hypothesisIds:['H-C1']},
];
const cloudEvidence:Observation[]=[
 {id:'EV-C1',title:'Sandbox role inventory',source:'IAM export',content:'Sample roles, bindings and scoped resources indexed',taskId:'T-C1',timestamp:'09:13:00'},
 {id:'EV-C2',title:'Broad policy action scope',source:'policy_evaluator',content:'Example role allows access to resources beyond the intended sandbox service',taskId:'T-C2',timestamp:'09:40:00'},
 {id:'EV-C3',title:'Independent policy evaluation',source:'policy_evaluator',content:'Separate sample policy evaluation reproduces the broad resource scope',taskId:'T-C3',timestamp:'10:04:00'},
];
const cloudHypotheses:Hypothesis[]=[
 {id:'H-C1',title:'Overly broad resource access',detail:'Example principal policy includes resources beyond its intended function.',priority:88,confidence:'High',status:'resolved',evidenceIds:['EV-C2','EV-C3'],nextAction:'Recommend least-privilege adjustments in report.'},
];
const cloudFindings:Finding[]=[
 {id:'F-C1',title:'Excessive sandbox principal permissions',severity:'medium',status:'verified',
 summary:'Illustrative policy analysis and a separate sample verification produced matching access conclusions.',
 impact:'A compromised principal could access resources outside the intended sample service.',
 originalEvidenceId:'EV-C2',verificationEvidenceId:'EV-C3'},
];
const cloudEvents:EventRecord[]=[
 {id:'E-C3',timestamp:'10:04:00',kind:'Verification',title:'Sample policy finding verified',detail:'Example verifier result linked to original observation.',taskId:'T-C3',evidenceId:'EV-C3'},
 {id:'E-C2',timestamp:'09:40:00',kind:'Analysis',title:'Broad resource scope identified',detail:'Policy analysis yielded candidate.',taskId:'T-C2',evidenceId:'EV-C2'},
 {id:'E-C1',timestamp:'09:13:00',kind:'Discovery',title:'Sandbox identity inventory complete',detail:'Example principal graph created.',taskId:'T-C1',evidenceId:'EV-C1'},
];
const make = (id:string,name:string,type:EngagementType,target:string,objective:string,
 status:Engagement['status'],mode:Engagement['mode'],access:Engagement['access'],data:{
 tasks:Task[],observations:Observation[],hypotheses:Hypothesis[],findings:Finding[],events:EventRecord[],
 elapsed:number,calls:number,tokens:number
}):Engagement=>({
 id,name,type,target,objective,status,mode,access,perspective:'blackbox',priority:'balanced',
 budget,elapsedMinutes:data.elapsed,usedCalls:data.calls,usedTokens:data.tokens,
 tasks:data.tasks,observations:data.observations,hypotheses:data.hypotheses,findings:data.findings,
 agents:type==='web'?webAgents:[
 {id:id+'-planner',name:'Investigation Coordinator',specialty:'Task planning',state:status,model:'Configured model · illustrative',calls:Math.floor(data.calls/2)},
 {id:id+'-specialist',name:type==='api'?'API Authorization Analyst':'Cloud IAM Analyst',specialty:type==='api'?'API access':'Policy analysis',state:status,model:'Configured model · illustrative',calls:data.calls-Math.floor(data.calls/2)}
 ],events:data.events,lastUpdated:'2026-11-23',source:'illustrative'
});
export const DEMO_ENGAGEMENTS:Engagement[]=[
 make('ENG-LAB-001','Local Web Application Assessment','web','http://127.0.0.1:3000',
 'Assess the application, independently verify security weaknesses and prioritize next investigations.',
 'running','autonomous','both',{tasks:webTasks,observations:webEvidence,hypotheses:webHypotheses,findings:webFindings,events:webEvents,elapsed:21,calls:27,tokens:56200}),
 make('ENG-API-002','Internal API Authorization Review','api','http://127.0.0.1:8080/api',
 'Compare authorized access across API roles and validate any discrepancies.',
 'paused','supervised','authenticated',{tasks:apiTasks,observations:apiEvidence,hypotheses:apiHypotheses,findings:apiFindings,events:apiEvents,elapsed:34,calls:31,tokens:68800}),
 make('ENG-CLOUD-003','Cloud IAM Configuration Assessment','cloud','sandbox-policy-export.json',
 'Analyze sandbox principal permissions and independently assess policy findings.',
 'completed','guided','authenticated',{tasks:cloudTasks,observations:cloudEvidence,hypotheses:cloudHypotheses,findings:cloudFindings,events:cloudEvents,elapsed:56,calls:44,tokens:95500})
];
