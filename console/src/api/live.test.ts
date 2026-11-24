import { describe, expect, it } from 'vitest';
import { mergeLedgerEvents, lastCursor, type LedgerEvent } from './live';
const make=(sequence:number,kind='tool.observation'):LedgerEvent=>({
  sequence,engagementId:'eng-test',eventId:'event-'+sequence,kind,origin:'agent',
  payload:{step:sequence},payloadSha256:('a'.repeat(63)+(sequence%10)),occurredAt:'2026-11-24T00:00:00Z',schemaVersion:1,
});
describe('durable event projections',()=>{
  it('sorts, deduplicates by cursor and handles gaps across other engagements',()=>{
    const found=mergeLedgerEvents([make(2),make(7)],[make(7),make(11),make(3)],'eng-test');
    expect(found.map(e=>e.sequence)).toEqual([2,3,7,11]);
    expect(lastCursor(found)).toBe(11);
  });
  it('does not combine other engagement streams',()=>{
    const other={...make(8),engagementId:'another-engagement'};
    expect(mergeLedgerEvents([make(3)],[other],'eng-test')).toEqual([make(3)]);
  });
  it('rejects conflicting evidence for the same event cursor',()=>{
    expect(()=>mergeLedgerEvents([make(3)],[{...make(3),payloadSha256:'b'.repeat(64)}],'eng-test')).toThrow(/Conflicting/);
  });
  it('returns empty cursor for first-time engagement',()=>{
    expect(lastCursor([])).toBe(0);
  });
});
