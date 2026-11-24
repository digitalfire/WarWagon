export type EngagementType = 'web' | 'api' | 'cloud';
export type OperatingMode = 'autonomous' | 'supervised' | 'guided';
export type EngagementStatus = 'running' | 'paused' | 'completed' | 'draft';
export type VerificationStatus = 'verified' | 'candidate' | 'rejected' | 'inconclusive';
export type TaskStatus = 'completed' | 'running' | 'queued' | 'blocked';
export type AccessType = 'guest' | 'authenticated' | 'both';

export interface EngagementBudget {
  minutes: number; modelCalls: number; tokens: number; workers: number; httpRps: number;
}
export interface Task {
  id: string; title: string; phase: string; status: TaskStatus;
  owner: string; detail: string; tool?: string; invocation?: string;
  result?: string; evidenceIds: string[]; hypothesisIds: string[];
}
export interface Observation {
  id: string; title: string; source: string; content: string; taskId: string;
  timestamp: string; digest?: string;
}
export interface Hypothesis {
  id: string; title: string; detail: string; priority: number;
  confidence: string; status: 'open' | 'testing' | 'resolved';
  evidenceIds: string[]; nextAction: string;
}
export interface Finding {
  id: string; title: string; severity: 'critical' | 'high' | 'medium' | 'low';
  status: VerificationStatus; summary: string; impact: string;
  originalEvidenceId: string; verificationEvidenceId?: string; counterEvidenceId?: string;
}
export interface Agent {
  id: string; name: string; specialty: string; state: string;
  model: string; taskId?: string; calls: number;
}
export interface EventRecord {
  id: string; timestamp: string; kind: string; title: string; detail: string;
  taskId?: string; evidenceId?: string;
}
export interface Engagement {
  id: string; name: string; type: EngagementType; target: string;
  objective: string; status: EngagementStatus; mode: OperatingMode; access: AccessType;
  perspective: 'blackbox' | 'graybox' | 'whitebox';
  priority: 'balanced' | 'impact' | 'coverage' | 'depth';
  budget: EngagementBudget; elapsedMinutes: number; usedCalls: number; usedTokens: number;
  tasks: Task[]; observations: Observation[]; hypotheses: Hypothesis[];
  findings: Finding[]; agents: Agent[]; events: EventRecord[];
  lastUpdated: string; source: 'illustrative';
}
export type WorkspaceTab = 'overview' | 'investigation' | 'plan' | 'frontier' |
  'graph' | 'agents' | 'findings' | 'verification' | 'evidence' | 'report' | 'settings';
export type MainPage = 'mission' | 'engagements' | 'new' | 'engagement' |
  'research' | 'arc' | 'system' | 'recorded';
