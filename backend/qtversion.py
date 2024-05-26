
import sys
from dataclasses import dataclass,replace
from enum import IntEnum
from typing import cast

from PySide6.QtCore import (QAbstractTableModel, QDateTime, QModelIndex, Qt,QAbstractItemModel,
                            QTimeZone, Slot,Signal,QDate)
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout,QGridLayout,QHeaderView,QMenu,QTreeWidgetItem,QComboBox,QDateEdit,QDialog,QPushButton,
                               QLabel,QSpinBox,QStackedLayout,QTabWidget,QFormLayout,QLineEdit,QListWidget,QAbstractItemView,
                               QMainWindow, QSizePolicy, QTableView, QWidget,QTextEdit,QTreeView,QTreeWidget,QDialogButtonBox)

import datetime

def get_ordinal(number,include_1=False):
        if number<2 and not include_1:
            return ''
        if number%100 > 3 and number%100 < 20:
            return f'{number}th '
        if number%10<4:
            return f"{number}{['th ','st ','nd ','rd '][number%10]}"
        return f'{number}th '
    

class CustomTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        QAbstractTableModel.__init__(self)
        self.column_count=365
        self.row_count=5

    def load_data(self, data):
        self.input_dates = [1,2,3,4,5]
        self.input_magnitudes = [1,2,3,4,5]

        self.column_count = 2
        self.row_count = len(self.input_magnitudes)

    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return (datetime.date(2024,1,1)+datetime.timedelta(days=section)).isoformat()
        else:
            return ('Adam','Bob','Charlie','Dave','Eric','Fred','George')[section]

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()

        if role == Qt.DisplayRole:
            return "yes"
        elif role == Qt.BackgroundRole:
            return QColor(Qt.white)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight

        return None

class CustomTableView(QTableView):
    @Slot()
    def selectionChanged(self,old,new):
        super().selectionChanged(old,new)
        print([(index.row(),index.column()) for index in old.indexes()],new)

    def contextMenuEvent(self, event):
        # Show the context menu
        context_menu=QMenu(self)
        for index in self.selectedIndexes():
            context_menu.addAction(f'{index.row()},{index.column()}')
        context_menu.exec(event.globalPos())
 
    def action1_triggered(self):
        # Handle the "Action 1" action
        pass
 
    def action2_triggered(self):
        # Handle the "Action 2" action
        pass
 
    def action3_triggered(self):
        # Handle the "Action 3" action
        pass

class Widget(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        # Getting the Model
        self.model = CustomTableModel()

        # Creating a QTableView
        self.table_view = CustomTableView()
        self.table_view.setModel(self.model)
        # QTableView Headers
        self.horizontal_header = self.table_view.horizontalHeader()
        self.vertical_header = self.table_view.verticalHeader()
        self.horizontal_header.setSectionResizeMode(
                               QHeaderView.ResizeToContents
                               )
        self.vertical_header.setSectionResizeMode(
                             QHeaderView.ResizeToContents
                             )
        self.horizontal_header.setStretchLastSection(False)

        # QWidget Layout
        self.main_layout = QHBoxLayout()
        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        ## Left layout
        size.setHorizontalStretch(1)
        self.table_view.setSizePolicy(size)
        self.main_layout.addWidget(self.table_view)

        # Set the layout to the QWidget
        self.setLayout(self.main_layout)

specialties={
            'dcc':{
                'theatre':{
                    'urology':[('Reid','8-1'),('Dunn','8-1')],
                    'general':[('Macdonald','1-5'),('Dick','1-5')]
                    },
                'icu':[('daytime','8-6'),('oncall','5-8')]}
        }

class ActivityTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(1)
        #self.setHeaderLabels(['Activities','Time'])
        self.insertTopLevelItems(0, self.add_branches(specialties))
    def add_branches(self,data):
        items=[]
        for key, values in data.items():
            item = QTreeWidgetItem([key])
            #item.setFirstColumnSpanned(True)
            #item.setCheckState(0,Qt.CheckState.PartiallyChecked)
            #item.setFlags(Qt.ItemFlag.ItemIsAutoTristate|Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsUserCheckable)
            if isinstance(values,list):
                for value in values:
                    child = QTreeWidgetItem([f"{value[0]} ({value[1]})"])
                    #child.setFlags(Qt.ItemFlag.ItemIsUserCheckable|Qt.ItemFlag.ItemIsEnabled)
                    #child.setCheckState(0,Qt.CheckState.Checked)
                    item.addChild(child)
            if isinstance(values,dict):
                for i in self.add_branches(values):
                    item.addChild(i)
            items.append(item)
        return items

class MainWindow(QMainWindow):
    def __init__(self, widget):
        QMainWindow.__init__(self)
        self.setWindowTitle("Earthquakes information")
        #self.setCentralWidget(widget)
        layout=QVBoxLayout()
        layout.addWidget(widget)
        self.rules_window=None
    
        button=QPushButton()
        button.setText('Add Demand')
        button.clicked.connect(self.show_dialog)
        layout.addWidget(button)
        
        main_widget=QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")

        ## Exit QAction
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)

        self.file_menu.addAction(exit_action)

        # Status Bar
        self.status = self.statusBar()
        self.status.showMessage("Data loaded and plotted yeah")

        # Window dimensions
        geometry = self.screen().availableGeometry()
        self.setFixedSize(geometry.width() * 0.8, geometry.height() * 0.7)
    
    @Slot()
    def show_dialog(self):
        self.rules_window=RuleWidget()
        self.rules_window.show()

class RuleType(IntEnum):
    DAILY=0
    WEEKLY=1
    MONTHLY=2
    WEEK_IN_MONTH=3
    GROUP=4

class GroupType(IntEnum):
    AND=0
    OR=1
    NOT=2

@dataclass
class RulesData():
    rule_id:int
    parent:int=None
    anchor_date:QDate=None
    interval:int=1
    weekday_no:int=0
    day:int=1
    rule_type:RuleType=RuleType.WEEKLY
    group_type:GroupType=GroupType.AND
    week_no:int=1
    children:list=None
    def __post_init__(self):
        if self.anchor_date is None:
            self.anchor_date=QDate(2024,1,1)
        if isinstance(self.anchor_date,tuple):
            self.anchor_date=QDate(*self.anchor_date)
        if self.children is None:
            self.children=[]
    def text(self):
        def weekday(i):
            return 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()[i]
        if self.rule_type==RuleType.GROUP:
            return{
                GroupType.AND:'All of...',
                GroupType.OR:'Any of...',
                GroupType.NOT:'None of...'
            }[self.group_type]
        anchor_date=datetime.date(*self.anchor_date.getDate())
        ruletext=""
        if self.rule_type<2:
            ruletext=f'every {get_ordinal(self.interval)}{["day",weekday(self.weekday_no),"month"][self.rule_type]}'
        if self.rule_type==2:
            ruletext=f'the {get_ordinal(self.day,include_1=True)} of every {get_ordinal(self.interval)}{["day",weekday(self.weekday_no),"month"][self.rule_type]}'
        if self.rule_type==3:
            ruletext=f'the {get_ordinal(self.week_no,include_1=True)}{weekday(self.weekday_no)} of every {get_ordinal(self.interval)}month'
        return f'{ruletext} starting {anchor_date.strftime("%d/%m/%Y")}'

class Widgets:
    interval:QComboBox
    anchor_date:QDateEdit
    weekday:QComboBox
    day:QComboBox
    week_in_month:QComboBox
    group_type:QComboBox
    add_group:QPushButton
    add_rule:QPushButton

class RuleTabWidget(QWidget):
    signal=Signal()
    def __init__(self,parent):
        super().__init__()
        self.widgets=Widgets()
        self._parent=parent

    def weekday(self,weekday_no):
        return "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()[weekday_no]
        
    def get_ordinal(self,number,include_1=False):
        if number<2 and not include_1:
            return ''
        if number%100 > 3 and number%100 < 20:
            return f'{number}th '
        if number%10<4:
            return f"{number}{['th ','st ','nd ','rd '][number%10]}"
        return f'{number}th '
    
    
    
    def make_combobox(self,values):
        widget=QComboBox()
        for i,x in enumerate(values):
            widget.insertItem(i,x)
        return widget
    def make_date_widget(self):
        widget=QDateEdit()
        widget.setCalendarPopup(True)
        return widget
    def make_label(self,text):
        label=QLabel()
        label.setText(text)
        return label
    def make_grid_layout(self,items):
        layout=QGridLayout()
        for row,row_items in enumerate(items):
            for column,item in enumerate(row_items):
                if item is not None:
                    layout.addWidget(item,row,column)
        layout.setColumnMinimumWidth(1,200)
        self.setLayout(layout)
        return layout

class DailyRuleWidget(RuleTabWidget):
    def __init__(self,data):
        super().__init__(data)
        interval_label=self.make_label('Frequency')
        self.widgets.interval=self.make_combobox(f'Every {self.get_ordinal(x+1)}day' for x in range(30))
        self.make_grid_layout((
            (interval_label,self.widgets.interval),
        ))
    def populate(self,data):
        data.interval=self.widgets.interval.currentIndex()+1
    def set_values(self,data):
        self.widgets.interval.setCurrentIndex(data.interval-1)

class WeeklyRuleWidget(RuleTabWidget):
    def __init__(self,data):
        super().__init__(data)
        weekday_label=self.make_label('Weekday')
        self.widgets.weekday=self.make_combobox(self.weekday(v) for v in range(7))
        interval_label=self.make_label('Frequency')
        self.widgets.interval=self.make_combobox(f'Every {self.get_ordinal(x+1)}week' for x in range(26))
        self.make_grid_layout((
            (weekday_label,self.widgets.weekday),
            (interval_label,self.widgets.interval),
        ))
    def populate(self,data):
        data.interval=self.widgets.interval.currentIndex()+1
        data.weekday_no=self.widgets.weekday.currentIndex()
        
    def set_values(self,data):
        self.widgets.interval.setCurrentIndex(data.interval-1)
        self.widgets.weekday.setCurrentIndex(data.weekday_no)

class MonthlyRuleWidget(RuleTabWidget):
    def __init__(self,data):
        super().__init__(data)
        day_label=self.make_label('Day')
        self.widgets.day=self.make_combobox(self.get_ordinal(v+1,include_1=True) for v in range(31))
        interval_label=self.make_label('Frequency')
        self.widgets.interval=self.make_combobox(f'Every {self.get_ordinal(x+1)}month' for x in range(12))
        self.make_grid_layout((
            (day_label,self.widgets.day),
            (interval_label,self.widgets.interval),
        ))
    def populate(self,data):
        data.interval=self.widgets.interval.currentIndex()+1
        data.day=self.widgets.day.currentIndex()+1
    def set_values(self,data):
        self.widgets.interval.setCurrentIndex(data.interval-1)
        self.widgets.day.setCurrentIndex(data.day-1)

class WeekInMonthRuleWidget(RuleTabWidget):
    def __init__(self,data):
        super().__init__(data)
        weekday_label=self.make_label('Weekday')
        self.widgets.weekday=self.make_combobox(self.weekday(v) for v in range(7))
        week_in_month_label=self.make_label('Week')
        self.widgets.week_in_month=self.make_combobox(self.get_ordinal(v+1,include_1=True) for v in range(5))
        interval_label=self.make_label('Frequency')
        self.widgets.interval=self.make_combobox(f'Every {self.get_ordinal(x+1)}month' for x in range(12))
        self.make_grid_layout((
            (weekday_label,self.widgets.weekday),
            (week_in_month_label,self.widgets.week_in_month),
            (interval_label,self.widgets.interval)
            ))
    def populate(self,data):
        data.interval=self.widgets.interval.currentIndex()+1
        data.weekday_no=self.widgets.weekday.currentIndex()
        data.week_no=self.widgets.week_in_month.currentIndex()+1
        
    def set_values(self,data):
        self.widgets.interval.setCurrentIndex(data.interval-1)
        self.widgets.weekday.setCurrentIndex(data.weekday_no)
        self.widgets.week_in_month.setCurrentIndex(data.week_no-1)

class GroupWidget(RuleTabWidget):
    def __init__(self,data):
        super().__init__(data)
        group_label=self.make_label('Group Type')
        self.widgets.group_type=self.make_combobox(('All must apply','Any can apply','None can apply'))
        self.make_grid_layout((
            (group_label,self.widgets.group_type),
        ))
    def populate(self,data):
        data.group_type=self.widgets.group_type.currentIndex()
        
    def set_values(self,data):
        self.widgets.group_type.setCurrentIndex(data.group_type)

class PopulatingWidget(QWidget):
    tab_widget:QTabWidget
    def populate(self,data):
        self.tab_widget.currentWidget().populate(data)

class EditRuleDialog(QDialog):
    data:RulesData
    signal=Signal()
    reload=Signal()
    
    def __init__(self,data):
        super().__init__()
        self.data=replace(data)
        layout=QVBoxLayout()
        if self.data.rule_type==RuleType.GROUP:
            self.widget=GroupWidget(self)
        else:
            self.widget=PopulatingWidget()
            self.widget.setLayout(QVBoxLayout())

            self.widget.tab_widget=QTabWidget()
            tabs={
                'Daily':DailyRuleWidget(self),
                'Weekly':WeeklyRuleWidget(self),
                'Monthly':MonthlyRuleWidget(self),
                'Week in Month':WeekInMonthRuleWidget(self),
            }
            for name,widget in tabs.items():
                self.widget.tab_widget.addTab(widget,name)
                widget.set_values(data)
            self.widget.tab_widget.currentChanged.connect(self.handle_tab_change)
            self.widget.tab_widget.setCurrentIndex(data.rule_type)
            form=QFormLayout()
            start_date=QDateEdit()
            start_date.setCalendarPopup(True)
            start_date.setDate(self.data.anchor_date)
            finish_date=QDateEdit()
            finish_date.setCalendarPopup(True)
            form.addRow('Starting date',start_date)
            form.addRow('Finishing date',finish_date)
            form_widget=QWidget()
            form_widget.setLayout(form)
            self.widget.layout().addWidget(form_widget)
            self.widget.layout().addWidget(self.widget.tab_widget)
        layout.addWidget(self.widget)
        actionbuttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        def handle_accept():
            self.accepted.emit()
        actionbuttons.accepted.connect(handle_accept)
        actionbuttons.rejected.connect(self.rejected)
        actionbuttons.accepted.connect(lambda:self.done(QDialog.DialogCode.Accepted))
        actionbuttons.rejected.connect(lambda:self.done(QDialog.DialogCode.Rejected))
        layout.addWidget(actionbuttons)
        self.setLayout(layout)
    def populate(self):
        self.widget.populate(self.data)

        
    @Slot(int)
    def handle_tab_change(self,index):
        self.data.rule_type=index
        

class RulesModel(QAbstractItemModel):
    counter=0
    datastore:dict[int,RulesData]={
        0:RulesData(rule_id=0,rule_type=RuleType.GROUP,group_type=GroupType.AND,children=[1,2,3]),
        1:RulesData(rule_id=1,rule_type=RuleType.GROUP,group_type=GroupType.OR,children=[4,5,6]),
        2:RulesData(rule_id=2,rule_type=RuleType.WEEKLY,weekday_no=0,interval=3,anchor_date=QDate(2024,1,12)),
        3:RulesData(rule_id=3,rule_type=RuleType.DAILY,interval=2,anchor_date=QDate(2024,1,12)),
        4:RulesData(rule_id=4,rule_type=RuleType.MONTHLY,interval=2,day=30,anchor_date=QDate(2024,1,12)),
        5:RulesData(rule_id=5,rule_type=RuleType.MONTHLY,interval=2,day=30,anchor_date=QDate(2024,1,12)),
        6:RulesData(rule_id=6,rule_type=RuleType.MONTHLY,interval=2,day=30,anchor_date=QDate(2024,1,12))}
    
    def get_new_index(self):
        return max(self.datastore.keys())+1
    def index(self,row,col,parent):
        parent_node=self.datastore[parent.internalId()] if parent.isValid() else RulesData(rule_id=-1,children=[0])
        return self.createIndex(row,col,id=parent_node.children[row])
    def removeRows(self,start_row,count,parent=QModelIndex()):
        if not parent.isValid(): return False
        parent_node:RulesData=parent.data(Qt.ItemDataRole.UserRole)
        child_rules=parent_node.children[start_row:start_row+count]
        if len(child_rules)==0:
            return False
        for rule in child_rules:
            self.delete_rule(rule)
        return True

    def delete_rule(self,rule_id):
        for key,v in self.datastore.items():
            if rule_id in v.children:
                self.datastore[key]=replace(v,children=[c for c in v.children if c!=rule_id])
                break
        del self.datastore[rule_id]
        self.layoutChanged.emit()
    def update_parents(self):
        new_datastore={}
        for k,v in self.datastore.items():
            for child in v.children:
                if new_datastore[child].parent is None:
                    new_datastore[child]=replace(self.datastore[child],parent=k)
        self.datastore.update(new_datastore)
    def get_parent_for_node(self,node:RulesData):
        for v in self.datastore.values():
            if node.rule_id in v.children:
                return v
        return None

    def add_rule(self,new_rule:RulesData):
        if new_rule.rule_id is None:
            new_rule.rule_id=self.get_new_index()
        parent_node=self.datastore[new_rule.parent]
        print (new_rule.rule_id)
        parent=self.datastore[parent_node.rule_id]
        orig_children=parent.children
        if new_rule.rule_id not in orig_children:
            self.datastore[parent.rule_id]=replace(parent,children=[*orig_children,new_rule.rule_id])
        self.datastore[new_rule.rule_id]=replace(new_rule,rule_id=new_rule.rule_id)
        self.layoutChanged.emit()
        return self.createIndex(len(orig_children),0,id=new_rule.rule_id)

    def parent(self,index):
        this_id=index.internalId()
        for k,v in self.datastore.items():
            if this_id in v.children:
                return self.createIndex(v.children.index(this_id),0,id=k)
        return QModelIndex()
    
    def get_index_for_node(self,node:RulesData):
        parent_node= self.get_parent_for_node(node) 
        if parent_node is not None:
            row=parent_node.children.index(node.rule_id)
        else:
            row=0
        return self.createIndex(row,0,id=node.rule_id)
    
    def rowCount(self,index):
        if not index.isValid():  # this is the root node
            return 1
        else:
            item=self.datastore[index.internalId()]
        return len(item.children)
    
    def columnCount(self,*args):
        return 1
    def data(self,index,role):
        
        if role==Qt.ItemDataRole.DisplayRole:
            return self.datastore[index.internalId()].text()
        if role==Qt.ItemDataRole.UserRole:
            return self.datastore[index.internalId()]
    def setData(self,index,value:RulesData,role):
        if role==Qt.ItemDataRole.UserRole:
            if value.rule_id is None:
                self.add_rule(value)
            self.datastore[index.internalId()]=value
        self.layoutChanged.emit()

class RulesView(QTreeView):
    changed=Signal(QModelIndex)
    def __init__(self,model):
        super().__init__()
        self.setModel(model)
        self.setHeaderHidden(True)
    def currentChanged(self,new,old):
        self.changed.emit(new)

class RuleWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout=QVBoxLayout()
        self.model=RulesModel()
        self.tree=RulesView(self.model)
        self.buttons=QWidget()
        self.buttons_layout=QHBoxLayout()
        button_spec=(
            ('Edit',self.edit_rule),
            ('Delete',self.delete_rule),
            ('Add rule',self.add_rule),
            ('Add group',self.add_group)
        )
        buttons={}
        for button_text,button_handler in button_spec:
            button=QPushButton()
            button.setText(button_text)
            button.clicked.connect(button_handler)
            self.buttons_layout.addWidget(button)
            buttons[button_text]=button

        self.buttons.setLayout(self.buttons_layout)
        self.activity_title_widget=QLineEdit()
        title_layout=QFormLayout()
        title_layout.addRow('Activity title',self.activity_title_widget)
        layout.addLayout(title_layout)
        layout.addWidget(self.tree)
        layout.addWidget(self.buttons)
        actionbuttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(actionbuttons)
        list_widget=QListWidget()
        #list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        list_widget.addItem('Hello')
        list_widget.addItem('Hello')
        for item in range(list_widget.count()):
            list_widget.item(item).setFlags(list_widget.item(item).flags()|Qt.ItemFlag.ItemIsUserCheckable)
            list_widget.item(item).setCheckState(Qt.CheckState.Unchecked)
        
        layout.addWidget(list_widget)
        self.setLayout(layout)
        
    def edit_rule(self):
        rule_to_edit=self.tree.currentIndex()
        self.tree.setExpanded(rule_to_edit,True)
        dialog=EditRuleDialog(rule_to_edit.data(Qt.ItemDataRole.UserRole))
        dialog.setModal(True)
        def save_rule():
            print('saving')
            model=rule_to_edit.model()
            dialog.populate()
            model.setData(rule_to_edit,dialog.data,Qt.ItemDataRole.UserRole)
        dialog.accepted.connect(save_rule)
        dialog.show()

    def delete_rule(self):
        rule_to_delete=self.tree.currentIndex()
        model=rule_to_delete.model()
        model.removeRow(rule_to_delete.row(),rule_to_delete.parent())

    def add_rule(self,rule_type=0):
        parent_index=self.tree.currentIndex()
        if parent_index.data(Qt.ItemDataRole.UserRole).rule_type!=RuleType.GROUP:
            parent_index=parent_index.parent()
        parent_node:RulesData=parent_index.data(Qt.ItemDataRole.UserRole)
        self.tree.setExpanded(parent_index,True)
        model=cast(RulesModel,parent_index.model())
        new_rule_id=model.get_new_index()
        dialog=EditRuleDialog(RulesData(rule_id=None,rule_type=rule_type,parent=parent_node.rule_id))
        dialog.setModal(True)
        def add_rule():
            dialog.populate()
            model.add_rule(dialog.data)
        dialog.accepted.connect(add_rule)
        dialog.show()
    def add_group(self):
        return self.add_rule(RuleType.GROUP)
    


    def handle_activate(self,*args):
        print ('activated',args)
    def handle_changed(self,*args):
        print ('changed',args)

def transform_date(utc, timezone=None):
    utc_fmt = "yyyy-MM-ddTHH:mm:ss.zzzZ"
    new_date = QDateTime().fromString(utc, utc_fmt)
    if timezone:
        new_date.setTimeZone(timezone)
    return new_date

def read_data(fname):
    # Read the CSV content
    df = pd.read_csv(fname)

    # Remove wrong magnitudes
    df = df.drop(df[df.mag < 0].index)
    magnitudes = df["mag"]

    # My local timezone
    timezone = QTimeZone(b"Europe/Berlin")

    # Get timestamp transformed to our timezone
    times = df["time"].apply(lambda x: transform_date(x, timezone))

    return times, magnitudes

if __name__ == "__main__":
    # Qt Application
    app = QApplication([])
    widget = Widget()
    window = MainWindow(widget)
    window.show()
    sys.exit(app.exec())
