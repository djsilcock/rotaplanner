
import React from 'react';
import TableCell from '@mui/material/TableCell';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import useSWR from 'swr'
import { useSocket } from '../lib/socketContext';

function useFetcher() {
    const socket=useSocket()
    return (...params) => {
        console.log(params)
        return new Promise(
            (resolve, reject) => socket
                .timeout(5000)
                .emit(...params,
                    (err, result) => err ? reject(err) : resolve({ result })))
            .catch(e => console.warn(e))
    }
}

export const Cell = (function Cell({ name, day, dutyType }) {
    const fetcher=useFetcher()
    const { data,mutate } = useSWR(['get_duties',day], fetcher)
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
            fetcher('set_duty', dutyType, shift, name, day),
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
