import type { ReactNode } from 'react';
import { Activity, FileCheck2, Boxes, FlaskConical, LayoutDashboard, Layers3, Menu, Plus, Settings2, Shield, UsersRound, X } from 'lucide-react';
import { useState } from 'react';
import type { MainPage } from '../domain/types';
import { useWorkspace } from '../state/workspace';
const groups:{title:string;items:{id:MainPage;label:string;icon:typeof Activity}[]}[]=[
  {title:'OPERATIONS',items:[{id:'mission',label:'Mission Control',icon:LayoutDashboard},{id:'live',label:'Live Engagement Events',icon:Activity},{id:'engagements',label:'Engagements',icon:Layers3},{id:'new',label:'New Engagement',icon:Plus}]},
  {title:'INTELLIGENCE',items:[{id:'recorded',label:'Recorded Run Evidence',icon:FileCheck2},{id:'research',label:'Research Laboratory',icon:FlaskConical},{id:'arc',label:'Architecture Council',icon:UsersRound}]},
  {title:'PLATFORM',items:[{id:'system',label:'Models & Tools',icon:Boxes}]},
];
export function Shell({children}:{children:ReactNode}) {
  const page=useWorkspace(s=>s.page),setPage=useWorkspace(s=>s.setPage),engagement=useWorkspace(s=>s.engagements.find(e=>e.id===s.engagementId));
  const [open,setOpen]=useState(false);
  const change=(p:MainPage)=>{setPage(p);setOpen(false);};
  return <div className="ww-shell">
    <aside className={'ww-sidebar '+(open?'is-open':'')}>
      <div className="ww-brand" onClick={()=>change('mission')} role="button" tabIndex={0} onKeyDown={e=>e.key==='Enter'&&change('mission')}>
        <span className="ww-mark"><Shield size={20}/></span><div><strong>WARWAGON</strong><small>AUTONOMOUS INTELLIGENCE</small></div>
        <button className="ww-mobile-close icon-button" onClick={e=>{e.stopPropagation();setOpen(false)}} aria-label="Close navigation"><X size={18}/></button>
      </div>
      <nav aria-label="Primary navigation">{groups.map(group=><div key={group.title} className="ww-nav-group">
        <span className="ww-overline">{group.title}</span>
        {group.items.map(({id,label,icon:Icon})=><button key={id} className={'ww-nav-link '+(page===id?'active':'')} onClick={()=>change(id)}><Icon size={17}/>{label}</button>)}
      </div>)}
      <div className="ww-nav-group"><span className="ww-overline">ACTIVE CONTEXT</span>
        <button className={'ww-nav-link '+(page==='engagement'?'active':'')} onClick={()=>change('engagement')}><Activity size={17}/> {engagement?.id||'Engagement'}</button>
      </div></nav>
      <div className="ww-sidebar-foot">
        <span className="ww-status-light"/> <span>UX PREVIEW · NO LIVE AGENTS</span>
        <a href="./recorded-runs.html">Open recorded evidence inspector ↗</a>
        <a href="./ux-reference.html">Original v2 reference ↗</a>
      </div>
    </aside>
    {open&&<button className="ww-backdrop" aria-label="Close navigation" onClick={()=>setOpen(false)}/>}
    <div className="ww-main-column">
      <header className="ww-topbar">
        <button className="icon-button ww-menu" onClick={()=>setOpen(true)} aria-label="Open navigation"><Menu size={19}/></button>
        <span><b>WARWAGON</b><span className="ww-breadcrumb"> / {page==='engagement'?engagement?.name:page.replace(/-/g,' ')}</span></span>
        <div className="ww-top-actions"><span className="ww-head-status"><span className="ww-status-light"/> CONCEPT MODE</span><button className="icon-button" onClick={()=>change('system')} title="Settings"><Settings2 size={18}/></button></div>
      </header>
      <main className="ww-main">
        <div className="ww-preview-banner"><Shield size={16}/><span>Interactive design preview. Engagement activity, findings and telemetry are simulated. Actual verified artifacts remain in the <a href="./recorded-runs.html">Recorded Run Inspector</a>.</span></div>
        {children}
      </main>
    </div>
  </div>;
}
