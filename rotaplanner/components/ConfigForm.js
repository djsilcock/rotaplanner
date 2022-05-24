import { Button, Checkbox } from "@mui/material";
import React from "react";
import { DateRangeDialog } from "./DateRangeDialog";
import { GenericComponent } from "./GenericComponent";


export function ConfigForm({ formSpec, id, values, constraintName,update,lastOne }) {
  const dispatch = ({ name, value }) => {
    update({ type: "updateField", constraintName,id, name, value });
  };
  if (!formSpec) return <div>no formspec</div>;
  return <><Checkbox checked={values.enabled} onClick={(e) => dispatch({ name: 'enabled', value: e.target.checked })}/>
    {formSpec.map((spec, i) => {
      if (typeof spec == "string") {
        return <span key={i}>{spec}</span>;
      }
      return (
        <GenericComponent
          key={i}
          allValues={values}
          value={values[spec.name]}
          dispatch={dispatch}
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
