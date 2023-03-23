"Main ui module"
from dataclasses import dataclass
from datetime import date, timedelta
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as mb
#import tkinter.filedialog as fd
from typing import Optional, cast
from warnings import warn
from copy import copy, deepcopy
import asyncio

import tksheet

from solver import solve
from datatypes import DutyCell,SessionDuty
import constraints

class View(tk.Tk):
    "Main view class"
    solver:Optional[asyncio.Task]
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
                self.data.setdefault((name,day),DutyCell(duties={}))
        self.sheet.headers([d.isoformat()+'\n' for d in self.dates])
        self.sheet.row_index(self.names)
        self.sheet.set_sheet_data(data=[
            [self.data[(name, day)] for day in self.dates] for name in self.names
        ],
            reset_highlights=False)
        self.highlight_pubhols()
        self.sheet.set_all_cell_sizes_to_text()


    def __init__(self, data=None, pubhols=()):
        super().__init__()
        self.result_queue=asyncio.Queue()
        self.solver=None
        self.dates = []
        self.data = {}
        self.title('Rota Solver')
        self.names = []
        self.pubhols = set()
        self.pubhols.update(pubhols)
        self.dutytypes = {}
        self.frame = ttk.Frame(self, name='maingrid',
                               borderwidth=5, relief=tk.GROOVE)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        # self.frame.grid(row=0, column=0, sticky='nw')
        self.editsession = {}
        self.sessiontype = tk.StringVar()
        self.locumtype = tk.StringVar()
        ttk.Label(self.frame, text='Sessions').grid(
            row=0, column=0, columnspan=2)
        for i, sess in enumerate(('am', 'pm', 'oncall')):
            self.editsession[sess] = tk.BooleanVar()
            ttk.Label(self.frame, text=sess).grid(row=i+1, column=1)
            ttk.Checkbutton(self.frame, variable=self.editsession[sess]).grid(
                row=i+1, column=0)
        buttonframe2 = ttk.Frame(self)
        ttk.Label(buttonframe2, text='Duty type:').grid(row=0, column=0)
        ttk.OptionMenu(buttonframe2, self.sessiontype, 'ICU', 'Theatre', 'NOC', 'Leave',
                       'Timeback', 'Nonclinical').grid(row=0, column=1, sticky='nw')
        ttk.Label(buttonframe2, text='Set locum:').grid(row=1, column=0)
        ttk.OptionMenu(buttonframe2, self.locumtype, 'Yes', 'No',
                       'Maybe').grid(row=1, column=1, sticky='nw')
        # buttonframe2.grid(row=0,column=1,sticky='nw')

        self.sheetframe = ttk.Frame(self, borderwidth=5, relief=tk.GROOVE)
        self.sheetframe.grid_rowconfigure(0, weight=1)
        self.sheetframe.grid_columnconfigure(0, weight=1)
        self.sheet = tksheet.Sheet(
            self.sheetframe,
            empty_horizontal=0,
            empty_vertical=0,
            header_height="2",
            data=[[]])
        self.update_data(data)
        self.sheet.popup_menu_add_command(
            'Set as duty', self.setduty, table_menu=True, header_menu=False)
        self.sheet.popup_menu_add_command(
            'Mark as locum', self.setlocum, table_menu=True, header_menu=False)
        self.sheet.popup_menu_add_command(
            'Lock duty', self.setlock, table_menu=True, header_menu=False)
        self.sheet.popup_menu_add_command(
            'Set public holiday', self.setph,
            header_menu=True, table_menu=False, index_menu=False)
        self.sheet.popup_menu_add_command(
            'Lock', lambda x: print('not implemented'),
            header_menu=True, table_menu=False, index_menu=False)
        self.sheet.enable_bindings("single_select",
                                   "drag_select",
                                   "select_all",
                                   "column_select",
                                   "row_select",
                                   "column_width_resize",
                                   "double_click_column_resize",
                                   "arrowkeys",
                                   "row_height_resize",
                                   "double_click_row_resize",
                                   "right_click_popup_menu",
                                   "rc_select", 'delete', 'undo'
                                   )
        self.sheet.extra_bindings('begin_delete', self.intercept_delete)
        self.sheet.extra_bindings('begin_undo', self.intercept_undo)
        self.sheet.grid(row=0, column=0, sticky='news', padx=5, pady=5)
        self.highlight_pubhols()
        self.sheetframe.grid(row=1, column=0, columnspan=2, sticky='news')
        self.protocol('WM_DELETE_WINDOW', self.onclose)
        menu = tk.Menu(self)
        self.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(
            label='Import from CLW export',
            command=self.save_data
        )
        file_menu.add_command(
            label='Save changes',
            command=self.save_data
        )
        file_menu.add_command(
            label='Exit',
            command=self.destroy
        )

        duty_menu = tk.Menu(menu, tearoff=False)
        duty_type_menu = tk.Menu(duty_menu, tearoff=False)
        for duty in ('ICU', 'Theatre', 'NOC', 'Timeback', 'Leave'):
            duty_type_menu.add_checkbutton(
                onvalue=duty, variable=self.sessiontype, label=duty)
        duty_menu.add_cascade(label='Duty type', menu=duty_type_menu)
        session_type_menu = tk.Menu(duty_menu, tearoff=False)
        for sess in ('am', 'pm', 'oncall'):
            self.editsession[sess] = tk.BooleanVar()
            session_type_menu.add_checkbutton(
                variable=self.editsession[sess], label=sess)
        duty_menu.add_cascade(label='Session type', menu=session_type_menu)
        solve_menu = tk.Menu(menu, tearoff=False)
        solve_menu.add_command(label='Solve', command=self.solve)
        constraint_menu = tk.Menu(solve_menu, tearoff=False)
        constraint_menu.add_command(label='constraint1')
        solve_menu.add_cascade(label='Setup constraints', menu=constraint_menu)
        menu.add_cascade(label='File', menu=file_menu)
        menu.add_cascade(label='Duties', menu=duty_menu)
        menu.add_cascade(label='Solve', menu=solve_menu)
        self.solve()
        
    def intercept_delete(self, evt):
        "Delete cell (before_delete handler)"
        #print('delete', evt)
        undo_storage = {}
        sessions_to_set = [k for k, v in self.editsession.items() if v.get()]
        for box, _ in evt.selectionboxes:
            row1, col1, row2, col2 = box
            for row in range(row1, row2):
                for col in range(col1, col2):
                    cell = self.sheet.get_cell_data(
                        r=row, c=col, return_copy=False)
                    if isinstance(cell, DutyCell):
                        for sess in sessions_to_set:
                            oldduty = cell.duties.pop(sess, None)
                            if oldduty:
                                undo_storage[(row, col, sess)] = cell.duties.pop(
                                    sess, None)
        if undo_storage:
            self.sheet.MT.undo_storage.append(
                ('modify_sessions', undo_storage))
        raise Exception()

    def intercept_undo(self, evt):
        "Handle undo"
        #print('undo', evt)
        match evt.storeddata:
            case ('modify_sessions', sess):
                for (row, col, sess), val in sess.items():
                    #print(('setting', row, col, sess, val))
                    if val:
                        cell = self.sheet.get_cell_data(
                            r=row, c=col, return_copy=False)
                        if isinstance(cell, DutyCell):
                            cell.duties[sess] = val
                            #print('updated cell', cell)
                        else:
                            self.sheet.set_cell_data(r=row, c=col, value=DutyCell(
                                duties={sess: val}), set_copy=False)  # type: ignore

        self.sheet.redraw()
        self.sheet.set_all_cell_sizes_to_text()

    def setduty(self):
        "Set duty as determined by menu"
        #print(self.sheet.get_selected_cells(), self.sessiontype.get())
        sessions_to_set = [k for k, v in self.editsession.items() if v.get()]
        new_duty = self.sessiontype.get()
        undo_storage = {}
        for row, col in self.sheet.get_selected_cells():
            cell = self.sheet.get_cell_data(r=row, c=col, return_copy=False)
            if isinstance(cell, DutyCell):
                for sess in sessions_to_set:
                    old_session = cell.duties.get(sess)
                    if old_session:
                        if old_session.duty != new_duty:
                            undo_storage[row, col, sess] = old_session
                            new_session = SessionDuty(
                                duty=new_duty, locum=old_session.locum, locked=old_session.locked)
                        else:
                            new_session = old_session
                    else:
                        new_session = SessionDuty(
                            duty=new_duty, locum=None, locked=False)
                        undo_storage[row, col, sess] = SessionDuty()
                    cell.duties[sess] = new_session
            else:
                raise Exception('not a dutycell instance')
            if undo_storage:
                self.sheet.MT.undo_storage.append(
                    ('modify_sessions', undo_storage))
        self.sheet.redraw()
        self.sheet.set_all_cell_sizes_to_text()

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

    def setlocum(self):
        "Set locum status as per menu"
        sessions_to_set = [k for k, v in self.editsession.items() if v.get()]
        locumtype = {'Yes': True, 'No': False}.get(self.locumtype.get())
        for row, col in self.sheet.get_selected_cells():
            cell = self.sheet.get_cell_data(r=row, c=col, return_copy=False)
            if isinstance(cell, DutyCell):
                for sess in sessions_to_set:
                    cell.duties.get(sess, SessionDuty(
                        duty="", locum=None, locked=False)).locum = locumtype
        self.sheet.redraw()
        self.sheet.set_all_cell_sizes_to_text()

    def setlock(self):
        "Protect from changes by solver"
        sessions_to_set = [k for k, v in self.editsession.items() if v.get()]

        duties_to_set = []
        for (row, col) in self.sheet.get_selected_cells():
            cell = cast(DutyCell, self.sheet.get_cell_data(
                r=row, c=col, return_copy=False))
            for sess, duty in cell.duties.items():
                if sess in sessions_to_set:
                    duties_to_set.append(duty)
        
        set_lock = any((not duty.locked) for duty in duties_to_set)
        for duty in duties_to_set:
            duty.locked = set_lock
        self.sheet.redraw()
        self.sheet.set_all_cell_sizes_to_text()

    def onclose(self, *_, **__):
        "Stop the program"
        if mb.askokcancel('Confirm', 'Are you sure?'):
            self.destroy()

    def save_data(self):
        "Save data to disc"
        #TODO: implement save data
        warn('Save not implemented yet')

    def solve(self):
        "launch solver in background thread"
        loop=asyncio.get_running_loop()
        loop.run_in_executor(None,solve,deepcopy(self.data), {},self.result_queue,loop)
        

initialdata = {
    ('Adam', date(2021, 1, 1)): DutyCell({'am': SessionDuty('ICU', False, False), 'pm': SessionDuty('ICU', False, False)}),
    ('Ben', date(2022, 2, 1)): DutyCell({'am': SessionDuty('ICU', False, False), 'pm': SessionDuty('ICU', False, False)}),
    ('Charlie', date(2022, 2, 1)): DutyCell({'am': SessionDuty('ICU', False, False), 'pm': SessionDuty('ICU', False, False)}),
    ('Debbie', date(2022, 2, 1)): DutyCell({'am': SessionDuty('ICU', False, False), 'pm': SessionDuty('ICU', False, False)}),
    ('Emma', date(2022, 2, 1)): DutyCell({'am': SessionDuty('ICU', False, False), 'pm': SessionDuty('ICU', False, False)}),
    ('Fiona', date(2022, 2, 1)): DutyCell({'am': SessionDuty('ICU', False, False), 'pm': SessionDuty('ICU', False, False)}),
    ('Gordon',date(2022,1,1)):DutyCell({'am':SessionDuty('THEATRE',False,False)})
}
async def dataqueue(ui:View):
    result_queue=ui.result_queue
    while True:
        ui.update_data(await result_queue.get(),overwrite=True)

async def uiloop():
    "run the main ui loop"
    ui = View(data=initialdata, pubhols={date(2022, 1, 1)})
    updater=asyncio.create_task(dataqueue(ui))
    try:
        while ui.children:
            await asyncio.sleep(0.1)
            ui.update()
    except asyncio.CancelledError:
        ui.destroy()
    finally:
        updater.cancel()

asyncio.run(uiloop())
