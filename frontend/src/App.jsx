import './App.css'

import {Component} from './component'
import {QueryClient,QueryClientProvider} from '@tanstack/solid-query'


const queryclient=new QueryClient({defaultOptions:{queries:{useErrorBoundary:true}}})

function App() {

  return (
    <QueryClientProvider client={queryclient}>
      <Component/>
      </QueryClientProvider>
  )
}

export default App
