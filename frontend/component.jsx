/*eslint-disable react/prop-types */

import { css, cx } from '@emotion/css'
import { useMemo, useRef, useCallback, useEffect, Suspense, useReducer, createContext, useContext, memo } from "react"


import {useQuery,useMutation,useQueryClient} from '@tanstack/react-query'
import useLocalConfig from "./localconfig"

const genericFetch = async ({queryKey}) => {
  const fetchresult=await fetch(`/${queryKey.join('/')}`)
    return await fetchresult.json()
  }

const getDutySelector = (name, date,session) => {
  const cellid = `${date}|${name}|${session}`
  return (data)=>data?.[cellid]
}


function DutyButton({ name, date, session, rowNo, colNo, sessionNo,isFocussed}) {
  const selector = useMemo(() => getDutySelector(name, date))
  const { data:duty } = useQuery({queryKey:['data'], queryFn:genericFetch, select: selector,staleTime:3600000 })
  const dutylabel = dutylabels[duty.duty ?? '-'] ?? { classname: 'unallocated', label: duty.duty ?? '?' }
  const dutyflags = duty?.flags ?? {}
  const focusDispatch = useContext(FocusDispatchContext)
  const { data:localconfig}=useQuery({queryKey:['localconfig'],queryFn:()=>Promise.resolve({'duty':'ICU'}),staleTime:Infinity,cacheTime:Infinity,suspense:true})  
  const queryClient=useQueryClient()
  const {mutate}=useMutation({
    mutationFn:(vars)=>fetch('/click',{method:'POST',body:JSON.stringify(vars)}).then(r=>r.json()),
    onSettled:()=>queryClient.invalidateQueries({queryKey:['data']})})
  const onClick = useCallback(() => {
    mutate({ name, date, session,duty:localconfig.duty })
    divRef.current.focus()
    focusDispatch({type:'click',cell:{ row: rowNo, col: colNo,shift:sessionNo }})
  })
  useEffect(() => {
    if (isFocussed) {
      divRef.current.focus()
    }
  }, [isFocussed])
  const divRef = useRef()
  const className = cx(dutyCSS, dutylabel.classname, isFocussed ? 'selected' : '')
  return <div tabIndex={-1} ref={divRef} key={session} className={className} {...{ onClick }}>
    {session}:{dutylabel.label}
    {dutyflags.confirmed ? '🔒' : ''}{dutyflags.locum ? '💷' : ''}
  </div>
}

const TableCell=memo(function TableCell({ name, date, rowNo, colNo,highlightShift }) {
  return <td>
      {['am', 'pm', 'oncall'].map(
        (session, i) => 
          <DutyButton 
            key={i}
            isFocussed={highlightShift==i}
            rowNo={rowNo} 
            colNo={colNo}
            sessionNo={i} 
            name={name} 
            date={date} 
            session={session} 
            />)}</td>
})
const containerCSS = css`
  display:grid;
  grid-template-columns: 1fr;
  grid-template-rows:min-content 1fr;
  max-height: calc(100vh - 20px);
  max-width: 100vw;
  overflow: auto;
  `
const mainTableCSS = css`
  white-space: nowrap;
  font-family: Verdana;
  font-size: 50%;
  margin: 0;
  border: none;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  border: 1px solid black;

  & td, & th {
    border: 1px solid black;
    padding: 0.5rem 1rem;
  }

  & thead th {
    padding: 3px;
    position: sticky;
    top: 0;
    z-index: 1;
    width: 25vw;
    background: white;
  }
  & td {
    background: #fff;
    padding: 4px 5px;
    text-align: left;
  }

  & table.hscroll tbody th {
    font-weight: 100;
    text-align: left;
    position: relative;
  }
  & thead th:first-child {
    position: sticky;
    left: 0;
    z-index: 2;
  }
  
  & tbody th {
    position: sticky;
    left: 0;
    background: white;
    z-index: 1;
  }

  `

const dutyCSS = css`
    width:100%;
    &:hover {
      background-color: #EEEEFF;
    }
    &.selected:focus {
      background-color: #EEFFFF;
    }
    &.icu {
      color: #0000DD;
    }
    &.theatre {
      color: #00DD00
    }
    &.unallocated {
      color: #DD0DDD
    }

    `

const dutylabels = {
  '-': { classname: 'unallocated', label: '-' },
  'ICU': { classname: 'icu', label: 'ICU' },
  'TH': { classname: 'theatre', label: 'Th' },
  'LEAVE': { classname: 'unallocated', label: 'Leave' }
}

function makeGridMovementReducer(MAX_ROW_INDEX) {
  return function gridMovementReducer(state, action) {
    const MAX_SHIFT_INDEX = 2
    console.log({state,action})
    switch (action.type){
      case 'keypress':
    switch (action.keyPressed) {
      case 'ArrowUp':
        if (state.shift == 0) {
          if (state.row == 0) return state
          return { ...state, row: state.row - 1, shift: MAX_SHIFT_INDEX }
        }
        return { ...state, shift: state.shift - 1 }
      case 'ArrowDown':
        if (state.shift == MAX_SHIFT_INDEX) {
          if (state.row == MAX_ROW_INDEX) return state
          return { ...state, row: state.row + 1, shift: 0 }
        }
        return { ...state, shift: state.shift + 1 }
      case 'ArrowLeft':
        if (state.col == 0) return state
        return { ...state, col: state.col - 1 }
      case 'ArrowRight':
        return { ...state, col: state.col + 1 }
    }
    break;
    case 'click':
      return {...state,...action.cell}
    default:
      console.log('?',action)
      return state
  }}
}

const FocusDispatchContext=createContext()
function MainTable() {
  const { data:config } = useQuery({queryKey:['gridconfig'], queryFn:genericFetch, suspense: true })
  const reducer=useMemo(()=>makeGridMovementReducer(config.names.length),[config.names.length])
  const [focusLocation, dispatch] = useReducer(reducer, { row: 0, col: 0, shift: 0 })
  const rows = config.names
  const cols = config.dates
  const keyDown = useCallback(e => {
    switch (e.key) {
      case 'ArrowUp':
      case 'ArrowDown':
      case 'ArrowLeft':
      case 'ArrowRight':
        e.preventDefault()
        dispatch({type:'keypress',keyPressed:e.key})
        break;
      default:
        break;
    }
  })
  const headrow = <tr><th>First</th>{cols.map(x => <th key={x}>{x}</th>)}</tr>
  const tblrows = rows.map((r, rowNo) => 
    <tr key={r}>
        <th>{r}</th>
        {cols.map((x, i) => 
          <TableCell 
            highlightShift={(focusLocation.row==rowNo&&focusLocation.col==i)?focusLocation.shift:-1}
            rowNo={rowNo} 
            colNo={i} 
            key={x} 
            name={r} 
            date={x} />)}
      </tr>)
  return <FocusDispatchContext.Provider value={dispatch}>
    <div className='bottom-panel' style={{ overflow: 'auto' }}>
    <table onKeyDown={keyDown} tabIndex={0} className={mainTableCSS}>
      <thead>{headrow}</thead>
      <tbody>{tblrows}</tbody>
    </table></div></FocusDispatchContext.Provider>
}

function ConstraintDialog(props){
  const {data:localconfig}=useLocalConfig()
  const constraintShown=localconfig.configEdit
  
}

function Component(props) {
  const {setQueryData,data:localconfig}=useLocalConfig()
  return <>
    <div><select value={localconfig?.duty} onChange={
        (e)=>{setQueryData(old=>({...old,duty:e.target.value}))}}>
      <option value={'ICU'}>ICU</option>
      <option value={'Th'}>Theatre</option>
      </select></div>
    <Suspense fallback={<span>Loading...</span>}>
      <div className={containerCSS}>
        <div></div>
        <MainTable />
      </div>
    </Suspense>
  </>
}


export {Component }