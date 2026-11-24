import type { ReactNode } from 'react';
import { CheckCircle2, CircleDashed, CirclePause, ShieldAlert } from 'lucide-react';
export function Panel({title,detail,action,children,className=''}:{title?:string;detail?:string;action?:ReactNode;children:ReactNode;className?:string}) {
  return <section className={'ww-panel '+className}>
    {(title||detail||action)&&<header className="ww-panel-head"><div>{title&&<h3>{title}</h3>}{detail&&<p>{detail}</p>}</div>{action}</header>}
    {children}
  </section>;
}
export function Pill({children,tone='muted'}:{children:ReactNode;tone?:'muted'|'good'|'warn'|'bad'|'blue'}) {
  return <span className={'ww-pill tone-'+tone}>{children}</span>;
}
export function Metric({label,value,detail}:{label:string;value:ReactNode;detail?:string}) {
  return <div className="ww-metric"><span>{label}</span><strong>{value}</strong>{detail&&<small>{detail}</small>}</div>;
}
export function Empty({title,detail}:{title:string;detail:string}) {
  return <div className="ww-empty"><CircleDashed size={22}/><strong>{title}</strong><p>{detail}</p></div>;
}
export function StatusIcon({status}:{status:string}) {
  if(status==='completed'||status==='verified')return <CheckCircle2 size={16} className="good-text"/>;
  if(status==='paused'||status==='blocked'||status==='candidate')return <CirclePause size={16} className="warn-text"/>;
  if(status==='rejected')return <ShieldAlert size={16} className="bad-text"/>;
  return <CircleDashed size={16} className="blue-text"/>;
}
export function Progress({value,max=100}:{value:number;max?:number}) {
  const percent=max>0?Math.max(0,Math.min(100,value/max*100)):0;
  return <div className="ww-progress" role="progressbar" aria-valuenow={value} aria-valuemax={max} aria-valuemin={0}><div style={{width:percent+'%'}}/></div>;
}
