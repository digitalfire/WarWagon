import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Shell } from './components/Shell';
import { useWorkspace } from './state/workspace';
import { MissionControl } from './screens/MissionControl';
import { NewEngagement } from './screens/NewEngagement';
import { EngagementWorkspace } from './screens/EngagementWorkspace';
import { ResearchLaboratory, ArchitectureCouncil, SystemIntegrations } from './screens/Supporting';
const queryClient = new QueryClient({defaultOptions:{queries:{retry:1,refetchOnWindowFocus:false}}});
function WorkspaceContent(){
  const page=useWorkspace(s=>s.page);
  switch(page){
    case 'mission':return <MissionControl/>;
    case 'engagements':return <MissionControl library/>;
    case 'new':return <NewEngagement/>;
    case 'engagement':return <EngagementWorkspace/>;
    case 'research':return <ResearchLaboratory/>;
    case 'arc':return <ArchitectureCouncil/>;
    case 'system':return <SystemIntegrations/>;
  }
}
export default function App(){
  return <QueryClientProvider client={queryClient}><Shell><WorkspaceContent/></Shell></QueryClientProvider>;
}
