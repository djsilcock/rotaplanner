from datetime import date,timedelta
import webview
import webview.menu as wm
from datastore import DataStore
import templating
import humps
import os
import pathlib

from pages.demand_templates import edit_demand_templates

datastore = DataStore()
datastore.load_data()
pubhols = {date(2022, 1, 1)}
datastore.pubhols.update(pubhols)
dutytypes = {}
editsession = {}

def batcher(it,size):
    it=iter(it)
    while True:
        try:
            out=[]
            for x in range(size):
                out.append(next(it))
            yield out
        except StopIteration:
            yield out

class MainPage():
    def get_page(self):
        return 'rota'
    def by_name(self):
        "get all data"
        return datastore.as_dict_by_name()
    def get_duty_for_staff_and_date(self,staff,day):
        return datastore.for_staff_and_date(staff,day)
    def get_table_config(self):
        return datastore.get_config()
    def set_activity(self,name,dutydate,activity):
        datastore.set_activity(name,dutydate,activity)
    def del_activity(self,name,dutydate,activity):
        datastore.clear_activity(name,dutydate,activity)
    def date_matches(self,day,ruleid,rules):
        return templating.rule_matches(day,ruleid,humps.decamelize(rules))
    def get_dates_matching_rules(self,month,year,rules):
        return list(batcher(templating.make_calendar(month,year,humps.decamelize(rules)),7))
    def get_demand_templates_for_week(self,day):
        day=date.fromisoformat(day)
        return humps.camelize([list(datastore.get_templates_for_day(day+timedelta(days=i),as_dict=True)) for i in range(7)])
    def get_demand_templates(self):
        return humps.camelize(
            {'default':{'id':None,
            'name':'Untitled',
            'start':8,
            'finish':17,
            'activity':None,
            'rules':{ 'root': { 'ruleId': 'root', 'ruleType': 'group', 'groupType': 'and', 'rules': [] } }
            },'templates':list(datastore.get_demand_templates(as_dict=True))})
    def update_demand_template(self,data):
        data=humps.decamelize(data)
        errors=templating.DemandTemplate.validate(data)
        if len(errors)>0:
            return {'errors':errors}
        datastore.update_demand_template(data)
        return {'status':'ok'}
        


def edit_supply_templates():
    pass

index_html=pathlib.Path(os.getcwd(),"..","frontend","dist","index.html")

#window = webview.create_window('Woah dude!',str(index_html),js_api=MainPage())
window = webview.create_window('Woah dude!','http://localhost:5173',js_api=MainPage())


menu_items = [
        wm.Menu(
            'Templates',
            [
                wm.MenuAction('Edit demand templates', lambda:edit_demand_templates(datastore)),
                wm.MenuAction('Edit supply templates', edit_supply_templates),
                wm.MenuSeparator(),
                wm.Menu(
                    'Random',
                    [
                        wm.MenuAction('Click Me', lambda:None),
                        wm.MenuAction('File Dialog', lambda:None),
                    ],
                ),
            ],
        ),
        wm.Menu('Nothing Here', [wm.MenuAction('This will do nothing', lambda:None)]),
    ]

def mainloop():
    pass

webview.start(func=mainloop,debug=True,menu=menu_items)