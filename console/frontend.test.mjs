import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
const read=path=>readFile(new URL(path,import.meta.url),"utf8");

test("default Vite index mounts the React app",async()=>{
 const html=await read("index.html");
 assert.match(html,/id="root"/);
 assert.match(html,/src\/main\.tsx/);
 assert.doesNotMatch(html,/DEMO \/ NO BACKEND/);
});

test("engagement components preserve the complete v2 navigation",async()=>{
 const workspace=await read("src/screens/EngagementWorkspace.tsx");
 for(const screen of ["Investigation","Mission Plan","Reasoning Frontier","Intelligence Graph","Agent Command","Findings","Verification","Evidence","Report"]){
  assert.ok(workspace.includes(screen),"missing engagement workspace: "+screen);
 }
 const main=await read("src/screens/MissionControl.tsx");
 assert.match(main,/Mission Control/);
 const builder=await read("src/screens/NewEngagement.tsx");
 assert.match(builder,/Mission briefing/i);
});

test("recorded run inspector and reference remain reachable",async()=>{
 const html=await read("recorded-runs.html");
 assert.match(html,/inspector\.js/);
 assert.match(html,/run-template/);
 assert.match(await read("src/components/Shell.tsx"),/recorded-runs\.html/);
 const ref=await read("ux-reference.html");
 assert.match(ref,/function consoleTab\(/);
});
