import { createVirtualizer } from '@tanstack/solid-virtual';
import {For,Show,createSignal,createMemo,createEffect,onCleanup,createComputed} from 'solid-js'
import {Paper} from '@suid/material'
import { Button, Menu, MenuItem } from "@suid/material";
import './table.css'
import {createQuery,QueryClientProvider,QueryClient,useQueryClient} from '@tanstack/solid-query'

const useClickOutside = (ref, callback) => {
    createEffect(() => {
      const listener = (event) => {
        const element = ref()
        if (!element || element.contains(event.target)) {
          return
        }
  
        callback(event)
      }
      document.addEventListener('click', listener)
  
      onCleanup(() => document.removeEventListener('click', listener))
    })
  }
async function getNames(){
  return fetch('/api/scheduling/names').then(r=>r.json())
}
async function activitiesQuery({queryKey}){
  return fetch(`/api/scheduling/assigned_activities?page=${queryKey[1]}`).then(r=>r.json())
}
async function getPossibleActivities({queryKey}){
  console.log(queryKey)
  return fetch(`/api/scheduling/possible_activities?start=${queryKey[1].x1}&finish=${queryKey[1].x2}`).then(r=>r.json())
  return ['one','two','three']
}

function getDateFromIndex(i){
  const d=new Date(2024,0,1);
  d.setDate(i);
  return d.toISOString().slice(0,10)}

export default function Table(){
  // The scrollable element for your list
  let parentRef
  
  // The virtualizer
  const rowVirtualizer = createVirtualizer(()=>({
    count: 10000,
    getScrollElement: () => parentRef,
    estimateSize: (i) => 50,
    horizontal:true,
    scrollMargin:100,
    getItemKey:getDateFromIndex
  }))
  const client=useQueryClient()
  async function updateActivities(key,activity,mode){
    fetch(`/api/scheduling/${mode}_activity`,{method:'post',body:JSON.stringify({key,activity}),headers:{'content-type':'application/json'}})
    .then(v=>v.json())
    .then(v=>{
      client.invalidateQueries({queryKey:['assigned_items']})
    })
  }
  const [rawcoords,setRawCoords]=createSignal({x0:null,y0:null,cx:null,cy:null})
  const derivedCoords=createMemo(()=>{
    const {x0,y0,cx,cy}=rawcoords()
    if (x0==null) return {x1:null,y1:null,x2:null,y2:null}
    return {x1:cx>x0 ? x0:cx,
    x2:cx>x0 ? cx:x0,
    y1:cy>y0 ? y0:cy,
    y2:cy>y0 ? cy:y0}
  })
  
  const [mouseIsDown,setMouseDown]=createSignal(false)
  const [anchorEl,setAnchorEl]=createSignal(null)
  //createComputed(()=>console.log(anchorEl()))
  //useClickOutside(()=>parentRef,()=>{if (!anchorEl()) setCoords(false)})
  const namesquery=createQuery(()=>({
    queryKey:['names'],
    queryFn:getNames
  }))
  //const possibleActivitiesQueryKey=createMemo(()=>['possibleActivities',coords()])
  const possibleActivities=createMemo(()=>{
    const {x1,x2,y1,y2}=derivedCoords()
    if (x1==null) return [[],[]]
    const date=new Date(x1)
    const available_sets=[]
    const allocated_sets=[]
    const cached_data={}
    for (let [key,data] of client.getQueriesData({queryKey:['assigned_items']})){
      console.log(key,data)
      Object.assign(cached_data,data)
    }
    for (let i=date.getDate();date.toISOString().slice(0,10)<=x2;date.setDate(i++)){
      let today=cached_data[date.toISOString().slice(0,10)]
      console.log({today,cached_data,date})
      for (let staff of namesquery.data.slice(y1,y2+1)){
        
          allocated_sets.push(new Set(today[staff]))
        }
          available_sets.push(new Set(today['']))
        
      }
    
    const avail_set=Array.from(available_sets.length>1?available_sets.reduce((prev,cur)=>prev.intersection(cur)):available_sets[0]??[])
    const alloc_set=Array.from(allocated_sets.length>1?allocated_sets.reduce((prev,cur)=>prev.union(cur)):allocated_sets[0]??[])
    console.log(available_sets,allocated_sets)
    return [avail_set,alloc_set]
})

  const setCoordsFromElement=(target,isDragging)=>{
    let {x0,y0}=rawcoords()
    if (!isDragging){
      x0=null
      y0=null
    }
    x0=x0??target.dataset.xindex
    y0=y0??target.dataset.yindex
    const cx=target.dataset.xindex,cy=target.dataset.yindex
    setRawCoords({x0,y0,cx,cy})
   
}
  let promiseFunction
  const showMenu=(coords,target)=>{
    setAnchorEl(target)
    setCoordsFromElement(target,true)
    new Promise((res,rej)=>{
      promiseFunction=res
    }).then(([item,mode])=>{
      updateActivities(coords,item,mode)
    }).then(()=>setAnchorEl(null))
  }
  createEffect(()=>console.log(parentRef))
  return (
    <div><Menu
    id="basic-menu"
    anchorEl={anchorEl()}
    open={!!anchorEl()}
    onClose={()=>{setAnchorEl(null)}}
    MenuListProps={{ "aria-labelledby": "basic-button" }}
  >
    <For each={possibleActivities()[0]}>{item=>
    <MenuItem 
      onClick={(e)=>{e.stopPropagation();promiseFunction?.([item,'add'])}}
      >Assign {item}</MenuItem>
    }</For>
    <For each={possibleActivities()[1]}>{item=>
    <MenuItem 
      onClick={(e)=>{e.stopPropagation();promiseFunction?.([item,'remove'])}}
      >Remove {item}</MenuItem>
    }</For>
  </Menu>
      {/* The scrollable element for your list */}
    
      <div>
      <div style={{float:'left'}}><For each={namesquery.data}>
        {(n,i)=><div
         class="table-container"
         style={{
                transform: `translateY(${i()*3+3}rem)`,
              }}>{n}</div>
            }</For></div>
      <div
        class="table"
        ref={parentRef}
      >
        
        
        {/* The large inner element to hold all of the items */}
        <div
          style={{
            width: `${rowVirtualizer.getTotalSize()}px`,
            height: '100%',
            position: 'relative',
          }}
          class="container"
          onMouseMove={(e)=>{
            e.stopPropagation()
            if (e.buttons==1 &&e.target.dataset.xindex){
            setCoordsFromElement(e.target,mouseIsDown())
            setMouseDown(true)
            }}}
          onNouseOver={(e)=>{if (mouseIsDown()&&e.target.dataset.xindex) {
            setCoordsFromElement(e.target)
            }}}
          onMouseUp={(e)=>{setMouseDown(false)}}
          onContextMenu={(e)=>{e.preventDefault();
            setCoordsFromElement(e.target,true)
            showMenu(derivedCoords(),e.target);}}
          
        >
          {/* Only the visible items in the virtualizer, manually positioned to be in view */}
          <For each={rowVirtualizer.getVirtualItems()}>
            {(virtualColumn) => {
              const query=createQuery(()=>({
                queryKey:['assigned_items',virtualColumn.key.slice(0,7)],
                queryFn:activitiesQuery,
                staleTime:500,
              }))
              return <>
              
              <div
              key={[virtualColumn.key,'date']}
              class="tablecell"
              style={{
                width: `${virtualColumn.size}px`,
                transform: `translate(${virtualColumn.start}px,0px)`,
              }}
            >
              {virtualColumn.key}
            </div>
              <For each={namesquery.data}>{(name,i)=> <div
              key={[virtualColumn.key,name]}
              data-xindex={virtualColumn.key}
              data-yindex={i()}
              tabIndex={-1}
              title={JSON.stringify(virtualColumn.key)}
              classList={{
                tablecell:true,
                selected:derivedCoords().x1!=false && (virtualColumn.key>=derivedCoords().x1 && virtualColumn.key<=derivedCoords().x2 && i()>=derivedCoords().y1 && i()<=derivedCoords().y2)}}
              style={{
                width: `${virtualColumn.size}px`,
                transform: `translate(${virtualColumn.start}px,${i()*3+3}rem)`,
              }}
            >
              <For each={query.data?.[virtualColumn.key]?.[name]} fallback="-">{i=><div>{i}</div>}</For>
            </div>}</For></>
          }}</For>
        </div>
      </div>
      </div>
    </div>
  )
}
