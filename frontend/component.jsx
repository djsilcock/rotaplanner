/*eslint-disable react/prop-types */
import { cx } from '@emotion/css'
import { useMemo, useRef, useCallback, useEffect, Suspense, useReducer, createContext, useContext, memo } from "react"

import {useInView} from 'react-intersection-observer'
import {useQuery,useMutation,useQueryClient} from '@tanstack/react-query'
import useLocalConfig from "./localconfig"

import './component.css'

const genericFetch = async ({queryKey}) => {
  const fetchresult=await fetch(`/${queryKey.join('/')}`)
    return await fetchresult.json()
  }

const getDutySelector = (name, date,session) => {
  const cellid = `${date.toISOString().slice(0,10)}|${name}|${session}`
  //return (data)=>{console.log(data,cellid);return {duty:'ICU',flags:[]}}
  return (data)=>data?.[cellid]
}

const dutyCSS='duty',mainTableCSS='main-table',containerCSS='container'
function DutyButton({ name, date, session, rowNo, colNo, sessionNo,isFocussed}) {
  const selector = useMemo(() => getDutySelector(name, date,session))
  const { data:duty } = useQuery({queryKey:['data'], queryFn:genericFetch, select: selector,staleTime:3600000 })
  const dutylabel = dutylabels[duty?.duty ?? '-'] ?? { classname: 'unallocated', label: duty?.duty ?? '?' }
  const dutyflags = duty?.flags ?? {}
  const focusDispatch = useContext(FocusDispatchContext)
  const { data:localconfig}=useQuery({queryKey:['localconfig'],queryFn:()=>Promise.resolve({'duty':'ICU'}),staleTime:Infinity,cacheTime:Infinity,suspense:true})  
  const queryClient=useQueryClient()
  const {mutate}=useMutation({
    mutationFn:(vars)=>fetch('/click',{method:'POST',body:JSON.stringify(vars)}).then(r=>r.json()),
    onSettled:()=>queryClient.invalidateQueries({queryKey:['data']})})
  const onClick = useCallback(() => {
    mutate({ name, date:date.toISOString().slice(0,10), session,duty:localconfig.duty })
    divRef.current.focus()
    focusDispatch({type:'click',cell:{ row: rowNo, col: colNo,shift:sessionNo }})
  })
  useEffect(() => {
    if (isFocussed) {
      divRef.current.focus()
    }
  }, [isFocussed])
  const divRef = useRef()
  const className = `${dutyCSS} ${dutylabel.classname} ${isFocussed ? 'selected' : ''}`
  return <div tabIndex={-1} ref={divRef} title={JSON.stringify({name,date,session})} key={session} className={className} {...{ onClick }}>
    {session}:{dutylabel.label}
    {dutyflags.confirmed ? '🔒' : ''}{dutyflags.locum ? '💷' : ''}
  </div>
}

const TableCell=memo(function TableCell({ name, dateOffset, startDate,rowNo, colNo,highlightShift,isLast }) {
  const {inView,ref}=useInView()
  const dispatch=useContext(IntersectionDispatchContext)
  useEffect(()=>{
      dispatch({type:'trailerVisible',rowNo,colNo,inView})
  },[isLast,inView])
  return <td ref={ref}>
      {['am', 'pm', 'oncall'].map(
        (session, i) => 
          <DutyButton 
            key={i}
            isFocussed={highlightShift==i}
            rowNo={rowNo} 
            colNo={colNo}
            sessionNo={i} 
            name={name} 
            date={new Date(startDate.valueOf()+86400000*colNo)} 
            session={session} 
            />)}</td>
})

const dutylabels = {
  '-': { classname: 'unallocated', label: '-' },
  'ICU': { classname: 'icu', label: 'ICU' },
  'TH': { classname: 'theatre', label: 'Th' },
  'LEAVE': { classname: 'unallocated', label: 'Leave' }
}

function makeGridMovementReducer(MAX_ROW_INDEX) {
  return function gridMovementReducer(state, action) {
    const MAX_SHIFT_INDEX = 2
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
const IntersectionDispatchContext=createContext()
function TrailerColumnCell({length}){
  const {ref,inView}=useInView()
  const dispatch=useContext(IntersectionDispatchContext)
  useEffect(()=>{
    if (inView){
      setTimeout(()=>{
      dispatch({type:'trailer',minLength:length+1})
    },5)}
  },[inView,length])
  return <td ref={ref}>{inView}X</td>
}
function MainTable() {
  const { data:config } = useQuery({queryKey:['gridconfig'], queryFn:genericFetch, suspense: true })
  const reducer=useMemo(()=>makeGridMovementReducer(config.names.length),[config.names.length])
  const [focusLocation, dispatch] = useReducer(reducer, { row: 0, col: 0, shift: 0 })
  const rows = ['fred']//config.names
  const [{cols},intersectionDispatch]=useReducer((oldstate,a)=>{
    let state=oldstate
    if (a.type=='trailer'){
      if (state.cols.length<a.minLength || state.cols.length<state.knownMax){
        state={
          ...state,
          cols:[...state.cols,state.cols.length],
          rowmaps:[...state.rowmaps,new Map(rows.map((x,i)=>[i,undefined]))]}
    }}
    if (a.type=='trailerVisible'){
        if (a.colNo>state.knownMax){
        state.rowmaps[a.colNo].set(a.rowNo,a.inView)
        }
        if (a.inView) return state
        for (let i=state.rowmaps.length-1;i>state.knownMax;i--){

        for (let v of state.rowmaps[i].values()){
          if (v!==false) {
            return state}
        }
        state={...state,cols:state.cols.slice(0,i),rowmaps:state.rowmaps.slice(0,i)}
      }
        }
      
    return state
  },{
    knownMax:config.knownDays,
    cols:Array.from({ length:config.knownDays }, (v, i) => i),
    rowmaps:Array.from({ length: config.knownDays },()=>new Map(rows.map((x,i)=>[i,undefined]))),
    })
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

  const startDate=Date.parse(config.minDate)
  const headrow = <tr><th>First</th>{cols.map(x => <th key={x}>{new Date(startDate.valueOf()+86400000*x).toISOString().slice(0,10)}</th>)}<th></th></tr>
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
            dateOffset={x}
            startDate={startDate}
            />)}
        <TrailerColumnCell length={cols.length}/>
      </tr>)
  return <FocusDispatchContext.Provider value={dispatch}>
    <IntersectionDispatchContext.Provider value={intersectionDispatch}>
    <div className='bottom-panel' style={{ overflow: 'auto' }}>
    <table onKeyDown={keyDown} tabIndex={0} className={mainTableCSS}>
      <thead>{headrow}</thead>
      <tbody>{tblrows}</tbody>
    </table></div></IntersectionDispatchContext.Provider></FocusDispatchContext.Provider>
}

function ConstraintDialog(props){
  const {data:localconfig}=useLocalConfig()
  const constraintShown=localconfig.configEdit
  
}

function Component(props) {
  const {setConfig,data:localconfig}=useLocalConfig()
  return <>
    <div><select value={localconfig?.duty} onChange={
        (e)=>{setConfig(old=>({...old,duty:e.target.value}))}}>
      <option value={'ICU'}>ICU</option>
      <option value={'Th'}>Theatre</option>
      </select></div>
      <hr/>
    <Suspense fallback={<span>Loading...</span>}>
      <div className={containerCSS}>
        <div></div>
        <MainTable />
      </div>
    </Suspense>
  </>
} 


export {Component }