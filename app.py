from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/charactercreation")
def charactercreation():
    return render_template("charactercreation.html")
    
@app.route("/wikipage")
def wikipage():
    return render_template("wikipage.html")    

if __name__ == "__main__":
    app.run(debug=True)
