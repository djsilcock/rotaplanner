
import { For, Index, Show, Switch, Match, createSignal, createEffect, createResource } from 'solid-js'
import { addDays } from 'date-fns'
import '../maintable.css'
import { RuleGroup } from './common'
import { CheckDates } from './common'
import { RulesContext } from './common'
import backend from '../backend'


function fetchTemplateList([date]) {
    console.log(arguments)
    if (!date) return [[], [], [], [], [], [], []]
    return backend.get_demand_templates_for_week(date.toISOString().slice(0, 10))
}

function fetchTemplates() {
    return backend.get_demand_templates()
}

function updateDemandTemplate(template) {
    backend.update_demand_template(template)
        .then(result => {
            if (result.errors) {
                alert(result.errors.join(','))
            }
        })
}

export default function TemplateEditor() {
    const [date, setDate] = createSignal()
    const [templateList, { refetch }] = createResource(fetchTemplates)
    const [templatesWeek] = createResource(() => [date(), templateList()], fetchTemplateList)
    createEffect(() => console.log(templateList()))
    createEffect(() => setDate(new Date()))
    return <Show when={templateList()} fallback='...'>
        <For each={templateList().templates}>
            {(template) => <div><a href="" onClick={(e) => { e.preventDefault(); backend.edit_template(template.id).then(() => refetch()) }}>{template.name}</a>
            </div>}
        </For>
        <a href="" onClick={(e) => { e.preventDefault(); backend.new_template().then(() => refetch()).then(() => alert('hello')) }}>(add new...)</a>
        <hr />
        <table style={{ 'font-size': '50%', 'width': '100%' }}>
            <tbody>
                <tr>
                    <For each={Array.from({ length: 7 }, (_, i) => addDays(new Date(), i))}>
                        {(day) => console.log(day) || <td style={{ border: '1px solid black' }}>{day?.toISOString().slice(0, 10)}</td>}
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




function ActivityTypeMenu(props) {
    return <ul style={{ 'list-style-type': 'none' }}>
        <For each={Object.entries(props.activities)}>
            {([key, value]) => <Switch>
                <Match when={typeof value == 'string'}>
                    <li><label><input type='radio' name='activitytype' value={key} onChange={e => e.target.checked && props.onChange(e.target.value)} checked={props.value == key} /> {value} ({JSON.stringify(props.value == key)})</label></li>
                </Match>
                <Match when={typeof value == 'object'}>
                    <li><details open={findDeep(props.value, value)}>
                        <summary>{key}</summary>
                        <div>
                            <ActivityTypeMenu activities={value} value={props.value} onChange={props.onChange} />
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
    createEffect(()=>{
        backend.get_demand_template()
        .then(result=>{
            setRules(result.rules)
            setActivityType(result.activity_type)
            setName(result.name)
            setStart(result.start)
            setFinish(result.finish)
        })
    })



    return <div>
        <h4>Edit activity</h4>
        <div class='template-editor-settings'>
            <div>Activity name: <input value={name()} onChange={e => setName(e.target.value)} /></div>
            Valid when day 1 is between <input type='date' />  and <input type='date' />
            <hr />
            This activity occurs:
            <RulesContext.Provider value={{ rules, setRules }}>
                <RuleGroup rule={rules().root} />
            </RulesContext.Provider>
            <ActivityTypeMenu activities={activityTypes} value={activityType()} templateId={null} onChange={setActivityType} />
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
            <CheckDates rules={rules()} />
        </div>
        <button onClick={() => { saveTemplate(); dialog.close() }}>Save</button>
        <button onClick={() => { props.refetch(); dialog.close() }}>Cancel</button>
        <div style={{ 'flex-grow': 1 }} />
    </div>
}

