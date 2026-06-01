import pymysql  # 1. Replaced sqlite3 with pymysql
import re
from datetime import datetime
from flask import Flask, render_template, request, g, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "whimsical_crochet_secret_key_2024"

# 2. Database connection configuration details
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'            # Change if your MySQL user is different
MYSQL_PASSWORD = 'tatakae139'  # Put your MySQL root password here
MYSQL_DB = 'db_crochet'

# --- Database Helpers ---

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            cursorclass=pymysql.cursors.Cursor, 
            autocommit=True
        )
        
        # ─── THE COMPLETE SQLITE-MIMIC WRAPPER ───
        class SQLiteStyleCursor:
            def __init__(self, real_cursor):
                self.real_cursor = real_cursor

            def execute(self, query, args=None):
                # AUTOMATIC PLACEHOLDER FIX: Swap SQLite '?' for MySQL '%s'
                if query and '?' in query:
                    query = query.replace('?', '%s')
                
                self.real_cursor.execute(query, args)
                return self

            def fetchone(self):
                row = self.real_cursor.fetchone()
                if row is None: return None
                return self._make_row(row)

            def fetchall(self):
                rows = self.real_cursor.fetchall()
                return [self._make_row(r) for r in rows]

            def _make_row(self, row_tuple):
                fields = [desc[0] for desc in self.real_cursor.description]
                
                clean_row_list = []
                for value in row_tuple:
                    if isinstance(value, datetime):
                        clean_row_list.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        clean_row_list.append(value)
                
                clean_row_tuple = tuple(clean_row_list)
                row_dict = dict(zip(fields, clean_row_tuple))
                
                class SQLiteRow(dict):
                    def __getitem__(self, key):
                        if isinstance(key, int):
                            return clean_row_tuple[key]
                        return super().__getitem__(key)
                        
                return SQLiteRow(row_dict)

        cursor_instance = SQLiteStyleCursor(connection.cursor())
        connection.execute = cursor_instance.execute
        # ─────────────────────────────────────────
        
        db = g._database = connection
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name      VARCHAR(100) NOT NULL,
                email     VARCHAR(150) UNIQUE NOT NULL,
                phone     VARCHAR(20)  NOT NULL,
                address   TEXT         NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                title       VARCHAR(150) NOT NULL,
                description TEXT,
                category    VARCHAR(100) NOT NULL,
                price       REAL         NOT NULL,
                quantity    INTEGER      NOT NULL,
                available   INTEGER      NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL REFERENCES users(user_id),
                product_id       INTEGER NOT NULL REFERENCES products(product_id),
                order_date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quantity_ordered INTEGER NOT NULL,
                total_price      REAL    NOT NULL
            );
        """)

        # Seed sample data if empty
        cur = db.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            db.executescript("""
                INSERT INTO products (title, description, category, price, quantity, available) VALUES
                ('Strawberry Plushie', 'A soft, chunky crocheted strawberry with a smiling face. Perfect for gifting!', 'Plushies', 18.00, 12, 12),
                ('Cloud Bear Plushie', 'Dreamy pastel bear stuffed with love. Hand-finished with embroidered eyes.', 'Plushies', 22.50, 8, 8),
                ('Floral Cardigan', 'Vintage-inspired open-front cardigan in blush pink with floral yoke detail.', 'Cardigans', 85.00, 5, 5),
                ('Cottagecore Vest', 'Earthy tones, cropped fit. Great for layering over blouses.', 'Cardigans', 65.00, 4, 4),
                ('Mug Cozy – Autumn', 'Keep your tea warm in this fall-themed mug sleeve with leaf motifs.', 'Cozies', 12.00, 20, 20),
                ('Book Sleeve', 'A padded crochet sleeve to protect your favorite novel.', 'Cozies', 15.00, 10, 10);

                INSERT INTO users (name, email, phone, address) VALUES
                ('Rose Whitmore', 'rose@example.com', '555-0101', '12 Bluebell Lane, Cotswold, UK'),
                ('Lily Fairfax',  'lily@example.com', '555-0202', '3 Primrose Ave, Bath, UK');
            """)
        db.commit()


# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    db = get_db()
    member_count  = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    product_count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    order_count   = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    low_stock     = db.execute("SELECT COUNT(*) FROM products WHERE available <= 2").fetchone()[0]
    recent_orders = db.execute("""
        SELECT o.order_id, u.name, p.title, o.quantity_ordered, o.total_price, o.order_date
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN products p ON o.product_id = p.product_id
        ORDER BY o.order_date DESC LIMIT 5
    """).fetchall()
    return render_template("dashboard.html",
        member_count=member_count,
        product_count=product_count,
        order_count=order_count,
        low_stock=low_stock,
        recent_orders=recent_orders)


# ─── Members ─────────────────────────────────────────────────────────────────

@app.route("/members", methods=["GET"])
def view_members():
    db = get_db()
    members = db.execute("SELECT * FROM users ORDER BY name").fetchall()
    return render_template("view_members.html", members=members)


@app.route("/members/add", methods=["GET"])
def add_member_form():
    return render_template("add_member.html")


@app.route("/members", methods=["POST"])
def create_member():
    name    = request.form.get("name", "").strip()
    email   = request.form.get("email", "").strip().lower()
    phone   = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()

    errors = []
    if not name:    errors.append("Name is required.")
    if not phone:   errors.append("Phone is required.")
    if not address: errors.append("Address is required.")
    if not email:
        errors.append("Email is required.")
    elif not re.match(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", email):
        errors.append("Please enter a valid email address.")

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("add_member.html",
            prefill=dict(name=name, email=email, phone=phone, address=address))

    db = get_db()
    try:
        existing = db.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("A member with that email already exists.", "error")
            return render_template("add_member.html",
                prefill=dict(name=name, email=email, phone=phone, address=address))

        db.execute(
            "INSERT INTO users (name, email, phone, address) VALUES (?, ?, ?, ?)",
            (name, email, phone, address)
        )
        db.commit()
        flash(f"Welcome, {name}! Member account created successfully. 🌸", "success")
        return redirect(url_for("view_members"))
    except Exception as ex:
        db.rollback()
        flash(f"Database error: {ex}", "error")
        return render_template("add_member.html",
            prefill=dict(name=name, email=email, phone=phone, address=address))


# ─── Products ────────────────────────────────────────────────────────────────

@app.route("/products", methods=["GET"])
def catalog():
    db = get_db()
    sort  = request.args.get("sort", "title")
    query = request.args.get("q", "").strip()
    allowed_sort = {"title", "category", "price"}
    if sort not in allowed_sort:
        sort = "title"

    if query:
        products = db.execute(
            f"SELECT * FROM products WHERE title LIKE ? OR category LIKE ? OR description LIKE ? ORDER BY {sort}",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()
    else:
        products = db.execute(f"SELECT * FROM products ORDER BY {sort}").fetchall()

    categories = db.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    return render_template("catalog.html", products=products,
                           sort=sort, query=query, categories=categories)


@app.route("/products/add", methods=["GET"])
def add_product_form():
    return render_template("add_product.html")


@app.route("/products", methods=["POST"])
def create_product():
    title       = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category    = request.form.get("category", "").strip()
    price_raw   = request.form.get("price", "").strip()
    qty_raw     = request.form.get("quantity", "").strip()

    errors = []
    if not title:    errors.append("Title is required.")
    if not category: errors.append("Category is required.")
    try:
        price = float(price_raw)
        if price <= 0: errors.append("Price must be greater than 0.")
    except (ValueError, TypeError):
        errors.append("Price must be a valid number.")
        price = 0
    try:
        quantity = int(qty_raw)
        if quantity < 0: errors.append("Quantity cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Quantity must be a whole number.")
        quantity = 0

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("add_product.html",
            prefill=dict(title=title, description=description,
                         category=category, price=price_raw, quantity=qty_raw))

    db = get_db()
    try:
        db.execute(
            "INSERT INTO products (title, description, category, price, quantity, available) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, category, price, quantity, quantity)
        )
        db.commit()
        flash(f"'{title}' added to the catalog! ✨", "success")
        return redirect(url_for("catalog"))
    except Exception as ex:
        db.rollback()
        flash(f"Database error: {ex}", "error")
        return render_template("add_product.html",
            prefill=dict(title=title, description=description,
                         category=category, price=price_raw, quantity=qty_raw))


@app.route("/products/update/<int:pid>", methods=["GET"])
def edit_product_form(pid):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE product_id = ?", (pid,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("catalog"))
    return render_template("edit_product.html", product=product)


@app.route("/products/update/<int:pid>", methods=["POST"])
def update_product(pid):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE product_id = ?", (pid,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("catalog"))

    title    = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    price_raw= request.form.get("price", "").strip()
    qty_raw  = request.form.get("quantity", "").strip()

    errors = []
    if not title:    errors.append("Title is required.")
    if not category: errors.append("Category is required.")
    try:
        price = float(price_raw)
        if price <= 0: errors.append("Price must be greater than 0.")
    except:
        errors.append("Price must be a valid number.")
        price = 0
    try:
        quantity = int(qty_raw)
        if quantity < 0: errors.append("Quantity cannot be negative.")
    except:
        errors.append("Quantity must be a whole number.")
        quantity = 0

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("edit_product.html", product=product)

    try:
        # Adjust available proportionally
        delta = quantity - product["quantity"]
        new_available = max(0, product["available"] + delta)
        db.execute(
            "UPDATE products SET title=?, category=?, price=?, quantity=?, available=? WHERE product_id=?",
            (title, category, price, quantity, new_available, pid)
        )
        db.commit()
        flash(f"'{title}' updated successfully! 🌷", "success")
        return redirect(url_for("catalog"))
    except Exception as ex:
        db.rollback()
        flash(f"Database error: {ex}", "error")
        return render_template("edit_product.html", product=product)


@app.route("/products/delete/<int:pid>", methods=["POST"])
def delete_product(pid):
    db = get_db()
    product = db.execute("SELECT title FROM products WHERE product_id = ?", (pid,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("catalog"))
    try:
        db.execute("DELETE FROM products WHERE product_id = ?", (pid,))
        db.commit()
        flash(f"'{product['title']}' removed from the catalog.", "success")
    except Exception as ex:
        db.rollback()
        flash(f"Could not delete: {ex}", "error")
    return redirect(url_for("catalog"))


# ─── Orders ──────────────────────────────────────────────────────────────────

@app.route("/orders", methods=["GET"])
def view_orders():
    db = get_db()
    orders = db.execute("""
        SELECT o.order_id, u.name AS customer, p.title AS product,
               p.category, o.quantity_ordered, o.total_price, o.order_date
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN products p ON o.product_id = p.product_id
        ORDER BY o.order_date DESC
    """).fetchall()
    return render_template("view_orders.html", orders=orders)


@app.route("/orders/new", methods=["GET"])
def order_form():
    db = get_db()
    members  = db.execute("SELECT user_id, name FROM users ORDER BY name").fetchall()
    products = db.execute(
        "SELECT product_id, title, price, available FROM products WHERE available > 0 ORDER BY title"
    ).fetchall()
    return render_template("order_form.html", members=members, products=products)


@app.route("/orders/create", methods=["POST"])
def create_order():
    user_id_raw  = request.form.get("user_id", "").strip()
    product_id_raw = request.form.get("product_id", "").strip()
    qty_raw      = request.form.get("quantity_ordered", "").strip()

    errors = []
    try:
        user_id = int(user_id_raw)
    except:
        errors.append("Please select a valid member.")
        user_id = None
    try:
        product_id = int(product_id_raw)
    except:
        errors.append("Please select a valid product.")
        product_id = None
    try:
        qty_ordered = int(qty_raw)
        if qty_ordered <= 0: errors.append("Order quantity must be at least 1.")
    except:
        errors.append("Quantity must be a whole number.")
        qty_ordered = 0

    db = get_db()
    members  = db.execute("SELECT user_id, name FROM users ORDER BY name").fetchall()
    products = db.execute(
        "SELECT product_id, title, price, available FROM products WHERE available > 0 ORDER BY title"
    ).fetchall()

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("order_form.html", members=members, products=products)

    try:
        user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            flash("Selected member does not exist.", "error")
            return render_template("order_form.html", members=members, products=products)

        product = db.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
        if not product:
            flash("Selected product does not exist.", "error")
            return render_template("order_form.html", members=members, products=products)

        if product["available"] < qty_ordered:
            flash(
                f"Not enough stock! Only {product['available']} unit(s) of '{product['title']}' available.",
                "error"
            )
            return render_template("order_form.html", members=members, products=products)

        total = round(product["price"] * qty_ordered, 2)
        db.execute(
            "INSERT INTO orders (user_id, product_id, quantity_ordered, total_price) VALUES (?, ?, ?, ?)",
            (user_id, product_id, qty_ordered, total)
        )
        db.execute(
            "UPDATE products SET available = available - ? WHERE product_id = ?",
            (qty_ordered, product_id)
        )
        db.commit()
        flash(
            f"Order placed for {user['name']}! {qty_ordered}× '{product['title']}' — £{total:.2f} 🛍️",
            "success"
        )
        return redirect(url_for("view_orders"))

    except Exception as ex:
        db.rollback()
        flash(f"Transaction error: {ex}", "error")
        return render_template("order_form.html", members=members, products=products)


if __name__ == "__main__":
    # init_db()
    app.run(debug=True)
