document.addEventListener('DOMContentLoaded',()=>{
    const table=document.getElementById("rota-table")
    let draglimit=""
    table.addEventListener('dragstart',e=>{
        const payload=JSON.stringify({
            date:e.target.dataset.activitydate,
            activityId:e.target.dataset.activityid
        })
        e.dataTransfer.setData('text/plain',payload)
        draglimit=e.target.dataset.activitydate
        console.log('dragging',e.target,draglimit)
    })
    table.addEventListener('dragend',e=>{
        document.querySelectorAll('.activitycell').forEach(cell=>{
            cell.classList.remove('dragover')
            draglimit=""
        })
    })
    document.querySelectorAll('.activitycell').forEach(cell=>{
        cell.addEventListener('dragover',e=>{
            if (draglimit==cell.dataset.date) e.preventDefault()
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
        draglimit=""
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