
import React from 'react'
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Button from '@mui/material/Button';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import TextField from '@mui/material/TextField';
import Link from '@mui/material/Link';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import locale from 'date-fns/locale/en-GB'
import isEqual from 'lodash/isEqual';
import { format,formatISO, parseISO } from 'date-fns';
import { names } from '../lib/names';
import { Cell } from '../components/Cell';
import { SettingsDialog } from '../components/SettingsDialog';
import { MessageDialog } from '../components/MessageDialog';
import { DateRangeDialog } from '../components/DateRangeDialog';
import { useDispatch, useSelector } from 'react-redux';
import { api, ReduxProvider } from '../lib/store';


const rotaEpoch = new Date(2020, 10, 2)

const { useGetDutiesQuery }=api

//Selectors
const selectors={
  getMessage:(state=>state?.statusMessage),
  getDaysArray: state => state.config.daysArray,
  getStartDate: state => state.config.startDate,
  getStartDateAndNumDays: state => state.config
}

//Actions
const actions={
  showTallies:(dateISO)=>({type:'remote/showTallies',payload:dateISO}),
  setStartDate:(startDate=>({
    type:'remote/setStartDate',
    payload:formatISO(startDate,{representation:'date'})}
    )),
  recalculate:()=>({type:'remote/recalculate'})
}

function MessageBox() {
  const message=useSelector(selectors.getMessage)
  return message
}




function DateLink({ date }) {
  const dispatch=useDispatch()
  const clickHandler = React.useCallback(() => {
    dispatch(actions.showTallies(date))
  },[date]) 
  return <Link sx={{ cursor: 'pointer' }} onClick={clickHandler}>
    {format(parseISO(date), "E d MMM")}
  </Link>

}

function App(){
  return <ReduxProvider><InnerApp/></ReduxProvider>
}

function InnerApp() {
  const [dutyType, setDutyType] = React.useState('DEFINITE_ICU')
  
  const config = useSelector(selectors.getStartDateAndNumDays)
  const { data:dutiesData }=useGetDutiesQuery(config)
  const dispatch = useDispatch()
  

  const handleChange = React.useCallback((evt, newValue) => {
    if (newValue !== null) {
      setDutyType(newValue)
    }
  }, [setDutyType])

  if (!dutiesData) return null
  
  return (
    <div className="App">
  
      <LocalizationProvider dateAdapter={AdapterDateFns} locale={locale}>
        <Paper>
            <Button onClick={() => { dispatch(actions.recalculate()) }}>
              recalculate
            </Button>
          <ToggleButtonGroup
            value={dutyType}
            exclusive
            onChange={handleChange}
            aria-label="text alignment"
          >
            <ToggleButton value="DEFINITE_ICU">ICU</ToggleButton>
            <ToggleButton value="DEFINITE_LOCUM_ICU">ICU(£)</ToggleButton>
            <ToggleButton value="ICU_MAYBE_LOCUM">ICU(£?)</ToggleButton>
            <ToggleButton value="LEAVE">Leave</ToggleButton>
            <ToggleButton value="NOC">NOC</ToggleButton>
            <ToggleButton value="CLEAR">Clear</ToggleButton>
          </ToggleButtonGroup>

          <DatePicker
            value={parseISO(config.startDate)}
            onChange={(newValue) => {
              dispatch(actions.setStartDate(newValue));
            }}
            minDate={rotaEpoch}
            showTodayButton
            renderInput={(params) => (
              <TextField variant="standard" {...params} />
            )}
          />
          <SettingsDialog />
          <DateRangeDialog onChange={(v)=>console.log(v)}/>
          <MessageBox/>
        </Paper>
          <MessageDialog/>
        <TableContainer component={Paper}>
          <Table style={{ border: "solid 1px" }}>
            <TableHead>
              <TableRow>
                <TableCell sx={{
                  position: "sticky",
                  left: 0,
                  background: "white",
                  boxShadow: "5px 2px 5px grey",
                  borderRight: "2px solid black",
                  zIndex:1000
                }}></TableCell>
                {dutiesData.days.map((day,i) => (
                  <TableCell key={i}>
                    <DateLink date={day}/>
                    </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {dutiesData.names.map((name, i) => (
                <>
                  <TableRow
                    key={i}
                    style={{ backgroundColor: i % 2 ? "#eeeeee" : "#dddddd" }}
                  >
                    <TableCell sx={{
                      position: "sticky",
                      left: 0,
                      background: "white",
                      borderRight: "2px solid black",
                      zIndex:1000
                    }}>{name}</TableCell>
                    {dutiesData.days.map((day) => (
                      <Cell
                        key={day}
                        dutyType={dutyType}
                        name={name}
                        day={day}
                      />
                    ))}
                  </TableRow>
                </>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        </LocalizationProvider>
    </div>
  );
}

export default App;


