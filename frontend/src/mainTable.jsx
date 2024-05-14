
import {
  createSignal,
  createResource, createMemo,
  Suspense, For
} from "solid-js"
import { createStore } from 'solid-js/store'

import './maintable.css'
import backend from './backend'

const dutyCSS = 'duty', mainTableCSS = 'main-table', containerCSS = 'container'

const dutylabels = {
  '-': { classname: 'unallocated', label: '-' },
  'ICU': { classname: 'icu', label: 'ICU' },
  'TH': { classname: 'theatre', label: 'Th' },
  'LEAVE': { classname: 'unallocated', label: 'Leave' }
}
const focusElements = []

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

function isweekend(isodate) {
  const d = new Date(isodate)
  return d.getDay() == 0 || d.getDay() == 6
}

const [lastUpdated,setLastUpdated]=createSignal(1)

window.api.setLastUpdated=setLastUpdated

function MainTable(props) {
  const [tableConfig]=createResource(lastUpdated,()=>backend.get_table_config(),{initialValue:{}})
  const minDate = () => tableConfig().minDate
  const maxDataDate = () => tableConfig().maxDate
  const names = () => tableConfig().names
  const pubhols = () => tableConfig().pubhols
  //createEffect(()=>console.log(props.remoteData.latest))
  const [dateVisibility, setDateVisibility] = createStore({})

  const displayedDates = createMemo(oldDisplayedDates => {
    const newDisplayedDates = []//...oldDisplayedDates]
    if (typeof minDate() == 'undefined') return oldDisplayedDates

    function* isoDateIterator(startdate){
      let currentDate=typeof startdate=='string'?Date.parse(startdate):startdate.valueOf()

      while (true){
        yield new Date(currentDate).toISOString().slice(0,10)
        currentDate+=86400000
      }
    }

    
    const dates=isoDateIterator(minDate())
    let visibility='before'
    let tail=30
    for (let currentDate of dates){
      if (currentDate>maxDataDate() && (visibility=='after' || tail<=0)) break
      newDisplayedDates.push(currentDate)
      if (typeof dateVisibility[currentDate]=='undefined') {
        tail--
      }
      
      
      if (dateVisibility[currentDate]){
        visibility='in'
      }else{
        if (visibility=='in'){
          visibility='after'
        }
      }
    }
    return newDisplayedDates
  }, [])


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
  function observe(el) {
    intersectionObserver.observe(el)
    //if (typeof focusElements[rowNo] == 'undefined') { focusElements[rowNo] = [] }
    //focusElements[rowNo][colNo] = el
  }

  function doclick(target, duty) {
    const newdata = {
      dutydate: target.dataset.celldate,
      name: target.dataset.staffname,
      activity: duty ?? props.duty
    }
    backend.set_activity(newdata)
      .then(() => setLastUpdated(x=>x+1))
  }
  function handleKeyPress(keyPressed) {
    const currentElement = document.activeElement
    const activeRow = Number(currentElement.dataset.rowno)
    const activeCol = Number(currentElement.dataset.colno)

    try {
      switch (keyPressed) {
        case 'ArrowUp':
          focusElements[activeRow - 1][activeCol].focus()
          break
        case 'ArrowDown':
          focusElements[activeRow + 1][activeCol].focus()
          break
        case 'ArrowLeft':
          focusElements[activeRow][activeCol - 1].focus()
          break
        case 'ArrowRight':
          focusElements[Number(activeRow)][Number(activeCol) + 1].focus()
          break
        case ' ':
          doclick(currentElement)
          break
        case 'Delete':
        case 'Backspace':
          doclick(currentElement, false)
      }
    } catch (e) {
      //
    }
  }

  const keyDown = e => {
    e.preventDefault()
    handleKeyPress(e.key)
  }
  const onclick = e => {
    e.preventDefault()
    const target = e.target.closest('.duty')
    if (target) {
      target.focus()
      doclick(target)
    }
  }

  return <div class='bottom-panel' ref={registerIntersectionObserver} onClick={onclick} style={{ overflow: 'auto' }}>
    <table onKeyDown={keyDown} tabIndex={0} class={mainTableCSS}>
      <thead>
        <tr>
          <th></th>
          <For each={displayedDates()}>
            {x => <th classList={{ pubhol: pubhols()?.indexOf(x) >= 0, wkend: isweekend(x) }}>{x}</th>}
          </For>
        </tr>
      </thead>
      <tbody>
        <For each={names()}>
          {(staffName, rowNo) =>
            <tr>
              <th>{staffName}</th>
              <For each={displayedDates()}>
                {(cellDate, colNo) =>{
                 
                  const [data]=createResource(lastUpdated,()=>backend.get_duty_for_staff_and_date(staffName,cellDate))
                  return <td classList={{ pubhol: pubhols()?.indexOf(cellDate) >= 0, wkend: isweekend(cellDate),duty:true }}
                      data-cellDate={cellDate}
                      data-staffName={staffName}
                      use:observe={cellDate}><Suspense fallback='...'>
                    <For each={data.latest || []}>
                      {(session, sessionNo) => {
                        const dutylabel = () => (dutylabels[session.duty] ?? { classname: 'unallocated', label: session.duty ?? '?' })
                        const dutyflags = () => (session.flags ?? {})
                        //createEffect(()=>console.log(cellDate,data()))
                        return <div
                          tabIndex={-1}
                          use:observe={[rowNo() * 3 + sessionNo(), colNo()]}
                          title={JSON.stringify({ staffName, cellDate, start:session.start, finish:session.finish })}
                          data-rowNo={rowNo() * 3 + sessionNo()}
                          data-colNo={colNo()}
                          data-cellDate={cellDate}
                          data-staffName={staffName}
                          data-sessionStart={session.start}
                          data-sessionFinish={session.finish}
                          classList={{
                            duty: true,
                            [dutylabel().classname]: true
                          }}>
                          {session.start % 24}-{session.finish % 24}:{dutylabel().label}
                          {dutyflags().confirmed ? '🔒' : ''}{dutyflags().locum ? '💷' : ''}
                        </div>;
                      }}
                    </For></Suspense></td>                }}
              </For>

            </tr>}
        </For>
      </tbody>

    </table></div>
}




function RotaView() {
  const [duty, setDuty] = createSignal()

  const [start,setStart]=createSignal(8)
  const [finish,setFinish]=createSignal(17)

  return <>

    Change to:<select ref={(el) => { setDuty(el.value) }} onChange={
      (e) => { setDuty(e.target.value) }}>
      <option value={'ICU'}>ICU</option>
      <option value={'TH'}>Theatre</option>
    </select>

    Start:<select value={start()} onChange={(e) => { setStart(Number(e.target.value)) }}>
      <For each={Array(48)}>
        {(hr, i) => <option disabled={i() > finish() } value={i()}>{String(i() % 24).padStart(2, '0')}{i()>23?'(+1)':''}</option>}
      </For>
    </select>
    Finish:<select value={finish()} onChange={(e) => { setFinish(Number(e.target.value)) }}>
      <For each={Array(48)}>
        {(hr, i) => <option disabled={i() < start()} value={i()}>{String(i() % 24).padStart(2, '0')}{i()>23?'(+1)':''}</option>}
      </For>
    </select>


    <hr />
    <Suspense fallback={<span>Loading...</span>}>
      <div class={containerCSS}>
        <div />
        <MainTable duty={duty()} start={start} finish={finish}/>
      </div>
    </Suspense>
  </>
}


export { RotaView }