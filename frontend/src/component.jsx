
import { createEffect, createSignal, on, createResource, createMemo, Suspense, createContext, For } from "solid-js"
import { createStore } from 'solid-js/store'

import useLocalConfig from "./localconfig"

import './component.css'


const dutyCSS = 'duty', mainTableCSS = 'main-table', containerCSS = 'container'



const dutylabels = {
  '-': { classname: 'unallocated', label: '-' },
  'ICU': { classname: 'icu', label: 'ICU' },
  'TH': { classname: 'theatre', label: 'Th' },
  'LEAVE': { classname: 'unallocated', label: 'Leave' }
}
const focusElements=[]

function handleKeyPress(keyPressed) {
  const MAX_SHIFT_INDEX = 2
  const currentElement=document.activeElement
  const activeRow=currentElement.dataset.rowno
  const activeCol=currentElement.dataset.colno
  console.log(activeRow,activeCol) 
  //console.log(focusElements[Number(activeCol)+1][Number(activeRow)+1])
  switch (keyPressed) {
    case 'ArrowUp':
      return (state) => {
        if (state.shift == 0) {
          if (state.row == 0) return state
          return { ...state, row: state.row - 1, shift: MAX_SHIFT_INDEX }
        }
        return { ...state, shift: state.shift - 1 }
      }
    case 'ArrowDown':
      return (state) => {
        if (state.shift == MAX_SHIFT_INDEX) {
          if (state.row == state.maxRow) return state
          return { ...state, row: state.row + 1, shift: 0 }
        }
        return { ...state, shift: state.shift + 1 }
      }
    case 'ArrowLeft':
      return (state) => {
        if (state.col == 0) return state
        return { ...state, col: state.col - 1 }
      }
    case 'ArrowRight':
      return (state) => {
        return { ...state, col: state.col + 1 }
      }
  }
}




/* expected data shape
{ minDate:string,
  maxDate:string,
  names:string[],
  data:{
    [date:string]:{
      [name:string]:{
        [session:string]:{duty:string,flags:string[]}
      }
    }
  }
}
*/
function MainTable() {
  const remoteData = createResource(() => fetch('/api/data').then(r => r.json())
  .catch(r=>r)
  .then(r=>({minDate:'2022-01-01',maxDataDate:'2023-01-01',names:[],data:{}})))
  const minDate = createMemo(() => remoteData.latest?.minDate ?? '2022-02-01')
  const maxDataDate = createMemo(() => remoteData.latest?.maxDate ?? '2023-01-01')
  const names = createMemo(() => remoteData.latest?.names ?? ['fred','barney'])
  const [displayedDates, doupdateDisplayedDates] = createSignal([])
  const dateVisibility = new Map()
  createEffect(()=>console.log(minDate()))
  const updateDisplayedDates = ()=>doupdateDisplayedDates(oldDisplayedDates => {
    console.log('updating')

    const newDisplayedDates = [...oldDisplayedDates]
    const prevDisplayedDates = new Set(oldDisplayedDates)
    function addDayToISODate(d) {
      return  (new Date(Date.parse(d)+86400000)).toISOString().slice(0,10)
      }
    let currentDate = minDate()
    let ctr=0
    console.log(currentDate,minDate(),maxDataDate())
    
    while (currentDate <= maxDataDate()) {
      
      if (!prevDisplayedDates.has(currentDate)) {newDisplayedDates.push(currentDate)};
      currentDate = addDayToISODate(currentDate)
      ctr++
      if (ctr>1000) break
    }
    //console.log(newDisplayedDates)
  
    let displayedDate
    let lastdateisVisible
    let passedvisiblezone = false
    const visibleDates=[]
    for (displayedDate of newDisplayedDates) {
      lastdateisVisible = dateVisibility.get(displayedDate)
      if (lastdateisVisible) { 
        passedvisiblezone = true
        visibleDates.push(displayedDate)
      }
      if (displayedDate > maxDataDate()) {
        if (passedvisiblezone && (lastdateisVisible == false))
          break
      }
    }
    console.log(visibleDates)
    if (lastdateisVisible) {
      newDisplayedDates.push(addDayToISODate(displayedDate))
    }
    return newDisplayedDates.filter((d) => d <= addDayToISODate(displayedDate))
  })
  createEffect(()=>{
    minDate()
    maxDataDate()
    updateDisplayedDates()
  })
  createEffect(()=>{console.log(names())})
  let intersectionObserver
  function registerIntersectionObserver(el) {
    console.log('register observer',el)
    intersectionObserver = new IntersectionObserver(
      entries => {
        for (let entry of entries) {
          //if (entry.isIntersecting) console.log(entry)
          dateVisibility.set(entry.target.dataset.celldate, entry.isIntersecting)
        }
        updateDisplayedDates()
      },
      { root: el })
  }
  function observe(el,data) 
  {
    const [rowNo,colNo]=data()
    intersectionObserver.observe(el)
    if (typeof focusElements[rowNo] =='undefined') {focusElements[rowNo]=[]}
    focusElements[rowNo][colNo]=el
  }
  const keyDown = (e => {
    switch (e.key) {
      case 'ArrowUp':
      case 'ArrowDown':
      case 'ArrowLeft':
      case 'ArrowRight':
        e.preventDefault()
        console.log(document.activeElement)
        console.log(focusElements)
        handleKeyPress(e.key)
        break;
      default:
        break;
    }
  })

  return <div class='bottom-panel' ref={registerIntersectionObserver} style={{ overflow: 'auto' }}>
      <For each={names()}>{(i)=><span>{i()}</span>}</For>
      <table onKeyDown={keyDown} tabIndex={0} class={mainTableCSS}>
        <thead>
          <tr>
            <th>First</th>
            <For each={displayedDates()}>
              {x => <th >{x}</th>}
            </For>
          </tr>
          </thead>
          <tbody>
          <For each={names()}>
            {(staffName, rowNo) =>
              <tr>
                <th>{staffName}</th>
                <For each={displayedDates()}>
                  {(cellDate, colNo) =>
                    <td >
                      <For each={['am', 'pm', 'oncall']}>
                        {(session, sessionNo) =>{
                            const data=createMemo(()=>remoteData[cellDate]?.[staffName]?.[session] ?? {duty:'-',flags:{}})
                            const dutylabel = () => (dutylabels[data.duty] ?? { classname: 'unallocated', label: data.data?.duty ?? '?' })
                            const dutyflags = () => (data.flags ?? {})
                            let divRef
                            return <div
                              tabIndex={-1}
                              use:observe={[rowNo()*3+sessionNo(),colNo()]}
                              title={JSON.stringify({ staffName, cellDate, session })}
                              data-rowNo={rowNo()*3+sessionNo()}
                              data-colNo={colNo()}
                              data-cellDate={cellDate}
                              data-staffName={staffName}
                              data-session={session}
                              classList={{
                                duty: true,
                                [dutylabel().classname]: true
                              }}>
                              {session}:{dutylabel().label}
                              {dutyflags().confirmed ? '🔒' : ''}{dutyflags().locum ? '💷' : ''}
                            </div>;
                          }}
                      </For></td>
                  }
                </For>

              </tr>}
          </For>
        </tbody>
        
      </table></div>
}

function ConstraintDialog(props) {
  const { data: localconfig } = useLocalConfig()
  const constraintShown = localconfig.configEdit

}

function Component(props) {
  const { setConfig, data: localconfig } = useLocalConfig()
  return <>
    <div><select value={localconfig?.duty} onChange={
      (e) => { setConfig(old => ({ ...old, duty: e.target.value })) }}>
      <option value={'ICU'}>ICU</option>
      <option value={'Th'}>Theatre</option>
    </select></div>
    <hr />
    <Suspense fallback={<span>Loading...</span>}>
      <div class={containerCSS}>
        <div />
        <MainTable />
      </div>
    </Suspense>
  </>
}


export { Component }