<script>
export default {
    name: 'MainTable',
    data() { },
    props: ['rows', 'cols'],
    computed: {
        style() {
            const styleString = `grid-template-columns: repeat(${this.cols}, auto);grid-template-rows: repeat(${this.rows}, auto);`
            console.log('style', styleString)
            return styleString
            }
        },
    mounted() { 
        this.$el.addEventListener('dragenter', (e) => {

            if (event.dataTransfer.types.includes('application/x-activity')) {
                //dragged item is an activity
                event.target.classList.add('dragover-activity')
                event.preventDefault()
            } else if (event.dataTransfer.types.includes('application/x-name')) {
                //dragged item is a name
                event.target.classList.add('dragover-name')
                event.preventDefault()
            }
        }
        )
        this.$el.addEventListener("dragleave",
            (event) => {
                console.log('dragleave', event.target)
                event.target.classList.remove('dragover-activity')
                event.target.classList.remove('dragover-name')
            }
        )
        this.$el.addEventListener("dragover",
            (event) => {
                if (event.dataTransfer.types.includes('application/x-activity')) {
                    event.preventDefault()

                }
                else if (event.dataTransfer.types.includes('application/x-name') && event.target.closest('.activity')) {
                    event.preventDefault()
                }
            }
        )
        this.$el.addEventListener("drop", (event) => {
            event.target.classList.remove('dragover-activity')
            event.target.classList.remove('dragover-name')
            let dropData, draggedData, dragType
            if (event.dataTransfer.types.includes('application/x-activity')) {
                dropData = event.target.dataset
                draggedData = JSON.parse(event.dataTransfer.getData('application/x-activity'))
                dragType = 'activity'
            } else if (event.dataTransfer.types.includes('application/x-name')) {
                dropData = event.target.closest('.activity')?.dataset
                if (!dropData) return
                draggedData = JSON.parse(event.dataTransfer.getData('application/x-name'))
                dragType = 'name'
            } else return

            event.preventDefault()
            console.log('drop', event)

            event.target.dispatchEvent(new CustomEvent('drop_done', {
                bubbles: true,
                detail: {
                    source_row: draggedData.row,
                    dragged_item: draggedData.item,
                    dest_row: dropData.row,
                    dest_col: dropData.col,
                    mode: draggedData.mode,
                    dragType: dragType
                }
            }
            ))
        }

        )
        this.$el.addEventListener("dragstart",
            (e) => {
                console.log('dragstart', e)
                let mode
                if (e.ctrlKey) {
                    mode = 'copy'
                } else {
                    mode = 'move'
                }
                if (e.target.matches('.activity')) {
                    console.log('activity', e.target.dataset)
                    e.dataTransfer.setData('application/x-activity', JSON.stringify({ mode, ...e.target.dataset }))
                } else if (e.target.matches('.activity-name')) {
                    console.log('name', e.target.dataset)
                    e.dataTransfer.setData('application/x-name', JSON.stringify({ mode, ...e.target.dataset }))
                } else {
                    console.warn('unidentified target', e.target)
                    return
                }
                //e.preventDefault()

            }

        )
    }
}   
</script>

<template>
    <div class="table-container" :style="style">
        <slot></slot>    
    </div>
</template>

<style>
.table-container {
    width: 100%;
    height: 100%;
    overflow: auto;
    border: 1px solid #ccc;
    border-radius: 4px;
    display:grid;
    grid-auto-flow: column;
}
</style>