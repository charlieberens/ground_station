# Create a flask server that serves everything in the public folder

from flask import Flask, send_from_directory # pip install flask

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