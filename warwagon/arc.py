"""Execute independent first-pass architecture reviews through real model calls.

No hidden multi-agent capability: each review is a separate invocation with isolated
messages. Same model/provider does not establish model diversity.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from warwagon.model import ChatModel

ROLES={
 "agent-intelligence":"Assess cognitive architectures, multi-agent autonomy and planning alternatives.",
 "distributed-systems":"Assess causal ordering, idempotency, replay and crash consistency.",
 "knowledge-data":"Assess source-of-truth, graph ontology, evidence and provenance.",
 "security-research":"Assess realism, scope of local fixtures, evidence and validation.",
 "evaluation-science":"Assess confounders, statistical validity, held-out tests and measurement.",
 "model-inference":"Assess context engineering, routing, provider parity and inference efficiency.",
 "developer-experience":"Assess interface stability, interoperability and contributor experience.",
 "adversarial-review":"Try to falsify key assumptions and reveal dangerous failure modes.",
 "research-skeptic":"Identify unsupported factual claims, absent evidence and alternatives."
}
SCHEMA={"type":"object","properties":{"verdict":{"type":"string"},"strengths":{"type":"array","items":{"type":"string"}},"blockers":{"type":"array","items":{"type":"string"}},"experiments":{"type":"array","items":{"type":"string"}},"unknowns":{"type":"array","items":{"type":"string"}}}}
def review(model,role,proposal):
    system=("You are the "+role+" reviewer. "+ROLES[role]+
      " Give a rigorous independent FIRST-PASS critique. Never assume other reviewers agree. "
      "Distinguish evidence from speculation. Return JSON object with keys verdict, strengths, blockers, experiments, unknowns. "
      "Use verdict support, conditional, needs-research or reject.")
    response=model.complete([{"role":"system","content":system},{"role":"user","content":proposal}])
    output=response["choices"][0]["message"].get("content","")
    return {"role":role,"model":model.model,"system_prompt_sha256":hashlib.sha256(system.encode()).hexdigest(),
            "response":output,"usage":response.get("usage",{}),"independent_context":True}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--proposal",type=Path,default=Path("docs/rfcs/RFC-0001-planner-research-v2.md"))
    ap.add_argument("--model",default=os.getenv("WW_MODEL",""))
    ap.add_argument("--base-url",default=os.getenv("WW_MODEL_BASE_URL","http://127.0.0.1:11434/v1"))
    ap.add_argument("--output",type=Path,default=Path("artifacts/arc-review.json"))
    args=ap.parse_args()
    if not args.model: ap.error("provide --model or WW_MODEL")
    proposal=args.proposal.read_text(encoding="utf-8")
    if len(proposal)>120000: ap.error("proposal exceeds 120k characters; freeze a smaller packet")
    model=ChatModel(args.base_url,args.model)
    reviews=[]
    for role in ROLES:
        reviews.append(review(model,role,proposal))
        print("review completed:",role)
    payload={"kind":"real_model_first_pass_reviews","proposal":str(args.proposal),
             "proposal_sha256":hashlib.sha256(proposal.encode()).hexdigest(),
             "model":args.model,
             "warning":"Separate model calls and contexts; if the same model handles all roles, this is NOT independent model consensus. No deliberation/synthesis or maintainer decision is implied.",
             "reviews":reviews}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print("Saved",args.output)
if __name__=="__main__":
    main()
