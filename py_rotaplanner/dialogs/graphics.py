from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QDrag, QPixmap
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout,QPushButton, QWidget,QLabel,QFrame,QScrollArea


class DragButton(QLabel):
    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec(Qt.DropAction.MoveAction)

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        scrollarea=QScrollArea()
        self.blayout = QHBoxLayout()
        self.blayout.addWidget(scrollarea)
        widget=QWidget()
        widget_layout=QVBoxLayout()
        for no,outer in enumerate((1,2,3)):
          inner_layout=QVBoxLayout()
          widget_layout.addLayout(inner_layout)
          inner_layout.addWidget(QLabel(f'Day {no}'))
          for i,l in enumerate(["A\nB", "B", "C", "D"][0:outer]):
            innermost_layout=QVBoxLayout()
            frame=QFrame()
            frame.setFrameStyle(QFrame.Shape.Box|QFrame.Shadow.Sunken)
            pb=QPushButton(l)
            innermost_layout.addWidget(pb,stretch=i)
            frame.setLayout(innermost_layout)
            inner_layout.addWidget(frame)
            
          #inner_layout.addStretch()
        widget.setLayout(widget_layout)
        scrollarea.setWidget(widget)
        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        e.accept()
    def dropEvent(self, e):
        pos = e.position()
        widget = e.source()
        self.blayout.removeWidget(widget)

        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            if pos.y() < w.y():
                # We didn't drag past this widget.
                # insert to the left of it.
                break
        else:
            # We aren't on the left hand side of any widget,
            # so we're at the end. Increment 1 to insert after.
            n += 1
        self.blayout.insertWidget(n, widget)

        e.accept()

app = QApplication([])
w = Window()
w.show()

app.exec()