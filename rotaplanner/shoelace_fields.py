from markupsafe import escape
from markupsafe import Markup

__all__ = (
    "CheckboxInput",
    "ColorInput",
    "DateInput",
    "DateTimeInput",
    "DateTimeLocalInput",
    "EmailInput",
    "FileInput",
    "HiddenInput",
    "ListWidget",
    "MonthInput",
    "NumberInput",
    "Option",
    "PasswordInput",
    "RadioInput",
    "RangeInput",
    "SearchInput",
    "Select",
    "SubmitInput",
    "TableWidget",
    "TextArea",
    "TextInput",
    "TelInput",
    "TimeInput",
    "URLInput",
    "WeekInput",
)


from wtforms.widgets import html_params


class Input:
    """
    Render a basic ``<input>`` field.

    This is used as the basis for most of the other input fields.

    By default, the `_value()` method will be called upon the associated field
    to provide the ``value=`` HTML attribute.
    """

    html_params = staticmethod(html_params)

    def __init__(self, input_type=None):
        if input_type is not None:
            self.input_type = input_type

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", self.input_type)
        kwargs.setdefault("label", field.label.text)
        if "value" not in kwargs:
            kwargs["value"] = field._value()
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)
        input_params = self.html_params(name=field.name, **kwargs)
        return Markup(f"<sl-input {input_params}></sl-input>")


class TextInput(Input):
    """
    Render a single-line text input.
    """

    input_type = "text"
    validation_attrs = [
        "required",
        "disabled",
        "readonly",
        "maxlength",
        "minlength",
        "pattern",
    ]


class PasswordInput(Input):
    """
    Render a password input.

    For security purposes, this field will not reproduce the value on a form
    submit by default. To have the value filled in, set `hide_value` to
    `False`.
    """

    input_type = "password"
    validation_attrs = [
        "required",
        "disabled",
        "readonly",
        "maxlength",
        "minlength",
        "pattern",
    ]

    def __init__(self, hide_value=True):
        self.hide_value = hide_value

    def __call__(self, field, **kwargs):
        if self.hide_value:
            kwargs["value"] = ""
        return super().__call__(field, **kwargs)


class CheckboxInput(Input):
    """
    Render a checkbox.

    The ``checked`` HTML attribute is set if the field's data is a non-false value.
    """

    input_type = "checkbox"
    validation_attrs = ["required", "disabled"]

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", self.input_type)

        if "value" not in kwargs:
            kwargs["value"] = field._value()
        flags = getattr(field, "flags", {})
        label = kwargs.pop("label", field.label.text)
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)
        input_params = self.html_params(name=field.name, **kwargs)
        return Markup(f"<sl-checkbox {input_params}>{label}</sl-checkbox>")


class RadioInput(Input):
    """
    Render a single radio button.

    This widget is most commonly used in conjunction with ListWidget or some
    other listing, as singular radio buttons are not very useful.
    """

    input_type = "radio"
    validation_attrs = ["required", "disabled"]

    def __call__(self, field, **kwargs):
        if field.checked:
            kwargs["checked"] = True
        return super().__call__(field, **kwargs)


class FileInput(Input):
    """Render a file chooser input.

    :param multiple: allow choosing multiple files
    """

    input_type = "file"
    validation_attrs = ["required", "disabled", "accept"]

    def __init__(self, multiple=False):
        super().__init__()
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        # browser ignores value of file input for security
        kwargs["value"] = False

        if self.multiple:
            kwargs["multiple"] = True

        return super().__call__(field, **kwargs)


class SubmitInput(Input):
    """
    Renders a submit button.

    The field's label is used as the text of the submit button instead of the
    data on the field.
    """

    input_type = "submit"
    validation_attrs = ["required", "disabled"]

    def __call__(self, field, **kwargs):
        kwargs.setdefault("value", field.label.text)
        return super().__call__(field, **kwargs)


class TextArea:
    """
    Renders a multi-line text area.

    `rows` and `cols` ought to be passed as keyword args when rendering.
    """

    validation_attrs = ["required", "disabled", "readonly", "maxlength", "minlength"]

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)
        textarea_params = html_params(name=field.name, **kwargs)
        textarea_innerhtml = escape(field._value())
        return Markup(
            f"<sl-textarea {textarea_params}>\r\n{textarea_innerhtml}</textarea>"
        )


class Select:
    """
    Renders a select field.

    If `multiple` is True, then the `size` property should be specified on
    rendering to make the field useful.

    The field must provide an `iter_choices()` method which the widget will
    call on rendering; this method must yield tuples of
    `(value, label, selected)` or `(value, label, selected, render_kw)`.
    It also must provide a `has_groups()` method which tells whether choices
    are divided into groups, and if they do, the field must have an
    `iter_groups()` method that yields tuples of `(label, choices)`, where
    `choices` is a iterable of `(value, label, selected)` tuples.
    """

    validation_attrs = ["required", "disabled"]

    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        if self.multiple:
            kwargs["multiple"] = True
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)
        kwargs.setdefault("label", field.label.text)
        if "value" not in kwargs:
            kwargs["value"] = (
                " ".join(field.data)
                if (self.multiple and field.data is not None)
                else field.data
            )
        select_params = html_params(name=field.name, **kwargs)
        html = [f"<sl-select {select_params}>"]
        if field.has_groups():
            for group, choices in field.iter_groups():
                optgroup_params = html_params(label=group)
                html.append(f"<sl-divider></sl-divider>")
                html.append(f"<small> {group} </small>")
                for choice in choices:
                    val, label, selected, render_kw = choice
                    html.append(self.render_option(val, label, selected, **render_kw))

        else:
            for choice in field.iter_choices():
                val, label, selected, render_kw = choice
                html.append(self.render_option(val, label, selected, **render_kw))
        html.append("</sl-select>")
        return Markup("".join(html))

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        if value is True:
            # Handle the special case of a 'True' value.
            value = str(value)

        options = dict(kwargs, value=value)
        if selected:
            options["selected"] = True
        return Markup(
            f"<sl-option {html_params(**options)}>{escape(label)}</sl-option>"
        )


class Option:
    """
    Renders the individual option from a select field.

    This is just a convenience for various custom rendering situations, and an
    option by itself does not constitute an entire field.
    """

    def __call__(self, field, **kwargs):
        return Select.render_option(
            field._value(), field.label.text, field.checked, **kwargs
        )


class SearchInput(Input):
    """
    Renders an input with type "search".
    """

    input_type = "search"
    validation_attrs = [
        "required",
        "disabled",
        "readonly",
        "maxlength",
        "minlength",
        "pattern",
    ]


class TelInput(Input):
    """
    Renders an input with type "tel".
    """

    input_type = "tel"
    validation_attrs = [
        "required",
        "disabled",
        "readonly",
        "maxlength",
        "minlength",
        "pattern",
    ]


class URLInput(Input):
    """
    Renders an input with type "url".
    """

    input_type = "url"
    validation_attrs = [
        "required",
        "disabled",
        "readonly",
        "maxlength",
        "minlength",
        "pattern",
    ]


class EmailInput(Input):
    """
    Renders an input with type "email".
    """

    input_type = "email"
    validation_attrs = [
        "required",
        "disabled",
        "readonly",
        "maxlength",
        "minlength",
        "pattern",
    ]


class DateTimeInput(Input):
    """
    Renders an input with type "datetime".
    """

    input_type = "datetime-local"
    validation_attrs = ["required", "disabled", "readonly", "max", "min", "step"]


class DateInput(Input):
    """
    Renders an input with type "date".
    """

    input_type = "date"
    validation_attrs = ["required", "disabled", "readonly", "max", "min", "step"]


class MonthInput(Input):
    """
    Renders an input with type "month".
    """

    input_type = "month"
    validation_attrs = ["required", "disabled", "readonly", "max", "min", "step"]


class WeekInput(Input):
    """
    Renders an input with type "week".
    """

    input_type = "week"
    validation_attrs = ["required", "disabled", "readonly", "max", "min", "step"]


class TimeInput(Input):
    """
    Renders an input with type "time".
    """

    input_type = "time"
    validation_attrs = ["required", "disabled", "readonly", "max", "min", "step"]


class DateTimeLocalInput(Input):
    """
    Renders an input with type "datetime-local".
    """

    input_type = "datetime-local"
    validation_attrs = ["required", "disabled", "readonly", "max", "min", "step"]


class NumberInput(Input):
    """
    Renders an input with type "number".
    """

    input_type = "number"
    validation_attrs = ["required", "disabled", "readonly", "max", "min", "step"]

    def __init__(self, step=None, min=None, max=None):
        self.step = step
        self.min = min
        self.max = max

    def __call__(self, field, **kwargs):
        if self.step is not None:
            kwargs.setdefault("step", self.step)
        if self.min is not None:
            kwargs.setdefault("min", self.min)
        if self.max is not None:
            kwargs.setdefault("max", self.max)
        return super().__call__(field, **kwargs)


class RangeInput(Input):
    """
    Renders an input with type "range".
    """

    input_type = "range"
    validation_attrs = ["disabled", "max", "min", "step"]

    def __init__(self, step=None):
        self.step = step

    def __call__(self, field, **kwargs):
        if self.step is not None:
            kwargs.setdefault("step", self.step)
        return super().__call__(field, **kwargs)


class ColorInput(Input):
    """
    Renders an input with type "color".
    """

    input_type = "color"
    validation_attrs = ["disabled"]


import wtforms.fields as fields


class BooleanField(fields.BooleanField):
    widget = CheckboxInput()


class StringField(fields.StringField):
    widget = TextInput()


class TextAreaField(fields.TextAreaField):
    widget = TextArea()


class PasswordField(fields.PasswordField):
    widget = PasswordInput()


class FileField(fields.FileField):
    widget = FileInput()


class MultipleFileField(fields.MultipleFileField):
    widget = FileInput(multiple=True)


HiddenField = fields.HiddenField


class SubmitField(fields.BooleanField):
    widget = SubmitInput()


class SearchField(fields.SearchField):
    widget = SearchInput()


class TelField(fields.TelField):
    widget = TelInput()


class URLField(fields.URLField):
    widget = URLInput()


class EmailField(fields.EmailField):
    widget = EmailInput()


class ColorField(fields.StringField):
    widget = ColorInput()


class DateTimeField(fields.DateTimeField):
    widget = DateTimeInput()


class DateField(fields.DateField):
    widget = DateInput()


class TimeField(fields.TimeField):
    widget = TimeInput()


class MonthField(fields.MonthField):
    widget = MonthInput()


class WeekField(fields.WeekField):
    widget = WeekInput()


class DateTimeLocalField(fields.DateTimeLocalField):
    widget = DateTimeLocalInput()


class SelectField(fields.SelectField):
    widget = Select()
    option_widget = Option()


class SelectMultipleField(fields.SelectMultipleField):
    widget = Select(multiple=True)
    option_widget = Option()

    def process_formdata(self, valuelist):
        try:
            self.data = list(self.coerce(x) for x in valuelist[0].split(" "))
        except ValueError as exc:
            raise ValueError(
                self.gettext(
                    "Invalid choice(s): one or more data inputs could not be coerced."
                )
            ) from exc
