
import { createEffect, createSignal, createResource, createMemo, Suspense, For } from "solid-js"
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
  const currentElement=document.activeElement
  const output={current:currentElement}
  const activeRow=Number(currentElement.dataset.rowno)
  const activeCol=Number(currentElement.dataset.colno)
  
  console.log(activeRow,activeCol) 
  try{
  switch (keyPressed) {
    case 'ArrowUp':
      focusElements[activeRow-1][activeCol].focus()
      break
    case 'ArrowDown':
      focusElements[activeRow+1][activeCol].focus()
      break
    case 'ArrowLeft':
      focusElements[activeRow][activeCol-1].focus()
      break    
    case 'ArrowRight':
      focusElements[Number(activeRow)][Number(activeCol)+1].focus()
      break
  }
  console.log(output)
} catch (e){
  //
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
  const [remoteData,{}] = createResource(
    //() => fetch('/api/data').then(r => r.json())
    ()=>(Promise.resolve({minDate:'2022-01-01',maxDate:'2023-01-01',names:['fred','barney'],data:{}})))

  const minDate = createMemo(() => remoteData.latest?.minDate)
  const maxDataDate = createMemo(() => remoteData.latest?.maxDate)
  const names = createMemo(() => remoteData.latest?.names)
  const [dateVisibility,setDateVisibility]=createStore({})
  const displayedDates=createMemo(oldDisplayedDates => {
    const newDisplayedDates = [...oldDisplayedDates]
    const prevDisplayedDates = new Set(oldDisplayedDates)
    function addDayToISODate(d) {
      return  (new Date(Date.parse(d)+86400000)).toISOString().slice(0,10)
      }
    let currentDate = minDate()
    while (currentDate <= maxDataDate()) {
      if (!prevDisplayedDates.has(currentDate)) {newDisplayedDates.push(currentDate)}
      currentDate = addDayToISODate(currentDate)
    }
  
    let displayedDate
    let lastdateisVisible
    let passedvisiblezone = false
    const visibleDates=[]
    for (displayedDate of newDisplayedDates) {
      lastdateisVisible = (dateVisibility[displayedDate]!=false)
      if (lastdateisVisible) { 
        passedvisiblezone = true
        visibleDates.push(displayedDate)
      }
      if (displayedDate > maxDataDate()) {
        if (passedvisiblezone && (lastdateisVisible == false))
          break
      }
    }
    if (lastdateisVisible) {
      newDisplayedDates.push(addDayToISODate(displayedDate))
    }
    return newDisplayedDates.filter((d) => d <= addDayToISODate(displayedDate))
  },[])
  let intersectionObserver
  function registerIntersectionObserver(el) {
    intersectionObserver = new IntersectionObserver(
      entries => {
        for (let entry of entries) {
          //if (entry.isIntersecting) console.log(entry)
          setDateVisibility(entry.target.dataset.celldate, entry.isIntersecting)
        }
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
  const keyDown = e => {
        e.preventDefault()
        handleKeyPress(e.key)
  }
  const onclick=e=>{
    e.preventDefault()
    const target=e.target.closest('.duty')
    if (target){
      console.log(target.dataset.celldate)
    }
  }

  return <div class='bottom-panel' ref={registerIntersectionObserver} onClick={onclick} style={{ overflow: 'auto' }}>
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
  return <>
    <div><select onChange={
      (e) => { console.log(e.target.value)}}>
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