import pymysql  # 1. Replaced sqlite3 with pymysql
import re
import os
from datetime import datetime
from flask import Flask, render_template, request, g, flash, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "whimsical_crochet_secret_key_2024"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    db = get_db()

    # Order status counts
    pending_count     = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'").fetchone()[0]
    in_progress_count = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'In Progress'").fetchone()[0]
    completed_count   = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'Completed'").fetchone()[0]

    # Total revenue
    rev_row = db.execute("SELECT SUM(total_price) FROM orders").fetchone()
    total_revenue = float(rev_row[0]) if rev_row[0] else 0.0

    # Total investment
    inv_row = db.execute("SELECT SUM(amount) FROM investments").fetchone()
    total_investment = float(inv_row[0]) if inv_row[0] else 0.0

    # Total profit
    total_profit = total_revenue - total_investment

    # New orders today
    new_orders_today = db.execute(
        "SELECT COUNT(*) FROM orders WHERE DATE(order_date) = CURDATE()"
    ).fetchone()[0]

    # Best-selling product by quantity
    best_seller = db.execute("""
        SELECT p.title, SUM(o.quantity_ordered) AS total_sold
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        GROUP BY p.product_id, p.title
        ORDER BY total_sold DESC LIMIT 1
    """).fetchone()

    # Recent 5 orders (using COALESCE for customer name)
    recent_orders = db.execute("""
        SELECT o.order_id, COALESCE(o.customer_name, u.name) AS name, p.title, 
               o.quantity_ordered, o.total_price, o.order_date, o.status
        FROM orders o
        LEFT JOIN customers u ON o.customer_id = u.customer_id
        JOIN products p ON o.product_id = p.product_id
        ORDER BY o.order_date DESC LIMIT 5
    """).fetchall()

    return render_template("dashboard.html",
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        total_revenue=total_revenue,
        total_profit=total_profit,
        new_orders_today=new_orders_today,
        best_seller=best_seller,
        recent_orders=recent_orders)

# ─── Investments ─────────────────────────────────────────────────────────────

@app.route("/investments", methods=["GET"])
def investments():
    db = get_db()
    
    # Get all investments
    inv_records = db.execute("SELECT * FROM investments ORDER BY date DESC").fetchall()
    
    # Total investment
    inv_row = db.execute("SELECT SUM(amount) FROM investments").fetchone()
    total_investment = float(inv_row[0]) if inv_row[0] else 0.0
    
    # Total revenue
    rev_row = db.execute("SELECT SUM(total_price) FROM orders").fetchone()
    total_revenue = float(rev_row[0]) if rev_row[0] else 0.0
    
    total_profit = total_revenue - total_investment
    
    return render_template("investments.html", 
                           investments=inv_records, 
                           total_investment=total_investment,
                           total_revenue=total_revenue,
                           total_profit=total_profit)

@app.route("/investments/add", methods=["POST"])
def add_investment():
    db = get_db()
    amount_raw = request.form.get("amount", "").strip()
    description = request.form.get("description", "").strip()
    
    if not description:
        flash("Description is required.", "error")
        return redirect(url_for("investments"))
        
    try:
        amount = float(amount_raw)
        if amount <= 0:
            flash("Investment amount must be greater than 0.", "error")
            return redirect(url_for("investments"))
    except ValueError:
        flash("Amount must be a valid number.", "error")
        return redirect(url_for("investments"))
        
    try:
        db.execute("INSERT INTO investments (amount, description) VALUES (?, ?)", (amount, description))
        db.commit()
        flash("Investment recorded successfully! 💸", "success")
    except Exception as ex:
        db.rollback()
        flash(f"Database error: {ex}", "error")
        
    return redirect(url_for("investments"))

@app.route("/investments/delete/<int:iid>", methods=["POST"])
def delete_investment(iid):
    db = get_db()
    try:
        db.execute("DELETE FROM investments WHERE investment_id = ?", (iid,))
        db.commit()
        flash("Investment deleted successfully.", "success")
    except Exception as ex:
        db.rollback()
        flash(f"Could not delete investment: {ex}", "error")
    return redirect(url_for("investments"))

@app.route("/investments/edit/<int:iid>", methods=["GET"])
def edit_investment_form(iid):
    db = get_db()
    investment = db.execute("SELECT * FROM investments WHERE investment_id = ?", (iid,)).fetchone()
    if not investment:
        flash("Investment not found.", "error")
        return redirect(url_for("investments"))
    return render_template("edit_investment.html", investment=investment)

@app.route("/investments/edit/<int:iid>", methods=["POST"])
def update_investment(iid):
    db = get_db()
    amount_raw = request.form.get("amount", "").strip()
    description = request.form.get("description", "").strip()
    
    if not description:
        flash("Description is required.", "error")
        return redirect(url_for("edit_investment_form", iid=iid))
        
    try:
        amount = float(amount_raw)
        if amount <= 0:
            flash("Investment amount must be greater than 0.", "error")
            return redirect(url_for("edit_investment_form", iid=iid))
    except ValueError:
        flash("Amount must be a valid number.", "error")
        return redirect(url_for("edit_investment_form", iid=iid))
        
    try:
        db.execute("UPDATE investments SET amount = ?, description = ? WHERE investment_id = ?", (amount, description, iid))
        db.commit()
        flash("Investment updated successfully! 💸", "success")
    except Exception as ex:
        db.rollback()
        flash(f"Database error: {ex}", "error")
        
    return redirect(url_for("investments"))


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

    # Handle optional image upload
    image_path = None
    file = request.files.get("image")
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        image_path = f"uploads/{filename}"

    db = get_db()
    try:
        db.execute(
            "INSERT INTO products (title, description, category, price, quantity, available, image_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, description, category, price, quantity, quantity, image_path)
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

    # Handle optional image upload (keep existing if none uploaded)
    image_path = product.get("image_path")
    file = request.files.get("image")
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        image_path = f"uploads/{filename}"

    try:
        # Adjust available proportionally
        delta = quantity - product["quantity"]
        new_available = max(0, product["available"] + delta)
        db.execute(
            "UPDATE products SET title=?, category=?, price=?, quantity=?, available=?, image_path=? WHERE product_id=?",
            (title, category, price, quantity, new_available, image_path, pid)
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
        SELECT o.order_id, COALESCE(o.customer_name, u.name) AS customer, 
               COALESCE(o.customer_email, u.email) AS customer_email,
               COALESCE(o.customer_phone, u.phone) AS customer_phone,
               COALESCE(o.customer_address, u.address) AS customer_address,
               p.title AS product, p.category, o.quantity_ordered, o.total_price, 
               o.order_date, o.status, o.payment_method
        FROM orders o
        LEFT JOIN customers u ON o.customer_id = u.customer_id
        JOIN products p ON o.product_id = p.product_id
        ORDER BY o.order_date DESC
    """).fetchall()
    return render_template("view_orders.html", orders=orders)


@app.route("/orders/new", methods=["GET"])
def order_form():
    db = get_db()
    products = db.execute(
        "SELECT product_id, title, price, available FROM products WHERE available > 0 ORDER BY title"
    ).fetchall()
    return render_template("order_form.html", products=products)


@app.route("/orders/create", methods=["POST"])
def create_order():
    customer_name    = request.form.get("customer_name", "").strip()
    customer_email   = request.form.get("customer_email", "").strip()
    customer_phone   = request.form.get("customer_phone", "").strip()
    customer_address = request.form.get("customer_address", "").strip()
    payment_method   = request.form.get("payment_method", "Online").strip()
    
    product_id_raw = request.form.get("product_id", "").strip()
    qty_raw      = request.form.get("quantity_ordered", "").strip()

    errors = []
    
    if not customer_name: errors.append("Customer name is required.")
    if not customer_email: errors.append("Customer email is required.")
    if not customer_phone: errors.append("Customer phone is required.")
    if not customer_address: errors.append("Customer address is required.")
    if payment_method not in ["COD", "Online"]: errors.append("Invalid payment method.")

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
    products = db.execute(
        "SELECT product_id, title, price, available FROM products WHERE available > 0 ORDER BY title"
    ).fetchall()

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("order_form.html", products=products, 
            customer_name=customer_name, customer_email=customer_email, 
            customer_phone=customer_phone, customer_address=customer_address, 
            payment_method=payment_method)

    try:
        product = db.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
        if not product:
            flash("Selected product does not exist.", "error")
            return render_template("order_form.html", products=products)

        if product["available"] < qty_ordered:
            flash(f"Not enough stock! Only {product['available']} unit(s) available.", "error")
            return render_template("order_form.html", products=products, 
                customer_name=customer_name, customer_email=customer_email, 
                customer_phone=customer_phone, customer_address=customer_address, 
                payment_method=payment_method)

        total = round(product["price"] * qty_ordered, 2)
        db.execute(
            """INSERT INTO orders (product_id, quantity_ordered, total_price, customer_name, customer_email, customer_phone, customer_address, payment_method) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_id, qty_ordered, total, customer_name, customer_email, customer_phone, customer_address, payment_method)
        )
        db.execute("UPDATE products SET available = available - ? WHERE product_id = ?", (qty_ordered, product_id))
        db.commit()
        flash(f"Order placed for {customer_name}! {qty_ordered}× '{product['title']}' — PKR {total:.2f} 🛍️", "success")
        return redirect(url_for("view_orders"))

    except Exception as ex:
        db.rollback()
        flash(f"Transaction error: {ex}", "error")
        return render_template("order_form.html", products=products, 
            customer_name=customer_name, customer_email=customer_email, 
            customer_phone=customer_phone, customer_address=customer_address, 
            payment_method=payment_method)

@app.route("/orders/update/<int:oid>", methods=["GET"])
def edit_order_form(oid):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE order_id = ?", (oid,)).fetchone()
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("view_orders"))
        
    products = db.execute(
        "SELECT product_id, title, price, available FROM products ORDER BY title"
    ).fetchall()
    
    return render_template("edit_order.html", order=order, products=products)

@app.route("/orders/update/<int:oid>", methods=["POST"])
def update_order(oid):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE order_id = ?", (oid,)).fetchone()
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("view_orders"))

    customer_name    = request.form.get("customer_name", "").strip()
    customer_email   = request.form.get("customer_email", "").strip()
    customer_phone   = request.form.get("customer_phone", "").strip()
    customer_address = request.form.get("customer_address", "").strip()
    payment_method   = request.form.get("payment_method", "Online").strip()
    
    product_id_raw = request.form.get("product_id", "").strip()
    qty_raw      = request.form.get("quantity_ordered", "").strip()

    errors = []
    
    if not customer_name: errors.append("Customer name is required.")
    if not customer_email: errors.append("Customer email is required.")
    if not customer_phone: errors.append("Customer phone is required.")
    if not customer_address: errors.append("Customer address is required.")
    if payment_method not in ["COD", "Online"]: errors.append("Invalid payment method.")

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

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("edit_order_form", oid=oid))

    try:
        product = db.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
        if not product:
            flash("Selected product does not exist.", "error")
            return redirect(url_for("edit_order_form", oid=oid))

        # Calculate difference in quantity to update product availability
        old_product_id = order["product_id"]
        old_qty = order["quantity_ordered"]
        
        if old_product_id == product_id:
            qty_diff = qty_ordered - old_qty
            if product["available"] < qty_diff:
                flash(f"Not enough stock! Only {product['available']} unit(s) available.", "error")
                return redirect(url_for("edit_order_form", oid=oid))
            db.execute("UPDATE products SET available = available - ? WHERE product_id = ?", (qty_diff, product_id))
        else:
            # Different product selected, restore old stock, check new stock
            old_product = db.execute("SELECT * FROM products WHERE product_id = ?", (old_product_id,)).fetchone()
            if product["available"] < qty_ordered:
                flash(f"Not enough stock! Only {product['available']} unit(s) available.", "error")
                return redirect(url_for("edit_order_form", oid=oid))
            
            db.execute("UPDATE products SET available = available + ? WHERE product_id = ?", (old_qty, old_product_id))
            db.execute("UPDATE products SET available = available - ? WHERE product_id = ?", (qty_ordered, product_id))

        total = round(product["price"] * qty_ordered, 2)
        db.execute(
            """UPDATE orders 
               SET product_id=?, quantity_ordered=?, total_price=?, 
                   customer_name=?, customer_email=?, customer_phone=?, 
                   customer_address=?, payment_method=?
               WHERE order_id=?""",
            (product_id, qty_ordered, total, customer_name, customer_email, customer_phone, customer_address, payment_method, oid)
        )
        db.commit()
        flash(f"Order #{oid} updated successfully!", "success")
        return redirect(url_for("view_orders"))

    except Exception as ex:
        db.rollback()
        flash(f"Transaction error: {ex}", "error")
        return redirect(url_for("edit_order_form", oid=oid))

@app.route("/orders/delete/<int:oid>", methods=["POST"])
def delete_order(oid):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE order_id = ?", (oid,)).fetchone()
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("view_orders"))
    try:
        db.execute("UPDATE products SET available = available + ? WHERE product_id = ?", (order["quantity_ordered"], order["product_id"]))
        db.execute("DELETE FROM orders WHERE order_id = ?", (oid,))
        db.commit()
        flash(f"Order #{oid} deleted and stock restored.", "success")
    except Exception as ex:
        db.rollback()
        flash(f"Could not delete order: {ex}", "error")
    return redirect(url_for("view_orders"))

@app.route("/orders/status/<int:oid>", methods=["POST"])
def update_order_status(oid):
    status = request.form.get("status", "Pending")
    if status not in {"Pending", "In Progress", "Completed"}:
        flash("Invalid status.", "error")
        return redirect(url_for("view_orders"))
    db = get_db()
    try:
        db.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, oid))
        db.commit()
        flash(f"Order #{oid} status updated to '{status}'.", "success")
    except Exception as ex:
        db.rollback()
        flash(f"Could not update status: {ex}", "error")
    return redirect(url_for("view_orders"))

@app.route("/products/delete-image/<int:pid>", methods=["POST"])
def delete_product_image(pid):
    db = get_db()
    product = db.execute("SELECT title, image_path FROM products WHERE product_id = ?", (pid,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("catalog"))
    try:
        if product["image_path"]:
            full_path = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(product["image_path"]))
            if os.path.exists(full_path):
                os.remove(full_path)
        db.execute("UPDATE products SET image_path = NULL WHERE product_id = ?", (pid,))
        db.commit()
        flash(f"Image for '{product['title']}' removed.", "success")
    except Exception as ex:
        db.rollback()
        flash(f"Could not delete image: {ex}", "error")
    return redirect(url_for("edit_product_form", pid=pid))

if __name__ == "__main__":
    # init_db()
    app.run(debug=True)

