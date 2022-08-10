import React from "react";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import DeleteIcon from '@mui/icons-material/Delete'
import Grid from "@mui/material/Grid";
import IconButton from "@mui/material/IconButton";
import TextField from "@mui/material/TextField";

import { format,formatISO,isValid, parseISO } from "date-fns";

function DateExclusion({ id, startdate, enddate, globalStart,globalEnd,dispatch }) {
  const setEnddate = (value) => dispatch({ type: 'modify', datetype: 'end', value, id })
  const setStartdate = (value) => dispatch({ type: 'modify', datetype: 'start', value, id })
  const errorStart = (value) => dispatch({ type: 'modify', datetype: 'errorStart', value, id })
  const errorEnd = (value) => dispatch({ type: 'modify', datetype: 'errorEnd', value, id })
  const deleteExclusion=()=>dispatch({type:'delete',id})
  return  <><Grid item xs={2}></Grid>
            <Grid item xs={4}>
              <DatePicker
                              label="From"
        maxDate={enddate||globalEnd}
        minDate={globalStart}
                              onChange={setStartdate}
        value={startdate}
        onError={errorStart}
                required
                renderInput={(params) => (
                  <TextField variant="standard" {...params} />
                )}
              />
            </Grid>
            <Grid item xs={4}>
              <DatePicker
                              label="To"
                              value={enddate}
        minDate={startdate||globalStart}
        maxDate={globalEnd}
                onChange={setEnddate}
        required
        onError={errorEnd}
                renderInput={(params) => (
                  <TextField variant="standard" {...params} />
                )}
              />
            </Grid>
            
    <Grid item xs={1}><IconButton onClick={deleteExclusion }sx={{margin:1}}><DeleteIcon/></IconButton></Grid>
    <Grid item xs={1}></Grid></>
}

export function DateRangeDialog({ value, onChange, name }) {
  const { startdate: origStartdate, enddate: origEnddate, exclusions: origExclusions } = (value || {})
  const [open, setOpen] = React.useState(false);  
  const handleClose = () => {
    setOpen(false);
  };
    const handleClickOpen=()=>setOpen(true)  
    const [startdate, setStartdate] = React.useState(null)
  const [enddate, setEnddate] = React.useState(null)
  React.useEffect(() => {
    setStartdate(origStartdate?parseISO(origStartdate):null)
    setEnddate(origEnddate?parseISO(origEnddate):null)
    setExclusion({type:'replace',newvalue:origExclusions||[]})
  },[origStartdate,origEnddate,origExclusions,open])
  const [exclusions, setExclusion] = React.useReducer(
    (state, action) => {
      switch (action.type) {
        case 'replace':
          return action.newvalue.map(x => ({
            start: parseISO(x.start),
            end: parseISO(x.end),
            errorStart: null,
            errorEnd:null
          }))
        case 'delete':
          return state.filter((_, i) => i != action.id)
        case 'modify':
          return state.map((x, i) => i == action.id ? { ...x, [action.datetype]: action.value } : x)
        case 'add':
          return [...state,{start:null,end:null,errorStart:null,errorEnd:null}]
      }
    },[]
  )
  const formInvalid = exclusions.some(exc => (exc.errorStart || exc.errorEnd)) || !exclusions.every(exc => (exc.start && exc.end))
  
  const displayText = (
    isValid(startdate) ? (
      isValid(enddate) ? (
        `between ${format(startdate,'d/M/yy')} and ${format(enddate,'d/M/yy')}`
      ) : (
        `starting ${ format(startdate, 'd/M/yy')}`
      )
    ) : (
        isValid(enddate) ? (
          `until ${format(enddate, 'd/M/yy')}`
        ) : (
          `for all dates`
        ) 
    )
  )
  const exclusionstext = exclusions.map(exc => (
    (isValid(exc.start)&&isValid(exc.end))?(
    (exc.start == exc.end) ? (
      format(exc.end, 'd/M/yy')
    ) : (
      `${format(exc.start, 'd/M/yy')}-${format(exc.start, 'd/M/yy')}`)):''))
  .join('\n')
  
  const handleOK = () => {
    onChange({
      name,
      value: {
        startdate: isValid(startdate) ? formatISO(startdate, { representation: 'date' }):null,
        enddate: isValid(enddate) ? formatISO(enddate, { representation: 'date' }) : null,
        exclusions: exclusions.map(exc => ({
          start: formatISO(exc.start, { representation: 'date' }),
          end: formatISO(exc.end, { representation: 'date' })
      }))
      },
      
    }
    )
    handleClose()
  }
  return (
    <>
      <Button size='small' variant='outlined' onClick={handleClickOpen} title={exclusionstext&&'Exclusions:\n'+exclusionstext}>
        Applies {displayText} {exclusions.length==0?'':'(with exclusions)'}
      </Button>
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Time period</DialogTitle>
        <DialogContent>
          <Grid container spacing={1}>
            <Grid item xs={1}></Grid>
            <Grid item xs={5}>
              <DatePicker
                              label="From"
                              maxDate={enddate}
                              onChange={setStartdate}
                value={startdate}
                clearable
                renderInput={(params) => (
                  <TextField variant="standard" {...params} />
                )}
              />
            </Grid>
            <Grid item xs={5}>
              <DatePicker
                              label="To"
                              value={enddate}
                              minDate={startdate}
                onChange={setEnddate}
                clearable
                renderInput={(params) => (
                  <TextField variant="standard" {...params} />
                )}
              />
            </Grid>
            
            <Grid item xs={1}></Grid>
            <Grid item xs={12}>{exclusions.length == 0 ? 'No exclusions' : 'Exclusions:'}</Grid>
            
            {exclusions.map(({ start, end }, i) =>(
              <DateExclusion
                key={i}
                id={i}
                startdate={start}
                enddate={end}
                globalEnd={enddate}
                globalStart={startdate}
                dispatch={setExclusion} />))}
            <Grid item xs={12}><Button onClick={()=>setExclusion({type:'add'})}>Add exclusion</Button></Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleOK} disabled={formInvalid}>OK</Button>
          
        </DialogActions>
      </Dialog>
    </>
  );
}
