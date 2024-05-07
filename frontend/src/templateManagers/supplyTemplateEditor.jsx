
import { For, Show, Switch, Match, createSignal, createEffect, createMemo, createResource, Suspense } from 'solid-js'

import { addDays, addWeeks, startOfWeek, setMonth, setYear, startOfMonth } from 'date-fns'
import '../maintable.css'
import { CheckDates, RuleGroup, RulesContext, dateMatches } from './common'

const staff = ['fred', 'barney', 'wilma', 'betty']
const availableDuties = ['Theatre', 'ICU', 'Non clinical', 'Zero', 'Leave']
const ruleClasses = {
    EN: () => ({ ruleType: "EN", frequency: 1, interval: "week" }),
    ENWM: () => ({ ruleType: "ENWM", weekNo: 1, monthFrequency: 1 })
}



function EditElement(props) {
    const duties = () => props.templateContent[props.cell]??[]
    function setDuty(idx, splice, newduty) {
        props.editTemplateContent((old) => (old ?? []).toSpliced(idx, splice, newduty))
    }
    
    return <div title={JSON.stringify({duties:duties(),cell:props.cell})}>
        <div style={{ 'font-size': '25%',padding:'4px' }}>{props.cell}</div>
        <For each={duties()} >
            {(duty, idx) => <DutyCell duty={duty} setDuty={newduty => setDuty(idx(), 1, newduty)} />
            }  
        </For>
        <DutyCell duty={null} setDuty={(newduty) => setDuty(duties().length, 0, newduty)} />
        </div>

}
function DutyCell(props) {
    let dialog
    const checkboxes = {}
    let startref, finishref
    function saveDuty() {
        props.setDuty({
            startTime: start(),
            finishTime: finish(),
            locations: Object.keys(allowedActivities()).filter(v=>allowedActivities()[v]),
        })
        dialog.close()
    }

    const [allowedActivities, setAllowedActivities] = createSignal({})
    const [start, setStart] = createSignal(0)
    const [finish, setFinish] = createSignal(0)
    const activityTree = createMemo(() => {
        const buildTree = (node) => {
            return {
                name: node.name,
                children: [
                    ...node.children.map(buildTree),
                    ...activities.filter((activity) => (activity.type == node.name)),

                ]
            }
        }
        return activityTypes.map(buildTree)
    })
    createEffect(() => {
        setStart(props.duty?.startTime ?? 8)
        setFinish(props.duty?.finishTime ?? 18)
    })
    return <>
        <div style={{ cursor: 'pointer'}} onClick={() => dialog.showModal()} title={JSON.stringify(props.duty)}>
            <Switch>
                <Match when={props.duty==null}>
                    <button style={{margin:'4px'}}>Add ➕</button>
                </Match>
                <Match when={props.duty}>
                    <div style={{ cursor: 'pointer',margin:'4px',border:'1px solid black',display:'grid','grid-template-columns':'1fr auto' }}>
                    <div>
                    <For each={props.duty.locations}>
                        {location=><div>{location}</div>}
                    </For>
                    </div>
                    <button>❌</button>
                    </div>
                </Match>
            </Switch>

        </div>
        <dialog ref={dialog}>
            <DemandActivityMenu activities={activityTree()} start={start()} finish={finish()} value={allowedActivities()} setValue={setAllowedActivities} />
            <hr />
            <fieldset>
                <legend>Filter activities</legend>
                Start:<select ref={startref} onChange={e => { setStart(e.target.value) }} value={start()}>
                    <For each={Array(25)}>
                        {(hr, i) => <option disabled={i()> finish()} value={i()}>{String(i()% 24).padStart(2, '0')}</option>}
                    </For>
                </select>
                Finish:<select ref={finishref} value={finish()} onChange={e => { setFinish(e.target.value) }}>
                    <For each={Array(25)}>
                        {(hr, i) => <option disabled={i()<start()} value={i()}>{String(i() % 24).padStart(2, '0')}</option>}
                    </For>
                </select>
            </fieldset>

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
        for (let branch of tree) {
            if (branch.type) {

                newState[branch.name] = value
            } else {
                Object.assign(newState, setAllChildren(branch.children, value))

            }
        }
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
                            disabled={activity.start < props.start || activity.finish > props.finish} />
                        {activity.name} ({activity.start}-{activity.finish})

                    </label></li>
                </Match>
                <Match when={activity.children && hasLeaf(activity.children)}>
                    <li><details>
                        <summary>
                            <input
                                type='checkbox'
                                indeterminate={someAreTrue(props.value, activity.children) && someAreFalse(props.value, activity.children)}
                                checked={!someAreFalse(props.value, activity.children)&&hasLeaf(activity.children)}
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

    for (let branch of tree) {
        if (branch.type) {
            if (selected[branch.name]) return true
        } else {
            if (someAreTrue(selected, branch.children)) {
                return true
                }
        }
    }
    return false
}
function someAreFalse(selected, tree) {
    if (typeof tree == 'undefined') return false

    for (let branch of tree) {
        if (branch.type) {
            if (!selected[branch.name]) return true
        } else {
            if (someAreFalse(selected, branch.children)) {
                return true
            }
        }
    }
    return false
}

function hasLeaf(tree) {
    if (typeof tree == 'undefined') return false

    for (let branch of tree) {
        if (branch.type) {
            return true
        } else {
            if (hasLeaf(branch.children)) {
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

    createEffect(()=>{
        console.log({templates:templates(),templateContent:templateContent()})
    })


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
                        <RuleGroup rule={rules().root} />
                    </RulesContext.Provider>

                    <CheckDates rules={rules}/>
                </div>
                
                <TemplateList templates={templates()} templateContent={templateContent()} editTemplates={editTemplates} editTemplateContent={editTemplateContent} />
                <button onClick={() => { saveTemplate(); dialog.close() }}>Save</button>
                <button onClick={() => { props.refetch(); dialog.close() }}>Cancel</button>
            </dialog></Suspense>
        <div style={{ 'flex-grow': 1 }} />
    </div>
}

export function TemplateList(props){
    function insertRow(idx){
        props.editTemplates(old=>old.toSpliced(idx,0,Math.random().toString(36).slice(2)))
    }
    function deleteRow(idx){
        props.editTemplates(old=>old.toSpliced(idx,1))
    }

    return <div class='supply-template-list'>

            <For each={props.templates}>
                {(x, dayNo) => [
                    <div style={{'align-content':'center'}}>
                        <div><strong>Day {dayNo() + 1}</strong></div>
                        <div><button onClick={() => deleteRow(dayNo())}>❌ Delete</button></div>
                        <div><button type="button" onClick={()=>insertRow(dayNo())}>➕ Add day</button></div>
                    </div>,
                    <div style={{border:'1px solid black'}}>
                            
                            <EditElement cell={x} templateContent={props.templateContent} editTemplateContent={f => props.editTemplateContent(old=>({...old,[x]:f(old[x])}))} />
                        </div>
                    

                ]}
            </For>
            
                <div class="addrow">
                    <button type="button" onClick={()=>insertRow(props.templates.length)}>➕ Add row</button>
                </div>
            
        
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

