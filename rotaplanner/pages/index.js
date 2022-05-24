
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

import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import locale from 'date-fns/locale/en-GB'

import { addDays, format } from 'date-fns';
import { dutyReducer} from '../lib/store';
import { names } from '../lib/names';
import { Cell } from '../components/Cell';
import { recalculate } from '../lib/recalculate';
import { SettingsDialog } from '../components/SettingsDialog';
import { setConstraint } from '../lib/setDuty';
import { Grid } from '@mui/material';
import { DateRangeDialog } from '../components/DateRangeDialog';

const days = Array(16 * 7).fill(0).map((x, i) => i)

function App() {

  const [dutyType, setDutyType] = React.useState('DEFINITE_ICU')
  const [startDate, setStartDate] = React.useState('2022-02-02')
  const handleChange = React.useCallback((evt, newValue) => {
    if (newValue !== null) {
      setDutyType(newValue)
    }
  }, [setDutyType])
  
  const [{ duties, message },setDuty]=React.useReducer(dutyReducer,undefined,dutyReducer)
  React.useEffect(() => {recalculate({ lastsaved: true }, setDuty) },[])
  return (
    <div className="App">
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
            <ToggleButton value="LEAVE">Leave</ToggleButton>
            <ToggleButton value="NOC">NOC</ToggleButton>
            <ToggleButton value="CLEAR">Clear</ToggleButton>
          </ToggleButtonGroup>

          <DatePicker
            value={startDate}
            onChange={(newValue) => {
              setStartDate(newValue);
            }}
            renderInput={(params) => (
              <TextField variant="standard" {...params} />
            )}
          />
          <SettingsDialog />
          <DateRangeDialog onChange={(v)=>console.log(v)}/>
          <span>{message}</span>
        </Paper>
       
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
                    {format(addDays(new Date("2022-05-02"), x), "E d MMM")}
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
                        day={day}
                        daytimeValue={duties[name]["DAYTIME"][day]}
                        oncallValue={duties[name]["ONCALL"][day]}
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
    </div>
  );
}

export default App;


