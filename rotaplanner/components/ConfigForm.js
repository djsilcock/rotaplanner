import { Button } from "@mui/material";
import React from "react";
import { DateRangeDialog } from "./DateRangeDialog";
import { GenericComponent } from "./GenericComponent";


export function ConfigForm({ formSpec, id, values, update }) {
  const dispatch = ({ name, value }) => {
    update({ type: "updateField", id, name, value });
  };
  if (!formSpec) return <div>no formspec</div>;

  return <>
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
    <Button sx={{ margin: 1 }} variant='outlined' size='small' onClick={() => update({ type: 'delete', id })}>Remove</Button></>
}
