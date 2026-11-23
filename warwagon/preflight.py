"""WarWagon model endpoint/tool-call preflight. Performs actual inference, no lab actions."""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.error
from warwagon.model import ChatModel

TOOL={"type":"function","function":{"name":"report_probe","description":"Return a diagnostic string. No side effects.","parameters":{"type":"object","properties":{"message":{"type":"string"}},"required":["message"]}}}

def check(model: ChatModel):
    response=model.complete([
        {"role":"system","content":"This is a tool-call compatibility test. Call report_probe with message 'warwagon-ok'. Do not answer only with text."},
        {"role":"user","content":"Use the report_probe tool now."}],tools=[TOOL])
    msg=response["choices"][0]["message"]
    calls=msg.get("tool_calls") or []
    match=False
    parsed=[]
    for call in calls:
        fn=call.get("function") or {}
        args=fn.get("arguments") or {}
        if isinstance(args,str):
            try: args=json.loads(args)
            except json.JSONDecodeError: args={}
        if not isinstance(args,dict): args={}
        parsed.append({"name":fn.get("name"),"arguments":args})
        if fn.get("name")=="report_probe" and args.get("message")=="warwagon-ok":
            match=True
    return {"model":model.model,"endpoint":model.base_url,"tool_call_seen":bool(calls),
            "tool_call_correct":match,"calls":parsed,"usage":response.get("usage",{}),
            "diagnostic": "pass" if match else "fail: model did not return expected structured function call"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",default=os.getenv("WW_MODEL",""))
    p.add_argument("--base-url",default=os.getenv("WW_MODEL_BASE_URL","http://127.0.0.1:11434/v1"))
    a=p.parse_args()
    if not a.model: p.error("--model or WW_MODEL is required")
    try:
        result=check(ChatModel(a.base_url,a.model))
    except (OSError,ValueError,urllib.error.HTTPError,urllib.error.URLError) as exc:
        print(json.dumps({"diagnostic":"error","error":str(exc),"type":type(exc).__name__},indent=2))
        sys.exit(2)
    print(json.dumps(result,indent=2))
    sys.exit(0 if result["tool_call_correct"] else 1)

if __name__=="__main__": main()
