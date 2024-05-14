import webview
import templating
import humps
from datetime import date,timedelta
from datastore import DataStore
import threading
from templating import DemandTemplate
from uuid import uuid4
from dataclasses import asdict

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


class DemandTemplateWindow():
    def __init__(self,datastore:DataStore):
        self._datastore=datastore
        self._window=None
        self._event=threading.Event()
    def create_window(self):
        self._window=webview.create_window('Demand Templates','http://localhost:5173',js_api=self)
        self._window.events.closed+=lambda:self._event.set()
        return self._event
    def get_page(self):
        return 'template'
    def date_matches(self,day,ruleid,rules):
        return templating.rule_matches(day,ruleid,humps.decamelize(rules))
    def get_dates_matching_rules(self,month,year,rules):
        return list(batcher(templating.make_calendar(month,year,humps.decamelize(rules)),7))
    def get_demand_templates_for_week(self,day):
        day=date.fromisoformat(day)
        return humps.camelize([list(self._datastore.get_templates_for_day(day+timedelta(days=i),as_dict=True)) for i in range(7)])
    def get_demand_templates(self):
        return humps.camelize(
            {'default':{'id':None,
            'name':'Untitled',
            'start':8,
            'finish':17,
            'activity':None,
            'rules':{ 'root': { 'ruleId': 'root', 'ruleType': 'group', 'groupType': 'and', 'rules': [] } }
            },'templates':list(self._datastore.get_demand_templates(as_dict=True))})
    def update_demand_template(self,data):
        data=humps.decamelize(data)
        errors=templating.DemandTemplate.validate(data)
        if len(errors)>0:
            return {'errors':errors}
        self._datastore.update_demand_template(data)
        return {'status':'ok'}
    def new_template(self):
        return self.edit_template(None)
    def edit_template(self,template_id):
        event=DemandTemplateDialog(self._datastore,template_id).create_window()
        event.wait()


class DemandTemplateDialog():
    def __init__(self,datastore,template_id):
        self._datastore=datastore
        self._window=None
        self._event=threading.Event()
        if template_id is not None:
            self._template=datastore.get_demand_template(template_id)
        else:
            self._template=DemandTemplate(rules={},name="Unititled",id=str(uuid4()),start=8,finish=17,activity_type='general')
    def create_window(self):
        self._window=webview.create_window('Edit Demand Template','http://localhost:5173',js_api=self)
        self._window.events.closed+=self._event.set
        return self._event
    def get_page(self):
        return 'demand_dialog'
    def get_demand_template(self):
        return asdict(self._template)

def edit_demand_templates(datastore):
    controller=DemandTemplateWindow(datastore=datastore)
    event=controller.create_window()
    event.wait()