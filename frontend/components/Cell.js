
import React from 'react';
import TableCell from '@mui/material/TableCell';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import { useDispatch, useSelector } from 'react-redux';
import isEqual from 'lodash/isEqual';

const selectors={
    getCellData:(date)=>(state)=>state?.duties[date]
}

const actions={
    setDuty:(dutyType,shift,name,day)=>({type:'remote/setDuty',dutyType,shift,name,day})
}
export const Cell = (function Cell({ name, day, dutyType }) {
    const dispatch=useDispatch()
    const getCellDataSelector=React.useMemo(()=>selectors.getCellData(day),[day])
    const data=useSelector(getCellDataSelector,isEqual)
    if (!data) return <TableCell>...</TableCell>
    const daytimeValue = data?.DAYTIME?.[name] ?? 'LOADING'
    const oncallValue = data?.ONCALL?.[name] ?? 'LOADING'
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
        dispatch(actions.setDuty(dutyType, shift, name, day));
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
