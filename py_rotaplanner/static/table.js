document.addEventListener('DOMContentLoaded',()=>{
    const table=document.getElementById("rota-table")
    table.addEventListener('dragstart',e=>{
        e.dataTransfer.setData('text/plain',e.target.id)
        console.log('dragging',e.target)
    })
    table.addEventListener('dragend',e=>{
        document.querySelectorAll('.activitycell').forEach(cell=>{
            cell.classList.remove('dragover')
        })
    })
    document.querySelectorAll('.activitycell').forEach(cell=>{
        cell.addEventListener('dragover',e=>{
            e.preventDefault()
        })
        cell.addEventListener('dragenter',e=>{
            cell.classList.add('dragover')
        })
        cell.addEventListener('dragleave',e=>{
            cell.classList.remove('dragover')
        })})
        
    table.addEventListener('drop',e=>{
        console.log('attempt to drop ',e.dataTransfer.getData('text/plain'),'into',e.target.id)
        const droptarget=e.target
        const activity=document.getElementById(e.dataTransfer.getData('text/plain'))
        console.log(droptarget,activity)
        const newdiv=document.createElement('div')
        newdiv.classList.add('spinner')
        droptarget.appendChild(newdiv)
        setTimeout(()=>{
            droptarget.removeChild(newdiv)
            droptarget.appendChild(activity)},2000)
    })
})