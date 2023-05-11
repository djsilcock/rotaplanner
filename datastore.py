from datatypes import DutyCell, SessionDuty
from storage import load_data,import_clw_csv,save_data
from datetime import date, timedelta

class DataStore:
    def __init__(self):
        self.data={}
        self.names=[]
        self.dates=[]
        self.pubhols=set()
    def update_data(self, data, overwrite=False):
        """update duty data in sheet
        data: dict of (name,date):DutyCell"""
        if overwrite:
            self.data.clear()
        self.data.update(data)
        mindate = min((key[1] for key in self.data),
                      default=date.today())
        maxdate = max((key[1] for key in self.data),
                      default=date.today())
        self.dates = [mindate+timedelta(days=i)
                      for i in range((maxdate-mindate).days+1)]
        self.names = sorted({d[0] for d in self.data})
        for day in self.dates:
            for name in self.names:
                self.data.setdefault((name, day), DutyCell(duties={}))
    def as_dict(self):
        data={}
        for (name,day),dutycell in self.data.items():
            cell={}
            for session in ('am','pm','oncall'):
                sessionduty=cell.setdefault(session,{})
                sessiondata:SessionDuty=dutycell.duties.get(session,SessionDuty())
                sessionduty['duty']=sessiondata.duty
                sessionduty['flags']={'locum':sessiondata.locum,'confirmed':sessiondata.locked}
            data[f'{day.isoformat()[0:10]}|{name}']=cell
        state={'data':data,'names':self.names,'dates':[d.isoformat() for d in self.dates],'pubhols':[ph.isoformat() for ph in self.pubhols]}
        return state
    def setduty(self,name,d,session,duty):
        "Set duty as determined by menu"
        # print(self.sheet.get_selected_cells(), self.sessiontype.get())
        new_duty = duty
        cell = self.data.get((name,date.fromisoformat(d)))
        if isinstance(cell, DutyCell):
            old_session = cell.duties.get(session)
            if old_session:
                if old_session.duty != new_duty:
                    new_session = SessionDuty(
                        duty=new_duty, locum=old_session.locum, locked=old_session.locked)
                else:
                    new_session = old_session
            else:
                new_session = SessionDuty(
                    duty=new_duty, locum=None, locked=False)
                
            cell.duties[session] = new_session
        else:
                raise TypeError('not a dutycell instance')
            

    def setlocum(self,name,d,session,locumtype):
        "Set duty as determined by menu"
        # print(self.sheet.get_selected_cells(), self.sessiontype.get())
        new_duty = locumtype
        undo_storage = {}
        cell = self.data.get((name,date.fromisoformat(d)))
        if isinstance(cell, DutyCell):
            old_session = cell.duties.get(session)
            if old_session:
                if old_session.locum != new_duty and old_session.duty:
                    new_session = SessionDuty(
                        duty=new_duty, locum=old_session.locum, locked=old_session.locked)
                    cell.duties[session] = new_session

    def setlock(self,name,d,session,locktype=None):
        "Set duty as determined by menu"
        # print(self.sheet.get_selected_cells(), self.sessiontype.get())    
        undo_storage = {}
        cell = self.data.get((name,date.fromisoformat(d)))
        if isinstance(cell, DutyCell):
            old_session = cell.duties.get(session)
            if old_session:
                new_lock=locktype if locktype is not None else not old_session.locked
                if old_session.duty:
                    new_session = SessionDuty(
                        duty=old_session.duty, locum=old_session.locum, locked=new_lock)
                    cell.duties[session] = new_session
    def save_data(self):
        "Save data to disc"
        save_data(self.data)
    def load_data(self):
        "load from file"
        try:
            self.update_data(load_data(), overwrite=True)
        except FileNotFoundError:
            pass
    def import_clw_csv(self,csvfile):
        self.update_data(import_clw_csv(csvfile))
