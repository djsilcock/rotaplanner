from datetime import date, timedelta
import json
import subprocess
from contextlib import contextmanager

import webview
import webview.menu as wm

from solver import solve
from datastore import DataStore



    

class View:
    "Main view class"
    def __init__(self, datastore=None, pubhols=()):
        self.datastore=datastore if datastore is not None else DataStore()
        self.datastore.pubhols.update(pubhols)
        self.dutytypes = {}
        self.editsession = {}
        self.window = webview.create_window('Hello', url='index.htm')
        @self.window.expose
        def duty_click(name,date,session):
            self.setduty(name,date,session,'ICU')
        @self.window.expose
        def refresh_data():
            print('refresh request')
            return self.update_ui_grid()
        self.menu_items = [
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
    def start(self,debug=False):
        webview.start(menu=self.menu_items,debug=debug)
    def dispatch_action(self,action,payload):
      
      self.window.evaluate_js(
         f'''console.log("dispatching",{json.dumps({"type":action,"payload":payload})})');
          window.store.do_dispatch({json.dumps({'type':action,'payload':payload})})''')

    def update_data(self, data, overwrite=False):
        """update duty data in sheet
        data: dict of (name,date):DutyCell"""
        self.datastore.update_data(data,overwrite)
        self.update_ui_grid()
    def update_ui_grid(self):
        if self.window:
          self.dispatch_action('grid/replaceState',self.datastore.as_dict())
        
    
    def setduty(self,name,d,session,duty):
        "Set duty as determined by menu"
        self.datastore.setduty(name,d,session,duty)
        self.update_ui_grid()

    def setlocum(self,name,d,session,locumtype):
        "Set duty as determined by menu"
        self.datastore.setlocum(name,d,session,locumtype)
        self.update_ui_grid()

    def setlock(self,name,d,session,locktype=None):
        "Set duty as determined by menu"
        self.datastore.setlock(name,d,session,locktype)
        self.update_ui_grid()

    def setph(self,d,value=None):
        "Menu command to toggle day as public holiday"
        match value:
            case None:
                if d in self.datastore.pubhols:
                    self.datastore.pubhols.remove(d)
                else:
                    self.datastore.pubhols.add(d)
            case True:
                self.datastore.pubhols.add(d)
            case False:
                if d in self.datastore.pubhols:
                    self.datastore.pubhols.remove(d)
            case _:
                raise TypeError('setph must be a boolean or None')

    
    
    def onclose(self, *_, **__):
        "Stop the program"
        if mb.askokcancel('Confirm', 'Are you sure?'):
            self.window.destroy()

    def save_data(self):
        "Save data to disc"
        self.datastore.save_data()

    def load_data(self):
        "load from file"
        self.datastore.load_data()

    def solve(self):
        "launch solver in background thread"
        def callback(result):
            self.update_data(result, overwrite=True)
        ftr = solve(self.datastore, {}, callback)
        ftr.add_done_callback(lambda f: f.result())

    def import_clw_csv(self):
        csvfile = fd.askopenfilename()
        if csvfile is None:
            return
        self.datastore.import_clw_csv(csvfile)




d=DataStore()
d.load_data()
ui = View(datastore=d, pubhols={date(2022, 1, 1)})
ui.start(debug=True)