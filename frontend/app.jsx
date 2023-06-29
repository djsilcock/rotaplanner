import {createRoot} from 'react-dom/client'
import {Component} from './component'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'


el=document.getElementById('root')
root=createRoot(el)
const queryclient=new QueryClient()
root.render(
  <QueryClientProvider client={queryclient}>
    <Component />
  </QueryClientProvider>
)
