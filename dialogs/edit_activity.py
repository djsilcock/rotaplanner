"Edit activity user interface"

import sys


from typing import cast
from uuid import uuid4
from datetime import time
import functools

from dataclasses import is_dataclass, fields, replace

from PySide6.QtCore import (  # pylint: disable=E0611
    QDateTime, QTime, Qt, Signal)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication, QDialog,
    QDialogButtonBox, QFormLayout, QHBoxLayout, QTimeEdit,
    QLineEdit, QListWidget, QListWidgetItem, QLabel,
    QMessageBox, QPushButton,
    QTreeWidget, QTreeWidgetItem,QTableWidget,QTableWidgetItem,
    QVBoxLayout, QWidget,QGridLayout)

from templating import (GroupType,RuleGroup,DemandTemplate)
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
    return {'dcc': 'DCC',
            'spa': 'SPA',
            'urology': 'Urology',
            'theatre': 'Theatre',
            'icu': 'ICU',
            'oncall': 'On-call'}



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

    def __init__(self, demand_template: DemandTemplate | None = None):
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
        if len(self.date_rule_widget.getRules().children)==0:
            QMessageBox.warning(self, 'Incomplete',
                                'No scheduling rules have been added')
            return
        activity_tags = self.transfer_list.currentSelection()[1]
        if len(activity_tags) == 0:
            if QMessageBox.question(self, 'Really', 'Continue with no tags selected?') == QMessageBox.StandardButton.No:
                return
        self.save_activity.emit(DemandTemplate(
            rules=self.tree.get_tree(),
            id=self.demand_template_id,
            name=self.activity_title_widget.text(),
            activity_tags=activity_tags,
            start_time=cast(
                time, self.activity_start_widget.time().toPython()),
            finish_time=cast(time, self.activity_finish_widget.time().toPython())))
        self.done(QDialog.DialogCode.Accepted)

class EditActivityOfferDialog(QDialog):
    save_activity=Signal()
    def __init__(self):
        super().__init__()
        layout=QFormLayout()
        self.setLayout(layout)
        tree_container=QVBoxLayout()
        tree_widget=QTableWidget(1,7)
        for week in (0,1):
          for day in (0,1,2,3,4,5,6):
            item=QTableWidgetItem()
            item.setText(str(day))
            item.setData(Qt.ItemDataRole.DisplayRole,"🔒This\nis\na\ntool\ntip")
            item.setBackground(QColor(Qt.GlobalColor.blue))
            tree_widget.setItem(week,day,item)
        tree_container.addWidget(tree_widget)
        button_bar=QHBoxLayout()
        button_bar.addWidget(add_day:=QPushButton('Add day'))
        button_bar.addWidget(del_day:=QPushButton('Delete day'))
        button_bar.addWidget(edit_day:=QPushButton('Edit day'))
            
        tree_container.addLayout(button_bar)
        
        rules_widget=DateRuleWidget(RuleGroup())
        layout.addRow('days',tree_container)

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
