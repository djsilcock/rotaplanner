import {Switch,Match,createSignal} from 'solid-js'

import './App.css'

import {RotaView} from './mainTable'
import TemplateEditor from './templateEditor'


function App() {
  const [page,setPage]=createSignal('rota')
  return <>
    <div>
      <select name="page" value={page()} onChange={e=>{setPage(e.target.value)}}>
        <option value="rota">Rota View</option>
        <option value="template">Template Manager</option>
        <option value="solver">Solver</option>
      </select>
    </div>
    <Switch fallback="??">
      <Match when={page()=='rota'}>
        <RotaView/>
      </Match>
      <Match when={page()=='template'}>
        <TemplateEditor/>
      </Match>
      <Match when={page()=="solver"}>
        Solver view
      </Match>
    </Switch>
    </>
}

export default App
