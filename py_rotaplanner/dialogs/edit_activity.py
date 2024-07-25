"Edit activity user interface"

import sys


from typing import cast
from uuid import uuid4
from datetime import time
import functools
from contextlib import contextmanager
from datastore import datastore

from dataclasses import is_dataclass, fields, replace

from PySide6.QtCore import (  # pylint: disable=E0611
    QDateTime, QTime, Qt, Signal)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication, QDialog,QComboBox,
    QDialogButtonBox, QFormLayout, QHBoxLayout, QTimeEdit,
    QLineEdit, QListWidget, QListWidgetItem, QLabel,QSpinBox,
    QMessageBox, QPushButton,QRadioButton,QButtonGroup,
    QTreeWidget, QTreeWidgetItem,QTableWidget,QTableWidgetItem,QGroupBox,
    QVBoxLayout, QWidget,QGridLayout)

from templating import (GroupType,RuleGroup,DemandTemplate,SupplyTemplate,SupplyTemplateEntry)
from dialogs.date_rules import DateRuleWidget


def populate_dataclass(datacls, values):
    field_values = {f.name: values[f.name]
                    for f in fields(datacls) if f.name in values}
    if isinstance(datacls, type):
        return datacls(**field_values)
    return replace(datacls, **field_values)


specialties = {
    'dcc': {
        'theatre': {
            'urology': [('Reid', '8-1'), ('Dunn', '8-1')],
            'general': [('Macdonald', '1-5'), ('Dick', '1-5')]
        },
        'icu': [('daytime', '8-6'), ('oncall', '5-8')]}
}


class ActivityTree(QTreeWidget):
    "Widget showing tree view of activities"

    def __init__(self):
        super().__init__()
        self.setColumnCount(1)
        # self.setHeaderLabels(['Activities','Time'])
        self.insertTopLevelItems(0, self.add_branches(specialties))

    def add_branches(self, data):
        "iteratively build tree from data"
        items = []
        for key, values in data.items():
            item = QTreeWidgetItem([key])
            if isinstance(values, list):
                for value in values:
                    child = QTreeWidgetItem([f"{value[0]} ({value[1]})"])
                    # child.setFlags(Qt.ItemFlag.ItemIsUserCheckable|Qt.ItemFlag.ItemIsEnabled)
                    # child.setCheckState(0,Qt.CheckState.Checked)
                    item.addChild(child)
            if isinstance(values, dict):
                for i in self.add_branches(values):
                    item.addChild(i)
            items.append(item)
        return items


def get_activity_tags():
    activities={act.id:f'Activity:{act.name}' for act in datastore.get_demand_templates()}
    activities.update( {'dcc': 'DCC',
            'spa': 'SPA',
            'urology': 'Urology',
            'theatre': 'Theatre',
            'icu': 'ICU',
            'oncall': 'On-call'})
    return activities



class TransferListWidget(QWidget):
    def __init__(self,options,__available='Available',**selected):
        super().__init__()
        columns=len(selected)
        listboxvalues=[set(options.keys())]
        listboxheaders=[__available]
        for header,s in selected.items():
            if not s.issubset(listboxvalues[0]):
                raise ValueError('sets must not have common items and must all be valid options')
            listboxvalues[0].difference_update(s)
            listboxvalues.append(s)
            listboxheaders.append(header.replace('_',' ').capitalize())
        self.listboxes=[]
        transfer_list_layout=QGridLayout()
        def move_all_items(from_list,to_list):
            while from_list.count()>0:
                to_list.addItem(from_list.takeItem(0))
        def move_item(from_list,to_list):    
            for item in from_list.selectedItems():
                to_list.addItem(from_list.takeItem(from_list.indexFromItem(item).row()))
        for i,s in enumerate(listboxvalues):
            listbox=QListWidget()
            self.listboxes.append(listbox)
            listbox.setSortingEnabled(True)
            for tag_id in s:
                item = QListWidgetItem(options[tag_id], listbox)
                item.setData(Qt.ItemDataRole.UserRole, tag_id)
            if i>0:
                transfer_buttons_layout=QVBoxLayout()
                transfer_buttons_layout.addWidget(transfer_right:=QPushButton('>'))
                transfer_buttons_layout.addWidget(transfer_all_right:=QPushButton('>>'))
                transfer_buttons_layout.addWidget(transfer_all_left:=QPushButton('<<'))
                transfer_buttons_layout.addWidget(transfer_left:=QPushButton('<'))
                transfer_left.clicked.connect(functools.partial(move_item,self.listboxes[i],self.listboxes[i-1]))
                transfer_right.clicked.connect(functools.partial(move_item,self.listboxes[i-1],self.listboxes[i]))
                transfer_all_left.clicked.connect(functools.partial(move_all_items,self.listboxes[i],self.listboxes[i-1]))
                transfer_all_right.clicked.connect(functools.partial(move_all_items,self.listboxes[i-1],self.listboxes[i]))
                transfer_list_layout.addLayout(transfer_buttons_layout,1,i*2-1)
            transfer_list_layout.addWidget(listbox,1,i*2)
            transfer_list_layout.addWidget(QLabel(listboxheaders[i]),0,i*2)

        self.setLayout(transfer_list_layout)
    def currentSelection(self):
        return [{listbox.item(i).data(Qt.ItemDataRole.UserRole) for i in range(listbox.count())} for listbox in self.listboxes]


class EditActivityDialog(QDialog):
    save_activity = Signal(DemandTemplate)
    date_rule_widget=None
    def __init__(self, demand_template: DemandTemplate | None = None,with_date_rules=True):
        super().__init__()
        self.rules_dialog = None
        layout = QVBoxLayout()
        if demand_template is None:
            demand_template = DemandTemplate(
                rules=RuleGroup(group_type=GroupType.AND),
                name='',
                id=str(uuid4()),
                start_time=time(8, 0),
                finish_time=time(17, 0),
                activity_tags=set()
            )
        self.demand_template_id = demand_template.id
        self.setWindowTitle('Add activity')

        self.activity_title_widget = QLineEdit()
        self.activity_title_widget.setText(demand_template.name)
        title_layout = QFormLayout()
        title_layout.addRow('Activity title', self.activity_title_widget)
        self.activity_start_widget = QTimeEdit(
            QTime(demand_template.start_time.hour, demand_template.start_time.minute))
        self.activity_finish_widget = QTimeEdit(
            QTime(demand_template.finish_time.hour, demand_template.finish_time.minute))
        title_layout.addRow('Start time', self.activity_start_widget)
        title_layout.addRow('Finish time', self.activity_finish_widget)
        layout.addLayout(title_layout)
        if with_date_rules:
            self.date_rule_widget=DateRuleWidget(demand_template.rules)
            title_layout.addRow('Date Rules',self.date_rule_widget)
        self.transfer_list=TransferListWidget(get_activity_tags(),selected=demand_template.activity_tags)
        title_layout.addRow('Tags',self.transfer_list)
        actionbuttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(actionbuttons)
        actionbuttons.accepted.connect(self.do_accept)
        actionbuttons.rejected.connect(self.close)
        self.setLayout(layout)

    def do_accept(self):
        if len(self.activity_title_widget.text()) == 0:
            QMessageBox.warning(self, 'Incomplete',
                                'Please enter a title for this activity')
            return
        if self.date_rule_widget and len(self.date_rule_widget.get_rules().children)==0:
            QMessageBox.warning(self, 'Incomplete',
                                'No scheduling rules have been added')
            return
        activity_tags = self.transfer_list.currentSelection()[1]
        if len(activity_tags) == 0:
            if QMessageBox.question(self, 'Really', 'Continue with no tags selected?') == QMessageBox.StandardButton.No:
                return
        self.save_activity.emit(DemandTemplate(
            rules=self.date_rule_widget.tree.get_tree() if self.date_rule_widget else None,
            id=self.demand_template_id,
            name=self.activity_title_widget.text(),
            activity_tags=activity_tags,
            start_time=cast(
                time, self.activity_start_widget.time().toPython()),
            finish_time=cast(time, self.activity_finish_widget.time().toPython())))
        self.done(QDialog.DialogCode.Accepted)


@contextmanager
def ctx(v):
    yield v

class EditActivityOfferEntryDialog(QDialog):
    save_activity = Signal(SupplyTemplateEntry)
    def __init__(self, supply_template: SupplyTemplateEntry | None = None):
        super().__init__()
        self.rules_dialog = None
        layout = QVBoxLayout()
        if supply_template is None:
            supply_template = SupplyTemplateEntry(
                dateoffset=1,
                activity_tags=set(),
                id=str(uuid4())
            )
        self.supply_template_id = supply_template.id
        self.setWindowTitle('Add activity')

        self.template_day = QSpinBox()
        self.template_day.setMinimum(1)
        title_layout = QFormLayout()
        title_layout.addRow('Template day', self.template_day)
        
        layout.addLayout(title_layout)

        self.transfer_list=TransferListWidget(get_activity_tags(),selected=supply_template.activity_tags)
        activities_layout=QVBoxLayout()
        activities_layout.addWidget(self.transfer_list)
        title_layout.addRow('Available activities',activities_layout)
        actionbuttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(actionbuttons)
        actionbuttons.accepted.connect(self.do_accept)
        actionbuttons.rejected.connect(self.close)
        self.setLayout(layout)
    def add_wildcard(self):
        self.rules_dialog=EditActivityDialog(with_date_rules=False)
        self.rules_dialog.setModal(True)
        self.rules_dialog.open()
    def do_accept(self):
        
        self.save_activity.emit(SupplyTemplateEntry(
            dateoffset=self.template_day.value(),
            activity_tags=self.transfer_list.currentSelection()[1],
            id=self.supply_template_id
        ))
        self.done(QDialog.DialogCode.Accepted)

class EditActivityOfferDialog(QDialog):
    save_activity = Signal(SupplyTemplate)
    def __init__(self, supply_template:SupplyTemplate | None = None):
        super().__init__()
        self.rules_dialog = None
        layout = QVBoxLayout()
        if supply_template is None:
            supply_template=SupplyTemplate(
                staff=set(),
                rules=RuleGroup(group_type=GroupType.AND),
                entries=(),
                name='',
                id=str(uuid4()))           
        self.supply_template_id = supply_template.id
        self.setWindowTitle('Add activities')

        self.staff_member = QComboBox()
        self.staff_member.addItem('fred','fred')
        self.activity_title_widget = QLineEdit()
        self.activity_title_widget.setText(supply_template.name)
        title_layout = QFormLayout()
        title_layout.addRow('Activity title', self.activity_title_widget)
        
        title_layout.addRow('Staff member', self.staff_member)
        
        layout.addLayout(title_layout)

        self.date_rule_widget=DateRuleWidget(supply_template.rules)
        title_layout.addRow('Date Rules',self.date_rule_widget)
        self.transfer_list=QTreeWidget()
        self.transfer_list.setColumnCount(2)
        self.transfer_list.setHeaderLabels(('Day','Activity'))
        activities=get_activity_tags()
            
        for activity in supply_template.entries:
            item=QTreeWidgetItem(self.transfer_list)
            item.setText(0,str(activity.dateoffset))
            item.setText(1,','.join(activities[tag] for tag in activity.activity_tags))
            item.setData(0,Qt.ItemDataRole.UserRole,activity)
        activities_layout=QVBoxLayout()
        activities_layout.addWidget(self.transfer_list)
        button_layout=QHBoxLayout()
        button_layout.addWidget(add_activity:=QPushButton('Add activity...'))
        button_layout.addWidget(edit_activity:=QPushButton('Add rest...'))
        button_layout.addWidget(del_activity:=QPushButton('Remove activity'))
        add_activity.clicked.connect(self.add_activity)
        del_activity.clicked.connect(self.del_activity)
        activities_layout.addLayout(button_layout)
        title_layout.addRow('Activities',activities_layout)
        
        actionbuttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(actionbuttons)
        actionbuttons.accepted.connect(self.do_accept)
        actionbuttons.rejected.connect(self.close)
        self.setLayout(layout)
    def del_activity(self):
        current_item=self.transfer_list.currentIndex()
        self.transfer_list.takeTopLevelItem(current_item.row())
    def add_activity(self):
        self.rules_dialog=EditActivityOfferEntryDialog()
        self.rules_dialog.setModal(True)
        self.rules_dialog.show()
        def add(new_activity:SupplyTemplateEntry):
            item=QTreeWidgetItem(self.transfer_list)
            item.setText(0,str(new_activity.dateoffset))
            activities=get_activity_tags()
            item.setText(1,','.join(activities[tag] for tag in new_activity.activity_tags))
            item.setData(0,Qt.ItemDataRole.UserRole,new_activity)
        self.rules_dialog.save_activity.connect(add)
    def do_accept(self):
        if len(self.activity_title_widget.text()) == 0:
            QMessageBox.warning(self, 'Incomplete',
                                'Please enter a title for this template')
            return
        if len(self.date_rule_widget.get_rules().children)==0:
            QMessageBox.warning(self, 'Incomplete',
                                'No scheduling rules have been added')
            return
        activities = [self.transfer_list.topLevelItem(i).data(0,Qt.ItemDataRole.UserRole) for i in range(self.transfer_list.topLevelItemCount())]
        if len(activities) == 0:
            QMessageBox.warning(self, 'Incomplete', 'No activities have been selected')
            return
        self.save_activity.emit(SupplyTemplate(
            staff={self.staff_member.currentData(Qt.ItemDataRole.UserRole)},
            rules=self.date_rule_widget.get_rules(),
            id=self.supply_template_id,
            name=self.activity_title_widget.text(),
            entries=tuple(activities),
            ))
        self.done(QDialog.DialogCode.Accepted)


def transform_date(utc, timezone=None):
    utc_fmt = "yyyy-MM-ddTHH:mm:ss.zzzZ"
    new_date = QDateTime().fromString(utc, utc_fmt)
    if timezone:
        new_date.setTimeZone(timezone)
    return new_date


if __name__ == "__main__":
    # Qt Application
    app = QApplication([])
    window = EditActivityDialog()
    window.show()
    sys.exit(app.exec())
