from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QListWidget,QListWidgetItem,QDialogButtonBox

from dialogs.edit_activity import EditActivityDialog
from templating import DemandTemplate

from datastore import DataStore

datastore=DataStore()

class DemandActivityDialog(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.edit_activity_dialog=None
        self.setWindowTitle('Demand Activities')
        button_spec = (
            ('Edit', self.edit_template),
            ('Delete', self.delete_template),
            ('New', self.add_template)
        )
        buttons = {}
        self.buttons=QDialogButtonBox()
        for button_text, button_handler in button_spec:
            button=self.buttons.addButton(button_text,QDialogButtonBox.ButtonRole.ActionRole)
            button.clicked.connect(button_handler)
            buttons[button_text] = button

        self.template_list_widget = QListWidget()
        for tag_id, template in datastore.demand_templates.items():
            item = QListWidgetItem(template.name, self.template_list_widget)
            item.setData(Qt.ItemDataRole.UserRole, tag_id)
            
        layout.addWidget(self.template_list_widget)
        layout.addWidget(self.buttons)
        actionbuttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        layout.addWidget(actionbuttons)
        actionbuttons.accepted.connect(self.do_accept)
        actionbuttons.rejected.connect(self.close)
        self.setLayout(layout)

    def do_accept(self):
        pass        

    def edit_template(self):
        rule_to_edit = self.template_list_widget.currentItem()
        self.edit_activity_dialog = EditActivityDialog(datastore.demand_templates[rule_to_edit.data(Qt.ItemDataRole.UserRole)])
        self.edit_activity_dialog.setModal(True)
        def save_rule(new_template):
            print('saving')
            rule_to_edit.setData(Qt.ItemDataRole.UserRole,new_template.id)
        self.edit_activity_dialog.save_activity.connect(save_rule)
        self.edit_activity_dialog.show()
        

    def delete_template(self):
        item=self.template_list_widget.takeItem(self.template_list_widget.currentRow())
        template_id=item.data(Qt.ItemDataRole.UserRole)
        datastore.delete_demand_template[template_id]
    def add_template(self):
        self.edit_activity_dialog = EditActivityDialog()
        self.edit_activity_dialog.setModal(True)
        def save_rule(new_template:DemandTemplate):
            new_item=QListWidgetItem(new_template.name,self.template_list_widget)
            new_item.setData(Qt.ItemDataRole.UserRole,new_template.id)
            datastore.update_demand_template(new_template)
        self.edit_activity_dialog.save_activity.connect(save_rule)
        self.edit_activity_dialog.show()
