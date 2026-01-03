from quart import Quart, render_template

app = Quart(__name__, static_folder="generated", static_url_path="/generated")


@app.route("/")
async def index():
    return await render_template("index.html.j2")
