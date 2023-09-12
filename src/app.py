from flask import Flask, render_template

app = Flask(__name__, template_folder='templates')

@app.route("/")
def index():
    # Render the template on the browser
    return render_template("abc.html")

if __name__ == "__main__":
    app.run()