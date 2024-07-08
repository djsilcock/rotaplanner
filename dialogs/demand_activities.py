from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QListWidget,QListWidgetItem,QDialogButtonBox

from dialogs.edit_activity import EditActivityDialog,EditActivityOfferDialog
from templating import DemandTemplate

from datastore import DataStore

datastore=DataStore()



class GenericActivityDialog(QDialog):
    window_title=NotImplemented
    edit_dialog_class=NotImplemented
    def get_template(self) ->dict:
        raise NotImplementedError
    def get_templates(self):
        raise NotImplementedError
    def update_template(self):
        raise NotImplementedError
    def delete_template_from_datastore(self):
        raise NotImplementedError
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.edit_activity_dialog=None
        self.setWindowTitle(self.window_title)
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
        for tag_id, template in self.get_templates().items():
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
        self.edit_activity_dialog = self.edit_dialog_class(self.get_template(rule_to_edit.data(Qt.ItemDataRole.UserRole)))
        self.edit_activity_dialog.setModal(True)
        def save_rule(new_template):
            print('saving')
            rule_to_edit.setData(Qt.ItemDataRole.UserRole,new_template.id)
        self.edit_activity_dialog.save_activity.connect(save_rule)
        self.edit_activity_dialog.show()
        

    def delete_template(self):
        item=self.template_list_widget.takeItem(self.template_list_widget.currentRow())
        template_id=item.data(Qt.ItemDataRole.UserRole)
        self.delete_template_from_datastore(template_id)
    def add_template(self):
        self.edit_activity_dialog = self.edit_dialog_class()
        self.edit_activity_dialog.setModal(True)
        def save_rule(new_template):
            new_item=QListWidgetItem(new_template.name,self.template_list_widget)
            new_item.setData(Qt.ItemDataRole.UserRole,new_template.id)
            self.update_template(new_template)
        self.edit_activity_dialog.save_activity.connect(save_rule)
        self.edit_activity_dialog.show()

class DemandActivityDialog(GenericActivityDialog):

    edit_dialog_class=EditActivityDialog
    window_title="Demand Activities"
    def delete_template_from_datastore(self,template_id):
        datastore.delete_demand_template(template_id)
    def get_template(self,template_id):
        return datastore.get_demand_template(template_id)
    def update_template(self,new_template):
        datastore.update_demand_template(new_template)
    def get_templates(self):
        return datastore.datastore.demand_templates
    

class SupplyActivityDialog(GenericActivityDialog):
    edit_dialog_class=EditActivityOfferDialog
    window_title="Supply offer templates"
    def delete_template_from_datastore(self,template_id):
        datastore.delete_supply_template(template_id)
    def get_template(self,template_id):
        return datastore.get_supply_template(template_id)
    def update_template(self,new_template):
        datastore.update_supply_template(new_template)
    def get_templates(self):
        return datastore.datastore.supply_templates
    