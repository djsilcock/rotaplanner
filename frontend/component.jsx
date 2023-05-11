
import {createSlice,current} from "@reduxjs/toolkit"
import { useDispatch, useSelector } from "react-redux"
import {css,cx} from '@emotion/css'
import { useMemo, useState, useRef, useCallback, useEffect } from "react"

import useRemoteApi from './remoteApi'

function DutyButton({name,date,session,duties,rowNo,colNo}){
        const remoteApi=useRemoteApi()
        const dutylabel=dutylabels[duties?.[session]?.duty ?? '-']??{classname:'unallocated',label:duties?.[session]?.duty??'?'}
        const dutyflags=duties?.[session]?.flags ??{}
        const isFocussed=useSelector((state)=>(
          (state?.grid?.selected?.row==rowNo)&&
          (state?.grid?.selected?.column==colNo)))
        const dispatch=useDispatch()
        const onClick=useCallback(()=>{
          remoteApi.dutyClick({name,date,session})
          divRef.current.focus()
          dispatch(gridSlice.actions.setGridSelection({row:rowNo,column:colNo}))
        })
        useEffect(()=>{
          if (isFocussed){
            divRef.current.focus()
          }
        },[isFocussed])
        const divRef=useRef()
        const className=cx(dutyCSS,dutylabel.classname,isFocussed?'selected':'')
        return <div tabIndex={-1} ref={divRef} key={session} className={className} {...{onClick}}>
            {session}:{dutylabel.label}
            {dutyflags.confirmed?'🔒':''}{dutyflags.locum?'💷':''}
            </div>
}
function TableCell({name,date,rowNo,colNo}){
    const duties=useSelector(state=>state.grid.data[`${date}|${name}`])
    return <td title={JSON.stringify(duties)}>{['am','pm','oncall'].map((session,i)=><DutyButton rowNo={rowNo*3+i} colNo={colNo} name={name} date={date} session={session} duties={duties}/>)}</td>
}
const containerCSS=css`
  display:grid;
  grid-template-columns: 1fr;
  grid-template-rows:min-content 1fr;
  max-height: calc(100vh - 20px);
  max-width: 100vw;
  `
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

  const dutyCSS=css`
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
      color: #DDDDDD
    }

    `
  
  const dutylabels={
    '-':{classname:'unallocated',label:'-'},
    'ICU':{classname:'icu',label:'ICU'},
    'TH':{classname:'theatre',label:'Th'},
    'LEAVE':{classname:'unallocated',label:'Leave'}
}

function MainTable(props){
    const rows= useSelector(state=>state.grid.names)
    const cols= useSelector(state=>state.grid.dates)
    const dispatch=useDispatch()
    const keyDown=useCallback(e=>{
      switch (e.key) {
        case 'ArrowUp':
        case 'ArrowDown':
        case 'ArrowLeft':
        case 'ArrowRight':
          e.preventDefault()
          dispatch(gridSlice.actions.arrowKey(e.key))
          break;
        default:
          break;
      }
    })
    headrow=<tr><th>First</th>{cols.map(x=><th key={x}>{x}</th>)}</tr>
    tblrows=rows.map((r,rowNo)=><tr key={r}><th>{r}</th>{cols.map((x,i)=><TableCell rowNo={rowNo} colNo={i} key={x} name={r} date={x}/>)}</tr>)
    return <div  className='bottom-panel' style={{overflow:'auto'}}>
        <table onKeyDown={keyDown} tabIndex={0} className={mainTableCSS}>
            <thead>{headrow}</thead>
            <tbody>{tblrows}</tbody>
            </table></div>
}
function MessageBox(props){
  const row=useSelector((state)=>state.grid.selected.row)
  const col=useSelector((state)=>state.grid.selected.column)
  return <div><div>{row}</div><div>{col}</div></div>
  
}
function Component(props){
    const remoteApi=useRemoteApi()
    const [title,setTitle]=useState('Not Yet')
    window.setThis=(content)=>setTitle(content)
    
    return <>
    <div className={containerCSS}>
    <div><h1>{title}</h1>
    <a onClick={()=>{remoteApi.output('Hello!!')}}>Click me</a>
    </div>
    <MainTable/>
    </div>
    </>
}

const gridSlice=createSlice({
    name:'grid',
    initialState:{selected:{row:0,column:0},dates:[],names:[],grid:{}},
  reducers: {
    setGridSelection(state,action){
      state.selected=action.payload
    },
    arrowKey(state,{payload}){
      switch (payload) {
        case 'ArrowUp':
          state.selected.row=Math.max(state.selected.row-1,0)
          break
        case 'ArrowDown':
          state.selected.row=Math.min(state.selected.row+1,state.names.length*3-1)
          break
        case 'ArrowLeft':
          state.selected.column=Math.max(state.selected.column-1,0)
          break
        case 'ArrowRight':
          state.selected.column=Math.min(state.dates.length-1,state.selected.column+1)
          break
    }
  }},
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
  }
})

export {gridSlice,Component}