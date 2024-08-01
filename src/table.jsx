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
  return fetch(`/api/scheduling/possible_activities?start=${queryKey[1]}&finish=${queryKey[2]}`).then(r=>r.json())
  return ['one','two','three']
}


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
    getItemKey:(i)=>({page:Math.floor(i/7),item:i%7,index:i})
  }))
  const client=useQueryClient()
  async function updateActivities(key,activity){
    fetch('/api/scheduling/add_activity',{method:'post',body:JSON.stringify({key,activity}),headers:{'content-type':'application/json'}})
    .then(v=>v.json())
    .then(v=>{
      client.invalidateQueries({queryKey:['assigned_items']})
    })
  }
  const [coords,setCoords]=createSignal(false)
  const [mouseIsDown,setMouseDown]=createSignal(false)
  const [menuVisible,setMenuVisible]=createSignal(false)
  const [anchorEl,setAnchorEl]=createSignal(null)
  createComputed(()=>console.log(anchorEl()))
  useClickOutside(()=>parentRef,()=>{if (!anchorEl()) setCoords(false)})
  const namesquery=createQuery(()=>({
    queryKey:['names'],
    queryFn:getNames
  }))
  const possibleActivitiesQueryKey=createMemo(()=>['possibleActivities',coords().x1??anchorEl()?.dataset?.xindex,coords().x2??anchorEl()?.dataset?.xindex])
  const possibleActivitiesQuery=createQuery(()=>({
    enabled:!!anchorEl(),
    queryKey:possibleActivitiesQueryKey(),
    queryFn:getPossibleActivities
  }))
  const setCoordsFromElement=(target)=>setCoords({
    x1:target.dataset.xindex,
    x2:target.dataset.xindex,
    y1:target.dataset.yindex,
    y2:target.dataset.yindex,
    x0:target.dataset.xindex,
    y0:target.dataset.yindex})
  let promiseFunction
  const showMenu=([_,x1,x2,y1,y2],target)=>{
    setAnchorEl(target)
    if (x1==null){
      setCoordsFromElement(target)
    }
    new Promise((res,rej)=>{
      promiseFunction=res
    }).then(item=>{
      updateActivities([x1,x2],item)
    }).then(()=>setAnchorEl(null))
  }
  return (
    <div ref={parentRef}>  <Menu
    id="basic-menu"
    anchorEl={anchorEl()}
    open={!!anchorEl()}
    onClose={()=>{setAnchorEl(null)}}
    MenuListProps={{ "aria-labelledby": "basic-button" }}
  >
    <For each={possibleActivitiesQuery.data}>{item=>
    <MenuItem onClick={(e)=>{e.stopPropagation();promiseFunction?.(item)}}>{item}</MenuItem>
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
            if (e.buttons==1 && !mouseIsDown()){
            setCoordsFromElement(e.target)
            setMouseDown(true)
            }}}
          onMouseOver={(e)=>{if (mouseIsDown()&&e.target.dataset.xindex) {
            setCoordsFromElement(e.target)
            }}}
          onMouseUp={(e)=>{setMouseDown(false)}}
          onContextMenu={(e)=>{e.preventDefault();
            setCoordsFromElement(e.target)
            showMenu(possibleActivitiesQueryKey(),e.target);}}
          
        >
          {/* Only the visible items in the virtualizer, manually positioned to be in view */}
          <For each={rowVirtualizer.getVirtualItems()}>
            {(virtualColumn) => {
              const query=createQuery(()=>({
                queryKey:['assigned_items',virtualColumn.key.page],
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
              {query.data?.[virtualColumn.key.item]?.date}
            </div>
              <For each={namesquery.data}>{(name,i)=> <div
              key={[virtualColumn.key,name]}
              data-xindex={virtualColumn.key.index}
              data-yindex={i()}
              tabIndex={-1}
              title={JSON.stringify(virtualColumn.key)}
              classList={{
                tablecell:true,
                selected:coords()!=false && (virtualColumn.key.index>=coords().x1 && virtualColumn.key.index<=coords().x2 && i()>=coords().y1 && i()<=coords().y2)}}
              style={{
                width: `${virtualColumn.size}px`,
                transform: `translate(${virtualColumn.start}px,${i()*3+3}rem)`,
              }}
            >
              <For each={query.data?.[virtualColumn.key.item]?.[name]}>{i=><div>{i}</div>}</For>
            </div>}</For></>
          }}</For>
        </div>
      </div>
      </div>
    </div>
  )
}
