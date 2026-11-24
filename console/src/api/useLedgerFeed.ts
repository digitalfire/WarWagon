import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getLedgerDetail, type LedgerEvent } from './live';
import { lastCursor, mergeLedgerEvents } from './live';

export type FeedState='connecting'|'connected'|'reconnecting'|'unavailable'|'idle';
export function useLedgerFeed(engagementId:string|null){
  const detail=useQuery({queryKey:['ledger-detail',engagementId],
    queryFn:()=>getLedgerDetail(engagementId!),enabled:engagementId!==null,
    retry:1,refetchOnWindowFocus:false});
  const [events,setEvents]=useState<LedgerEvent[]>([]);
  const [status,setStatus]=useState<FeedState>('idle');
  const [error,setError]=useState<string|null>(null);
  useEffect(()=>{
    const snapshot=detail.data;
    if(!engagementId||!snapshot||snapshot.engagement.id!==engagementId)return;
    let active=true;
    const seed=mergeLedgerEvents([],snapshot.events,engagementId);
    setEvents(seed);
    setError(null);
    setStatus('connecting');
    // The server has bounded SSE connections. EventSource automatically reconnects
    // with Last-Event-ID, while initial ?after avoids a snapshot-to-stream race.
    const sse=new EventSource('/api/v1/engagements/'+encodeURIComponent(engagementId)+'/events?after='+lastCursor(seed));
    sse.onopen=()=>{if(active){setStatus('connected');setError(null);}};
    sse.addEventListener('engagement.event',event=>{
      if(!active)return;
      try{
        const parsed=JSON.parse((event as MessageEvent).data) as LedgerEvent;
        if(parsed.engagementId!==engagementId||parsed.schemaVersion!==1)return;
        setEvents(previous=>{
          try{return mergeLedgerEvents(previous,[parsed],engagementId);}
          catch(err){setError(err instanceof Error?err.message:'Event conflict');sse.close();setStatus('unavailable');return previous;}
        });
      }catch{setError('Malformed streamed event');setStatus('unavailable');sse.close();}
    });
    sse.onerror=()=>{if(active)setStatus(previous=>previous==='unavailable'?'unavailable':'reconnecting');};
    return ()=>{active=false;sse.close();};
  },[engagementId,detail.data]);
  // No simulated fallback. Errors surface in the UI.
  return {detail,events,status,error};
}
