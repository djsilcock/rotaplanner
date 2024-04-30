
import { For, Index, Show, Switch, Match, createSignal, createEffect, createContext, useContext, createMemo, createResource, Suspense } from 'solid-js'

import { addDays, addWeeks, differenceInCalendarDays, differenceInCalendarMonths, startOfWeek, parseISO, setMonth, setYear, startOfMonth } from 'date-fns'
import './maintable.css'
import { RuleGroup,RulesContext,dateMatches } from './common'

const staff = ['fred', 'barney', 'wilma', 'betty']
const availableDuties = ['Theatre', 'ICU', 'Non clinical', 'Zero', 'Leave']
const ruleClasses = {
    EN: () => ({ ruleType: "EN", frequency: 1, interval: "week" }),
    ENWM: () => ({ ruleType: "ENWM", weekNo: 1, monthFrequency: 1 })
}



function EditElement(props) {
    const duties = () => props.templateContent[props.cell]
    function setDuty(idx, splice, newduty) {
        props.editTemplateContent((old) => {
            const newduties = []
            let prevduty = { finishTime: 0 }
            let currentduty
            for (let duty of (old ?? []).toSpliced(idx, splice, newduty)) {
                currentduty = { ...duty, gapStart: prevduty.finishTime }
                prevduty.gapFinish = duty.startTime
                newduties.push(currentduty)
                prevduty = currentduty
            }
            currentduty.gapFinish = 24
            return newduties
        })
    }
    return <div title={JSON.stringify(duties())}>
        <div style={{ 'font-size': '25%' }}>{props.cell}</div>
        <For each={duties()} fallback={<DutyCell duty={{ placeholder: true, gapStart: 0, gapFinish: 24 }} setDuty={(newduty) => setDuty(0, 0, newduty)} />}>
            {(duty, idx) => <>
                <Show when={idx() == 0 && duty.startTime > 0}>
                    <DutyCell duty={{ placeholder: true, gapStart: 0, gapFinish: duty.startTime }} setDuty={(newduty) => setDuty(0, 0, newduty)} />
                </Show>
                <DutyCell duty={duty} setDuty={newduty => setDuty(idx(), 1, newduty)} />
                <Show when={duty.finishTime != duty.gapFinish}>
                    <DutyCell duty={{ placeholder: true, gapStart: duty.finishTime, gapFinish: duty.gapFinish }} setDuty={(newduty) => setDuty(idx() + 1, 0, newduty)} />
                </Show></>}
        </For></div>

}
function DutyCell(props) {
    let dialog
    const checkboxes = {}
    let startref, finishref
    function saveDuty() {
        props.setDuty({
            startTime: Number(startref.value),
            finishTime: Number(finishref.value),
            locations: availableDuties.filter(d => checkboxes[d].checked),
            gapStart: props.duty.gapStart,
            gapFinish: props.duty.gapFinish
        })
        dialog.close()
    }
    
    const [allowedActivities, setAllowedActivities] = createSignal({})
    const [start,setStart]=createSignal(0)
    const [finish,setFinish]=createSignal(0)
    const activityTree=createMemo(()=>{
        const buildTree=(node)=>{
            return{
                name:node.name,
                children:[
                    ...node.children.map(buildTree),
                    ...activities.filter((activity)=>(activity.type==node.name)),

                ]
            }
        }
        return activityTypes.map(buildTree)
    })
    createEffect(()=>{
        setStart(props.duty.startTime)
        setFinish(props.duty.finishTime)
    })
    createEffect(()=>console.log({start:start(),finish:finish()}))
    return <>
        <div style={{ cursor: 'pointer' }} onClick={() => dialog.showModal()}>
            <Switch>
                <Match when={props.duty.placeholder}>
                    Add +
                </Match>
                <Match when={!props.duty.placeholder}>
                    {(props.duty.startTime + 8) % 24}-{(props.duty.finishTime + 8) % 24}:{props.duty.locations.join(',')}
                </Match>
            </Switch>

        </div>
        <dialog ref={dialog}>
            <DemandActivityMenu activities={activityTree()} start={start()} finish={finish()} value={allowedActivities()} setValue={setAllowedActivities} />
            Start:<select ref={startref} onChange={e=>{setStart(e.target.value)}} value={props.duty.startTime}>
                <For each={Array(25)}>
                    {(hr, i) => <option disabled={i() < props.duty.gapStart || i() > props.duty.gapFinish} value={i()}>{String((i() + 8) % 24).padStart(2, '0')}</option>}
                </For>
            </select>
            Finish:<select ref={finishref} value={props.duty.finishTime} onChange={e=>{setFinish(e.target.value)}}>
                <For each={Array(25)}>
                    {(hr, i) => <option disabled={i() < props.duty.gapStart || i() > props.duty.gapFinish} value={i()}>{String((i() + 8) % 24).padStart(2, '0')}</option>}
                </For>
            </select>
            <h4>Acceptable duties</h4>
            <For each={availableDuties}>
                {(duty) => <div><input ref={checkboxes[duty]} type="checkbox" checked={props.duty?.locations?.includes(duty)} />{duty}</div>}
            </For>
            <button type="button" onClick={saveDuty}>ok</button>
            <button type="button" onClick={() => { props.setDuty(); dialog.close() }}>Delete</button>
            <button type="button" onClick={() => dialog.close()}>Close</button>
        </dialog>
    </>
}

const activityTypes = [
    {
        name: 'Clinical',
        children: [
            {
                name: 'Theatres',
                children: [
                    {
                        name: 'Urology',
                        children: []
                    },
                    {
                        name: 'General Surgery',
                        children: []
                    },
                    {
                        name: 'ENT',
                        children: []
                    },
                    {
                        name: 'OMFS',
                        children: []
                    }
                ]
            },
            {
                name: 'ICU',
                children: [
                    {
                        name: 'ICU Daytime',
                        children: []
                    }, {
                        name: 'ICU oncall',
                        children: []
                    }
                ]
            }
        ]
    }
]



const activities = [
    {
        name: 'Ms Reid AM',
        type: 'Urology',
        start: 8,
        finish: 13
    },
    {
        name: 'Mr Dunn AM',
        type: 'Urology',
        start: 8,
        finish: 13
    },
    {
        name: 'JDS PM',
        type: 'Urology',
        start: 13,
        finish: 18
    },
    {
        name: 'Ms Nesbitt AM',
        type: 'General Surgery',
        start: 8,
        finish: 13
    },
    {
        name: 'Mr Anderson AM',
        type: 'General Surgery',
        start: 13,
        finish: 18
    }
]

function DemandActivityMenu(props) {

    
    function setAllChildren(tree, value) {
        const newState = {}
        for (let [key, branch] of Object.entries(tree)) {
            switch (branch.type) {
                case 'activity':
                    newState[key] = value
                    break
                case 'category':
                    Object.assign(newState, setAllChildren(branch.children, value))

            }
        }
        console.log(tree, value, newState)
        return newState
    }

    return <ul style={{ 'list-style-type': 'none' }}>
        <For each={props.activities}>
            {(activity) => <Switch>
                <Match when={activity.type}>
                    <li><label>
                        <input 
                            type='checkbox' 
                            value={activity.name} 
                            onChange={e => props.setValue(old => ({ ...old, [activity.name]: e.target.checked }))} 
                            checked={props.value[activity.name]} 
                            disabled={activity.start<props.start||activity.finish>props.finish}/> 
                        {activity.name} ({activity.start}-{activity.finish})
            
                        </label></li>
                </Match>
                <Match when={activity.children}>
                    <li><details>
                        <summary>
                            <input
                                type='checkbox'
                                indeterminate={someAreTrue(props.value, activity.children) && someAreFalse(props.value, activity.children)}
                                checked={!someAreFalse(props.value, activity.children)}
                                onChange={(e) => props.setValue(old => ({ ...old, ...setAllChildren(activity.children, e.target.checked) }))}
                            />
                            {activity.name}
                        </summary>
                        <div>
                            <DemandActivityMenu activities={activity.children} start={props.start} finish={props.finish} value={props.value} setValue={props.setValue} />
                        </div>
                    </details></li>
                </Match>
            </Switch>
            }
        </For>
    </ul>

}

function someAreTrue(selected, tree) {
    if (typeof tree == 'undefined') return false

    for (let [key, value] of Object.entries(tree)) {
        switch (typeof value) {
            case 'string':
                if (selected[key]) return true
                break
            case 'object':
                if (someAreTrue(selected, value)) {
                    return true
                }
        }
    }
    return false
}
function someAreFalse(selected, tree) {
    if (typeof tree == 'undefined') return false

    for (let [key, value] of Object.entries(tree)) {
        switch (typeof value) {
            case 'string':
                if (!selected[key]) return true
                break
            case 'object':
                if (someAreFalse(selected, value)) {
                    return true
                }
        }
    }
    return false
}



export default function TemplateEditor() {
    const [templateList, { mutate, refetch }] = createResource(fetchTemplates, { initialValue: { default: fakeEditTemplateApiResponse, templates: [] } })
    return <Suspense>
        <For each={templateList().templates}>
            {(template, i) => <div>
                <EditTemplateDialog
                    template={template}
                    mutate={fxn => mutate(old => ({ ...old, templates: old.templates.toSpliced(i(), 1, fxn(old.templates[i()])) }))}
                    refetch={refetch} />
            </div>}
        </For>
        <EditTemplateDialog template={templateList().default} mutate={fxn => mutate(old => ({ ...old, default: fxn(old.default) }))} refetch={refetch} />
    </Suspense>
}


const fakeEditTemplateApiResponse = {
    id: null,
    name: 'Untitled',
    appliesToStaff: Object.fromEntries(staff.map(x => [x, false])),
    templates: [1, 2, 3, 4, 5, 6, 7].map(() => Math.random().toString(36).slice(2)),
    templateContent: {},
    rules: { root: { ruleId: 'root', ruleType: 'group', groupType: 'and', rules: [] } }
}

function fetchTemplates(signal, options) {
    console.log(options)
    if (options.refetching) return fetch('/api/updateTemplates', { method: 'POST', body: JSON.stringify(options.refetching) }).then(r => r.json())

    return fetch('/api/getTemplates').then(r => r.json())
}



export function EditTemplateDialog(props) {
    const [appliesToStaff, setAppliesToStaff] = createSignal({})
    const [templates, editTemplates] = createSignal([])

    const [templateContent, editTemplateContent] = createSignal({})
    const [rules, setRules] = createSignal({ root: { ruleId: 'root', ruleType: 'group', groupType: 'and', rules: [] } })
    const setRule = (ruleId, newRule) => setRules((old) => ({ ...old, [ruleId]: newRule }))
    const [name, setName] = createSignal('Untitled')

    createEffect(() => {
        console.log(props.template)
        setAppliesToStaff(props.template.appliesToStaff)
        editTemplates(props.template.templates)
        editTemplateContent(props.template.templateContent)
        setRules(props.template.rules)
        setName(props.template.name)
    })

    function saveTemplate() {
        props.refetch({
            appliesToStaff: appliesToStaff(),
            templates: templates(),
            templateContent: templateContent(),
            rules: rules(),
            name: name(),
            id: props.template.id
        })
    }




    let dialog

    const weeklyTemplate = createMemo(() => {
        const days = [...templates()]
        const chunks = []
        while (days.length > 0) {
            chunks.push(days.splice(0, 7))
        }
        return chunks
    })

    function doStaffChange(id) {
        const staffAffected = {}
        document.querySelectorAll(`#${id} input`).forEach(el => { console.log(el); staffAffected[el.value] = el.checked })
        setAppliesToStaff(staffAffected)
        console.log(staffAffected)
    }
    function addRowAbove() {
        const newRow = [1, 2, 3, 4, 5, 6, 7].map(() => Math.random().toString(36).slice(2))
        editTemplates((old) => ([...newRow, ...old]))

    }
    function addRowBelow() {
        const newRow = [1, 2, 3, 4, 5, 6, 7].map(() => Math.random().toString(36).slice(2))
        editTemplates(old => ([...old, ...newRow]))
    }
    function deleteRow(idx) {
        editTemplates(old => old.length == 1 ? [1, 2, 3, 4, 5, 6, 7].map(() => Math.random().toString(36).slice(2)) : old.toSpliced(idx() * 7, 7))
    }
    const [cal, setCal] = createSignal(new Date())
    return <div style={{ display: 'flex', 'width': '100vw' }}>
        <div style={{ 'flex-grow': '1' }}>&nbsp;</div>
        <Suspense fallback='...'>
            <Switch>
                <Match when={props.template.id == null}>
                    <a href="" onClick={(e) => { e.preventDefault(); dialog.showModal() }}>(add new...)</a>
                </Match>
                <Match when={props.template.id != null}>
                    <a href="" onClick={(e) => { e.preventDefault(); dialog.showModal() }}>{name()}</a>
                </Match>
            </Switch>
            <dialog ref={dialog}>
                <h4>Template Editor</h4>
                <div class='template-editor-settings'>
                    <div>Description: <input value={name()} onChange={e => setName(e.target.value)} /></div>
                    <details id={props.template.id ?? 'newtemplate'}>
                        <summary>
                            Applies to: {staff.filter(sn => (appliesToStaff()[sn])).join(',') || '(none)'}
                        </summary>
                        <For each={staff}>
                            {sm => <div><input type="checkbox" value={sm} onClick={(e) => { doStaffChange(props.template.id ?? 'newtemplate') }} checked={appliesToStaff()[sm]} />{sm}</div>}
                        </For>
                    </details>
                    Valid when day 1 is between <input type='date' />  and <input type='date' />
                    <hr />
                    This template is valid when:
                    <RulesContext.Provider value={{ rules, setRule, templates: templates }}>
                        <RuleGroup ruleId='root' />
                    </RulesContext.Provider>

                    <select valuex={cal().getMonth()} onChange={(e) => setCal(old => setMonth(old, Number(e.target.value)))}>
                        <option value="0">Jan</option>
                        <option value="1">Feb</option>
                        <option value="2">Mar</option>
                        <option value="3">Apr</option>
                        <option value="4">May</option>
                        <option value="5">Jun</option>
                        <option value="6">Jul</option>
                        <option value="7">Aug</option>
                        <option value="8">Sep</option>
                        <option value="9">Oct</option>
                        <option value="10">Nov</option>
                        <option value="11">Dec</option>
                    </select>
                    <input type='number' value={cal().getFullYear()} onChange={(e) => setCal((old) => setYear(old, e.target.value))} />
                    <table style={{ border: '1px solid black', 'border-collapse': 'collapse', 'text-align': 'center' }}>
                        <thead>
                            <tr>
                                <th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th>
                            </tr>
                        </thead>
                        <For each={[0, 1, 2, 3, 4, 5].map(i => addWeeks(startOfWeek(startOfMonth(cal())), i))}>
                            {weekStart =>
                                <tr>
                                    <For each={[0, 1, 2, 3, 4, 5, 6].map(i => addDays(weekStart, i))}>
                                        {day => <td style={
                                            {
                                                border: '1px solid black',
                                                padding: '2px',
                                                color: dateMatches(day, 'root', rules, templates) ? 'black' : 'gray',
                                                'text-decoration': dateMatches(day, 'root', rules, templates) ? 'none' : 'line-through'
                                            }}>{day.getDate()}</td>}
                                    </For>
                                </tr>}
                        </For>
                    </table>
                </div>
                <span title={JSON.stringify(templates())}>hover</span>
                <TemplateGrid templates={templates()} templateContent={templateContent()} editTemplates={editTemplates} editTemplateContent={editTemplateContent} />
                <button onClick={() => { saveTemplate(); dialog.close() }}>Save</button>
                <button onClick={() => { props.refetch(); dialog.close() }}>Cancel</button>
            </dialog></Suspense>
        <div style={{ 'flex-grow': 1 }} />
    </div>
}

export function TemplateGrid(props) {

    const weeklyTemplate = createMemo(() => {
        const days = [...props.templates]
        const chunks = []
        while (days.length > 0) {
            chunks.push(days.splice(0, 7))
        }
        return chunks
    })

    function addRowAbove() {
        console.log('add above')
        const newRow = [1, 2, 3, 4, 5, 6, 7].map(() => Math.random().toString(36).slice(2))
        props.editTemplates((old) => ([...newRow, ...old]))

    }
    function addRowBelow() {
        console.log('add below')
        const newRow = [1, 2, 3, 4, 5, 6, 7].map(() => Math.random().toString(36).slice(2))
        props.editTemplates(old => ([...old, ...newRow]))
    }
    function deleteRow(idx) {
        props.editTemplates(old => old.length == 1 ? [1, 2, 3, 4, 5, 6, 7].map(() => Math.random().toString(36).slice(2)) : old.toSpliced(idx() * 7, 7))
    }
    return <table class="main-table template">
        <tbody>
            <Show when={props.templates.length > 0}>
                <tr>
                    <td class="addrow" colspan={8}>
                        <button type="button" onClick={addRowAbove}>➕ Add row</button>
                    </td>
                </tr>
            </Show>
            <For each={weeklyTemplate()}>
                {(row, weekNo) => (<tr>
                    <td><button onClick={() => deleteRow(weekNo)}>❌ Delete</button></td>
                    <For each={row}>
                        {(x) => <td>
                            <strong>Day {props.templates.indexOf(x) + 1}</strong>
                            <EditElement cell={x} templateContent={props.templateContent} editTemplateContent={f => props.editTemplateContent(x, f)} />
                        </td>}
                    </For>

                </tr>)}
            </For>
            <tr>
                <td class="addrow" colspan={8}>
                    <button type="button" onClick={addRowBelow}>➕ Add row</button>
                </td>
            </tr>
        </tbody>
    </table>
}

