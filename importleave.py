from io import StringIO
import csv

def get_duties_list_from_csv(csvdata):
    csvinfo=list(csv.DictReader(StringIO(csvdata)))
    for duty in csvinfo:
        if 'ICU' not in duty['Location']:
            continue
        if duty['Day'] in ['Monday','Tuesday','Wednesday','Thursday','Friday']:
            if duty['Session'] in ['am','pm']:
                yield (duty['Date'],duty['Session'].upper(),duty['Person'],'ICU_MAYBE_LOCUM')
                continue
        #must be a weekend or oncall
        if duty['Session'] in ('eve','night'):
            shift="ONCALL"
        else: 
            shift=duty['Session'].upper()
        sessiontype='DEFINITE_ICU_LOCUM' if duty['Assignment type'] != "" else 'DEFINITE_ICU'
        yield(duty['Date'],shift,duty['Person',sessiontype])
        
            
