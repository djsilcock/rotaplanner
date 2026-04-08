from quart import Quart, render_template
from quart_schema import QuartSchema
from rotaplanner.database import database_connection
import rotaplanner.database.commands as db_commands
from datetime import date
from decimal import Decimal
import dataclasses
import uuid

app = Quart(__name__, static_folder="generated", static_url_path="/generated")
QuartSchema(app)
app.debug = True
app.config["TESTING"] = True
app.json.sort_keys = False


def _default(o):
    if isinstance(o, date):
        return date.isoformat(o)

    if isinstance(o, (Decimal, uuid.UUID)):
        return str(o)

    if dataclasses and dataclasses.is_dataclass(o):
        return dataclasses.asdict(o)  # type: ignore[arg-type]

    if hasattr(o, "__html__"):
        return str(o.__html__())

    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


app.json.default = _default


@app.while_serving
async def setup_db_connection():
    with database_connection() as conn:
        app.db_connection = conn
        yield


@app.route("/")
async def index():
    return await render_template("index.html.j2")


app.cli.command("init-db")(db_commands.setup_database)
app.cli.command("populate-db")(db_commands.populate_database)
