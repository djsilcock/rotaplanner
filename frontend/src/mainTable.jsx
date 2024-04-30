
import {
  createSignal,
  createResource, createMemo,
  Suspense, For
} from "solid-js"
import { createStore } from 'solid-js/store'

import './maintable.css'


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

function MainTable(props) {
  const minDate = () => props.remoteData.latest?.minDate
  const maxDataDate = () => props.remoteData.latest?.maxDate
  const names = () => props.remoteData.latest?.names
  const pubhols = () => props.remoteData.latest?.pubhols
  //createEffect(()=>console.log(props.remoteData.latest))
  const [dateVisibility, setDateVisibility] = createStore({})

  const displayedDates = createMemo(oldDisplayedDates => {
    const newDisplayedDates = []//...oldDisplayedDates]
    if (typeof minDate() == 'undefined') return oldDisplayedDates
    function addDayToISODate(d) {
      try {
        return (new Date(Date.parse(d) + 86400000)).toISOString().slice(0, 10)
      } catch (e) {
        console.error(e, d)
      }
    }
    let currentDate = minDate()
    while (currentDate <= maxDataDate() || newDisplayedDates.length < 30) {
      newDisplayedDates.push(currentDate)
      currentDate = addDayToISODate(currentDate)
    }

    let displayedDate
    let lastdateisVisible
    let passedvisiblezone = false
    const visibleDates = []
    for (displayedDate of newDisplayedDates) {
      lastdateisVisible = (dateVisibility[displayedDate] != false)
      if (lastdateisVisible) {
        passedvisiblezone = true
        visibleDates.push(displayedDate)
      }
      if (displayedDate > maxDataDate()) {
        if (passedvisiblezone && (lastdateisVisible == false))
          break
      }
    }
    while ((dateVisibility[displayedDate] == false) && !passedvisiblezone) {
      //extra dates which are now off the left of the screen
      displayedDate = addDayToISODate(displayedDate)
      newDisplayedDates.push(displayedDate)
    }
    while (dateVisibility[displayedDate] == true) {
      displayedDate = addDayToISODate(displayedDate)
      visibleDates.push(displayedDate)
      newDisplayedDates.push(displayedDate)
    }
    return newDisplayedDates.filter((d) => d <= displayedDate)
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
  function observe(el, data) {
    const [rowNo, colNo] = data()
    intersectionObserver.observe(el)
    if (typeof focusElements[rowNo] == 'undefined') { focusElements[rowNo] = [] }
    focusElements[rowNo][colNo] = el
  }
  function doclick(target, duty) {
    const newdata = {
      dutydate: target.dataset.celldate,
      name: target.dataset.staffname,
      sessionStart: props.start()*3600,
      sessionFinish: props.finish()*3600,
      duty: duty ?? props.duty
    }
    console.log(newdata)
    props.submit(newdata)
      .then(() => props.refetch())
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
                {(cellDate, colNo) =>
                  <td classList={{ pubhol: pubhols()?.indexOf(cellDate) >= 0, wkend: isweekend(cellDate),duty:true }}
                      data-cellDate={cellDate}
                      data-staffName={staffName}>
                    <For each={props.remoteData.latest.data?.[cellDate]?.[staffName] || []}>
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
                    </For></td>
                }
              </For>

            </tr>}
        </For>
      </tbody>

    </table></div>
}




function RotaView(props) {
  const [duty, setDuty] = createSignal()
  const [remoteData, { mutate, refetch }] = createResource(
    (_, { value, refetching }) => console.log('fetching...') || fetch('/api/by_name')
      .then(r => r.json())
  )

  function submit(data) {
    return fetch('/api/update_duty', { method: 'POST', body: JSON.stringify(data) })
  }

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
        <MainTable duty={duty()} remoteData={remoteData} mutate={mutate} submit={submit} refetch={refetch} start={start} finish={finish}/>
      </div>
    </Suspense>
  </>
}


export { RotaView }