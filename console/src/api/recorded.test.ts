import { describe, expect, it } from 'vitest';
import type { RecordedRunDetail, RecordedEvent } from './recorded';
describe('recorded evidence contract',()=>{
  it('retains provenance and differentiates a status claim from vulnerability discovery',()=>{
    const event:RecordedEvent={id:'004',kind:'verification',summary:'Benign status verification',
      verification:{kind:'benign_head_evidence_verification',schema_version:1,
        verified:true,reason:null,claim_source:'model',
        trace_sha256:'a'.repeat(64),expectation_sha256:'b'.repeat(64),supplied_claim_sha256:null}};
    expect(event.verification?.verified).toBe(true);
    expect(event.verification?.claim_source).toBe('model');
  });
  it('types the read-only evidence source independently of illustrative engagement fixtures',()=>{
    const run:Pick<RecordedRunDetail,'id'|'source'|'schemaVersion'>={id:'confirmation',source:'recorded',schemaVersion:1};
    expect(run.source).toBe('recorded');
  });
});
