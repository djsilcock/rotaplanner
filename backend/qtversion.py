
import sys

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Slot,Qt
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout,QHeaderView,QMenu,QPushButton,
                               QMainWindow, QSizePolicy, QTableView, QWidget)

import datetime

from dialogs.edit_activity import EditActivityDialog
from dialogs.demand_activities import DemandActivityDialog

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
        self.rules_window=DemandActivityDialog()
        self.rules_window.show()


if __name__ == "__main__":
    # Qt Application
    app = QApplication([])
    widget = Widget()
    window = MainWindow(widget)
    window.show()
    sys.exit(app.exec())
