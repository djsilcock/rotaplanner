
import sys
from dataclasses import dataclass,replace
from enum import IntEnum

from PySide6.QtCore import (QAbstractTableModel, QDateTime, QModelIndex, Qt,QAbstractItemModel,
                            QTimeZone, Slot,Signal,QDate)
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout,QGridLayout,QHeaderView,QMenu,QTreeWidgetItem,QComboBox,QDateEdit,QDialog,QPushButton,
                               QLabel,QSpinBox,QStackedLayout,QTabWidget,
                               QMainWindow, QSizePolicy, QTableView, QWidget,QTextEdit,QTreeView,QTreeWidget)

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
        self.setColumnCount(2)
        self.setHeaderLabels(['Activities','Time'])
        self.insertTopLevelItems(0, self.add_branches(specialties))
    def add_branches(self,data):
        items=[]
        for key, values in data.items():
            item = QTreeWidgetItem([key])
            item.setFirstColumnSpanned(True)
            item.setCheckState(0,Qt.CheckState.PartiallyChecked)
            item.setFlags(Qt.ItemFlag.ItemIsAutoTristate|Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsUserCheckable)
            if isinstance(values,list):
                for value in values:
                    child = QTreeWidgetItem(value)
                    child.setFlags(Qt.ItemFlag.ItemIsUserCheckable|Qt.ItemFlag.ItemIsEnabled)
                    child.setCheckState(0,Qt.CheckState.Checked)
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
        self.tree=ActivityTree()
        self.rules_window=None
        
        layout.addWidget(self.tree)
    
        button=QPushButton()
        button.setText('Show dialog')
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
    @property
    def data(self) ->RulesData:
        return self._parent.data
    @property
    def model(self) ->'RulesModel':
        return self._parent.model
    def __init__(self,parent):
        super().__init__()
        self.widgets=Widgets()
        self._parent=parent

    def weekday(self,weekday_no=None):
        if weekday_no is None:
            weekday_no=self.data.weekday_no
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
        widget.currentIndexChanged.connect(self.handle_changes)
        return widget
    def make_date_widget(self):
        widget=QDateEdit()
        widget.setCalendarPopup(True)
        widget.dateChanged.connect(self.handle_changes)
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
        anchor_date_label=self.make_label('Starting date')
        self.widgets.anchor_date=self.make_date_widget()
        self.make_grid_layout((
            (interval_label,self.widgets.interval),
            (anchor_date_label,self.widgets.anchor_date)
        ))
    def handle_changes(self):
        self.data.anchor_date=self.widgets.anchor_date.date()
        self.data.interval=self.widgets.interval.currentIndex()+1
        self.signal.emit()
    def reload(self):
        self.widgets.anchor_date.setDate(self.data.anchor_date)
        self.widgets.interval.setCurrentIndex(self.data.interval-1)


class WeeklyRuleWidget(RuleTabWidget):
    def __init__(self,data):
        super().__init__(data)
        weekday_label=self.make_label('Weekday')
        self.widgets.weekday=self.make_combobox(self.weekday(v) for v in range(7))
        interval_label=self.make_label('Frequency')
        self.widgets.interval=self.make_combobox(f'Every {self.get_ordinal(x+1)}week' for x in range(26))
        anchor_date_label=self.make_label('Starting date')
        self.widgets.anchor_date=self.make_date_widget()
        self.make_grid_layout((
            (weekday_label,self.widgets.weekday),
            (interval_label,self.widgets.interval),
            (anchor_date_label,self.widgets.anchor_date)
        ))
    def handle_changes(self):
        self.data.anchor_date=self.widgets.anchor_date.date()
        self.data.interval=self.widgets.interval.currentIndex()+1
        self.data.weekday_no=self.widgets.weekday.currentIndex()
        self.signal.emit()
    def reload(self):
        self.widgets.anchor_date.setDate(self.data.anchor_date)
        self.widgets.interval.setCurrentIndex(self.data.interval-1)
        self.widgets.weekday.setCurrentIndex(self.data.weekday_no)

class MonthlyRuleWidget(RuleTabWidget):
    def __init__(self,data):
        super().__init__(data)
        day_label=self.make_label('Day')
        self.widgets.day=self.make_combobox(self.get_ordinal(v+1,include_1=True) for v in range(31))
        interval_label=self.make_label('Frequency')
        self.widgets.interval=self.make_combobox(f'Every {self.get_ordinal(x+1)}month' for x in range(12))
        anchor_date_label=self.make_label('Starting date')
        self.widgets.anchor_date=self.make_date_widget()
        self.make_grid_layout((
            (day_label,self.widgets.day),
            (interval_label,self.widgets.interval),
            (anchor_date_label,self.widgets.anchor_date)
        ))
    def handle_changes(self):
        self.data.anchor_date=self.widgets.anchor_date.date()
        self.data.interval=self.widgets.interval.currentIndex()+1
        self.data.day=self.widgets.day.currentIndex()+1
        self.signal.emit()
    def reload(self):
        self.widgets.anchor_date.setDate(self.data.anchor_date)
        self.widgets.interval.setCurrentIndex(self.data.interval-1)
        self.widgets.day.setCurrentIndex(self.data.day-1)


class WeekInMonthRuleWidget(RuleTabWidget):
    def __init__(self,data):
        super().__init__(data)
        weekday_label=self.make_label('Weekday')
        self.widgets.weekday=self.make_combobox(self.weekday(v) for v in range(7))
        week_in_month_label=self.make_label('Week')
        self.widgets.week_in_month=self.make_combobox(self.get_ordinal(v+1,include_1=True) for v in range(5))
        interval_label=self.make_label('Frequency')
        self.widgets.interval=self.make_combobox(f'Every {self.get_ordinal(x+1)}month' for x in range(12))
        anchor_date_label=self.make_label('Starting date')
        self.widgets.anchor_date=self.make_date_widget()
        self.make_grid_layout((
            (weekday_label,self.widgets.weekday),
            (week_in_month_label,self.widgets.week_in_month),
            (interval_label,self.widgets.interval),
            (anchor_date_label,self.widgets.anchor_date)
        ))
    def handle_changes(self):
        self.data.anchor_date=self.widgets.anchor_date.date()
        self.data.interval=self.widgets.interval.currentIndex()+1
        self.data.weekday_no=self.widgets.weekday.currentIndex()
        self.data.week_no=self.widgets.week_in_month.currentIndex()+1
        self.signal.emit()
    def reload(self):
        self.widgets.anchor_date.setDate(self.data.anchor_date)
        self.widgets.interval.setCurrentIndex(self.data.interval-1)
        self.widgets.weekday.setCurrentIndex(self.data.weekday_no)
        self.widgets.week_in_month.setCurrentIndex(self.data.week_no-1)

class GroupWidget(RuleTabWidget):
    def __init__(self,data):
        super().__init__(data)
        group_label=self.make_label('Group Type')
        self.widgets.group_type=self.make_combobox(('All must apply','Any can apply','None can apply'))
        self.widgets.add_group=QPushButton()
        self.widgets.add_group.setText('Add group')
        self.widgets.add_group.clicked.connect(self.add_group)
        self.widgets.add_rule=QPushButton()
        self.widgets.add_rule.setText('Add rule')
        self.widgets.add_rule.clicked.connect(self.add_rule)
        self.make_grid_layout((
            (group_label,self.widgets.group_type),
            (None,self.widgets.add_rule),(None,self.widgets.add_group)
        ))
    @Slot()
    def add_group(self):
        self.model.add_rule(self.data,rule_type=RuleType.GROUP)
    @Slot()
    def add_rule(self):
        self.model.add_rule(self.data)
    def handle_changes(self):
        self.data.group_type=self.widgets.group_type.currentIndex()
        self.signal.emit()
    def reload(self):
        self.widgets.group_type.setCurrentIndex(self.data.group_type)

class EditRuleWidget(QWidget):
    signal=Signal()
    reload=Signal()
    def __init__(self,model:QAbstractItemModel):
        super().__init__()
        self.data=RulesData(rule_id=-1)
        self.model=model
        self.tab_layout=QTabWidget()
        self.tabs={
            'Daily':DailyRuleWidget(self),
            'Weekly':WeeklyRuleWidget(self),
            'Monthly':MonthlyRuleWidget(self),
            'Week in Month':WeekInMonthRuleWidget(self),
        }
        self.group_widget=GroupWidget(self)
        self.group_widget.signal.connect(self.model.layoutChanged)
        for name,widget in self.tabs.items():
            self.tab_layout.addTab(widget,name)
            widget.signal.connect(self.signal)
            widget.signal.connect(self.model.layoutChanged)
        self.tab_layout.currentChanged.connect(self.handle_tab_change)
        self.stack=QStackedLayout()
        self.stack.addWidget(self.tab_layout)
        self.stack.addWidget(self.group_widget)
        self.setLayout(self.stack)
        for v in self.tabs.values():
            v.reload()
    @Slot(int)
    def handle_tab_change(self,index):
        self.data.rule_type=index
        self.model.layoutChanged.emit()
    def edit_rule(self,index:QModelIndex):
        rule:RulesData=index.data(Qt.ItemDataRole.UserRole)
        self.data=rule
        for v in self.tabs.values():
            v.reload()
        if rule.rule_type==RuleType.GROUP:
            self.stack.setCurrentWidget(self.group_widget)
        else:
            self.stack.setCurrentWidget(self.tab_layout)
            self.tab_layout.setCurrentIndex(rule.rule_type)
        

class RulesModel(QAbstractItemModel):
    counter=0
    datastore={
        0:RulesData(rule_id=0,rule_type=RuleType.GROUP,group_type=GroupType.AND,children=[1,2,3]),
        1:RulesData(rule_id=1,rule_type=RuleType.GROUP,group_type=GroupType.OR,children=[4,5,6]),
        2:RulesData(rule_id=2,rule_type=RuleType.WEEKLY,weekday_no=0,interval=3,anchor_date=QDate(2024,1,12)),
        3:RulesData(rule_id=3,rule_type=RuleType.DAILY,interval=2,anchor_date=QDate(2024,1,12)),
        4:RulesData(rule_id=4,rule_type=RuleType.MONTHLY,interval=2,day=30,anchor_date=QDate(2024,1,12)),
        5:RulesData(rule_id=5,rule_type=RuleType.MONTHLY,interval=2,day=30,anchor_date=QDate(2024,1,12)),
        6:RulesData(rule_id=6,rule_type=RuleType.MONTHLY,interval=2,day=30,anchor_date=QDate(2024,1,12))}
    
    def index(self,row,col,parent):
        parent_node=self.datastore[parent.internalId()] if parent.isValid() else RulesData(rule_id=-1,children=[0])
        return self.createIndex(row,col,id=parent_node.children[row])
    def delete_rule(self,rule_id):
        for v in self.datastore.values():
            if rule_id in v.children:
                v.children.remove(rule_id)
        self.layoutChanged.emit()
    def update_parents(self):
        new_datastore={}
        for k,v in self.datastore.items():
            for child in v.children:
                new_datastore[child]=replace(self.datastore[child],parent=k)
        self.datastore.update(new_datastore)

    def add_rule(self,parent,**kwargs):
        new_rule_id=max(self.datastore.keys())+1
        orig_children=parent.children
        self.datastore[parent.rule_id]=replace(parent,children=[*orig_children,new_rule_id])
        self.datastore[new_rule_id]=RulesData(**kwargs)
        self.layoutChanged.emit()

    def parent(self,index):
        this_id=index.internalId()
        for k,v in self.datastore.items():
            if this_id in v.children:
                return self.createIndex(v.children.index(this_id),0,id=k)
        return QModelIndex()
    def rowCount(self,index):
        if not index.isValid():
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
    def setData(self,index,value,role):
        if role==Qt.ItemDataRole.UserRole:
            self.datastore[index.internalId()]=value
        self.dataChanged.emit()

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
        model=RulesModel()
        self.tree=RulesView(model)
        self.rule_editor=EditRuleWidget(model)
        self.tree.activated.connect(self.handle_activated)
        self.tree.changed.connect(self.rule_editor.edit_rule)
        layout.addWidget(self.tree)
        layout.addWidget(self.rule_editor)
        
        self.setLayout(layout)
    def handle_activated(self,*args):
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
