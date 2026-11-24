import { describe, expect, it } from 'vitest';
import { DEMO_ENGAGEMENTS } from '../demo/fixtures';
describe('three engagement archetypes',()=>{
  it('includes web, api and cloud with distinct operating modes',()=>{
    expect(DEMO_ENGAGEMENTS.map(e=>e.type)).toEqual(['web','api','cloud']);
    expect(DEMO_ENGAGEMENTS.map(e=>e.mode)).toEqual(['autonomous','supervised','guided']);
    expect(new Set(DEMO_ENGAGEMENTS.map(e=>e.id)).size).toBe(3);
  });
  it('keeps finding evidence linked to an originating observation',()=>{
    for(const engagement of DEMO_ENGAGEMENTS)for(const finding of engagement.findings){
      expect(engagement.observations.some(e=>e.id===finding.originalEvidenceId)).toBe(true);
      if(finding.verificationEvidenceId)
        expect(engagement.observations.some(e=>e.id===finding.verificationEvidenceId)).toBe(true);
    }
  });
  it('keeps unverified findings separate from claimed sample verification',()=>{
    expect(DEMO_ENGAGEMENTS[0].findings[0].status).toBe('candidate');
    expect(DEMO_ENGAGEMENTS[2].findings[0].status).toBe('verified');
    expect(DEMO_ENGAGEMENTS.every(e=>e.source==='illustrative')).toBe(true);
  });
});