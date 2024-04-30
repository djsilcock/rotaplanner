
import { For, Index, Show, Switch, Match, createSignal, createEffect, createContext, useContext,createResource,children } from 'solid-js'
import { addDays, addWeeks, differenceInCalendarDays, differenceInCalendarMonths, startOfWeek, parseISO, setMonth, setYear, startOfMonth } from 'date-fns'
import '../maintable.css'

const staff = ['fred', 'barney', 'wilma', 'betty']
const availableDuties = ['Theatre', 'ICU', 'Non clinical', 'Zero', 'Leave']
const ruleClasses = {
    en: () => ({ ruleType: "en", frequency: 1, interval: "week" }),
    enwm: () => ({ ruleType: "enwm" })
}
function getOrdinalSuffix(num) {
    if (num % 100 > 10 && num % 100 < 20) return 'th'
    if (num % 10 == 1) return 'st'
    if (num % 10 == 2) return 'nd'
    if (num % 10 == 3) return 'rd'
    return 'th'
}


function EditElement(props) {
    const duties = () => props.templateContent()[props.cell]
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
    return <div>
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
            Start:<select ref={startref} value={props.duty.startTime}>
                <For each={Array(25)}>
                    {(hr, i) => <option disabled={i() < props.duty.gapStart || i() > props.duty.gapFinish} value={i()}>{String((i() + 8) % 24).padStart(2, '0')}</option>}
                </For>
            </select>
            Finish:<select ref={finishref} value={props.duty.finishTime}>
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

function getRuleDescription(rule) {
    if (!rule) return "no rule here"
    let displayText = ""
    const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    const anchorDate = new Date(rule.anchorDate)
    switch (rule.ruleType) {
        case 'en':
            switch (rule.interval) {
                case "day":
                    displayText += "every"
                    displayText += (rule.frequency == 1) ? 'day' : `${rule.frequency}${getOrdinalSuffix(rule.frequency)} day`
                    break
                case "week":
                    displayText += "every "
                    displayText += (rule.frequency == 1) ? '' : `${rule.frequency}${getOrdinalSuffix(rule.frequency)} `
                    displayText += weekdays[anchorDate.getDay()]
                    break
                case "month":
                    displayText += "the "
                    displayText += `${anchorDate.getDate()}${getOrdinalSuffix(anchorDate.getDate())}`
                    displayText += ` of every `
                    displayText += (rule.frequency == 1) ? 'month' : `${rule.frequency}${getOrdinalSuffix(rule.frequency)} month`
            }
            displayText += ` from ${rule.anchorDate}`
            return displayText

        case 'enwm':
            {
                const d = new Date(rule.anchorDate)
                const wkday = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][d.getDay()]
                const weekno = Math.floor(d.getDate() / 7) + 1
                return `${displayText} the ${weekno}${getOrdinalSuffix(weekno)} ${wkday} of every ${rule.frequency == 1 ? " " : `${rule.frequency}${getOrdinalSuffix(rule.frequency)}`} month starting ${rule.anchorDate}`
            }

    }
}
const RulesContext = createContext()

function RuleGroup(props) {
    const { rules, setRules } = useContext(RulesContext)
    const [editingRuleId, setEditingRuleId] = createSignal(null)
    let dialog, editRuleCallback, cancelEditRule
    createEffect(()=>console.log(rules()))

    function editRule(newRule) {
        console.log(newRule)
        const parentId = props.rule.ruleId
        setRules(state => {
            const newState = { ...state }
            if (newRule.ruleId == null) {
                newRule.ruleId = Math.random().toString(36).slice(2)
                newState[parentId] = {
                    ...state[parentId],
                    rules: [...state[parentId].rules, newRule.ruleId]
                }
            }
            newState[newRule.ruleId] = {...newRule}
            console.log(newState)
            return newState
        })
    }

    function deleteRule(ruleId) {
        setRules(old => ({ ...old, [ruleId]: undefined }))
    }

    function addGroup() {
        const newGroupId = Math.random().toString(36).slice(2)
        const parentId = props.ruleId
        setRules(state => {
            const newState = {}
            newState[parentId] = {
                ...state[parentId],
                rules: [...state[parentId].rules, newGroupId]
            }
            newState[newGroupId] = { ruleType: 'group', groupType: 'and', ruleId: newGroupId, rules: [] }
            return newState
        })
    }


    return <div class='rule-group'>
        <select value={props.rule.groupType}
            onChange={(e) => setRules(state => (
                {
                    ...state,
                    [props.rule.ruleId]: {
                        ...state[props.rule.ruleId],
                        groupType: e.target.value
                    }
                }))}>
            <option value='or'>any of</option>
            <option value='and'>all of</option>
            <option value='not'>none of</option>
        </select>
        <ul style={{ 'margin-block-start': '2px', 'list-style-type': 'none' }}>
            <For each={props.rule.rules}>
                {(ruleId) => {
                    const rule = ()=>rules()[ruleId]
                    return <Switch fallback={JSON.stringify(rule())}>
                        <Match when={typeof rule() == 'undefined'} >Eh?</Match>
                        <Match when={rule().ruleType == 'group'}>
                            <li>
                                <button
                                    type='button'
                                    onClick={() => deleteRule(ruleId)}
                                    style={{ 'font-size': '50%' }}>
                                    X
                                </button>
                                group
                                <RuleGroup rule={rule()} />
                            </li>
                        </Match>
                        <Match when={true}>
                            <li>
                                <button type='button' onClick={() => deleteRule(ruleId)} style={{ 'font-size': '50%' }}>X</button>
                                <RuleDialog rule={rule()} onSubmit={editRule}>
                                    {dialog => <a href="" onClick={(e) => { e.preventDefault(); dialog.showModal() }}>
                                        {() => getRuleDescription(rule())}
                                    </a>}
                                </RuleDialog>
                            </li>
                        </Match>
                    </Switch>
                }}
            </For>
            <li>
                <RuleDialog rule={{ ruleId: null }}>
                    {dialog => <button type='button' onClick={() => dialog.showModal()} style={{ 'font-size': '50%' }}>Add rule</button>}

                </RuleDialog>
                <button type='button' onClick={addGroup} style={{ 'font-size': '50%' }}>Add group</button>
            </li>
        </ul>

    </div>
}

function RuleDialog(props) {
    const [rule, setRule] = createSignal(Object.assign({}, ruleClasses.enwm(), ruleClasses.en()))
    createEffect(() => reset())
    function reset() {
        if (!props.rule.ruleId) {
            setRule({
                anchorDate: (new Date()).toISOString().slice(0, 10),
                ...ruleClasses.enwm(),
                ...ruleClasses.en()
            })
            return
        }
        setRule({ ...props.rule })
    }
    const display = children(() => props.children)
    let dialog
    return <>
        <dialog ref={dialog}>
            Rule type: <select
                value={rule().ruleType}
                onChange={(e) => { setRule((oldrule) => ({ ...oldrule, ruleType: e.target.value })) }}>
                <option value="">Select...</option>
                <option value="en">Every nth day/week/month</option>
                <option value="enwm">Every nth week of month</option>
            </select>
            <hr />
            {() => getRuleDescription(rule())}

            <div>
                <input type='hidden' name='id' value={rule.id} />
                <Switch>
                    <Match when={rule().ruleType == "en"}>
                        <table>
                            <tbody>
                                <Show when={props.templates}>
                                <tr><td>Template day</td>
                                <td>
                                    <select value={rule().templateDay} onChange={(e) => { setRule((old) => ({ ...old, templateDay: e.target.value })) }} >
                                        <For each={props.templates}>
                                            {(templateId, idx) => <option value={templateId}>Day {idx() + 1}</option>}
                                        </For>

                                    </select>
                                </td></tr>
                                </Show>
                                <tr>
                                    <td>Interval</td>
                                    <td><input
                                        type="number"
                                        name="frequency"
                                        value={rule().frequency}
                                        max={100}
                                        min={1}
                                        style={{ width: '3em' }}
                                        onChange={(e) => { setRule((old) => ({ ...old, frequency: e.target.value })) }} />
                                    </td>
                                </tr>
                                <tr>
                                    <td>Interval type</td><td><select name="interval" value={rule().interval} onChange={e => setRule(old => ({ ...old, interval: e.target.value }))}>
                                        <option value='day'>day</option>
                                        <option value='week'>week</option>
                                        <option value='month'>month</option>
                                    </select>
                                    </td></tr>
                                <tr><td>Start date</td>
                                    <td><input type="date" name="anchor_date" value={rule().anchorDate} onChange={e => setRule((old) => ({ ...old, anchorDate: e.target.value }))} />
                                    </td></tr>
                            </tbody>
                        </table>

                        <hr />
                    </Match>
                    <Match when={() => rule().ruleType == "enwm"}>
                        <table>
                            <tbody>
                                <tr>
                                    <td>Interval</td>
                                    <td>
                                        <select
                                            value={() => rule().frequency}
                                            name="month_frequency"
                                            onChange={e => setRule((old) => ({ ...old, frequency: e.target.value }))}>
                                            <Index each={Array(12)}>
                                                {(x, i) => <option value={i + 1}>{(i == 0 ? "every month " : `every ${i + 1}${getOrdinalSuffix(i + 1)} month`)}</option>}
                                            </Index>
                                        </select>
                                    </td>
                                </tr>
                                <tr><td>Start date</td>
                                    <td><input type="date" name="anchor_date" value={rule().anchorDate} onChange={e => setRule((old) => ({ ...old, anchorDate: e.target.value }))} />
                                    </td></tr>
                            </tbody>
                        </table>

                    </Match>

                </Switch>
            </div>
            <button onClick={() => { props.onSubmit(rule()); dialog.close() }}>OK</button>
            <button onClick={() => { reset(); dialog.close() }}>Close</button>

        </dialog>
        {display()(dialog)}
    </>
}

function fetchTemplateList([date]) {
    console.log(arguments)
    if (!date) return [[], [], [], [], [], [], []]
    return fetch('/api/getDemandTemplatesForWeek?date=' + date.toISOString().slice(0, 10)).then(r => r.json())
}
export default function TemplateEditor() {
    const [date, setDate] = createSignal()
    const [templateList, { refetch }] = createResource(fetchTemplates)
    const [templatesWeek] = createResource(() => [date(), templateList()], fetchTemplateList)
    createEffect(() => console.log(templateList()))
    createEffect(() => setDate(new Date()))
    return <Show when={templateList()} fallback='...'>
        <For each={templateList().templates}>
            {(template) => <div>
                <EditTemplateDialog
                    template={template}
                    refetch={refetch} />
            </div>}
        </For>
        <EditTemplateDialog template={templateList()?.default} refetch={refetch} />
        <hr />
        <table style={{'font-size':'50%','width':'100%'}}>
            <tbody>
                <tr>
                    <For each={Array.from({ length: 7 }, (_, i) => addDays(new Date(), i))}>
                        {(day) => console.log(day) || <td style={{border:'1px solid black'}}>{day?.toISOString().slice(0, 10)}</td>}
                    </For>
                </tr>
                <tr>
                    <For each={templatesWeek()}>
                        {i => <td><For each={i}>{t => <div>{t.name} ({t.start}-{t.finish})</div>}</For></td>}
                    </For>
                </tr>
            </tbody>
        </table>
    </Show>
}


function fetchTemplates() {
    return fetch('/api/getDemandTemplates').then(r => r.json())
}

function updateDemandTemplate(template) {
    return fetch('/api/updateDemandTemplates', { method: 'POST', body: JSON.stringify(template) }).then(r => r.json())
}

function ActivityTypeMenu(props) {
    return <ul style={{ 'list-style-type': 'none' }}>
        <For each={Object.entries(props.activities)}>
            {([key, value]) => <Switch>
                <Match when={typeof value == 'string'}>
                    <li><label><input type='radio' name={`${props.templateId}-activitytype`} value={key} onChange={e => e.target.checked && props.onChange(e.target.value)} checked={props.value == key} /> {value} ({JSON.stringify(props.value == key)})</label></li>
                </Match>
                <Match when={typeof value == 'object'}>
                    <li><details open={findDeep(props.value, value)}>
                        <summary>{key}</summary>
                        <div>
                            <ActivityTypeMenu activities={value} templateId={props.templateId} value={props.value} onChange={props.onChange} />
                        </div>
                    </details></li>
                </Match>
            </Switch>
            }
        </For>
    </ul>

}

function findDeep(target, object) {
    if (typeof object == 'undefined') return false

    for (let [key, value] of Object.entries(object)) {
        switch (typeof value) {
            case 'string':
                if (key == target) return true
                break
            case 'object':
                if (findDeep(target, value)) {
                    return true
                }
        }
    }
    return false
}

const activityTypes = {
    'Clinical': {
        'Theatres': {
            urology: 'Urology',
            gensurg: 'General Surgery',
            maxfax: 'OMFS',
            ent: 'enT'
        },
        'ICU': {
            daytime: 'ICU daytime',
            icuOC: 'ICU oncall'
        },
        'Clinic': {
            poac: 'Preassessment Clinic'
        }
    },
    'Non-Clinical': {
        admin: 'Admin',
        'Leave': {
            al: 'Annual Leave',
            sl: 'Study Leave',
            to: 'Time owed'
        }
    }
}

export function EditTemplateDialog(props) {
    const [rules, setRules] = createSignal({ root: { ruleId: 'root', ruleType: 'group', groupType: 'and', rules: [] } })

    const [activityType, setActivityType] = createSignal()
    const [name, setName] = createSignal('Untitled')
    const [start, setStart] = createSignal(8)
    const [finish, setFinish] = createSignal(17)

    createEffect(() => reset())

    function reset() {
        setRules(props.template.rules)
        setName(props.template.name)
        setActivityType(props.template.activityType)
    }

    async function saveTemplate() {
        const payload = {
            rules: rules(),
            name: name(),
            id: props.template.id,
            activityType: activityType(),
            start: start(),
            finish: finish()
        }
        console.log(payload)
        await updateDemandTemplate(payload)
        props.refetch()
    }

    let dialog



    return <div style={{ display: 'flex', 'width': '100vw' }}>
        <div style={{ 'flex-grow': '1' }}>&nbsp;</div>
        <Show when={props.template}>
            <Switch>
                <Match when={props.template.id == null}>
                    <a href="" onClick={(e) => { e.preventDefault(); dialog.showModal() }}>(add new...)</a>
                </Match>
                <Match when={props.template.id != null}>
                    <a href="" onClick={(e) => { e.preventDefault(); dialog.showModal() }}>{name()}</a>
                </Match>
            </Switch>
            <dialog ref={dialog} style={{ 'text-align': 'left', 'margin-left': '1em' }}>
                <h4>Edit activity</h4>
                <div class='template-editor-settings'>
                    <div>Activity name: <input value={name()} onChange={e => setName(e.target.value)} /></div>
                    Valid when day 1 is between <input type='date' />  and <input type='date' />
                    <hr />
                    This activity occurs:
                    <RulesContext.Provider value={{ rules, setRules }}>
                        <RuleGroup rule={rules().root} />
                    </RulesContext.Provider>
                    <ActivityTypeMenu activities={activityTypes} value={activityType()} templateId={props.template.id} onChange={setActivityType} />
                    <hr />
                    <table>
                        <tbody>
                            <tr>
                                <td>Start time</td>
                                <td>
                                    <select onChange={e => setStart(e.target.value)} value={start()}>
                                        <Index each={Array.from({ length: 36 })}>
                                            {(x, index) => <option value={index} disabled={index > finish()}>
                                                {index % 24}:00 <Show when={index > 23}>(+1)</Show>
                                            </option>}
                                        </Index>
                                    </select>
                                </td>
                            </tr>
                            <tr>
                                <td>Finish time</td>
                                <td>
                                    <select onChange={e => setFinish(e.target.value)} value={finish()}>
                                        <Index each={Array.from({ length: 36 })}>
                                            {(x, index) => <option value={index} disabled={index < start()}>
                                                {index % 24}:00 <Show when={index > 23}>(+1)</Show></option>}
                                        </Index>
                                    </select>
                                </td>
                            </tr>


                        </tbody>
                    </table>
                    <hr />
                    <CheckDates rules={rules()}/>
                </div>
                <button onClick={() => { saveTemplate(); dialog.close() }}>Save</button>
                <button onClick={() => { props.refetch(); dialog.close() }}>Cancel</button>
            </dialog>
        </Show>
        <div style={{ 'flex-grow': 1 }} />
    </div>
}

function CheckDates(props){
    const [cal, setCal] = createSignal(new Date())
    
    return <details>
    <summary>Check dates...</summary>

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
                                color: dateMatches(day, 'root', props.rules) ? 'black' : 'gray',
                                'text-decoration': dateMatches(day, 'root', props.rules) ? 'none' : 'line-through'
                            }}>{day.getDate()}</td>}
                    </For>
                </tr>}
        </For>
    </table>
</details>
}

function dateMatches(date, ruleId, rules, valueIfNull) {
    const rule = rules()[ruleId]
    if (typeof rule == 'undefined') return valueIfNull
    if (typeof date == 'string') return dateMatches(parseISO(date), ruleId, rules)
    const anchorDate = parseISO(rule.anchorDate ?? '')
    let result
    switch (rule.ruleType) {
        case 'group':
            switch (rule.groupType) {
                case 'and':
                    result = rule.rules.every(item => dateMatches(date, item, rules, true))
                    break
                case 'or':
                    result = rule.rules.some(item => dateMatches(date, item, rules, false))
                    break
                case 'not':
                    result = !rule.rules.some(item => dateMatches(date, item, rules, false))
                    break
                default:
                    console.error(rule.groupType)
                    throw 'bad rule'
            }
            break
        case 'en':
            switch (rule.interval) {
                case 'month':
                    if (date.getDate() != anchorDate.getDate()) return false
                    result = (differenceInCalendarMonths(date, anchorDate) % rule.frequency == 0)
                    break
                case 'week':
                    result = (differenceInCalendarDays(date, anchorDate) % (rule.frequency * 7) == 0)
                    break
                case 'day':
                    result(differenceInCalendarDays(date, anchorDate) % rule.frequency) == 0
                    break
                default:
                    throw 'bad rule'
            }
            break
        case 'enwm':
            if (date.getDay() != anchorDate.getDay()) return false
            if (Math.floor((date.getDate() - 1) / 7) != Math.floor((anchorDate.getDate() - 1) / 7)) return false
            result = (differenceInCalendarMonths(date, anchorDate) % rule.frequency == 0)
    }
    return result
}