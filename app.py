from flask import Flask, render_template, request, redirect
import json
import os

app = Flask(__name__)

# JSON dosya yolları
KITAPLAR_DOSYASI = "data/kitaplar.json"
UYELER_DOSYASI = "data/uyeler.json"
ODUNCLER_DOSYASI = "data/oduncler.json"


# -------------------------
# Yardımcı JSON Fonksiyonları
# -------------------------

def json_oku(dosya_yolu):
    if not os.path.exists(dosya_yolu):
        return []

    with open(dosya_yolu, "r", encoding="utf-8") as dosya:
        return json.load(dosya)


def json_yaz(dosya_yolu, veri):
    with open(dosya_yolu, "w", encoding="utf-8") as dosya:
        json.dump(veri, dosya, ensure_ascii=False, indent=4)


# -------------------------
# Dashboard - Ana Sayfa
# -------------------------

@app.route("/")
def anasayfa():
    kitaplar = json_oku(KITAPLAR_DOSYASI)
    uyeler = json_oku(UYELER_DOSYASI)
    oduncler = json_oku(ODUNCLER_DOSYASI)

    veriler = {
        "toplam_kitap": len(kitaplar),
        "mevcut_kitap": len(kitaplar) - len(oduncler),
        "odunc_verilen": len(oduncler),
        "uye_sayisi": len(uyeler)
    }

    return render_template("index.html", veriler=veriler)


# -------------------------
# Login - Burcu
# -------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        kullanici_adi = request.form.get("kullanici_adi")
        sifre = request.form.get("sifre")

        if kullanici_adi == "admin" and sifre == "1234":
            return redirect("/")

        hata = "Kullanıcı adı veya şifre hatalı."
        return render_template("login.html", hata=hata)

    return render_template("login.html")


# -------------------------
# Kitaplar
# -------------------------

@app.route("/kitaplar")
def kitaplar():
    kitap_listesi = json_oku(KITAPLAR_DOSYASI)
    return render_template("kitaplar.html", kitaplar=kitap_listesi)


# -------------------------
# Ödünç Verme - Aleyna
# -------------------------

@app.route("/odunc-ver", methods=["GET", "POST"])
def odunc_ver():
    kitaplar = json_oku(KITAPLAR_DOSYASI)
    uyeler = json_oku(UYELER_DOSYASI)
    oduncler = json_oku(ODUNCLER_DOSYASI)

    if request.method == "POST":
        kitap_adi = request.form.get("kitap_adi")
        uye_adi = request.form.get("uye_adi")
        tarih = request.form.get("tarih")

        yeni_odunc = {
            "kitap_adi": kitap_adi,
            "uye_adi": uye_adi,
            "tarih": tarih,
            "durum": "Ödünç Verildi"
        }

        oduncler.append(yeni_odunc)
        json_yaz(ODUNCLER_DOSYASI, oduncler)

        return redirect("/odunc-ver")

    return render_template(
        "odunc_ver.html",
        kitaplar=kitaplar,
        uyeler=uyeler,
        oduncler=oduncler
    )


# -------------------------
# İade Alma - Havin
# -------------------------

@app.route("/iade-al")
def iade_al():
    oduncler = json_oku(ODUNCLER_DOSYASI)
    return render_template("iade_al.html", oduncler=oduncler)


@app.route("/iade-et/<int:index>")
def iade_et(index):
    oduncler = json_oku(ODUNCLER_DOSYASI)

    if 0 <= index < len(oduncler):
        oduncler.pop(index)
        json_yaz(ODUNCLER_DOSYASI, oduncler)

    return redirect("/iade-al")


# -------------------------
# Uygulamayı Çalıştır
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)