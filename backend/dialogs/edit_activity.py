"Edit activity user interface"

import sys


from typing import cast
from uuid import uuid4
from datetime import date, time,timedelta

from dataclasses import is_dataclass, fields, replace

from PySide6.QtCore import ( # pylint: disable=E0611
                            QDateTime,QTime, Qt, Signal)
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication, QDialog,
    QDialogButtonBox, QFormLayout, QHBoxLayout, QTimeEdit,
    QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton,
    QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget)

from templating import (DailyRule, GroupType, MonthlyRule, Rule, RuleGroup,  # pylint: disable=import-error
                        DateRangeRule, DateTagsRule, DateType,
                        RuleType, WeekInMonthRule, WeeklyRule, DemandTemplate)

from dialogs.forms import Form, ComboBoxField, DateField, RadioButtonField, HiddenField # pylint: disable=import-error


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


def rule_text(rule):
    "generate explanatory text for rule"
    match rule:
        case RuleGroup():
            return {
                GroupType.AND: 'All of...',
                GroupType.OR: 'Any of...',
                GroupType.NOT: 'None of...'
            }[rule.group_type]

        case DailyRule():
            return f'every {get_ordinal(rule.day_interval)}day'
        case WeeklyRule():
            return f'every {get_ordinal(rule.week_interval)}{weekday(rule.weekday)}'
        case MonthlyRule():
            return f'the {get_ordinal(rule.day,include_1=True)} of every {get_ordinal(rule.month_interval)}month'
        case WeekInMonthRule():
            return f'the {get_ordinal(rule.week_no,include_1=True)}{weekday(rule.weekday)} of every {get_ordinal(rule.month_interval)}month'
        case DateRangeRule():
            return f'is between {rule.start_date.strftime("%d/%m/%Y")} and {rule.finish_date.strftime("%d%m/%Y")}'


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
    weekday = ComboBoxField(
        label='Weekday',
        values={v: weekday(v) for v in range(7)},
        is_visible=lambda x: x['rule_type'] in (
            RuleType.WEEKLY, RuleType.WEEK_IN_MONTH),
        default_value=0)
    week_interval = ComboBoxField(
        label='Frequency',
        values={x: f'Every {get_ordinal(x)}week' for x in range(1, 27)},
        is_visible=lambda x: x['rule_type'] == RuleType.WEEKLY,
        default_value=1)
    anchor_date = DateField(
        label='Including date',
        is_visible=lambda x: x['rule_type'] in (
            RuleType.WEEKLY, RuleType.DAILY,RuleType.MONTHLY,RuleType.WEEK_IN_MONTH),
        default_value=date.today())

    day = ComboBoxField(label='Day', values={v: get_ordinal(v+1, include_1=True) for v in range(1, 32)},
                        is_visible=lambda x: x['rule_type'] == RuleType.MONTHLY,
                        default_value=1)
    week_no = ComboBoxField(label='Week of month', values={v: get_ordinal(v, include_1=True) for v in range(1, 6)},
                            is_visible=lambda x: x['rule_type'] == RuleType.WEEK_IN_MONTH,
                            default_value=1)
    month_interval = ComboBoxField(label='Frequency', values={x: f'Every {get_ordinal(x)}month' for x in range(1, 13)},
                                   is_visible=lambda x: x['rule_type'] in (
                                       RuleType.MONTHLY, RuleType.WEEK_IN_MONTH),
                                   default_value=1)
    start_date = DateField(label='Starting Date',
                           is_visible=lambda x: x['rule_type'] == RuleType.DATE_RANGE,
                           default_value=date.today(),
                           maximum=lambda v:v['finish_date'])
    finish_date = DateField(label='Finishing Date',
                            is_visible=lambda x: x['rule_type'] == RuleType.DATE_RANGE,
                            default_value=date.today(),
                            minimum=lambda v:v['start_date'])
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
        self.original_rule=data
        layout = QVBoxLayout()
        if data.rule_type == RuleType.GROUP:
            self.form = GroupForm()
        else:
            self.form = RuleForm()
            self.form.values.subscribe(self.validate_entries)
        self.form.populate(data)
        layout.addWidget(self.form.form())
        actionbuttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        actionbuttons.accepted.connect(self.handle_save)
        actionbuttons.rejected.connect(self.on_cancel)
        layout.addWidget(actionbuttons)
        self.setLayout(layout)

    def validate_entries(self,key,value):
        with self.form.values.batch() as values:
            match key:
                case 'anchor_date':
                    if value is None:
                        return
                    assert isinstance(value,date)
                    match values['rule_type']:
                        case RuleType.WEEKLY:
                            values['weekday']=value.weekday()
                        case RuleType.WEEK_IN_MONTH:
                            values['weekday']=value.weekday()
                            values['week_no']=value.day//7+1
                case 'weekday'|'week_no':
                    match values['rule_type']:
                        case RuleType.WEEKLY:
                            values['anchor_date']+=timedelta(days=value-values['anchor_date'].weekday())
                        case RuleType.WEEK_IN_MONTH:
                            year,month,_=values['anchor_date'].timetuple()[0:3]
                            starting_weekday=date(year,month,1).weekday()
                            first_week=date(year,month,1)+timedelta(days=(7+values['weekday']-starting_weekday)%7)
                            target_week=first_week+timedelta(days=values['week_no']*7-7)
                            if target_week.month!=month:
                                target_week=first_week+timedelta(days=21)
                                values['week_no']=4
                            values['anchor_date']=target_week
                case 'day':
                    year,month,_=values['anchor_date'].timetuple()[0:3]
                    values['anchor_date']=date(year,month,value)
                


    def handle_save(self):
        print('save handler')
        rule=None
        def check_not_incomplete(*field_names):
            for f in field_names:
                if self.form.values[f] is None:
                    raise ValidationError('please complete all the fields')
        match dict(self.form.values):
            case {'rule_type':RuleType.DAILY,'day_interval':day_interval}:
                check_not_incomplete('day_interval')
                rule=DailyRule(day_interval=day_interval)
            case {'rule_type':RuleType.WEEKLY,'week_interval':week_interval,'weekday':weekday}:
                check_not_incomplete('week_interval','weekday')
                rule=WeeklyRule(week_interval=week_interval,weekday=weekday)
            case {'rule_type':RuleType.WEEK_IN_MONTH,'month_interval':month_interval,'weekday':weekday,'week_no':week_no}:
                check_not_incomplete('month_interval','weekday','week_no')
                rule=WeekInMonthRule(month_interval=month_interval,weekday=weekday,week_no=week_no)
            case {'rule_type':RuleType.MONTHLY,'month_interval':month_interval,'day':day}:
                check_not_incomplete('month_interval','day')
                rule=MonthlyRule(month_interval=month_interval,day=day)
            case {'rule_type':RuleType.DATE_RANGE,'start_date':start_date,'finish_date':finish_date,'range_type':range_type}:
                check_not_incomplete('start_date','finish_date','range_type')
                rule=DateRangeRule(start_date=start_date,finish_date=finish_date,range_type=range_type)
            case {'rule_type':RuleType.DATE_TAGS,'label':label,'date_type':date_type}:
                check_not_incomplete('date_type','label')
                rule=DateTagsRule(label=label,date_type=date_type)
            case {'rule_type':RuleType.GROUP,'group_type':group_type}:
                check_not_incomplete('group_type')
                assert is_dataclass(self.original_rule)
                assert not isinstance(self.original_rule,type)
                rule=replace(self.original_rule,group_type=group_type)
        self.done(QDialog.DialogCode.Accepted)
        self.on_save.emit(rule)

    def on_cancel(self):
        self.done(QDialog.DialogCode.Rejected)


def get_activity_tags():
    return {'dcc': 'DCC',
            'spa': 'SPA',
            'urology': 'Urology',
            'theatre': 'Theatre',
            'icu': 'ICU',
            'oncall': 'On-call'}


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

        def build_tree(item):
            node = self.get_rule(item)
            if node.rule_type == RuleType.GROUP:
                node.children = [build_tree(child)
                                 for child in item.takeChildren()]
            return node
        tree = build_tree(root)
        print(tree)
        return tree


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

        self.tree = RulesView(demand_template.rules)
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
        layout.addWidget(self.tree.treeview)
        layout.addWidget(self.buttons)
        self.tag_list_widget = QListWidget()
        for tag_id, tag_label in sorted(get_activity_tags().items(), key=lambda i: i[1]):
            item = QListWidgetItem(tag_label, self.tag_list_widget)
            item.setData(Qt.ItemDataRole.UserRole, tag_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if tag_id in demand_template.activity_tags else Qt.CheckState.Unchecked)

        layout.addWidget(self.tag_list_widget)
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
        if self.tree.treeview.topLevelItem(0).childCount() == 0:
            QMessageBox.warning(self, 'Incomplete',
                                'No scheduling rules have been added')
            return
        activity_tags = {
            item.data(Qt.ItemDataRole.UserRole)
            for row in range(self.tag_list_widget.count())
            if (item := self.tag_list_widget.item(row)).checkState() == Qt.CheckState.Checked}
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
