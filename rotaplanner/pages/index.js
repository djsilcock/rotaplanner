
import { Observer } from 'mobx-react-lite'
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
import { useSWRConfig } from 'swr';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import locale from 'date-fns/locale/en-GB'

import { addDays, format,differenceInCalendarDays, isValid, formatISO } from 'date-fns';
import { dutyReducer} from '../lib/store';
import { names } from '../lib/names';
import { Cell } from '../components/Cell';
import { recalculate } from '../lib/recalculate';
import { SettingsDialog } from '../components/SettingsDialog';
import { MessageDialog } from '../components/MessageDialog';
import { DateRangeDialog } from '../components/DateRangeDialog';

import {useSocket,SocketProvider } from '../lib/socketContext';

const rotaEpoch = new Date(2020, 10, 2)

function MessageBox() {
  const [message, setMessage] = React.useState('meh')
  const socket=useSocket()
  React.useEffect(() => {
    if (!socket) return
    socket.on('progress', data => {
      setMessage(`Objective:${data.objective}, time:${data.time}s`)
    })
    socket.on('message',data=>{setMessage(data.message)})
    socket.on('solveStatus', data => {
      setMessage(`Solver status: ${data.statusName}`)
    })
  },[socket])
  return message
}



function SocketIO() {
  const { cache, mutate } = useSWRConfig()
  const socket=useSocket()
  React.useEffect(() => {
    if (!socket) return
    socket.on('connect', () => {
      console.log('connected')
      socket.emit('echo','hello!')
    })
    socket.on('greeting', (data) => { console.log(data) })
    socket.onAny((evt, data) => console.log({ evt, data }))
    socket.on('reload', () => {
      for (let k of cache.keys()){ console.log(k); mutate(k) }
    })
  }, [cache,mutate,socket])
  return null
}

function DateLink({ date }) {
  const socket=useSocket()
  const clickHandler = React.useCallback(() => {
    socket.emit('show_tallies',formatISO(date,{representation:'date'}))
  },[date,socket])
  return <Link sx={{ cursor: 'pointer' }} onClick={clickHandler}>
    {format(date, "E d MMM")}
  </Link>

}

function App() {
  const [dutyType, setDutyType] = React.useState('DEFINITE_ICU')
  const [proposedStartDate, setProposedStartDate] = React.useState(rotaEpoch)
  const [startDate,setStartDate]=React.useState(null)
  const handleChange = React.useCallback((evt, newValue) => {
    if (newValue !== null) {
      setDutyType(newValue)
    }
  }, [setDutyType])
  React.useEffect(() => {
    if (isValid(proposedStartDate)){
      setStartDate(proposedStartDate)
    }
  }, [proposedStartDate])
  React.useEffect(() => {
    setProposedStartDate(new Date())
  },[])
  const days = React.useMemo(() => isValid(startDate) ? (
    Array(16 * 7).fill(0).map((x, i) => i + differenceInCalendarDays(startDate, rotaEpoch))) : [], [startDate])
  
  const [{ duties, message },setDuty]=React.useReducer(dutyReducer,undefined,dutyReducer)
  return (
    <div className="App">
      <SocketProvider>
      <LocalizationProvider dateAdapter={AdapterDateFns} locale={locale}>
        <Paper>
          <Button onClick={() => recalculate(duties,setDuty)}>recalculate</Button>
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
            value={startDate}
            onChange={(newValue) => {
              setProposedStartDate(newValue);
            }}
            minDate={rotaEpoch}
            showTodayButton
            renderInput={(params) => (
              <TextField variant="standard" {...params} />
            )}
          />
          <SettingsDialog />
          <DateRangeDialog onChange={(v)=>console.log(v)}/>
          <MessageBox/><SocketIO/>
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
                {days.map((x) => (
                  <TableCell key={x}>
                    <DateLink date={addDays(rotaEpoch,x)}/>
                    </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {names.map((name, i) => (
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
                    {days.map((day) => (
                      <Cell
                        key={day}
                        dutyType={dutyType}
                        name={name}
                        day={format(addDays(rotaEpoch, day), "yyyy-MM-dd")}
                        
                        setDuty={setDuty}
                      />
                    ))}
                  </TableRow>
                </>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        </LocalizationProvider>
      </SocketProvider>
    </div>
  );
}

export default App;

