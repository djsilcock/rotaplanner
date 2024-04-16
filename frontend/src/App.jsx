import {Switch,Match,createSignal} from 'solid-js'


import {RotaView} from './mainTable'
import TemplateEditor from './templateEditor'




function App() {
  const [page,setPage]=createSignal('rota')

  var eventSource = new EventSource("/api/logging");
                    eventSource.addEventListener("message", event => {
                         console.log(event.data)
                    });
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
