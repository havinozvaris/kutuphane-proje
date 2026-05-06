from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'library.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE NOT NULL,
        category TEXT DEFAULT 'Klasik',
        year INTEGER,
        status TEXT DEFAULT 'Mevcut',
        borrower_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        active INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        member_id INTEGER,
        loan_date TEXT DEFAULT CURRENT_TIMESTAMP,
        return_date TEXT,
        status TEXT DEFAULT 'Aktif',
        FOREIGN KEY(book_id) REFERENCES books(id),
        FOREIGN KEY(member_id) REFERENCES members(id)
    )''')

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
        c.executemany("INSERT INTO books (title, author, isbn, category, year, status) VALUES (?,?,?,?,?,?)", books)

    c.execute("SELECT COUNT(*) FROM members")
    if c.fetchone()[0] == 0:
        members = [
            ("Ahmet Yılmaz", "ahmet@email.com", "0532-111-2233"),
            ("Ayşe Kaya", "ayse@email.com", "0533-222-3344"),
            ("Mehmet Demir", "mehmet@email.com", "0534-333-4455"),
            ("Zeynep Arslan", "zeynep@email.com", "0535-444-5566"),
            ("Can Türk", "can@email.com", "0536-555-6677"),
        ]
        c.executemany("INSERT INTO members (name, email, phone) VALUES (?,?,?)", members)

        c.execute("UPDATE books SET status='Ödünçte', borrower_id=1 WHERE id=3")
        c.execute("UPDATE books SET status='Ödünçte', borrower_id=2 WHERE id=8")
        c.execute("UPDATE books SET status='Ödünçte', borrower_id=3 WHERE id=12")
        c.execute("INSERT INTO loans (book_id, member_id) VALUES (3,1),(8,2),(12,3)")
        c.execute("UPDATE books SET status='Rezerve', borrower_id=4 WHERE id=6")
        c.execute("UPDATE books SET status='Rezerve', borrower_id=5 WHERE id=15")

    conn.commit()
    conn.close()

@app.route('/')
def dashboard():
    conn = get_db()
    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    available = conn.execute("SELECT COUNT(*) FROM books WHERE status='Mevcut'").fetchone()[0]
    loaned = conn.execute("SELECT COUNT(*) FROM books WHERE status='Ödünçte'").fetchone()[0]
    reserved = conn.execute("SELECT COUNT(*) FROM books WHERE status='Rezerve'").fetchone()[0]
    total_members = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    active_loans = conn.execute("SELECT COUNT(*) FROM loans WHERE status='Aktif'").fetchone()[0]
    recent_loans = conn.execute("""
        SELECT l.id, b.title, m.name, l.loan_date FROM loans l
        JOIN books b ON l.book_id=b.id
        JOIN members m ON l.member_id=m.id
        WHERE l.status='Aktif' ORDER BY l.loan_date DESC LIMIT 5
    """).fetchall()
    conn.close()
    return render_template('dashboard.html',
        total_books=total_books, available=available, loaned=loaned,
        reserved=reserved, total_members=total_members,
        active_loans=active_loans, recent_loans=recent_loans)

# BOOKS
@app.route('/books')
def books():
    conn = get_db()
    q = request.args.get('q', '')
    books = conn.execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? ORDER BY id DESC",
        (f'%{q}%', f'%{q}%', f'%{q}%')
    ).fetchall()
    conn.close()
    return render_template('books.html', books=books, q=q)

@app.route('/books/add', methods=['GET','POST'])
def add_book():
    if request.method == 'POST':
        d = request.form
        conn = get_db()
        try:
            conn.execute("INSERT INTO books (title,author,isbn,category,year) VALUES (?,?,?,?,?)",
                (d['title'], d['author'], d['isbn'], d.get('category','Klasik'), d.get('year') or None))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('books.html', error="Bu ISBN zaten kayıtlı!", books=[])
        conn.close()
        return redirect(url_for('books'))
    return render_template('books.html', books=[], error=None)

@app.route('/books/edit/<int:id>', methods=['GET','POST'])
def edit_book(id):
    conn = get_db()
    if request.method == 'POST':
        d = request.form
        conn.execute("UPDATE books SET title=?,author=?,isbn=?,category=?,year=? WHERE id=?",
            (d['title'], d['author'], d['isbn'], d.get('category','Klasik'), d.get('year') or None, id))
        conn.commit()
        conn.close()
        return redirect(url_for('books'))
    book = conn.execute("SELECT * FROM books WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('books.html', books=[book], error=None)

@app.route('/books/delete/<int:id>', methods=['POST'])
def delete_book(id):
    conn = get_db()
    conn.execute("DELETE FROM books WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('books'))

# MEMBERS
@app.route('/members')
def members():
    conn = get_db()
    q = request.args.get('q', '')
    members = conn.execute(
        "SELECT m.*, COUNT(l.id) as loan_count FROM members m "
        "LEFT JOIN loans l ON m.id=l.member_id AND l.status='Aktif' "
        "WHERE m.name LIKE ? OR m.email LIKE ? OR m.phone LIKE ? "
        "GROUP BY m.id ORDER BY m.id DESC",
        (f'%{q}%', f'%{q}%', f'%{q}%')
    ).fetchall()
    conn.close()
    return render_template('uyeler.html', members=members, q=q)

@app.route('/members/add', methods=['GET','POST'])
def add_member():
    if request.method == 'POST':
        d = request.form
        conn = get_db()
        try:
            conn.execute("INSERT INTO members (name,email,phone) VALUES (?,?,?)",
                (d['name'], d['email'], d.get('phone','')))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('uye_ekle.html', error="Bu e-posta zaten kayıtlı!", member=None)
        conn.close()
        return redirect(url_for('members'))
    return render_template('uye_ekle.html', member=None, error=None)

@app.route('/members/edit/<int:id>', methods=['GET','POST'])
def edit_member(id):
    conn = get_db()
    if request.method == 'POST':
        d = request.form
        conn.execute("UPDATE members SET name=?,email=?,phone=? WHERE id=?",
            (d['name'], d['email'], d.get('phone',''), id))
        conn.commit()
        conn.close()
        return redirect(url_for('members'))
    member = conn.execute("SELECT * FROM members WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('uye_ekle.html', member=member, error=None)

@app.route('/members/delete/<int:id>', methods=['POST'])
def delete_member(id):
    conn = get_db()
    conn.execute("DELETE FROM members WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('members'))

# LOANS
@app.route('/loans')
def loans():
    conn = get_db()
    available_books = conn.execute("SELECT * FROM books WHERE status='Mevcut'").fetchall()
    all_members = conn.execute("SELECT * FROM members").fetchall()
    active_loans = conn.execute("""
        SELECT l.*, b.title, b.isbn, m.name as member_name
        FROM loans l JOIN books b ON l.book_id=b.id JOIN members m ON l.member_id=m.id
        WHERE l.status='Aktif' ORDER BY l.loan_date DESC
    """).fetchall()
    conn.close()
    return render_template('odunc_ver.html', available_books=available_books, all_members=all_members, active_loans=active_loans)

@app.route('/loans/add', methods=['POST'])
def add_loan():
    d = request.form
    conn = get_db()
    conn.execute("INSERT INTO loans (book_id, member_id) VALUES (?,?)", (d['book_id'], d['member_id']))
    conn.execute("UPDATE books SET status='Ödünçte', borrower_id=? WHERE id=?", (d['member_id'], d['book_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('loans'))

@app.route('/loans/return/<int:id>', methods=['POST'])
def return_loan(id):
    conn = get_db()
    loan = conn.execute("SELECT * FROM loans WHERE id=?", (id,)).fetchone()
    if loan:
        conn.execute("UPDATE loans SET status='İade', return_date=CURRENT_TIMESTAMP WHERE id=?", (id,))
        conn.execute("UPDATE books SET status='Mevcut', borrower_id=NULL WHERE id=?", (loan['book_id'],))
        conn.commit()
    conn.close()
    return redirect(url_for('loans'))

@app.route('/iade-al')
def iade_al():
    conn = get_db()
    loaned_books = conn.execute("""
        SELECT l.id as loan_id, b.title, b.isbn, m.name as member_name, l.loan_date 
        FROM loans l 
        JOIN books b ON l.book_id = b.id 
        JOIN members m ON l.member_id = m.id 
        WHERE l.status = 'Aktif' 
        ORDER BY l.loan_date DESC
    """).fetchall()
    conn.close()
    return render_template('iade_al.html', loaned_books=loaned_books)

@app.route('/reports')
def reports():
    conn = get_db()
    by_category = conn.execute("SELECT category, COUNT(*) as cnt FROM books GROUP BY category").fetchall()
    by_status = conn.execute("SELECT status, COUNT(*) as cnt FROM books GROUP BY status").fetchall()
    top_borrowed = conn.execute("""
        SELECT b.title, b.author, COUNT(l.id) as times
        FROM loans l JOIN books b ON l.book_id=b.id
        GROUP BY b.id ORDER BY times DESC LIMIT 5
    """).fetchall()
    conn.close()
    return render_template('reports.html', by_category=by_category, by_status=by_status, top_borrowed=top_borrowed)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)