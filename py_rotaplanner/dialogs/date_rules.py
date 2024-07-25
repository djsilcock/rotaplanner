"Edit activity user interface"

import sys


from typing import cast
from uuid import uuid4
from datetime import date, time, timedelta
import functools

from dataclasses import is_dataclass, fields, replace

from PySide6.QtCore import (  # pylint: disable=E0611
    QDateTime, QTime, Qt, Signal)
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication, QDialog,
    QDialogButtonBox, QFormLayout, QHBoxLayout, QTimeEdit,
    QLineEdit, QListWidget, QListWidgetItem, QLabel,
    QMessageBox, QPushButton,
    QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,QGridLayout)

from templating import (DailyRule, GroupType, MonthlyRule, Rule, RuleGroup,  # pylint: disable=import-error
                        DateRangeRule, DateTagsRule, DateType,
                        RuleType, WeekInMonthRule, WeeklyRule, DemandTemplate)

from dialogs.forms import Form, ComboBoxField, DateField, RadioButtonField, HiddenField  # pylint: disable=import-error


def get_ordinal(number, include_1=False):
    """convert 1,2,3 etc to 1st,2nd,3rd
    param:include_1: if false then generates blank space for 1 
    (ie for every month, every second month etc)"""
    if number < 2 and not include_1:
        return ''
    if number % 100 > 3 and number % 100 < 20:
        return f'{number}th '
    if number % 10 < 4:
        return f"{number}{['th ','st ','nd ','rd '][number%10]}"
    return f'{number}th '



def rule_text(rule):
    "generate explanatory text for rule"
    match rule:
        case RuleGroup():
            return {
                GroupType.AND: 'All of...',
                GroupType.OR: 'Any of...',
                GroupType.NOT: 'None of...'
            }[rule.group_type]

        case DailyRule(day_interval=day_interval) | {'rule_type': RuleType.DAILY, 'day_interval': day_interval}:
            return f'every {get_ordinal(day_interval)}day'
        case WeeklyRule(
                week_interval=week_interval, anchor_date=anchor_date) | {'rule_type': RuleType.WEEKLY, 'week_interval': week_interval, 'anchor_date': anchor_date}:
            return f'every {get_ordinal(week_interval)}{weekday(anchor_date.weekday())}'
        case MonthlyRule(
                month_interval=month_interval, anchor_date=anchor_date) | {'rule_type': RuleType.MONTHLY, 'month_interval': month_interval, 'anchor_date': anchor_date}:
            return f'the {get_ordinal(anchor_date.day,include_1=True)} of every {get_ordinal(month_interval)}month'
        case WeekInMonthRule(month_interval=month_interval, anchor_date=anchor_date) | {'rule_type': RuleType.WEEK_IN_MONTH, 'month_interval': month_interval, 'anchor_date': anchor_date}:
            week_no = anchor_date.day//7+1
            return f'the {get_ordinal(week_no,include_1=True)}{weekday(anchor_date.weekday())} of every {get_ordinal(month_interval)}month'
        case DateRangeRule(start_date=start_date, finish_date=finish_date) | {'rule_type': RuleType.DATE_RANGE, 'start_date': start_date, 'finish_date': finish_date}:
            return f'is between {start_date.strftime("%d/%m/%Y")} and {finish_date.strftime("%d/%m/%Y")}'
        case _:
            return ""


def weekday(weekday_no: int):
    """day of week as text
    weekday_no: Day of week (Monday=0) """
    return "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()[weekday_no]


class GroupForm(Form):
    group_type = RadioButtonField(
        label='Group Type',
        values={GroupType.AND: 'All must apply',
                GroupType.OR: 'Any can apply',
                GroupType.NOT: 'None can apply'})
    rule_type = HiddenField(default_value=RuleType.GROUP)


class RuleForm(Form):
    rule_type = ComboBoxField(
        label='Rule type',
        values={
            RuleType.DAILY: 'Daily',
            RuleType.WEEKLY: 'Weekly',  # ,WeeklyRuleWidget(data)),
            RuleType.MONTHLY: 'Monthly',  # MonthlyRuleWidget(data)),
            # WeekInMonthRuleWidget(data)),
            RuleType.WEEK_IN_MONTH: 'Week in Month',
            RuleType.DATE_RANGE: 'Date Range',  # DateRangeWidget(data)),
            RuleType.DATE_TAGS: 'Date Tags',  # DateRangeWidget(data)),
        },
        default_value=RuleType.DAILY
    )
    day_interval = ComboBoxField(
        values={x: f'Every {get_ordinal(x)}day' for x in range(1, 31)},
        label='Frequency',
        is_visible=lambda x: x['rule_type'] == RuleType.DAILY,
        default_value=1
    )
    week_interval = ComboBoxField(
        label='Frequency',
        values={x: f'Every {get_ordinal(x)}week' for x in range(1, 27)},
        is_visible=lambda x: x['rule_type'] == RuleType.WEEKLY,
        default_value=1)
    anchor_date = DateField(
        label='Including date',
        is_visible=lambda x: x['rule_type'] in (
            RuleType.WEEKLY, RuleType.DAILY, RuleType.MONTHLY, RuleType.WEEK_IN_MONTH),
        default_value=date.today())

    month_interval = ComboBoxField(label='Frequency', values={x: f'Every {get_ordinal(x)}month' for x in range(1, 13)},
                                   is_visible=lambda x: x['rule_type'] in (
                                       RuleType.MONTHLY, RuleType.WEEK_IN_MONTH),
                                   default_value=1)
    start_date = DateField(label='Starting Date',
                           is_visible=lambda x: x['rule_type'] == RuleType.DATE_RANGE,
                           default_value=date.today(),
                           maximum=lambda v: v['finish_date'])
    finish_date = DateField(label='Finishing Date',
                            is_visible=lambda x: x['rule_type'] == RuleType.DATE_RANGE,
                            default_value=date.today(),
                            minimum=lambda v: v['start_date'])
    range_type = RadioButtonField(
        label='Date range type',
        values={DateType.INCLUSIVE: 'Include these dates',
                DateType.EXCLUSIVE: 'Exclude these dates'},
        is_visible=lambda x: x['rule_type'] == RuleType.DATE_RANGE,
        default_value=DateType.INCLUSIVE)


class ValidationError(ValueError):
    pass


class EditRuleDialog(QDialog):
    signal = Signal()
    reload = Signal()
    on_save = Signal(Rule)
    group_widget = None

    def __init__(self, data: Rule):
        super().__init__()
        self.original_rule = data
        layout = QVBoxLayout()
        self.explanation = QLabel()
        if data.rule_type == RuleType.GROUP:
            self.form = GroupForm()
        else:
            self.form = RuleForm()
            self.form.values.subscribe(self.generate_explanation)
        self.form.populate(data)
        layout.addWidget(self.form.form())
        layout.addWidget(self.explanation)
        self.explanation.setText('This is the explanation')
        actionbuttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        actionbuttons.accepted.connect(self.handle_save)
        actionbuttons.rejected.connect(self.on_cancel)
        layout.addWidget(actionbuttons)
        self.setLayout(layout)

    def generate_explanation(self, key, value):
        self.explanation.setText(rule_text(self.form.values))

    def handle_save(self):
        print('save handler')
        rule = None

        def check_not_incomplete(*field_names):
            for f in field_names:
                if self.form.values[f] is None:
                    raise ValidationError('please complete all the fields')
        match dict(self.form.values):
            case {'rule_type': RuleType.DAILY, 'day_interval': day_interval,'anchor_date':anchor_date}:
                rule = DailyRule(day_interval=day_interval)
            case {'rule_type': RuleType.WEEKLY, 'week_interval': week_interval,'anchor_date':anchor_date}:
                rule = WeeklyRule(week_interval=week_interval,anchor_date=anchor_date)
            case {'rule_type': RuleType.WEEK_IN_MONTH, 'month_interval': month_interval,'anchor_date':anchor_date}:
                rule = WeekInMonthRule(
                    month_interval=month_interval, anchor_date=anchor_date)
            case {'rule_type': RuleType.MONTHLY, 'month_interval': month_interval,'anchor_date':anchor_date}:
                rule = MonthlyRule(month_interval=month_interval)
            case {'rule_type': RuleType.DATE_RANGE, 'start_date': start_date, 'finish_date': finish_date, 'range_type': range_type}:
                check_not_incomplete('start_date', 'finish_date', 'range_type')
                rule = DateRangeRule(
                    start_date=start_date, finish_date=finish_date, range_type=range_type)
            case {'rule_type': RuleType.DATE_TAGS, 'label': label, 'date_type': date_type}:
                check_not_incomplete('date_type', 'label')
                rule = DateTagsRule(label=label, date_type=date_type)
            case {'rule_type': RuleType.GROUP, 'group_type': group_type}:
                check_not_incomplete('group_type')
                assert is_dataclass(self.original_rule)
                assert not isinstance(self.original_rule, type)
                rule = replace(self.original_rule, group_type=group_type)
            case _:
                raise ValueError('unrecognised form entry')
        self.done(QDialog.DialogCode.Accepted)
        self.on_save.emit(rule)

    def on_cancel(self):
        self.done(QDialog.DialogCode.Rejected)


default_rules_tree = RuleGroup(group_type=GroupType.AND)


class RulesView:
    def __init__(self, rules):
        self.treeview = QTreeWidget()
        def make_rules_tree(node):
            item = QTreeWidgetItem()
            item.setData(0, Qt.ItemDataRole.UserRole, node)
            item.setData(0, Qt.ItemDataRole.DisplayRole, rule_text(node))
            if isinstance(node, RuleGroup):
                for child in node.children:
                    item.addChild(make_rules_tree(child))
            return item
        self.treeview.addTopLevelItem(make_rules_tree(rules))
        self.treeview.setColumnCount(1)

    def get_rule(self, item=None):
        if item is None:
            item = self.treeview.currentItem()
        return item.data(0, Qt.ItemDataRole.UserRole)

    def set_rule(self, rule, item=None):
        if item is None:
            item = self.treeview.currentItem()
        current_node = item.data(0, Qt.ItemDataRole.UserRole)
        if (current_node.rule_type == RuleType.GROUP) != (rule.rule_type == RuleType.GROUP):
            raise ValueError('should not change to/from a group')
        item.setData(0, Qt.ItemDataRole.UserRole, rule)
        item.setData(0, Qt.ItemDataRole.DisplayRole, rule_text(rule))

    def get_item(self):
        return self.treeview.currentItem()

    def add_rule(self, parent, rule):
        parent = self.get_group(parent)
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.ItemDataRole.UserRole, rule)
        item.setData(0, Qt.ItemDataRole.DisplayRole, rule_text(rule))

    def get_group(self, item: QTreeWidgetItem):
        node = self.get_rule(item)
        if node.rule_type != RuleType.GROUP:
            item = item.parent()
        item.setExpanded(True)
        return item

    def delete_selected_rule(self):
        item = self.get_item()
        if item.parent() is None:
            return
        item.parent().takeChild(item.parent().indexOfChild(item))

    def get_tree(self):
        root = self.treeview.topLevelItem(0)
        def traverse_tree(item:QTreeWidgetItem):
            node = self.get_rule(item)
            if node.rule_type == RuleType.GROUP:
                node.children = [traverse_tree(item.child(i))
                                 for i in range(item.childCount())]
            return node
        tree = traverse_tree(root)
        print(tree)
        return tree

class DateRuleWidget(QWidget):
    def __init__(self,rules):
        super().__init__()
        layout=QVBoxLayout()
        self.tree = RulesView(rules)
        self.tree.treeview.setCurrentItem(self.tree.treeview.topLevelItem(0))
        self.buttons = QWidget()
        self.buttons_layout = QHBoxLayout()
        button_spec = (
            ('Edit', self.edit_rule),
            ('Delete', self.delete_rule),
            ('Add rule', self.add_rule),
            ('Add group', self.add_group)
        )
        buttons = {}
        for button_text, button_handler in button_spec:
            button = QPushButton()
            button.setText(button_text)
            button.clicked.connect(button_handler)
            self.buttons_layout.addWidget(button)
            buttons[button_text] = button

        self.buttons.setLayout(self.buttons_layout)
        layout.addWidget(self.tree.treeview)
        layout.addWidget(self.buttons)
        self.setLayout(layout)
    def get_rules(self):
        return self.tree.get_tree()
    def edit_rule(self):
        item_to_edit = self.tree.get_item()
        self.rules_dialog = EditRuleDialog(self.tree.get_rule())
        self.rules_dialog.setModal(True)

        def save_rule(new_rule):
            self.tree.set_rule(new_rule, item_to_edit)

        self.rules_dialog.on_save.connect(save_rule)
        self.rules_dialog.show()

    def delete_rule(self):
        self.tree.delete_selected_rule()

    def add_rule_or_group(self, RuleClass: type[Rule]):  # pylint: disable=invalid-name
        parent_item = self.tree.get_item()
        self.rules_dialog = EditRuleDialog(RuleClass())
        self.rules_dialog.setModal(True)

        def add_rule(new_rule):
            self.tree.add_rule(parent_item, new_rule)
        self.rules_dialog.on_save.connect(add_rule)
        self.rules_dialog.show()

    def add_rule(self):
        return self.add_rule_or_group(DailyRule)

    def add_group(self):
        return self.add_rule_or_group(RuleGroup)

