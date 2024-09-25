import { For, Show,Index,Switch, Match, createEffect, createSignal,children,useContext,createContext, createResource } from 'solid-js';
import backend from '../backend'

export function RuleGroup(props) {
    const { rules, setRules } = useContext(RulesContext);
    createEffect(() => console.log(rules()));

    function editRule(newRule) {
        console.log(newRule);
        const parentId = props.rule.ruleId;
        setRules(state => {
            const newState = { ...state };
            if (newRule.ruleId == null) {
                newRule.ruleId = Math.random().toString(36).slice(2);
                newState[parentId] = {
                    ...state[parentId],
                    rules: [...state[parentId].rules, newRule.ruleId]
                };
            }
            newState[newRule.ruleId] = { ...newRule };
            console.log(newState);
            return newState;
        });
    }

    function deleteRule(ruleId) {
        setRules(old => ({ ...old, [ruleId]: undefined }));
    }

    function addGroup() {
        const newGroupId = Math.random().toString(36).slice(2);
        const parentId = props.ruleId;
        setRules(state => {
            const newState = {};
            newState[parentId] = {
                ...state[parentId],
                rules: [...state[parentId].rules, newGroupId]
            };
            newState[newGroupId] = { ruleType: 'group', groupType: 'and', ruleId: newGroupId, rules: [] };
            return newState;
        });
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
                    const rule = () => rules()[ruleId];
                    return <Switch fallback={JSON.stringify(rule())}>
                        <Match when={typeof rule() == 'undefined'}>Eh?</Match>
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
                                    {open => <a href="" onClick={(e) => { e.preventDefault(); open(); }}>
                                        {() => getRuleDescription(rule())}
                                    </a>}
                                </RuleDialog>
                            </li>
                        </Match>
                    </Switch>;
                }}
            </For>
            <li>
                <RuleDialog rule={{ ruleId: null }} onSubmit={editRule}>
                    {open => <button type='button' onClick={() => open()} style={{ 'font-size': '50%' }}>Add rule</button>}

                </RuleDialog>
                <button type='button' onClick={addGroup} style={{ 'font-size': '50%' }}>Add group</button>
            </li>
        </ul>

    </div>;
}

export function RuleDialog(props) {
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
    const open=()=>{
        dialog.showModal()
        reset()
    }
    return <>
        <dialog ref={dialog}>
            Rule type: <select
                value={rule().ruleType}
                onChange={(e) => { setRule((oldrule) => ({ ...oldrule, ruleType: e.target.value })) } }>
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
                                            <select value={rule().templateDay} onChange={(e) => { setRule((old) => ({ ...old, templateDay: e.target.value })) } }>
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
                                        onChange={(e) => { setRule((old) => ({ ...old, frequency: e.target.value })) } } />
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
            <button onClick={() => { props.onSubmit(rule()); dialog.close() } }>OK</button>
            <button onClick={() => { reset(); dialog.close() } }>Close</button>

        </dialog>
        {display()(open)}
    </>
}
export function CheckDates(props) {
    const [month, setMonth] = createSignal(1)
    const [year,setYear]=createSignal(2024)
    const signal=()=>[month(),year(),props.rules]
    const [calendar]=createResource(signal,([month,year,rules])=>backend.get_dates_matching_rules(month,year,rules),{initialValue:[]})
    return <details>
        <summary>Check dates...</summary>

        <select onChange={(e) => setMonth(Number(e.target.value))}>
            <option value="1">Jan</option>
            <option value="2">Feb</option>
            <option value="3">Mar</option>
            <option value="4">Apr</option>
            <option value="5">May</option>
            <option value="6">Jun</option>
            <option value="7">Jul</option>
            <option value="8">Aug</option>
            <option value="9">Sep</option>
            <option value="10">Oct</option>
            <option value="11">Nov</option>
            <option value="12">Dec</option>
        </select>

        <input type='number' value={year()} onChange={(e) => setYear(e.target.value)} />
        <table style={{ border: '1px solid black', 'border-collapse': 'collapse', 'text-align': 'center' }}>
            <thead>
                <tr>
                    <th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th>
                </tr>
            </thead>
            <For each={calendar()}>
                {week => <tr>
                    <For each={week}>
                        {day => <td style={{
                            border: '1px solid black',
                            padding: '2px',
                            color: day.active ? 'black' : 'gray',
                            'text-decoration': day.active ? 'none' : 'line-through'
                        }}>{day.date}</td>}
                    </For>
                </tr>}
            </For>
        </table>
    </details>
}
export function dateMatches(date, ruleId, rules) {
    return backend.date_matches(date,ruleId,rules)
}
export const RulesContext = createContext()
export function getRuleDescription(rule) {
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
export const ruleClasses = {
    en: () => ({ ruleType: "en", frequency: 1, interval: "week" }),
    enwm: () => ({ ruleType: "enwm" })
}
export function getOrdinalSuffix(num) {
    if (num % 100 > 10 && num % 100 < 20) return 'th'
    if (num % 10 == 1) return 'st'
    if (num % 10 == 2) return 'nd'
    if (num % 10 == 3) return 'rd'
    return 'th'
}

