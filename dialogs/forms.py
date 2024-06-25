"Library for generating forms"

from typing import Any, Callable
from contextlib import contextmanager
from collections import ChainMap

from PySide6.QtWidgets import QWidget, QComboBox, QDateEdit, QRadioButton, QVBoxLayout, QFormLayout  # pylint: disable=E0611
from PySide6.QtCore import QDate  # pylint: disable=E0611


class SignallingDict(dict):
    "dict subclass that notifies subscribers of changes"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._suppression_level=0
        self._subscribers = set()

    def subscribe(self, callback: Callable[[str, Any], None]):
        "add callback"
        self._subscribers.add(callback)

    def __setitem__(self, key: Any, value: Any) -> None:
        old_value = self.get(key)
        super().__setitem__(key, value)
        if old_value != value and self._suppression_level<=0:
            self.notify_all(key)

    def set_quietly(self, key, value):
        "set without triggering callbacks"
        super().__setitem__(key, value)

    def update(self, *others, **kwargs):
        for other in [*others, kwargs]:
            items = getattr(
                other, 'items', lambda: other)  # pylint: disable=cell-var-from-loop
            for k, v in items():
                self[k] = v

    def notify_all(self, key=None):
        "notify all subscribers"
        keys = self.keys() if key is None else [key]
        for cb in self._subscribers:
            for k in keys:
                cb(k, self[k])

    @contextmanager
    def suppress_notifications(self):
        self._suppression_level+=1
        yield
        self._suppression_level-=1

    @contextmanager
    def batch(self):
        top_layer={}
        temp=ChainMap(top_layer,self)
        yield temp
        self.update(top_layer)



class Form:
    "Base class for creation of forms. Subclass or pass dict of fields to the constructor"

    def __init__(self, fields=None):
        self.fields = {}
        self.values = SignallingDict()
        if fields is None:
            fields = {}
        fields.update(self.__class__.__dict__)
        for name, definition in fields.items():
            if isinstance(definition, Field) or (
                    isinstance(definition, type) and issubclass(definition, Field)):
                field_instance = definition()
            else:
                continue
            self.fields[fieldname := (
                definition.name if definition.name is not None else name)] = field_instance
            field_instance.register(fieldname, self)
            self.values.set_quietly(fieldname, field_instance.default_value)

    def populate(self, obj_or_dict):
        "fill form with values from dict or dataclass"
        if isinstance(obj_or_dict, dict):
            self.values.update(dict)
        else:
            for f in self.fields:
                if hasattr(obj_or_dict, f):
                    self.values[f] = getattr(obj_or_dict, f)

    def form(self):
        "generate form as QWidget"
        form_widget = QWidget()
        form_layout = QFormLayout()
        form_widget.setLayout(form_layout)
        for field in self.fields.values():
            form_layout.addRow(field.label, field.widget())

            def make_fn(f):
                def isvisible(*args):  # pylint: disable=W0613
                    form_layout.setRowVisible(f.widget(), f.is_visible())
                return isvisible
            self.values.subscribe(make_fn(field))
        self.values.notify_all()
        return form_widget


class Field:
    "Base class for fields"
    name = None
    label = None
    form: Form = None  # type: ignore
    default_value = None
    _widget = None
    _is_visible = None

    def __init__(self, *,
                 name=None,
                 label=None,
                 is_visible: Callable = None,  # type: ignore
                 default_value=None):
        if name is not None:
            self.name = name
        if label is not None:
            self.label = label
        if is_visible is not None:
            self._is_visible = is_visible
        if default_value is not None:
            self.default_value = default_value

    def __call__(self):
        return self

    def is_visible(self) -> bool:
        "return True if field should be visible"
        if self._is_visible is not None:
            return self._is_visible(self.form.values)
        return True

    def process_input(self, input_value):
        "override to process value from widget before storing"
        return input_value

    def process_display(self, stored_value):
        "overribe to process value from storage before displaying"
        return stored_value

    def __repr__(self):
        return f'Field(name={self.name})'

    def values_changed(self, key, value):
        "triggered when values in storage are changed"
        if key == self.name or key is None:
            self.set_display_value(value)

    def register(self, name, owner: Form):
        "register field instance with the given form"
        self.name = name
        self.form = owner
        self.set_display_value(self.default_value)
        self.form.values.subscribe(self.values_changed)

    def widget(self):
        "widget"
        raise NotImplementedError

    def set_display_value(self, value):
        "set value of widget"
        raise NotImplementedError

    def update_value(self, value):
        "store value in storage"
        self.form.values[self.name] = self.process_input(value)


class SingleSelectField(Field):
    "Base class for fields with a single selection"
    _widget = None
    _values: list = None  # type: ignore
    _labels: dict = None  # type: ignore

    def __init__(self, *, values=None, **kwargs):
        super().__init__(**kwargs)
        if self._values is None:
            self._labels = self.values()
        if values is not None:
            self._labels.update(values)
        self._values = list(self._labels.keys())

    def add_values(self, values):
        "add options"
        self._labels.update(values)
        self._values = list(self._labels.keys())
        return self

    def values(self):
        "override in a subclass to provide values"
        return {}

    def set_display_value(self, value):
        raise NotImplementedError


class ComboBoxField(SingleSelectField):
    "ComboBox widget"

    def widget(self):
        if self._widget is not None:
            return self._widget
        self._widget = QComboBox()
        for i, x in enumerate(self._values):
            self.widget().insertItem(i, self._labels[x])
        self._widget.currentIndexChanged.connect(self.update_value)
        return self._widget

    def set_display_value(self, value):
        value = self.process_display(value)
        if value in self._values:
            self.widget().setCurrentIndex(self._values.index(value))

    def update_value(self, value):
        value = self._values[value]
        return super().update_value(value)


class RadioButtonField(SingleSelectField):
    "Displays options as a radiobutton set"
    _widgets: dict[str, QRadioButton] | None = None

    def widget(self):
        if self._widget is None:
            self._widget = QWidget()
            layout = QVBoxLayout()
            self._widget.setLayout(layout)
            self._widgets = {}
            for key, value in self._labels.items():
                new_widget = QRadioButton(value)
                self._widgets[key] = new_widget
                layout.addWidget(new_widget)
                new_widget.clicked.connect(self._on_click)

        return self._widget

    def _on_click(self):
        assert self._widgets is not None
        for k, v in self._widgets.items():
            if v.isChecked():
                self.update_value(k)

    def set_display_value(self, value):
        if self._widgets is None:
            self.widget()  # for the side-effects
            assert self._widgets is not None
        if value is None:
            for v in self._widgets.values():
                v.setChecked(False)
                return
        try:
            self._widgets[value].setChecked(True)
        except KeyError as e:
            raise ValueError(
                f'{value} is not a valid value for this radiobutton set') from e


class DateField(Field):
    "Displays datetime.date value field as a Date selector"
    _widget: QDateEdit = None  # type: ignore

    def __init__(self, *, maximum=None, minimum=None, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, 'maximum'):
            self.maximum = maximum
            if not callable(self.maximum):
                old_max = self.maximum
                self.maximum = lambda x: old_max
        if not hasattr(self, 'minimum'):
            self.minimum = minimum
            if not callable(self.minimum):
                old_min = self.minimum
                self.minimum = lambda x: old_min
        assert callable(self.maximum)
        assert callable(self.minimum)

    def widget(self):
        if self._widget is not None:
            return self._widget
        self._widget = QDateEdit()
        self._widget.setCalendarPopup(True)
        self._widget.dateChanged.connect(self.update_value)
        return self._widget

    def update_value(self, value):
        value = value.toPython()
        return super().update_value(value)

    def values_changed(self, key, value):
        assert callable(self.maximum)
        assert callable(self.minimum)
        max_date = self.maximum(self.form.values)
        min_date = self.minimum(self.form.values)
        if max_date is not None:
            self.widget().setMaximumDate(QDate(*max_date.timetuple()[0:3]))
        if min_date is not None:
            self.widget().setMinimumDate(QDate(*min_date.timetuple()[0:3]))

        return super().values_changed(key, value)

    def set_display_value(self, value):
        value = self.process_display(value)
        if value is None:
            self.widget().clear()
            return
        self.widget().setDate(QDate(*value.timetuple()[0:3]))


class HiddenField(Field):
    "Always returns the default value"

    def widget(self):
        if self._widget is None:
            self._widget = QWidget()
        return self._widget

    def is_visible(self):
        return False

    def set_display_value(self, value):
        return


if __name__ == "__main__":
    new_dict = SignallingDict()
    new_dict.subscribe(print)
    new_dict.update({1: 2, 3: 4, 5: 6})
    new_dict.update(rhubarb=8)
