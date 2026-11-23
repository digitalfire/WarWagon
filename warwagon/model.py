"""Small provider-neutral client for OpenAI-compatible Chat Completions."""
import json
import os
import urllib.parse
import urllib.request

class ChatModel:
    def __init__(self, base_url: str, model: str, timeout: int = 120):
        url = urllib.parse.urlsplit(base_url)
        if url.scheme not in ("http","https") or not url.hostname or url.username or url.password:
            raise ValueError("base_url must be an HTTP(S) URL without embedded credentials")
        if url.scheme == "http" and url.hostname not in ("localhost","127.0.0.1","::1"):
            raise ValueError("plain HTTP model access is restricted to local endpoints")
        if not model:
            raise ValueError("model is required")
        self.base_url=base_url.rstrip("/")
        self.model=model
        self.timeout=timeout

    def complete(self, messages, tools=None):
        payload={"model":self.model,"messages":messages,"temperature":0}
        if tools:
            payload["tools"]=tools
            payload["tool_choice"]="auto"
        body=json.dumps(payload).encode()
        headers={"Content-Type":"application/json"}
        key=os.getenv("WW_MODEL_API_KEY","")
        if key:
            headers["Authorization"]="Bearer "+key
        request=urllib.request.Request(self.base_url+"/chat/completions",
                                       data=body,headers=headers,method="POST")
        with urllib.request.urlopen(request,timeout=self.timeout) as response:
            data=json.loads(response.read(4_000_000))
        if not data.get("choices"):
            raise ValueError("model returned no choices")
        return data
