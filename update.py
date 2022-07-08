import shelve

with shelve.open('datafile',writeback=True) as db:
    for date,shifts in db.items():
        for shift,names in shifts.items():
            for name,duty in names.items():
                if duty=='DEFINITE_ICU':
                    names[name]='ICU_MAYBE_LOCUM'