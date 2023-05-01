
import {createSlice,current} from "@reduxjs/toolkit"
import { useSelector } from "react-redux"
import {css,cx} from '@emotion/css'
import { useMemo, useState, useRef, useCallback } from "react"

import useRemoteApi from './remoteApi'

function DutyButton({name,date,session,duties}){
        const remoteApi=useRemoteApi()
        const dutylabel=dutylabels[duties?.[session]?.duty ?? '-']??{classname:unallocatedCSS,label:duties?.[session]?.duty??'?'}
        const dutyflags=duties?.[session]?.flags ??{}
        const onClick=useCallback(()=>{
          remoteApi.dutyClick({name,date,session})
          divRef.current.focus()
        })
        const onBlur=useCallback(()=>{
          console.log(`blurred ${name}${date}${session}`)
        })
        const onFocus=useCallback(()=>{console.log(`focussed ${name}${date}${session}`)})
        const divRef=useRef()
        
        return <div tabIndex={-1} ref={divRef} key={session} className={dutylabel.classname} {...{onClick,onBlur,onFocus}}>
            {session}:{dutylabel.label}
            {dutyflags.confirmed?'🔒':''}{dutyflags.locum?'💷':''}
            </div>
}
function TableCell({name,date}){
    const duties=useSelector(state=>state.grid.data[`${date}|${name}`])
    return <td title={JSON.stringify(duties)}>{['am','pm','oncall'].map(session=><DutyButton name={name} date={date} session={session} duties={duties}/>)}</td>
}

const mainTableCSS=css`
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

  const baseCSS=css`
    width:100%;
    &:hover {
      background-color: #EEEEFF
    }
    &:focus {
      background-color: #EEFFFF
    }
    `
  const icuCSS=cx(baseCSS,css`color: #0000DD;`)
  const theatreCSS=cx(baseCSS,css`color: #00DD00;`)
  const unallocatedCSS=cx(baseCSS,css`color: #DDDDDD;`)
  
  const dutylabels={
    '-':{classname:unallocatedCSS,label:'-'},
    'ICU':{classname:icuCSS,label:'ICU'},
    'TH':{classname:theatreCSS,label:'Th'},
    'LEAVE':{classname:unallocatedCSS,label:'Leave'}
}
console.log(dutylabels)
function MainTable(props){
    const rows= useSelector(state=>state.grid.names)
    const cols= useSelector(state=>state.grid.dates)
    headrow=<tr><th>First</th>{cols.map(x=><th key={x}>{x}</th>)}</tr>
    tblrows=rows.map(r=><tr><th>{r}</th>{cols.map(x=><TableCell key={x} name={r} date={x}/>)}</tr>)
    return <div className='bottom-panel'>
        <table className={mainTableCSS}>
            <thead>{headrow}</thead>
            <tbody>{tblrows}</tbody>
            </table></div>
}
function Component(props){
    const remoteApi=useRemoteApi()
    const [title,setTitle]=useState('Not Yet')
    window.setThis=(content)=>setTitle(content)
    return <>
    <div className='container'>
    <h1>{title}</h1>
    <a onClick={()=>{remoteApi.output('Hello!!')}}>Click me</a>
    
    <MainTable/>
    </div>
    </>
}

const gridSlice=createSlice({
    name:'grid',
    initialState:window.initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase('grid/setDuty', (state, action)=> {
        const {payload:{date,staff,session,duty}} = action
        if (!state.names.includes(staff)){
          state.names.push(staff)
          state.names.sort()
        }
        if (!state.dates.includes(date)){
          const parseDate=(dt)=>{const [y,m,d]=[...dt.split('-')];return new Date(y,Number(m)-1,d)}
          const minDate=parseDate((date<state.dates[0])?date:state.dates[0])
          const maxDate=parseDate((date>state.dates.slice(-1)[0])?date:state.dates.slice(-1)[0])
          state.dates=[]
          for (let d=minDate.valueOf();d<=maxDate.valueOf();d+=86400000){
            let thisDate=new Date(d)
            state.dates.push(thisDate.toISOString().slice(0,10))
          }
        }
        console.log(action)
        key=`${date}|${staff}`
        state.data[key]=state.data[key]??{}
        state.data[key][session]=state.data[key][session]??{}
        state.data[key][session].duty=duty
        console.log(current(state))
        }
      )
      .addCase('grid/setFlag', (state, action) => {
        const {payload:{date,staff,session,flags}}=action
        key=`${date}|${staff}`
        console.log(action)
        state.data[key]=state.data[key]??{}
        state.data[key][session]=state.data[key][session]??{}
        state.data[key][session].flags=state.data[key][session].flags??{}
        Object.assign(state.data[key][session].flags,flags)
        console.log(current(state))
        }
        
      )
      // You can chain calls, or have separate `builder.addCase()` lines each time
      .addCase('grid/replaceState', (_, {payload:newState}) => {
        console.log(newState)
        return newState
      })
      .addDefaultCase((state,action)=>{console.log({state,action})})
  },
})


export {gridSlice,Component}