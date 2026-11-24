/** Version 1 persisted engagement event API, distinct from illustrative React fixtures. */
export interface LedgerEngagement {
  id:string;title:string;target:string;model:string|null;state:'created'|'running'|'completed'|'failed'|'canceled';
  createdAt:string;updatedAt:string;source:'recorded';
}
export interface LedgerEvent {
  sequence:number;engagementId:string;eventId:string;kind:string;origin:string;
  payload:Record<string,unknown>;payloadSha256:string;occurredAt:string;schemaVersion:1;
}
export interface LedgerCatalog {schemaVersion:1;source:'recorded';engagements:LedgerEngagement[]}
export interface LedgerDetail {schemaVersion:1;source:'recorded';engagement:LedgerEngagement;events:LedgerEvent[];hasMore:boolean}
export class LedgerApiError extends Error {}
async function get<T>(path:string):Promise<T> {
  const response=await fetch('/api/v1'+path,{headers:{Accept:'application/json'}});
  if(!response.ok)throw new LedgerApiError('Engagement gateway returned HTTP '+response.status);
  return await response.json() as T;
}
export const getLedgerCatalog=()=>get<LedgerCatalog>('/engagements');
export const getLedgerDetail=(id:string)=>get<LedgerDetail>('/engagements/'+encodeURIComponent(id));
export function mergeLedgerEvents(existing:LedgerEvent[],incoming:LedgerEvent[],engagementId:string):LedgerEvent[] {
  const records=new Map<number,LedgerEvent>();
  for(const event of [...existing,...incoming]){
    if(!Number.isSafeInteger(event.sequence)||event.sequence<1||
      event.schemaVersion!==1||event.engagementId!==engagementId)continue;
    const older=records.get(event.sequence);
    if(older && older.payloadSha256!==event.payloadSha256){
      // Never silently replace a committed event with conflicting evidence.
      throw new Error('Conflicting event at sequence '+event.sequence);
    }
    records.set(event.sequence,event);
  }
  return [...records.values()].sort((a,b)=>a.sequence-b.sequence);
}
export function lastCursor(events:LedgerEvent[]):number{
  return events.reduce((cursor,event)=>Math.max(cursor,event.sequence),0);
}
