
import { For, Show, Switch, Match, createSignal, createEffect } from 'solid-js'
import { createStore, unwrap } from 'solid-js/store'
import './maintable.css'

const staff = ['fred', 'barney', 'wilma', 'betty']
const availableDuties=['Theatre','ICU','Non clinical','Zero','Leave']
const ruleClasses = {
    EN: () => ({ ruleType: "EN", frequency: 1, interval: "week", anchorDate: '2022-01-01' }),
    ENM: () => ({ ruleType: "ENM", day: 1, monthFrequency: 1, anchorDate: '2022-01-01' }),
    ENWM: () => ({ ruleType: "ENWM", weekNo: 1, monthFrequency: 1, anchorDate: '2022-01-01' })
}
function getOrdinalSuffix(num){
    if (num%100>10 && num%100<20) return 'th'
    if (num%10==1) return 'st'
    if (num%10==2) return 'nd'
    if (num%10==3) return 'rd'
    return 'th'
}

function AnchorElement(props) {
    const [dialogOpen, setDialogOpen] = createSignal(false)
    const [rules, setRules] = createStore([])
    let dialog
    function addRule(ruleType) {
        setRules(old => [...old, ruleClasses[ruleType]()])
    }
    return <><div class="anchor">
        <button type="button" 
            classList={{'has-rules':rules.length>0}} 
            onClick={() => dialog.showModal()}
            title={rules.map((rule)=>{
                switch(rule.ruleType){
                    case "EN":
                        return `Every ${rule.frequency} ${rule.interval}${rule.frequency>1?'s':''} from ${rule.anchorDate}`
                    case "ENM":
                        {
                        const d=new Date(Date.parse(rule.anchorDate))
                        const day=Math.floor(d.getDate())
                        const monthFreq=rule.monthFrequency==1?"":`${rule.monthFrequency}${getOrdinalSuffix(rule.monthFrequency)}`
                        return `${day}${getOrdinalSuffix(day)} of every ${monthFreq} month starting ${rule.anchorDate}`
                        }
                    case "ENWM":
                        {const d=new Date(Date.parse(rule.anchorDate))
                            const wkday=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][d.getDay()]
                            const weekno=Math.floor(d.getDate()/7)+1
                            return `${weekno}${getOrdinalSuffix(weekno)} ${wkday} of every ${rule.monthFrequency == 1 ? " " : getOrdinalSuffix(rule.monthFrequency)} month starting ${rule.anchorDate}` 
                }
            }}).join(',')}
            >
                ⚓
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
            <For each={rules}>
                {(rule, i) => <div>
                    <button style={{'font-size':'50%'}}onClick={() => setRules(old=>old.toSpliced(i(),1))}>❌ Delete</button>
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
                            <select value={rule.interval} onChange={e => setRules(i(), 'interval', e.target.value)}>
                                <option value='day'>day</option>
                                <option value='week'>week</option>
                                <option value='month'>month</option>
                            </select>
                            starting
                            <input type="date" value={rule.anchorDate} onChange={e => setRules(i(), 'anchorDate', e.target.value)} />
                        
                        <hr />
                    </Match>
                    <Match when={rule.ruleType == "ENM"}>
                            The {()=>{
                                const d=new Date(Date.parse(rule.anchorDate))
                                const day=Math.floor(d.getDate())
                                return `${day}${getOrdinalSuffix(day)} `
                                }} of every
                            <input
                                type="number"
                                value={rule.monthFrequency}
                                max={100}
                                min={1}
                                style={{ width: '3em' }}
                                onChange={(e) => { setRules(i(), 'monthFrequency', e.target.value) }} />
                            {() => (rule.monthFrequency == 1 ? " " : getOrdinalSuffix(rule.monthFrequency))} month
                            starting
                            <input type="date" value={rule.anchorDate} onChange={e => setRules(i(), 'anchorDate', e.target.value)} />
                        
                    </Match>
                    <Match when={rule.ruleType == "ENWM"}>
                        
                            
                            The {()=>{
                                const d=new Date(Date.parse(rule.anchorDate))
                                const wkday=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][d.getDay()]
                                const weekno=Math.floor(d.getDate()/7)+1
                                return `${weekno}${getOrdinalSuffix(weekno)} ${wkday}`
                                }} of every
                            <input
                                type="number"
                                value={rule.monthFrequency}
                                max={100}
                                min={1}
                                style={{ width: '3em' }}
                                onChange={(e) => { setRules(i(), 'monthFrequency', e.target.value) }} />
                            {() => (rule.monthFrequency == 1 ? " " : getOrdinalSuffix(rule.monthFrequency))} month
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

function EditElement(props){
    const [duties,setDuties]=createStore(['add'])
    function makeSetDuty(idx){
        return function(newduty){
            setDuties(idx,newduty)
            if (idx==0){
                setDuties((old)=>['add',...old])
            }
        }
    }
    return <For each={duties}>
        {(duty,idx)=><DutyCell duty={duty} setDuty={makeSetDuty(idx())}/>}
    </For>
    
}
function DutyCell(props){
    let dialog
    const checkboxes={}
    createEffect(()=>{console.log(checkboxes)})
    return <>
        <div style={{cursor:'pointer'}} onClick={()=>dialog.showModal()}>
        <Switch>
            <Match when={props.duty=='add'}>
                <div onClick={()=>dialog.showModal()}>Add ➕</div>
            </Match>
            <Match when={props.duty!='add'}>
                {props.duty.startTime}-{props.duty.finishTime}:props.duty.locations.join(',')
            </Match>
        </Switch>
        </div>
        <dialog ref={dialog}>
            <h4>Acceptable duties</h4>
            <For each={availableDuties}>
                {(duty)=><div><input ref={checkboxes[duty]} type="checkbox"/>{duty}</div>}
            </For>
            <button type="button" onClick={()=>console.log(availableDuties.filter(d=>checkboxes[d].checked))}>ok</button>
            <button type="button" onClick={()=>dialog.close()}>Close</button>
        </dialog>
        </>
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
                    {(row, idx) => (<tr>
                        <td><button onClick={() => deleteRow(idx)}>❌ Delete</button></td>
                        <For each={row}>
                            {x => <td>
                                <AnchorElement cell={x} />
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
        <dialog />
    </>
}