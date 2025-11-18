from flask import Flask, render_template
import requests

app = Flask(__name__)

API_BASE = "https://www.dnd5eapi.co/api/2014"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/charactercreation")
def charactercreation():
    # Example: Get classes and races for dropdown menus
    classes = requests.get(f"{API_BASE}/classes").json().get("results", [])
    races   = requests.get(f"{API_BASE}/races").json().get("results", [])

    return render_template("charactercreation.html", classes=classes, races=races)
    
@app.route("/wikipage")
def wikipage():
    return render_template("wikipage.html")  

@app.route('/class/<index>')
def class_detail(index):
    data = requests.get(f"{API_BASE}/classes/{index}").json()
    return render_template("class_detail.html", data=data)

@app.route("/classpage")
def classpage():
    return render_template("classpage.html")


@app.route("/spell")
def spellpage():
    spell_list = requests.get(f"{API_BASE}/spells").json().get("results", [])
    return render_template("spellpage.html", spells=spell_list)


@app.route("/item")
def itempage():
    item_list = requests.get(f"{API_BASE}/equipment").json().get("results", [])
    return render_template("itempage.html", items=item_list)





    

if __name__ == "__main__":
    app.run(debug=True)
