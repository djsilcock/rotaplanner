import { createVirtualizer } from '@tanstack/solid-virtual';
import {For,Show,createSignal,createMemo,createEffect,onCleanup,createComputed, Match} from 'solid-js'
import {Paper} from '@suid/material'
import { Button, Menu, MenuItem,ToggleButton,ToggleButtonGroup} from "@suid/material";
import './table.css'
import {createQuery,QueryClientProvider,QueryClient,useQueryClient} from '@tanstack/solid-query'
import * as batshit from "@yornaath/batshit";


const batcher = batshit.create({
    name: 'activities',
    fetcher: async (ids) => {
      console.log(ids)
      return fetch('/api/activities/assignments',{method:'post',headers:{'content-type':'application/json'},body:JSON.stringify({dates:ids})}).then(r=>r.json())},
    scheduler:batshit.windowScheduler(100),
    resolver: batshit.indexedResolver(),
  });


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
  return ['andy','brian','charlie','davie']
  return fetch('/api/scheduling/names').then(r=>r.json())
}

async function activitiesQuery({queryKey}){
  return []
  return batcher.fetch(queryKey[1])
}


function getDateFromIndex(i){
  const d=new Date(2024,0,1);
  d.setDate(i);
  return d.toISOString().slice(0,10)}

export default function Table(){
  const client=useQueryClient()

  async function updateActivities(key,activity,mode){
    fetch(`/api/scheduling/${mode}_activity`,{method:'post',body:JSON.stringify({key,activity}),headers:{'content-type':'application/json'}})
    .then(v=>v.json())
    .then(v=>{
      client.invalidateQueries({queryKey:['assigned_items']})
    })
  }
  
  

  const [displayMode,setDisplayMode]=createSignal('staff')
  
  const [visibleDates,setVisibleDates]=createSignal({start:'2000-01-01',finish:'2000-03-01'})

  const registerParent=(el)=>{
    return
    let timeout
    function datesetter(){
      clearTimeout(timeout)
      timeout=setTimeout(()=>setVisibleDates({start:document.elementFromPoint(el.getBoundingClientRect().left+1,el.getBoundingClientRect().top+1).dataset['xindex'],
        finish:document.elementFromPoint(el.getBoundingClientRect().right-1,el.getBoundingClientRect().top+1).dataset['xindex']}),200)
    }
    
    el.addEventListener('scroll',datesetter)
    const mo=new MutationObserver(datesetter)
    mo.observe(el,{childList:true,subtree:true})
    datesetter()
  }
  return (
    <div>
      {/* The scrollable element for your list */}
    <div><ToggleButtonGroup
  color="primary"
  value={displayMode()}
  size='small'
  sx={{padding:'5px'}}
  exclusive
  onChange={(e,val)=>{if (val!=null) setDisplayMode(val)}}
  aria-label="mode"
>
  <ToggleButton value="activity">By Activity</ToggleButton>
  <ToggleButton value="staff">By Staff</ToggleButton>

</ToggleButtonGroup></div>

      <Switch>
        <Match when={displayMode()=='staff'}>
          <TableByStaff registerParent={registerParent} visibleDates={visibleDates}/>
        </Match>
        <Match when={displayMode()=='activity'}>
          <TableByActivity visibleDates={visibleDates}/>
        </Match>
      </Switch>
      </div>
      
  )
}

function TableByStaff(props){
  const client=useQueryClient()
  const namesquery=createQuery(()=>({
    queryKey:['names'],
    queryFn:getNames
  }))
  
  const [selectionBox,setSelectionBox]=createSignal(null)
  const [anchorEl,setAnchorEl]=createSignal(null)
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

  function limit(element,{initialX,currentX,initialY,currentY}){
    const {left,right,top,bottom}=element.getBoundingClientRect()
    const _x1=Math.min(initialX,currentX),_x2=Math.max(initialX,currentX)
    const _y1=Math.min(initialY,currentY),_y2=Math.max(initialY,currentY)
    if (_x1>right || _x2<left || _y1>bottom || _y2<top) return null
    return {
      x1: Math.floor(Math.max(left,_x1)),
      x2: Math.floor(Math.min(right,_x2)),
      y1: Math.floor(Math.max(top,_y1)),
      y2: Math.floor(Math.min(bottom,_y2))
    }
  }
  function mousehandler(el){
    let interval
    let scrolldelta=0
    let initialX=null
    let initialY=null
    let currentX=null
    let currentY=null
    let initialXRelative=null
    let initialYRelative=null
    let dragbox=null
  el.addEventListener('pointermove',e=>{
    if (e.buttons&1){
      if (!dragbox){
        el.setPointerCapture(1)
        dragbox=document.body.appendChild(document.createElement('div'))
        dragbox.classList.add('dragbox')
        console.log(dragbox)
        interval=setInterval(()=>{
          if (scrolldelta){
          el.scrollBy(scrolldelta,0)
        }},100)
        initialXRelative=e.clientX-el.getBoundingClientRect().left+el.scrollLeft
        initialYRelative=e.clientY-el.getBoundingClientRect().top +el.scrollTop
              
    }
    if (!!dragbox){
      scrolldelta=0
      let bcr=el.getBoundingClientRect()
      initialX=initialXRelative+bcr.left-el.scrollLeft
      initialY=initialYRelative+bcr.top -el.scrollTop
      currentX=e.clientX
      currentY=e.clientY
      let coords=limit(el,{currentX,currentY,initialX,initialY})
      dragbox.style.left=`${coords.x1}px`
      dragbox.style.top=`${coords.y1}px`
      dragbox.style.width=`${coords.x2-coords.x1}px`
      dragbox.style.height=`${coords.y2-coords.y1}px`
      if (e.clientX>bcr.right){
        scrolldelta=e.clientX-bcr.right
        }
      if (e.clientX<bcr.left){
        scrolldelta=e.clientX-bcr.left
      }
    }
  }})
  el.addEventListener('lostpointercapture',e=>{
    //document.body.removeChild(dragbox)
    dragbox=null
    clearInterval(interval)
    const allCells=document.querySelectorAll('.tablecell')
    allCells.forEach(el=>{
      console.log(el.getBoundingClientRect())
      if (!!limit(el,{currentX,currentY,initialX,initialY})) el.classList+=' selected'
      })
  })
  }

  const possibleActivities=createMemo(()=>{
    return [[],[]]
    
    if (x1==null) return [[],[]]
    const date=new Date(x1)
    const available_sets=[]
    const allocated_sets=[]
    const cached_data={}
    for (let [key,data] of client.getQueriesData({queryKey:['activities']})){
      Object.assign(cached_data,{[key[1]]:data})
    }
    console.log({cached_data})
    for (let i=date.getDate();date.toISOString().slice(0,10)<=x2;date.setDate(i++)){
      let today=cached_data[date.toISOString().slice(0,10)]??[]
      for (let staff of namesquery.data.slice(y1,y2+1)){
          allocated_sets.push(new Set(today.filter(activity=>activity.staff_assignments.find(assn=>assn.staff.name==name))))
        }
          available_sets.push(new Set(today.map(a=>a.name)))
      }
    
    const avail_set=Array.from(available_sets.length>1?available_sets.reduce((prev,cur)=>prev.intersection(cur)):available_sets[0]??[])
    const alloc_set=Array.from(allocated_sets.length>1?allocated_sets.reduce((prev,cur)=>prev.union(cur)):allocated_sets[0]??[])
    console.log({avail_set})
    return [avail_set,alloc_set]
})

  return <><Menu
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
</Menu><div id='table' style="position:relative;display:grid;grid-auto-rows:3rem;width:100vw;grid-template-columns:auto 1fr;">
  <For each={namesquery.data??[]}>
    {(n,i)=><div
     class="tablecell namecell"
     style={{
            width:'100px',
            'grid-row':i()+2,
            'grid-column':1,
          }}>{n}</div>
        }</For>
  
    
    <div
      use:mousehandler
      style={{
        'display':'grid',
        'grid-row':`1 / span ${namesquery.data?.length + 2}`,
        'grid-column':2,
        'grid-template-rows':'subgrid',
        'grid-auto-columns':'minmax(5rem,auto)',
        'overflow-x':'scroll',
        'overflow-y':'clip'
      }}
      class="container"
      //ref={props.registerParent}
      onContextMenu={(e)=>{e.preventDefault();
        setCoordsFromElement(e.target,true)
        showMenu(null,e.target);}}
    >
      <For each={Array.from({length:1000},(_,i)=>({key:getDateFromIndex(i),index:i}))}>
        {(virtualColumn) => {
          const query=createQuery(()=>({
            queryKey:['activities',virtualColumn.key],
            queryFn:activitiesQuery,
            //enabled:virtualColumn.key>=props.visibleDates().start && virtualColumn.key<=props.visibleDates().finish,
            enabled:false,
            staleTime:500,
          }))
      
          return <>
          
          <div
          key={[virtualColumn.key,'date']}
          data-xindex={virtualColumn.key}
          class="tablecell"
          style={{
            'grid-column': virtualColumn.index+1,
            'grid-row':1
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
            tablecell:true}}
            style={{
            'grid-column':virtualColumn.index+1,
            'grid-row':i()+2
          }}
        > <Switch>
          <Match when={query.error}>⚠️</Match>
          <Match when={query.isPending}><div class="spinner"></div></Match>
          <Match when={true}>
          <For each={query.data?.filter(activity=>activity.staff_assignments.find(assn=>assn.staff.name==name))} fallback="">{i=><div>{i}</div>}</For>
          </Match>
          </Switch>
        </div>}</For></>
      }}</For>
    </div>
  </div>
  </>
}

function TableByActivity(props){
  
  const [anchorEl,setAnchorEl]=createSignal(null)
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
  
  
  return <><div id='table' style="position:relative;display:grid;grid-auto-rows:3rem;width:100vw;grid-template-columns:auto 1fr;">
  <For each={[1,2,3]}>
    {(n,i)=><div
     class="tablecell namecell"
     style={{
            width:'100px',
            'grid-row':i()+2,
            'grid-column':1,
          }}>{n}</div>
        }</For>
  
    
    <div
      style={{
        'display':'grid',
        'grid-row':`1 / span ${namesquery.data?.length + 2}`,
        'grid-column':2,
        'grid-template-rows':'subgrid',
        'grid-auto-columns':'minmax(5rem,auto)',
        'overflow-x':'scroll',
        'overflow-y':'clip'
      }}
      class="container"
      ref={props.registerParent}
      onContextMenu={(e)=>{e.preventDefault();
        setCoordsFromElement(e.target,true)
        showMenu(null,e.target);}}
    >
      <For each={Array.from({length:1000},(_,i)=>({key:getDateFromIndex(i),index:i}))}>
        {(virtualColumn) => {
          const query=createQuery(()=>({
            queryKey:['activities',virtualColumn.key],
            queryFn:activitiesQuery,
            enabled:virtualColumn.key>=props.visibleDates().start && virtualColumn.key<=props.visibleDates().finish,
            staleTime:500,
          }))
      
          return <>
          
          <div
          key={[virtualColumn.key,'date']}
          data-xindex={virtualColumn.key}
          class="tablecell"
          style={{
            'grid-column': virtualColumn.index+1,
            'grid-row':1
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
          class='tablecell'
          style={{
            'grid-column':virtualColumn.index+1,
            'grid-row':i()+2
          }}
        > <Switch>
          <Match when={query.error}>⚠️</Match>
          <Match when={query.isPending}><div class="spinner"></div></Match>
          <Match when={true}>
          <For each={query.data?.filter(activity=>true)} fallback="">{i=><div>{i}</div>}</For>
          </Match>
          </Switch>
        </div>}</For></>
      }}</For>
    </div>
  </div>
  </>
}