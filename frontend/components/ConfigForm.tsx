import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox"
import React from "react";
import { api } from "../lib/store";
import { DateRangeDialog } from "./DateRangeDialog";
import { GenericComponent } from "./GenericComponent";

const { useUpdateConstraintConfigValueMutation,useGetConstraintInterfaceQuery,useRemoveConstraintRuleMutation } = api

export function ConfigForm({id, values, type, lastOne }) {
  const [updater] = useUpdateConstraintConfigValueMutation()
  const [deleteRule] = useRemoveConstraintRuleMutation()
  const {data:formSpec,refetch:refreshFormSpec}=useGetConstraintInterfaceQuery({id,type,...values})
  const updateField = ({ name, value }) => {
    updater({type,id,name,value });
  };
  if (!formSpec) return <div>...</div>;
  return <><Checkbox checked={values.enabled} onClick={(e) => updateField({ name: 'enabled', value: !values.enabled})}/>
    {formSpec.map((spec, i) => {
      if (typeof spec == "string") {
        return <span key={i}>{spec}</span>;
      }
      return (
        <GenericComponent
          key={i}
          onChange={updateField}
          onBlur={refreshFormSpec}
          value={values[spec.name]}
          {...spec}
        />
      );
    })
    }
    <br />
    <DateRangeDialog name='daterange' value={values.daterange} onChange={updateField} />
    {lastOne ? null : <Button sx={{ margin: 1 }} variant='outlined' size='small' onClick={() => deleteRule({ type, id })}>Remove</Button>}
     </>
}
