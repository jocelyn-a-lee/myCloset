
from flask import Flask, render_template, request
from wardrobe import generate_outfit

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    outfit = None
    score = None
    season = "fall"

    if request.method == "POST":
        season = request.form.get("season", "fall")
        outfit, score = generate_outfit(season)

    return render_template(
        "index.html",
        outfit=outfit,
        score=score,
        season=season
    )

if __name__ == "__main__":
    app.run(debug=True, port=5002)
