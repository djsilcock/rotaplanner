from quart import Quart, render_template
from new_rotaplanner.database import database_connection

app = Quart(__name__, static_folder="generated", static_url_path="/generated")
app.debug = True
app.config["TESTING"] = True


@app.while_serving
async def setup_db_connection():
    with database_connection() as conn:
        app.db_connection = conn
        yield


@app.route("/")
async def index():
    return await render_template("index.html.j2")
