"""Mako templating support for Rotaplanner."""

from mako.lookup import TemplateLookup
from starlette.responses import HTMLResponse


class MakoTemplates:
    def __init__(self, *directories, module_directory=None):
        self.lookup = TemplateLookup(
            directories=[*directories], module_directory=module_directory
        )

    def get_template(self, template_name):
        return self.lookup.get_template(template_name)

    def TemplateResponse(self, template_name, context, **kwargs):
        content = self.lookup.get_template(template_name).render(**context)
        return HTMLResponse(content, **kwargs)


templates = MakoTemplates(
    "rotaplanner/templates", module_directory="rotaplanner/template_modules"
)
