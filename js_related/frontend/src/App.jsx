import {createSignal, createEffect} from 'solid-js'
import {Dynamic} from 'solid-js/web'
import "./App.css"

import {RotaView} from './mainTable'
import TemplateEditor from './templateManagers/demandTemplates'
import { EditTemplateDialog } from './templateManagers/demandTemplates'
import SupplyTemplateEditor from './templateManagers/supplyTemplateEditor'

import backend from './backend'

const pages={
  blank:()=><div/>,
  rota:RotaView,
  template:TemplateEditor,
  demand_dialog:EditTemplateDialog,
  supply:SupplyTemplateEditor,
  solver:()=><div>Solver</div>

}

function App() {
  const [page,setPage]=createSignal('blank')
  createEffect(()=>backend.get_page().then(setPage))
  return <div class="main">
    <Dynamic component={pages[page()]}/>
    </div>
}

export default App
