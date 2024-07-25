
import sys

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Slot,Qt
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout,QHeaderView,QMenu,QPushButton,QMessageBox,
                               QMainWindow, QSizePolicy, QTableView, QWidget)

import datetime
import random
import string

from dialogs.edit_activity import EditActivityDialog
from dialogs.demand_activities import DemandActivityDialog,SupplyActivityDialog

from templating import get_templates_for_date_range

from datastore import datastore


def get_ordinal(number,include_1=False):
        if number<2 and not include_1:
            return ''
        if number%100 > 3 and number%100 < 20:
            return f'{number}th '
        if number%10<4:
            return f"{number}{['th ','st ','nd ','rd '][number%10]}"
        return f'{number}th '
    

class CustomTableModel(QAbstractTableModel):
    start_date=datetime.date(2024,1,1)
    def __init__(self, data=None):
        QAbstractTableModel.__init__(self)
        self.column_count=365
        datastore.subscribe(self.layoutChanged.emit)

    def rowCount(self, parent=QModelIndex()):
        return len(datastore.names)+1

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return (self.start_date+datetime.timedelta(days=section)).isoformat()
        else:
            if section==len(datastore.names):
                return '(uncovered)'
            return datastore.names[section]

    def data(self, index, role=Qt.DisplayRole):

        column = index.column()
        row = index.row()
        if row==len(datastore.names):
            staff=None
        else:
            staff=datastore.names[index.row()]
        day=self.start_date+datetime.timedelta(days=index.column())
        if staff is None:
            all_activities=set(activity.id for activity in datastore.get_activities_for_day(day))
            for staffmember in datastore.names:
                all_activities.difference_update(set(datastore.for_staff_and_date(staffmember,day)))
            activities=[act for t in all_activities if (act:=datastore.get_activity(t))]
        else:
            activities=[act for t in datastore.for_staff_and_date(staff,day) if (act:=datastore.get_activity(t))is not None]
        if role == Qt.ItemDataRole.ToolTipRole:
                return '\n'.join(a.name for a in activities)
        
        elif role == Qt.BackgroundRole:
            return QColor(Qt.GlobalColor.white)
        
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight
        elif role == Qt.ItemDataRole.DisplayRole:
            if len(activities)==0:
                return '-'
            if len(activities)>1:
                return f'{sorted(activities,key=lambda a:a.start_time)[0].name} (+{len(activities)-1})'

            return activities[0].name
        elif role == Qt.ItemDataRole.UserRole:
            return (staff,self.start_date+datetime.timedelta(days=index.column()))
        return None
    

class CustomTableView(QTableView):
        
    def contextMenuEvent(self, event):
        # Show the context menu
        context_menu=QMenu(self)
        dates:list[datetime.date]=[self.model().data(index,Qt.ItemDataRole.UserRole)[1] for index in self.selectedIndexes()]
        activities=set.intersection(*[{activity.id for activity in datastore.get_activities_for_day(date)} for date in dates])
        activities=sorted((datastore.get_activity(template_id) for template_id in activities),key=lambda a:a.start_time)
        def handle_menuclick(action):
            for index in self.selectedIndexes():
                name,day=self.model().data(index,Qt.ItemDataRole.UserRole)
                datastore.toggle_activity(name,day,action.data())
            self.resizeRowsToContents()
        for a in activities:
            menutext=a.name
            item=context_menu.addAction(menutext)
            item.setData(a.id)
        context_menu.triggered.connect(handle_menuclick)
        context_menu.exec(event.globalPos())
 
    
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


class MainWindow(QMainWindow):
    def __init__(self, widget):
        QMainWindow.__init__(self)
        self.setWindowTitle("Rota solver")
        #self.setCentralWidget(widget)
        layout=QVBoxLayout()
        layout.addWidget(widget)
        self.rules_window=None
    
        
        main_widget=QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")
        self.template_menu=self.menu.addMenu('Templating')
        edit_demand=QAction('Demand templates...',self)
        edit_demand.triggered.connect(self.show_demand_dialog)
        self.template_menu.addAction(edit_demand)
        
        edit_supply=QAction('Supply templates...',self)
        edit_supply.triggered.connect(self.show_supply_dialog)
        self.template_menu.addAction(edit_supply)

        manage_expectations=QAction('Expectations...',self)
        manage_expectations.triggered.connect(self.not_implemented)
        self.template_menu.addAction(manage_expectations)
        

        
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
    def show_demand_dialog(self):
        self.rules_window=DemandActivityDialog()
        self.rules_window.setModal(True)
        self.rules_window.show()
    def show_supply_dialog(self):
        self.rules_window=SupplyActivityDialog()
        self.rules_window.setModal(True)
        self.rules_window.show()

    def not_implemented(self):
        return QMessageBox.warning(self,'Under construction',"This bit isn't built yet")

if __name__ == "__main__":
    # Qt Application
    app = QApplication([])
    widget = Widget()
    window = MainWindow(widget)
    window.show()
    sys.exit(app.exec())
