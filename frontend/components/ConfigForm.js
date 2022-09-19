import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox"
import React from "react";
import { useDispatch } from "react-redux";
import { api } from "../lib/store";
import { DateRangeDialog } from "./DateRangeDialog";
import { GenericComponent } from "./GenericComponent";



const actions = {
  updateConstraintField:({constraintName,id,name,value})=>({type:'remote/updateConstraintField',constraintName,id,name,value})
}

export function ConfigForm({ formSpec, id, values, constraintName, update, lastOne }) {
  const dispatch=useDispatch()

  const updateField = ({ name, value }) => {
    dispatch(actions.updateConstraintField({constraintName,id, name, value }));
  };
  if (!formSpec) return <div>no formspec</div>;
  return <><Checkbox checked={values.enabled} onClick={(e) => updateField({ name: 'enabled', value: e.target.checked })}/>
    {formSpec.map((spec, i) => {
      if (typeof spec == "string") {
        return <span key={i}>{spec}</span>;
      }
      return (
        <GenericComponent
          key={i}
          dispatch={updateField}
          {...spec}
        />
      );
    })
    }
    <br />
    <DateRangeDialog name='daterange' value={values.daterange} onChange={dispatch} />
    {lastOne ? null : <Button sx={{ margin: 1 }} variant='outlined' size='small' onClick={() => update({ type: 'delete', constraintName, id })}>Remove</Button>}
     </>
}
