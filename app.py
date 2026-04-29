from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def anasayfa():
    veriler = {
        "toplam_kitap": 16,
        "mevcut_kitap": 11,
        "odunc_verilen": 3,
        "uye_sayisi": 5
    }
    return render_template("index.html", veriler=veriler)

if __name__ == "__main__":
    app.run(debug=True)