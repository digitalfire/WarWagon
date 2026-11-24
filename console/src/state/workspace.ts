import { create } from 'zustand';
import type { Engagement, MainPage, WorkspaceTab } from '../domain/types';
import { DEMO_ENGAGEMENTS } from '../demo/fixtures';
export interface OperatorNote {id:string; engagementId:string; kind:'ask'|'direct'|'command'; content:string; createdAt:string;}
interface WorkspaceState {
 page:MainPage;tab:WorkspaceTab;engagementId:string;engagements:Engagement[];
 taskId:string|null;hypothesisId:string|null;findingId:string|null;evidenceId:string|null;
 operatorMode:OperatorNote['kind'];operatorNotes:OperatorNote[];
 setPage:(page:MainPage)=>void;setTab:(tab:WorkspaceTab)=>void;
 openEngagement:(id:string,tab?:WorkspaceTab)=>void;
 selectTask:(id:string)=>void;selectHypothesis:(id:string)=>void;
 selectFinding:(id:string)=>void;selectEvidence:(id:string)=>void;
 setOperatorMode:(mode:OperatorNote['kind'])=>void;addOperatorNote:(content:string)=>void;
 createDraft:(engagement:Engagement)=>void;
}
export const useWorkspace=create<WorkspaceState>((set,get)=>({
 page:'mission',tab:'overview',engagementId:DEMO_ENGAGEMENTS[0].id,engagements:[...DEMO_ENGAGEMENTS],
 taskId:null,hypothesisId:null,findingId:null,evidenceId:null,operatorMode:'direct',operatorNotes:[],
 setPage:page=>set({page}),setTab:tab=>set({tab}),
 openEngagement:(id,tab='overview')=>set({page:'engagement',engagementId:id,tab,taskId:null,hypothesisId:null,findingId:null,evidenceId:null}),
 selectTask:id=>set({taskId:id,tab:'investigation',page:'engagement'}),
 selectHypothesis:id=>set({hypothesisId:id,tab:'frontier',page:'engagement'}),
 selectFinding:id=>set({findingId:id,tab:'verification',page:'engagement'}),
 selectEvidence:id=>set({evidenceId:id,tab:'evidence',page:'engagement'}),
 setOperatorMode:operatorMode=>set({operatorMode}),
 addOperatorNote:content=>set(state=>({operatorNotes:[{id:crypto.randomUUID(),engagementId:get().engagementId,kind:state.operatorMode,content,createdAt:new Date().toLocaleTimeString()},...state.operatorNotes]})),
 createDraft:engagement=>set(state=>({engagements:[engagement,...state.engagements],engagementId:engagement.id,page:'engagement',tab:'overview'})),
}));
