
import { For, Index, Show, Switch, Match, createSignal, createEffect } from 'solid-js'
import { createStore, unwrap } from 'solid-js/store'
import './maintable.css'

const staff = ['fred', 'barney', 'wilma', 'betty']
const availableDuties = ['Theatre', 'ICU', 'Non clinical', 'Zero', 'Leave']
const ruleClasses = {
    EN: () => ({ ruleType: "EN", frequency: 1, interval: "week", anchorDate: '2022-01-01' }),
    ENM: () => ({ ruleType: "ENM", day: 1, monthFrequency: 1, anchorDate: '2022-01-01' }),
    ENWM: () => ({ ruleType: "ENWM", weekNo: 1, monthFrequency: 1, anchorDate: '2022-01-01' })
}
function getOrdinalSuffix(num) {
    if (num % 100 > 10 && num % 100 < 20) return 'th'
    if (num % 10 == 1) return 'st'
    if (num % 10 == 2) return 'nd'
    if (num % 10 == 3) return 'rd'
    return 'th'
}

function AnchorElement(props) {
    const [dialogOpen, setDialogOpen] = createSignal(false)
    const [rules, setRules] = createStore([])
    let dialog
    function addRule(ruleType) {
        setRules(old => [...old, ruleClasses[ruleType]()])
    }
    createEffect(() => {
        for (let rule of rules) console.log(rule)
    })
    return <><div class="anchor">
        <button type="button"
            classList={{ 'has-rules': rules.length > 0 }}
            onClick={() => dialog.showModal()}
            title={rules.map((rule) => {
                switch (rule.ruleType) {
                    case "EN":
                        return `Every ${rule.frequency} ${rule.interval}${rule.frequency > 1 ? 's' : ''} from ${rule.anchorDate}`
                    case "ENM":
                        {
                            const d = new Date(Date.parse(rule.anchorDate))
                            const day = Math.floor(d.getDate())
                            const monthFreq = rule.monthFrequency == 1 ? "" : `${rule.monthFrequency}${getOrdinalSuffix(rule.monthFrequency)}`
                            return `${day}${getOrdinalSuffix(day)} of every ${monthFreq} month starting ${rule.anchorDate}`
                        }
                    case "ENWM":
                        {
                            const d = new Date(Date.parse(rule.anchorDate))
                            const wkday = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][d.getDay()]
                            const weekno = Math.floor(d.getDate() / 7) + 1
                            return `${weekno}${getOrdinalSuffix(weekno)} ${wkday} of every ${rule.monthFrequency == 1 ? " " : getOrdinalSuffix(rule.monthFrequency)} month starting ${rule.anchorDate}`
                        }
                }
            }).join(',')}
        >
            ⚓ Day {props.day + 1}
        </button>
    </div>
        <dialog ref={dialog}>
            Add rule type: <select onChange={(e) => { addRule(e.target.value); e.target.value = "" }}>
                <option value="">Select...</option>
                <option value="EN">Every nth day</option>
                <option value="ENM">Every nth of month</option>
                <option value="ENWM">Every nth week of month</option>
            </select>
            <hr />
            <RuleGroup rules={rules} />

            <For each={rules}>
                {(rule, i) => <div>
                    <button style={{ 'font-size': '50%' }} onClick={() => setRules(old => old.toSpliced(i(), 1))}>❌ Delete</button>
                    <Switch>
                        <Match when={rule.ruleType == "EN"}>
                            Every
                            <input
                                type="number"
                                value={rule.frequency}
                                max={100}
                                min={1}
                                style={{ width: '3em' }}
                                onChange={(e) => { setRules(i(), 'frequency', e.target.value) }} />
                            {() => (rule.frequency == 1 ? " " : getOrdinalSuffix(rule.frequency))}
                            <select value={rule.interval} onChange={e => { console.log(i(), 'interval', e.target.value); setRules(i(), 'interval', e.target.value) }}>
                                <option value='day'>day</option>
                                <option value='week'>week</option>
                                <option value='month'>month</option>
                            </select>
                            starting
                            <input type="date" value={rule.anchorDate} onChange={e => setRules(i(), 'anchorDate', e.target.value)} />

                            <hr />
                        </Match>
                        <Match when={rule.ruleType == "ENM"}>
                            The {() => {
                                const d = new Date(Date.parse(rule.anchorDate))
                                const day = Math.floor(d.getDate())
                                return `${day}${getOrdinalSuffix(day)} `
                            }} of
                            <select
                                value={rule.monthFrequency}
                                onChange={(e) => { setRules(i(), 'monthFrequency', e.target.value) }} >
                                <Index each={Array(12)}>
                                    {(x, i) => <option value={i + 1}>{(i == 0 ? "every month " : `every ${i + 1}${getOrdinalSuffix(i + 1)} month`)}</option>}
                                </Index>
                            </select>
                            starting
                            <input type="date" value={rule.anchorDate} onChange={e => setRules(i(), 'anchorDate', e.target.value)} />
                        </Match>
                        <Match when={rule.ruleType == "ENWM"}>
                            The {() => {
                                const d = new Date(Date.parse(rule.anchorDate))
                                const wkday = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][d.getDay()]
                                const weekno = Math.floor(d.getDate() / 7) + 1
                                return `${weekno}${getOrdinalSuffix(weekno)} ${wkday}`
                            }} of
                            <select
                                value={rule.monthFrequency}
                                onChange={(e) => { setRules(i(), 'monthFrequency', e.target.value) }} >
                                <Index each={Array(12)}>
                                    {(x, i) => <option value={i + 1}>{(i == 0 ? "every month " : `every ${i + 1}${getOrdinalSuffix(i + 1)} month`)}</option>}
                                </Index>
                            </select>
                            starting
                            <input type="date" value={rule.anchorDate} onChange={e => setRules(i(), 'anchorDate', e.target.value)} />

                        </Match>

                    </Switch>
                </div>}
            </For>

            <button onClick={() => dialog.close()}>Close</button>
        </dialog>
    </>
}

function EditElement(props) {
    const [duties, setDuties] = createStore([])
    function makeSetDuty(idx, splice = 1) {
        return function (...newduty) {
            console.log(newduty)
            setDuties(old => old.toSpliced(idx, splice, ...newduty))
            setDuties((old) => {
                const newduties = []
                let prevduty = { finishTime: 0 }
                let currentduty
                for (let duty of old) {
                    currentduty = { ...duty, gapStart: prevduty.finishTime }
                    prevduty.gapFinish = duty.startTime
                    newduties.push(currentduty)
                    prevduty = currentduty
                }
                currentduty.gapFinish = 24
                return newduties
            })

        }
    }
    return <For each={duties} fallback={<DutyCell duty={{ placeholder: true, gapStart: 0, gapFinish: 24 }} setDuty={makeSetDuty(0, 0)} />}>
        {(duty, idx) => <>
            <Show when={idx() == 0 && duty.startTime > 0}>
                <DutyCell duty={{ placeholder: true, gapStart: 0, gapFinish: duty.startTime }} setDuty={makeSetDuty(0, 0)} />
            </Show>
            <DutyCell duty={duty} setDuty={makeSetDuty(idx(), 1)} />
            <Show when={duty.finishTime != duty.gapFinish}>
                <DutyCell duty={{ placeholder: true, gapStart: duty.finishTime, gapFinish: duty.gapFinish }} setDuty={makeSetDuty(idx() + 1, 0)} />
            </Show></>}
    </For>

}
function DutyCell(props) {
    let dialog
    const checkboxes = {}
    createEffect(() => { console.log(checkboxes) })
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
    let displayText
    const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    const anchorDate = new Date(rule.anchorDate)

    switch (rule.ruleType) {
        case 'EN':
            switch (rule.interval) {
                case "day":
                    displayText = "every "
                    displayText += (rule.frequency == 1) ? 'day' : `${rule.frequency}${getOrdinalSuffix(rule.frequency)} day`
                    break
                case "week":
                    displayText = "every "
                    displayText += (rule.frequency == 1) ? '' : `${rule.frequency}${getOrdinalSuffix(rule.frequency)} `
                    displayText += weekdays[anchorDate.getDay()]
                    break
                case "month":
                    displayText = "the "
                    displayText += `${anchorDate.getDate()}${getOrdinalSuffix(anchorDate.getDate())}`
                    displayText += ` of every `
                    displayText += (rule.frequency == 1) ? 'month' : `${rule.frequency}${getOrdinalSuffix(rule.frequency)} month`
            }
            displayText += ` from ${rule.anchorDate}`
            return displayText

        case 'ENM':
            {
                const d = new Date(Date.parse(rule.anchorDate))
                const day = Math.floor(d.getDate())
                const monthFreq = rule.monthFrequency == 1 ? "" : `${rule.monthFrequency}${getOrdinalSuffix(rule.monthFrequency)}`
                return `${day}${getOrdinalSuffix(day)} of every ${monthFreq} month starting ${rule.anchorDate}`

            }
        case 'ENWM':
            {
                const d = new Date(rule.anchorDate)
                const wkday = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][d.getDay()]
                const weekno = Math.floor(d.getDate() / 7) + 1
                return `${weekno}${getOrdinalSuffix(weekno)} ${wkday} of every ${rule.monthFrequency == 1 ? " " : `${rule.monthFrequency}${getOrdinalSuffix(rule.monthFrequency)}`} month starting {rule.anchorDate}`
            }

    }
}

function RuleGroup(props) {
    function doclick(e, idx) {
        e.preventDefault()
        console.log(props.rules[idx])
    }
    function enRuleText(rule) {
        let displayText
        const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        const anchorDate = new Date(rule.anchorDate)

        switch (rule.interval) {
            case "day":
                displayText = "every "
                displayText += (rule.frequency == 1) ? 'day' : `${rule.frequency}${getOrdinalSuffix(rule.frequency)} day`
                break
            case "week":
                displayText = "every "
                displayText += (rule.frequency == 1) ? '' : `${rule.frequency}${getOrdinalSuffix(rule.frequency)} `
                displayText += weekdays[anchorDate.getDay()]
                break
            case "month":
                displayText = "the "
                displayText += `${anchorDate.getDate()}${getOrdinalSuffix(anchorDate.getDate())}`
                displayText += ` of every `
                displayText += (rule.frequency == 1) ? 'month' : `${rule.frequency}${getOrdinalSuffix(rule.frequency)} month`
        }
        return displayText
    }

    createEffect(() => console.log(props.rules))
    return <div class='rule-group'>
        <select><option>any of</option><option>all of</option></select>
        <ul style={{ 'margin-block-start': '2px', 'list-style-type': 'square' }}>
            <For each={props.rules}>
                {(rule, idx) => {
                    let dialog
                    return <li>
                        <a href="" onClick={(e) => { e.preventDefault(); dialog.showModal() }}>
                            {() => getRuleDescription(rule)}
                        </a>
                        <RuleDialog ref={dialog} rule={rule} onSubmit={() => dialog.close()} />
                    </li>
                }}
            </For>
            <li><button type='button' style={{ 'font-size': '50%' }}>Add</button></li>
        </ul>
    </div>
}

function RuleDialog(props) {
    const [rule, setRule] = createSignal(Object.assign({}, ruleClasses.ENWM(), ruleClasses.ENM(), ruleClasses.EN(), props.rule))
    createEffect(() => console.log(rule()))

    return <dialog ref={props.ref}>
        Rule type: <select 
            value={rule().ruleType}
            onChange={(e) => { setRule((oldrule) => ({ ...oldrule, ruleType: e.target.value })) }}>
            <option value="">Select...</option>
            <option value="EN">Every nth day</option>
            <option value="ENM">Every nth of month</option>
            <option value="ENWM">Every nth week of month</option>
        </select>
        <hr />
        {() => getRuleDescription(rule())}

        <div>
            <Switch>
                <Match when={rule().ruleType == "EN"}>
                    <table>
                        <tbody>
                            <tr><td>Template day</td>
                            <td><input
                                    type="number"
                                    value={rule().templateDay}
                                    max={100}
                                    min={1}
                                    style={{ width: '3em' }}
                                    onChange={(e) => { setRule((old) => ({ ...old, templateDay: e.target.value })) }} /></td></tr>
                            <tr>
                                <td>Interval</td>
                                <td><input
                                    type="number"
                                    value={rule().frequency}
                                    max={100}
                                    min={1}
                                    style={{ width: '3em' }}
                                    onChange={(e) => { setRule((old) => ({ ...old, frequency: e.target.value })) }} />
                                </td>
                            </tr>
                            <tr>
                                <td>Interval type</td><td><select value={rule().interval} onChange={e => setRule(old => ({ ...old, interval: e.target.value }))}>
                                    <option value='day'>day</option>
                                    <option value='week'>week</option>
                                    <option value='month'>month</option>
                                </select>
                                </td></tr>
                            <tr><td>Start date</td>
                                <td><input type="date" value={rule().anchorDate} onChange={e => setRule((old) => ({ ...old, anchorDate: e.target.value }))} />
                                </td></tr>
                        </tbody>
                    </table>

                    <hr />
                </Match>
                <Match when={rule().ruleType == "ENM"}>
                    The {() => {
                        const d = new Date(Date.parse(rule().anchorDate))
                        const day = Math.floor(d.getDate())
                        return `${day}${getOrdinalSuffix(day)} `
                    }} of
                    <select
                        value={() => rule().monthFrequency}
                        onChange={e => setRule((old) => ({ ...old, monthFrequency: e.target.value }))}
                    >
                        <Index each={Array(12)}>
                            {(x, i) => <option value={i + 1}>{(i == 0 ? "every month " : `every ${i + 1}${getOrdinalSuffix(i + 1)} month`)}</option>}
                        </Index>
                    </select>
                    starting
                    <input
                        type="date"
                        value={() => rule().anchorDate}
                        onChange={e => setRule((old) => ({ ...old, anchorDate: e.target.value }))}
                    />
                </Match>
                <Match when={() => rule().ruleType == "ENWM"}>
                    The {() => {
                        const d = new Date(Date.parse(rule().anchorDate))
                        const wkday = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][d.getDay()]
                        const weekno = Math.floor(d.getDate() / 7) + 1
                        return `${weekno}${getOrdinalSuffix(weekno)} ${wkday}`
                    }} of
                    <select
                        value={() => rule().monthFrequency}
                        onChange={e => setRule((old) => ({ ...old, monthFrequency: e.target.value }))}>
                        <Index each={Array(12)}>
                            {(x, i) => <option value={i + 1}>{(i == 0 ? "every month " : `every ${i + 1}${getOrdinalSuffix(i + 1)} month`)}</option>}
                        </Index>
                    </select>
                    starting
                    <input type="date" value={() => rule().anchorDate}
                        onChange={e => setRule((old) => ({ ...old, anchorDate: e.target.value }))}
                    />

                </Match>

            </Switch>
        </div>

        <button onClick={() => props.onSubmit()}>Close</button>
    </dialog>
}

export default function TemplateEditor() {
    const [appliesToStaff, setAppliesToStaff] = createSignal(Object.fromEntries(staff.map(x => [x, false])))
    const [template, editTemplate] = createSignal([[1, 2, 3, 4, 5, 6, 7]])
    function doStaffChange(e) {
        setAppliesToStaff(old => ({ ...old, [e.target.value]: e.target.checked }))
    }
    function addRowAbove() {
        editTemplate((old) => ([[1, 2, 3, 4, 5, 6, 7], ...old]))
    }
    function addRowBelow() {
        editTemplate(old => ([...old, [1, 2, 3, 4, 5, 6, 7]]))
    }
    function deleteRow(idx) {
        editTemplate(old => old.length == 1 ? [[1, 2, 3, 4, 5, 6, 7]] : old.toSpliced(idx(), 1))
    }
    return <>
        <h4>Template Editor</h4>
        <div class='template-editor-settings'>
            <div>Description: <input /></div>
            <details onChange={doStaffChange}>
                <summary>
                    Applies to: {staff.filter(sn => (appliesToStaff()[sn])).join(',') || '(none)'}
                </summary>
                <For each={staff}>
                    {sm => <div><input type="checkbox" value={sm} checked={appliesToStaff()[sm]} />{sm}</div>}
                </For>
            </details>
            From: <input type='date' />  to <input type='date' />
            <hr />
            Applies when:
            <RuleGroup />

        </div>
        <table class="main-table template">
            <tbody>
                <Show when={template().length > 0}>
                    <tr>
                        <td class="addrow" colspan={8}>
                            <button type="button" onClick={addRowAbove}>➕ Add row</button>
                        </td>
                    </tr>
                </Show>
                <For each={template()}>
                    {(row, weekNo) => (<tr>
                        <td><button onClick={() => deleteRow(weekNo)}>❌ Delete</button></td>
                        <For each={row}>
                            {(x, dayNo) => <td>
                                <AnchorElement cell={x} day={weekNo() * 7 + dayNo()} />
                                <EditElement cell={x} />
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
    </>
}