from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import hashlib
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "libraryos_secret_key"

@app.template_filter('tarih')
def tarih_formatla(tarih):
    if tarih:
        dt = datetime.strptime(tarih[:19], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y")
    return ""

DB_PATH = os.path.join(os.path.dirname(__file__), "library.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



def sifre_hashle(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()


def admin_required():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("uye_dashboard"))

    return None


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            category TEXT DEFAULT 'Klasik',
            year INTEGER,
            status TEXT DEFAULT 'Mevcut',
            borrower_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            member_id INTEGER,
            loan_date TEXT DEFAULT CURRENT_TIMESTAMP,
            return_date TEXT,
            status TEXT DEFAULT 'Aktif',
            deposit INTEGER DEFAULT 0,
            FOREIGN KEY(book_id) REFERENCES books(id),
            FOREIGN KEY(member_id) REFERENCES members(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        reserve_date TEXT DEFAULT CURRENT_TIMESTAMP,
        expire_date TEXT,
        status TEXT DEFAULT 'Bekliyor',
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(book_id) REFERENCES books(id)
        )
    """)
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        books = [
            ("Suç ve Ceza", "Fyodor Dostoyevski", "978-975-10-0001", "Klasik", 1866, "Mevcut"),
            ("Sefiller", "Victor Hugo", "978-975-10-0002", "Klasik", 1862, "Mevcut"),
            ("Anna Karenina", "Lev Tolstoy", "978-975-10-0003", "Klasik", 1878, "Ödünçte"),
            ("Don Kişot", "Miguel de Cervantes", "978-975-10-0004", "Klasik", 1605, "Mevcut"),
            ("Karamazov Kardeşler", "Fyodor Dostoyevski", "978-975-10-0005", "Klasik", 1880, "Mevcut"),
            ("Savaş ve Barış", "Lev Tolstoy", "978-975-10-0006", "Klasik", 1869, "Rezerve"),
            ("Madame Bovary", "Gustave Flaubert", "978-975-10-0007", "Klasik", 1857, "Mevcut"),
            ("Büyük Umutlar", "Charles Dickens", "978-975-10-0008", "Klasik", 1861, "Ödünçte"),
            ("Moby Dick", "Herman Melville", "978-975-10-0009", "Macera", 1851, "Mevcut"),
            ("Simyacı", "Paulo Coelho", "978-975-10-0010", "Roman", 1988, "Mevcut"),
            ("Yüzyıllık Yalnızlık", "Gabriel García Márquez", "978-975-10-0011", "Roman", 1967, "Mevcut"),
            ("Küçük Prens", "Antoine de Saint-Exupéry", "978-975-10-0012", "Çocuk", 1943, "Ödünçte"),
            ("Hayvan Çiftliği", "George Orwell", "978-975-10-0013", "Distopya", 1945, "Mevcut"),
            ("1984", "George Orwell", "978-975-10-0014", "Distopya", 1949, "Mevcut"),
            ("Cesur Yeni Dünya", "Aldous Huxley", "978-975-10-0015", "Distopya", 1932, "Rezerve"),
            ("Martin Eden", "Jack London", "978-975-10-0016", "Klasik", 1909, "Mevcut"),
        ]

        c.executemany("""
            INSERT INTO books 
            (title, author, isbn, category, year, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, books)

    c.execute("SELECT COUNT(*) FROM members")
    if c.fetchone()[0] == 0:
        members = [
            ("Ahmet Yılmaz", "ahmet@email.com", "0532-111-2233"),
            ("Ayşe Kaya", "ayse@email.com", "0533-222-3344"),
            ("Mehmet Demir", "mehmet@email.com", "0534-333-4455"),
            ("Zeynep Arslan", "zeynep@email.com", "0535-444-5566"),
            ("Can Türk", "can@email.com", "0536-555-6677"),
        ]

        c.executemany("""
            INSERT INTO members (name, email, phone)
            VALUES (?, ?, ?)
        """, members)

        c.execute("UPDATE books SET status='Ödünçte', borrower_id=1 WHERE id=3")
        c.execute("UPDATE books SET status='Ödünçte', borrower_id=2 WHERE id=8")
        c.execute("UPDATE books SET status='Ödünçte', borrower_id=3 WHERE id=12")

        c.execute("""
            INSERT INTO loans (book_id, member_id, deposit)
            VALUES (3,1,0), (8,2,0), (12,3,0)
        """)

        c.execute("UPDATE books SET status='Rezerve', borrower_id=4 WHERE id=6")
        c.execute("UPDATE books SET status='Rezerve', borrower_id=5 WHERE id=15")

    c.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO users (username, name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "admin",
            "admin",
            "admin@libraryos.com",
            "",
            sifre_hashle("admin123"),
            "admin"
        ))

    conn.commit()
    conn.close()


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        login_type = request.form.get("login_type")
        conn = get_db()

        if login_type == "admin":
            username = request.form.get("admin_username", "").strip()
            password = request.form.get("admin_password", "")

            user = conn.execute("""
                SELECT * FROM users
                WHERE username=? AND password_hash=? AND role='admin'
            """, (username, sifre_hashle(password))).fetchone()

        else:
            email = request.form.get("member_email", "").strip()
            password = request.form.get("member_password", "")

            user = conn.execute("""
                SELECT * FROM users
                WHERE email=? AND password_hash=? AND role='member'
            """, (email, sifre_hashle(password))).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            session["email"] = user["email"]

            if user["role"] == "admin":
                return redirect(url_for("dashboard"))

            return redirect(url_for("uye_dashboard"))

        error = "Kullanıcı adı/e-posta veya şifre hatalı!"

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        password_repeat = request.form.get("password_repeat", "")

        if not username or not name or not email or not phone or not password or not password_repeat:
            error = "Lütfen tüm alanları doldurun."
            return render_template("register.html", error=error)

        if len(username) < 3:
            error = "Kullanıcı adı en az 3 karakter olmalıdır."
            return render_template("register.html", error=error)

        if len(email) < 8:
            error = "E-posta adresi çok kısa."
            return render_template("register.html", error=error)

        if len(email) > 80:
            error = "E-posta adresi çok uzun."
            return render_template("register.html", error=error)

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            error = "Geçerli bir e-posta adresi girin."
            return render_template("register.html", error=error)

        if len(phone) < 10:
            error = "Telefon numarası çok kısa."
            return render_template("register.html", error=error)

        if len(password) < 6:
            error = "Şifre en az 6 karakter olmalıdır."
            return render_template("register.html", error=error)

        if password != password_repeat:
            error = "Şifreler eşleşmiyor."
            return render_template("register.html", error=error)

        conn = get_db()

        existing_username = conn.execute(
            "SELECT id FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing_username:
            conn.close()
            error = "Bu kullanıcı adı zaten kullanılıyor."
            return render_template("register.html", error=error)

        existing_email = conn.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing_email:
            conn.close()
            error = "Bu e-posta zaten kayıtlı."
            return render_template("register.html", error=error)

        existing_phone = conn.execute(
            "SELECT id FROM users WHERE phone=?",
            (phone,)
        ).fetchone()

        if existing_phone:
            conn.close()
            error = "Bu telefon numarası zaten kayıtlı."
            return render_template("register.html", error=error)

        try:
            conn.execute("""
                INSERT INTO users (username, name, email, phone, password_hash, role)
                VALUES (?, ?, ?, ?, ?, 'member')
            """, (
                username,
                name,
                email,
                phone,
                sifre_hashle(password)
            ))

            conn.execute("""
                INSERT INTO members (name, email, phone)
                VALUES (?, ?, ?)
            """, (name, email, phone))

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            conn.close()
            error = "Bu kullanıcı adı, e-posta veya telefon zaten kayıtlı."

    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- ÜYE PANELİ ---
@app.route("/uye")
def uye_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()

    # giriş yapan üye
    member = conn.execute(
        "SELECT id FROM members WHERE email=?",
        (session.get("email"),)
    ).fetchone()

    stats = {"total": 0, "active": 0, "reserved": 0}
    user_books = []

    if member:
        m_id = member["id"]

        # toplam ödünç
        stats["total"] = conn.execute(
            "SELECT COUNT(*) FROM loans WHERE member_id=?",
            (m_id,)
        ).fetchone()[0]

        # aktif ödünç
        stats["active"] = conn.execute(
            "SELECT COUNT(*) FROM loans WHERE member_id=? AND status='Aktif'",
            (m_id,)
        ).fetchone()[0]

        # rezervasyon (users.id kullanılıyor)
        stats["reserved"] = conn.execute("""
            SELECT COUNT(*)
            FROM reservations
            WHERE user_id=? AND status='Bekliyor'
        """, (session["user_id"],)).fetchone()[0]

        # aktif kitaplar
        user_books = conn.execute("""
            SELECT b.title, l.loan_date, l.status 
            FROM loans l 
            JOIN books b ON l.book_id = b.id 
            WHERE l.member_id=? AND l.status='Aktif'
        """, (m_id,)).fetchall()

    conn.close()

    return render_template(
        "member_home.html",
        stats=stats,
        user_books=user_books
    )

@app.route("/dashboard")
def dashboard():
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()

    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    available = conn.execute("SELECT COUNT(*) FROM books WHERE status='Mevcut'").fetchone()[0]
    loaned = conn.execute("SELECT COUNT(*) FROM books WHERE status='Ödünçte'").fetchone()[0]
    reserved = conn.execute("SELECT COUNT(*) FROM books WHERE status='Rezerve'").fetchone()[0]
    total_members = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    active_loans = conn.execute("SELECT COUNT(*) FROM loans WHERE status='Aktif'").fetchone()[0]

    recent_loans = conn.execute("""
        SELECT l.id, b.title, m.name, l.loan_date
        FROM loans l
        JOIN books b ON l.book_id = b.id
        JOIN members m ON l.member_id = m.id
        WHERE l.status='Aktif'
        ORDER BY l.loan_date DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_books=total_books,
        available=available,
        loaned=loaned,
        reserved=reserved,
        total_members=total_members,
        active_loans=active_loans,
        recent_loans=recent_loans
    )


@app.route("/books")
def books():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    q = request.args.get("q", "")

    books = conn.execute("""
    SELECT 
        MIN(b.id) as id,
        b.title,
        b.author,
        MIN(b.isbn) as isbn,
        b.category,
        b.year,

        COUNT(*) as toplam_adet,

        SUM(
            CASE 
                WHEN b.status = 'Mevcut' THEN 1
                ELSE 0
            END
        ) as mevcut_adet

    FROM books b

    WHERE 
        b.title LIKE ?
        OR b.author LIKE ?
        OR b.isbn LIKE ?

    GROUP BY 
        b.title,
        b.author,
        b.category,
        b.year

    ORDER BY id DESC
""", (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    
    conn.close()
    return render_template("books.html", books=books, q=q)

@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    kontrol = admin_required()
    if kontrol:
        return kontrol

    if request.method == "POST":
        d = request.form
        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO books (title, author, isbn, category, year)
                VALUES (?, ?, ?, ?, ?)
            """, (
                d["title"],
                d["author"],
                d["isbn"],
                d.get("category", "Klasik"),
                d.get("year") or None
            ))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return render_template("add_book.html", error="Bu ISBN zaten kayıtlı!")

        conn.close()
        return redirect(url_for("books"))

    return render_template("add_book.html", error=None)


@app.route("/books/edit/<int:id>", methods=["GET", "POST"])
def edit_book(id):
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()

    if request.method == "POST":
        d = request.form

        conn.execute("""
            UPDATE books
            SET title=?, author=?, isbn=?, category=?, year=?
            WHERE id=?
        """, (
            d["title"],
            d["author"],
            d["isbn"],
            d.get("category", "Klasik"),
            d.get("year") or None,
            id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("books"))

    book = conn.execute("SELECT * FROM books WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("books.html", books=[book], error=None)


@app.route("/books/delete/<int:id>", methods=["POST"])
def delete_book(id):
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()
    conn.execute("DELETE FROM books WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("books"))


@app.route("/members")
def members():
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()
    q = request.args.get("q", "")

    members = conn.execute("""
        SELECT m.*, COUNT(l.id) AS loan_count
        FROM members m
        LEFT JOIN loans l ON m.id = l.member_id AND l.status='Aktif'
        WHERE m.name LIKE ? OR m.email LIKE ? OR m.phone LIKE ?
        GROUP BY m.id
        ORDER BY m.id DESC
    """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()

    conn.close()

    return render_template("uyeler.html", members=members, q=q)


@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    kontrol = admin_required()
    if kontrol:
        return kontrol

    if request.method == "POST":
        d = request.form
        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO members (name, email, phone)
                VALUES (?, ?, ?)
            """, (d["name"], d["email"], d.get("phone", "")))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return render_template("uye_ekle.html", error="Bu e-posta veya telefon zaten kayıtlı!", member=None)

        conn.close()
        return redirect(url_for("members"))

    return render_template("uye_ekle.html", member=None, error=None)


@app.route("/members/edit/<int:id>", methods=["GET", "POST"])
def edit_member(id):
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()

    if request.method == "POST":
        d = request.form

        conn.execute("""
            UPDATE members
            SET name=?, email=?, phone=?
            WHERE id=?
        """, (d["name"], d["email"], d.get("phone", ""), id))

        conn.commit()
        conn.close()

        return redirect(url_for("members"))

    member = conn.execute("SELECT * FROM members WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("uye_ekle.html", member=member, error=None)


@app.route("/members/delete/<int:id>", methods=["POST"])
def delete_member(id):
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()
    conn.execute("DELETE FROM members WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("members"))


@app.route("/loans")
def loans():
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()

    available_books = conn.execute("""
        SELECT *
        FROM books
        WHERE status='Mevcut'
        ORDER BY title
    """).fetchall()

    all_members = conn.execute("""
        SELECT *
        FROM members
        ORDER BY name
    """).fetchall()

    active_loans = conn.execute("""
        SELECT l.*, b.title, b.isbn, m.name AS member_name
        FROM loans l
        JOIN books b ON l.book_id = b.id
        JOIN members m ON l.member_id = m.id
        WHERE l.status='Aktif'
        ORDER BY l.loan_date DESC
    """).fetchall()

    conn.close()

    return render_template(
        "odunc_ver.html",
        available_books=available_books,
        all_members=all_members,
        active_loans=active_loans
    )


@app.route("/loans/add", methods=["POST"])
def add_loan():
    kontrol = admin_required()
    if kontrol:
        return kontrol

    d = request.form

    member_id = d["member_id"]
    book_id = d["book_id"]
    deposit = int(d.get("deposit", 0))

    if deposit < 0:
        deposit = 0

    conn = get_db()

    loan_count = conn.execute("""
        SELECT COUNT(*)
        FROM loans
        WHERE member_id=? AND status='Aktif'
    """, (member_id,)).fetchone()[0]

    if loan_count >= 3:
        conn.close()
        return redirect(url_for("loans", error="Bu üye zaten 3 kitap almış!"))

    conn.execute("""
        INSERT INTO loans (book_id, member_id, deposit)
        VALUES (?, ?, ?)
    """, (book_id, member_id, deposit))

    conn.execute("""
        UPDATE books
        SET status='Ödünçte', borrower_id=?
        WHERE id=?
    """, (member_id, book_id))

    conn.commit()
    conn.close()

    return redirect(url_for("loans"))


# --- YENİLENEN İADE ALMA FONKSİYONU (HASAR VE SUCCESS BİLDİRİMİ ENTEGRELİ) ---
@app.route("/loans/return/<int:id>", methods=["POST"])
def return_loan(id):
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()
    
    # HTML formundan gelen hasar bedelini yakalıyoruz
    hasar_bedeli = float(request.form.get("hasar_bedeli", 0))

    # İade edilecek ödünç kaydını bulalım
    loan = conn.execute("SELECT * FROM loans WHERE id=?", (id,)).fetchone()

    if loan:
        alinan_depozito = float(loan["deposit"] or 0)
        
        # Üyeye geri ödenecek net tutarı hesapla (Negatif olmasın kontrolü)
        geri_odenecek = alinan_depozito - hasar_bedeli
        if geri_odenecek < 0:
            geri_odenecek = 0

        # Ödünç kaydını 'İade' durumuna çek
        conn.execute("""
            UPDATE loans
            SET status='İade', return_date=CURRENT_TIMESTAMP
            WHERE id=?
        """, (id,))

        # Kitabı tekrar 'Mevcut' durumuna getir
        conn.execute("""
            UPDATE books
            SET status='Mevcut', borrower_id=NULL
            WHERE id=?
        """, (loan["book_id"],))

        conn.commit()
        conn.close()

        # Hoca kriterine uygun dinamik başarı bildirimi mesajı
        if hasar_bedeli > 0:
            msg = f"İade işlemi tamamlandı! {int(hasar_bedeli)} TL hasar kesintisi yapıldı. Üyeye geri iade edilen tutar: {int(geri_odenecek)} TL"
        else:
            msg = f"İade işlemi başarıyla tamamlandı! Kitap hasarsız teslim alındı, {int(alinan_depozito)} TL depozito eksiksiz iade edildi."

        # Mesajı url parametresi olarak iade_al sayfasına gönderiyoruz
        return redirect(url_for("iade_al", success=msg))

    conn.close()
    return redirect(url_for("iade_al"))


@app.route("/iade-al")
def iade_al():
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()

    loaned_books = conn.execute("""
        SELECT 
            l.id AS loan_id,
            b.title,
            b.isbn,
            m.name AS member_name,
            l.loan_date,
            l.deposit
        FROM loans l
        JOIN books b ON l.book_id = b.id
        JOIN members m ON l.member_id = m.id
        WHERE l.status='Aktif'
        ORDER BY l.loan_date DESC
    """).fetchall()

    conn.close()

    return render_template("iade_al.html", loaned_books=loaned_books)


@app.route("/reports")
def reports():
    kontrol = admin_required()
    if kontrol:
        return kontrol

    conn = get_db()

    by_category = conn.execute("""
        SELECT category, COUNT(*) AS cnt
        FROM books
        GROUP BY category
    """).fetchall()

    by_status = conn.execute("""
        SELECT status, COUNT(*) AS cnt
        FROM books
        GROUP BY status
    """).fetchall()

    top_borrowed = conn.execute("""
        SELECT b.title, b.author, COUNT(l.id) AS times
        FROM loans l
        JOIN books b ON l.book_id = b.id
        GROUP BY b.id
        ORDER BY times DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        by_category=by_category,
        by_status=by_status,
        top_borrowed=top_borrowed
    )

@app.route("/uye/kitaplar")
def uye_kitaplar():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    member = conn.execute(
        "SELECT id FROM members WHERE email=?",
        (session["email"],)
    ).fetchone()

    member_id = member["id"] if member else None

    books = conn.execute("""
        SELECT 
            b.*,
            l.id AS loan_id,

            (
                SELECT COUNT(*)
                FROM books b2
                WHERE b2.title = b.title
            ) AS toplam_adet,

            (
                SELECT COUNT(*)
                FROM books b3
                WHERE b3.title = b.title
                AND b3.status = 'Mevcut'
            ) AS mevcut_adet

        FROM books b

        LEFT JOIN loans l 
        ON b.id = l.book_id AND l.status='Aktif'

        ORDER BY b.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "member_books.html",
        books=books,
        member_id=member_id
    )


@app.route("/uye_profil")
def uye_profil():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    # member id bul
    member = conn.execute(
        "SELECT id FROM members WHERE email=?",
        (user["email"],)
    ).fetchone()

    book_count = 0

    if member:
        book_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM loans WHERE member_id=? AND status='Aktif'",
            (member["id"],)
        ).fetchone()["cnt"]

    conn.close()

    return render_template(
        "uye_profil.html",
        user=user,
        book_count=book_count,
        last_login=session.get("last_login", "Bilinmiyor")
    )




@app.route("/sifre_degistir", methods=["POST"])
def sifre_degistir():

    if "user_id" not in session:
        return redirect(url_for("login"))

    eski = request.form["old_password"]
    yeni = request.form["new_password"]

    conn = get_db()

    user = conn.execute(
        "SELECT password_hash FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user["password_hash"] != sifre_hashle(eski):
        conn.close()
        return "Eski şifre yanlış"

    conn.execute(
        "UPDATE users SET password_hash=? WHERE id=?",
        (sifre_hashle(yeni), session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("uye_profil")) 




@app.route("/odunc-al/<int:book_id>", methods=["POST"])
def odunc_al(book_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    book = conn.execute(
        "SELECT * FROM books WHERE id=?",
        (book_id,)
    ).fetchone()

    if not book or book["status"] != "Mevcut":
        conn.close()
        return "Bu kitap ödünç alınamaz"

    member = conn.execute(
        "SELECT id FROM members WHERE email=?",
        (session["email"],)
    ).fetchone()

    if not member:
        conn.close()
        return "Üye bulunamadı"

    conn.execute("""
        INSERT INTO loans (book_id, member_id, status, deposit)
        VALUES (?, ?, 'Aktif', 0)
    """, (book_id, member["id"]))

    conn.execute("""
        UPDATE books
        SET status='Ödünçte', borrower_id=?
        WHERE id=?
    """, (member["id"], book_id))

    conn.commit()
    conn.close()

    return redirect(url_for("uye_kitaplar"))





@app.route("/iade-et/<int:loan_id>", methods=["POST"])
def iade_et(loan_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    loan = conn.execute(
        "SELECT * FROM loans WHERE id=?",
        (loan_id,)
    ).fetchone()

    if not loan:
        conn.close()
        return "Kayıt bulunamadı"

    conn.execute("""
        UPDATE loans
        SET status='İade', return_date=CURRENT_TIMESTAMP
        WHERE id=?
    """, (loan_id,))

    conn.execute("""
        UPDATE books
        SET status='Mevcut', borrower_id=NULL
        WHERE id=?
    """, (loan["book_id"],))

    conn.commit()
    conn.close()


    return redirect(url_for("uye_kitaplar"))

@app.route("/uye/rezervasyonlar")
def uye_rezervasyonlar():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Süresi dolan rezervasyonları güncelle
    expired = conn.execute("""
        SELECT id, book_id FROM reservations
        WHERE expire_date < ?
        AND status = 'Bekliyor'
    """, (now,)).fetchall()

    for r in expired:
        conn.execute("""
            UPDATE reservations
            SET status = 'Süresi Doldu'
            WHERE id = ?
        """, (r["id"],))

        conn.execute("""
            UPDATE books
            SET status = 'Mevcut'
            WHERE id = ?
        """, (r["book_id"],))

    conn.commit()

    # Kullanıcının rezervasyonları
    reserved_books = conn.execute("""
        SELECT r.id,
               b.title,
               r.reserve_date,
               r.expire_date,
               r.status
        FROM reservations r
        JOIN books b ON r.book_id = b.id
        WHERE r.user_id = ?
        ORDER BY r.id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "uye_rezervasyonlar.html",
        reserved_books=reserved_books
    )


@app.route("/rezervasyon/<int:book_id>", methods=["POST"])
def rezervasyon_yap(book_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    # Kitap kontrol
    book = conn.execute("""
        SELECT status FROM books WHERE id=?
    """, (book_id,)).fetchone()

    if not book or book["status"] != "Mevcut":
        conn.close()
        return "Bu kitap şu an rezerve edilemez"

    # Aynı rezervasyon var mı?
    existing = conn.execute("""
        SELECT id FROM reservations
        WHERE user_id=? AND book_id=? AND status='Bekliyor'
    """, (session["user_id"], book_id)).fetchone()

    if existing:
        conn.close()
        return redirect(url_for("uye_kitaplar"))

    # 2 günlük süre
    expire_date = datetime.now() + timedelta(days=2)

    conn.execute("""
        INSERT INTO reservations
        (user_id, book_id, expire_date, status)
        VALUES (?, ?, ?, 'Bekliyor')
    """, (
        session["user_id"],
        book_id,
        expire_date.strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.execute("""
        UPDATE books
        SET status='Rezerve'
        WHERE id=?
    """, (book_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("uye_kitaplar"))


@app.route("/rezervasyon_iptal/<int:id>")
def rezervasyon_iptal(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    r = conn.execute("""
        SELECT book_id FROM reservations
        WHERE id=? AND user_id=?
    """, (id, session["user_id"])).fetchone()

    if r:
        conn.execute("""
            DELETE FROM reservations WHERE id=?
        """, (id,))

        conn.execute("""
            UPDATE books
            SET status='Mevcut'
            WHERE id=?
        """, (r["book_id"],))

        conn.commit()

    conn.close()

    return redirect(url_for("uye_rezervasyonlar"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)