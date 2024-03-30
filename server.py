"""
Run this file to start a web server running the visualization. You can just open index.html though. Not sure why I made this. 
"""

from flask import Flask, send_from_directory

app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory("public", "index.html")


@app.route("/historical")
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("public", path)


if __name__ == "__main__":
    app.run(debug=True)
