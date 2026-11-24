/** Typed, read-only projection of existing WarWagon evidence fixture artifacts. */
export interface Usage {prompt_tokens?:number;completion_tokens?:number;total_tokens?:number}
export interface Invocation {response_id?:string;response_model?:string;finish_reason?:string;usage?:Usage}
export interface RecordedObservation {
  kind:string;schema_version:number;timestamp_utc:string;method:string;url:string;
  status_code:number;redirects_followed:number;total_seconds:number;error_type:string|null;
}
export interface RecordedToolCall {id:string;type:string;function:{name:string;arguments:string}}
export interface VerifierResult {
  kind:'benign_head_evidence_verification';schema_version:1;verified:boolean;reason:string|null;
  claim_source:'model'|'supplied';trace_sha256:string;expectation_sha256:string;supplied_claim_sha256:string|null;
}
export interface RecordedEvent {
  id:string;kind:'tool_call'|'observation'|'claim'|'verification';summary:string;
  tool?:RecordedToolCall;observation?:RecordedObservation;
  claim?:{observation_sha256:string;status_code:number};verification?:VerifierResult;usage?:Usage;sha256?:string;
}
export interface RecordedRunSummary {
  id:'confirmation'|'checkpoint';source:'recorded';model:string;target:string;
  observedStatus:number;observedAt:string;modelCalls:number;tokens:number|null;
  modelVerdict:'verified'|'rejected'|'unverified';traceSha256:string;
}
export interface RecordedRunDetail {
  id:RecordedRunSummary['id'];source:'recorded';schemaVersion:1;traceSha256:string;observationSha256:string;
  trace:{kind:'benign_head_evidence_run';schema_version:1;model:string;tool_call:RecordedToolCall;
    tool_invocation:Invocation;observation:RecordedObservation;claim:{observation_sha256:string;status_code:number};
    claim_invocation:Invocation;observation_reused:boolean;claim_reused:boolean};
  verifications:VerifierResult[];events:RecordedEvent[];
}
export interface RunCatalog {schemaVersion:1;source:'recorded';runs:RecordedRunSummary[]}
export class RecordedApiError extends Error {}
const base='/api/v1';
async function read<T>(path:string):Promise<T>{
  const response=await fetch(base+path,{headers:{Accept:'application/json'}});
  if(!response.ok)throw new RecordedApiError('Recorded artifact gateway returned HTTP '+response.status);
  return await response.json() as T;
}
export const getRecordedRuns=()=>read<RunCatalog>('/runs');
export const getRecordedRun=(id:RecordedRunSummary['id'])=>read<RecordedRunDetail>('/runs/'+encodeURIComponent(id));
