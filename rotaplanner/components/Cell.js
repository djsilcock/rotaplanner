
import React from 'react';
import TableCell from '@mui/material/TableCell';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import useSWR from 'swr'

function fetcher(url) {
    return fetch(url)
        .then(r => r.json())
}

function setDuty(values) {
    return fetch('/backend/setduty', { method: 'POST', body: JSON.stringify(values) })
        .then(r => r.json())
        .then(r => console.log(r) || r)
    
}

export const Cell=(function Cell({ name, day, dutyType}) {   
    const { data,mutate } = useSWR(`/backend/getduties/${day}`, fetcher)
    if (!data) return <TableCell>...</TableCell>
    const daytimeValue = data?.result?.DAYTIME?.[name] ?? 'LOADING'
    const oncallValue = data?.result?.ONCALL?.[name] ?? 'LOADING'
    const props1 = {
        ICU: ['blue', <>?&nbsp;ICU</>],
        LOCUM_ICU: ['blue', <>?&nbsp;ICU(£)</>],
        DEFINITE_ICU: ['green', 'ICU'],
        DEFINITE_LOCUM_ICU: ['green', 'ICU(£)'],
        ICU_MAYBE_LOCUM: ['green', 'ICU(£?)'],
        THEATRE:['gray','Th'],
        LEAVE: ['gray', 'Leave'],
        NOC: ['orange', 'NOC'],
        TIMEBACK:['gray','TS'],
        LOADING:['gray','...']
    }[daytimeValue] || ['gray', '-'];
    const props2 = {
        ICU: ['navy', <>?&nbsp;ICU</>],
        LOCUM_ICU: ['navy', <>?&nbsp;ICU(£)</>],
        DEFINITE_ICU: ['darkgreen', 'ICU'],
        DEFINITE_LOCUM_ICU: ['darkgreen', 'ICU(£)'],
        ICU_MAYBE_LOCUM:['darkgreen','ICU(£?)'],
        LEAVE: ['gray', 'Leave'],
        NOC: ['orange', 'NOC'],
        LOADING: ['gray', '...']
    }[oncallValue] || ['gray', '-'];
    
    const handleClick = (shift) => () => {
        console.log({ origdata: data })
        const newdata = { DAYTIME: { ...data?.result?.DAYTIME }, ONCALL: { ...data?.result?.ONCALL } }
        newdata[shift][name] = dutyType
        console.log({optimisticData:newdata})
        mutate(
            setDuty({ duty: dutyType, shift, name, day }),
            {
                optimisticData: { result: newdata },
                populateCache: true,
            }
        );
    };
    return <TableCell style={{ border: 'solid 1px' }} title={`${name} ${day}`}>
        <ButtonGroup
            orientation="vertical"
            aria-label="vertical outlined button group"
            size='small'
        ><Button style={{ border: 'none', width: '100%', height: '100%', color: props1[0] }} onClick={handleClick('DAYTIME')}>{props1[1]}</Button>
            <Button style={{ border: 'none', width: '100%', height: '100%', color: props2[0] }} onClick={handleClick('ONCALL')}>{props2[1]}</Button></ButtonGroup>
    </TableCell>;
})
