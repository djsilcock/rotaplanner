from datetime import date, timedelta
import json
import subprocess
from contextlib import contextmanager

import webview
import webview.menu as wm

from solver import solve, solver_manager
from datatypes import DutyCell, SessionDuty
from storage import load_data,import_clw_csv,save_data

def output(*args):
    print(*args)
    win.evaluate_js('window.setThis("Now!")')

@contextmanager
def esbuild_handler():
    sp = subprocess.Popen(["yarn", "esbuild", "--bundle", "--watch","--jsx=automatic", "--outfile=../jsfile.js","app.jsx"],
                          shell=True, cwd='./frontend')
    yield
    print('stop esbuild...')
    sp.terminate()
    sp.wait()


class View:
    "Main view class"
    def __init__(self, data=None, pubhols=()):
        self.dates = []
        self.data = {}
        self.names = []
        self.pubhols = set()
        self.pubhols.update(pubhols)
        self.dutytypes = {}
        self.editsession = {}
        self.window=None
    def build_files(self):
      with open('index.htm', 'w') as htmlfile:
        htmlfile.write(f"""
      <html>
      <head>
      </head>
      <body>
      <div id=root></div>
      <script>
      window.initialState={json.dumps(self.update_ui_grid())}
      </script>
      <script src="jsfile.js"></script>
      </body>
      </html>
      """)

    def start(self):
        self.window = webview.create_window('Hello', url='index.htm')
        @self.window.expose
        def duty_click(name,date,session):
            self.setduty(name,date,session,'ICU')
        menu_items = [
        wm.Menu(
            'File',
            [
                wm.MenuAction('Import from CLW export', self.import_clw_csv),
                wm.MenuAction('Save', self.save_data),
                wm.MenuAction('Exit', self.window.destroy),
            ]),
        wm.Menu(
            'Solver',
                    [
                        wm.MenuAction('Solve', self.solve),
                        ]
                )
            ]
        
        webview.start(menu=menu_items,debug=True)
    def dispatch_action(self,action,payload):
      self.window.evaluate_js(f'console.log("dispatching",{json.dumps({"type":action,"payload":payload})})')
      self.window.evaluate_js(f"window.store.dispatch({json.dumps({'type':action,'payload':payload})})")

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
        self.update_ui_grid()
    def update_ui_grid(self):
        data={}
        for (name,day),dutycell in self.data.items():
            cell={}
            for session in ('am','pm','oncall'):
                sessionduty=cell.setdefault(session,{})
                sessiondata:SessionDuty=dutycell.duties.get(session,SessionDuty())
                sessionduty['duty']=sessiondata.duty
                sessionduty['flags']={'locum':sessiondata.locum,'confirmed':sessiondata.locked}
            data[f'{day.isoformat()[0:10]}|{name}']=cell
        state={'data':data,'names':self.names,'dates':[d.isoformat() for d in self.dates]}
        if self.window:
          self.dispatch_action('grid/replaceState',state)
        return state
    
    def setduty(self,name,d,session,duty):
        "Set duty as determined by menu"
        # print(self.sheet.get_selected_cells(), self.sessiontype.get())
        new_duty = duty
        undo_storage = {}
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
            
        self.update_ui_grid()

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
                    self.update_ui_grid()

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
                    self.update_ui_grid()

    def highlight_pubhols(self):
        "Highlight public holidays and weekends"
        self.sheet.dehighlight_columns(columns='all', redraw=True)
        self.sheet.highlight_columns(columns=[i for i, d in enumerate(
            self.dates) if d.weekday() > 4], bg='#ddddff')
        self.sheet.highlight_columns(columns=[i for i, d in enumerate(
            self.dates) if d in self.pubhols], bg='#ffffcc')
        self.sheet.redraw()
        self.sheet.set_all_cell_sizes_to_text()

    def setph(self):
        "Menu command to toggle day as public holiday"
        match self.sheet.get_currently_selected():
            case ('column', col):
                pubhol = self.dates[col]
                if pubhol in self.pubhols:
                    self.pubhols.remove(pubhol)
                else:
                    self.pubhols.add(pubhol)
                self.highlight_pubhols()
            case _:
                warn(
                    f'Expected ("column",col), got {self.sheet.get_currently_selected()}')

    
    
    def onclose(self, *_, **__):
        "Stop the program"
        if mb.askokcancel('Confirm', 'Are you sure?'):
            self.destroy()

    def save_data(self):
        "Save data to disc"
        save_data(self.data)

    def load_data(self):
        "load from file"
        try:

            self.update_data(load_data(), overwrite=True)
        except FileNotFoundError:
            pass

    def solve(self):
        "launch solver in background thread"
        def callback(result):
            self.update_data(result, overwrite=True)
        ftr = solve(self.data, {}, callback)
        ftr.add_done_callback(lambda f: f.result())

    def import_clw_csv(self):
        csvfile = fd.askopenfilename()
        if csvfile is None:
            return
        data = import_clw_csv(csvfile)
        self.update_data(data)


ui = View(data={}, pubhols={date(2022, 1, 1)})
with esbuild_handler():
    ui.load_data()
    ui.build_files()
    ui.start()