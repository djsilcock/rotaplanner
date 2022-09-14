import shelve

with shelve.open('datafile',writeback=True) as db:
    for date in db:
        try:
            am=db[date]['DAYTIME']
            pm=db[date]['DAYTIME']
            oc=db[date]['ONCALL']
            db[date]={'AM':am,'PM':pm,'ONCALL':oc}
        except KeyError:
            pass
        