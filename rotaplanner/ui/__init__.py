from rotaplanner.app import app

from rotaplanner.ui.table import table_blueprint

app.register_blueprint(table_blueprint)
