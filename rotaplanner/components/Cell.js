
import React from 'react';
import TableCell from '@mui/material/TableCell';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import useSWR from 'swr'

function fetcher(url) {
    return fetch(url)
        .then(r => r.json())
        .then(r => { console.log(r); return r})
}

function setDuty(values) {
    return fetch('/backend/setduty', { method: 'POST', body: JSON.stringify(values) })
    .then(r=>r.json())
}

export const Cell=(function Cell({ name, day, dutyType}) {   
    const { data,mutate } = useSWR(`/backend/getduties/${day}`, fetcher)
    if (!data) return <TableCell>...</TableCell>
    const daytimeValue = data? data.result[`${name}-DAYTIME`]:'LOADING'
    const oncallValue = data? data.result[`${name}-ONCALL`]:'LOADING'
    const props1 = {
        ICU: ['blue', <>?&nbsp;ICU</>],
        LOCUM_ICU: ['blue', <>?&nbsp;ICU(£)</>],
        DEFINITE_ICU: ['green', 'ICU'],
        DEFINITE_LOCUM_ICU:['green','ICU(£)'],
        THEATRE:['gray','Th'],
        LEAVE: ['gray', 'Leave'],
        NOC: ['orange', 'NOC'],
        LOADING:['gray','...']
    }[daytimeValue] || ['gray', '-'];
    const props2 = {
        ICU: ['navy', <>?&nbsp;ICU</>],
        LOCUM_ICU: ['navy', <>?&nbsp;ICU(£)</>],
        DEFINITE_ICU: ['darkgreen', 'ICU'],
        DEFINITE_LOCUM_ICU:['darkgreen','ICU(£)'],
        LEAVE: ['gray', 'Leave'],
        NOC: ['orange', 'NOC'],
        LOADING: ['gray', '...']
    }[oncallValue] || ['gray', '-'];
    
    const handleClick = (shift) => () => {
        mutate(
            setDuty({ duty: dutyType, shift, name, day }),
            {
                optimisticData: { ...data, [`${name}-${shift}`]: dutyType },
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
