import { createVirtualizer } from '@tanstack/solid-virtual';
import {For,Show,createSignal,createMemo,createEffect,onCleanup} from 'solid-js'
import {Paper} from '@suid/material'
import './table.css'

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
const name=['Adam','Bob','Charlie','Derek']
export default function Table(){


  // The scrollable element for your list
  let parentRef

  // The virtualizer
  const rowVirtualizer = createVirtualizer({
    count: 10000,
    getScrollElement: () => parentRef,
    estimateSize: () => 50,
    horizontal:true,
    scrollMargin:100
  })
  const [coords,setCoords]=createSignal(false)
  const [mouseIsDown,setMouseDown]=createSignal(false)
  const [menuVisible,setMenuVisible]=createSignal(false)
  useClickOutside(()=>parentRef,()=>{setCoords(false)})
  const [menuRef,setMenuRef]=createSignal(null)
  useClickOutside((menuRef,()=>setMenuVisible(false)))
  
  return (
    <>
        <Show when={menuVisible()}>
            <div ref={setMenuRef} style={{
               left:`${menuVisible()[0]}px`,
                top:`${menuVisible()[1]}px`
               }}
                class="menu">
                    <div class='menuitem'>Menu</div>
                    </div>
        </Show>
      {/* The scrollable element for your list */}
      <div>
      <div style={{float:'left'}}><For each={name}>
        {(n,i)=><div
         class="table-container"
         style={{
                transform: `translateY(${i()*3}rem)`,
              }}>{n}</div>
            }</For></div>
      <div
        ref={parentRef}
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
          onMouseDown={(e)=>{
            e.stopPropagation()
            if (e.buttons==1){
            setCoords({
                x1:e.target.dataset.xindex,
                x2:e.target.dataset.xindex,
                y1:e.target.dataset.yindex,
                y2:e.target.dataset.yindex})
            setMouseDown(true)
            }}}
          onMouseOver={(e)=>{if (mouseIsDown()&&e.target.dataset.xindex) {
            setCoords(({x1,x2,y1,y2})=>({
                x1:Math.min(x1,e.target.dataset.xindex),
                x2:Math.max(x2,e.target.dataset.xindex),
                y1:Math.min(y1,e.target.dataset.yindex),
                y2:Math.max(y2,e.target.dataset.yindex)
            }))}}}
          onMouseUp={(e)=>{setMouseDown(false)}}
          onContextMenu={(e)=>{e.preventDefault();console.log(e);setMenuVisible([e.pageX,e.pageY])}}
          
        >
            
          {/* Only the visible items in the virtualizer, manually positioned to be in view */}
          <For each={rowVirtualizer.getVirtualItems()}>
            {(virtualColumn) => (
                <For each={name}>{(row,i)=> <div
              key={[virtualColumn.key,row]}
              data-xindex={virtualColumn.key}
              data-yindex={i()}
              tabIndex={-1}
              classList={{
                tablecell:true,
                selected:coords()!=false && (virtualColumn.key>=coords().x1 && virtualColumn.key<=coords().x2 && i()>=coords().y1 && i()<=coords().y2)}}
              style={{
                
                width: `${virtualColumn.size}px`,
                transform: `translate(${virtualColumn.start}px,${i()*3}rem)`,
              }}
              

            >
              Row {virtualColumn.index}
            </div>}</For>
          )}</For>
        </div>
      </div>
      </div>
    </>
  )
}
