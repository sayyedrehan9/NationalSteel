from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime
from functools import wraps
import webbrowser
import threading

# ============================================================
# NATIONAL STEEL - OWNER MANAGEMENT SYSTEM
# COMPLETE STABLE VERSION
# ============================================================

app = Flask(__name__)
app.secret_key = "national-steel-owner-secret-2026"

import sys

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    import sys

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    import sys

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# DATABASE PATH
# ============================================================

DB_NAME = os.path.join(BASE_DIR, "nationalsteel.db")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# DATABASE HELPERS
# ============================================================

def column_exists(conn, table_name, column_name):

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(
        row["name"] == column_name
        for row in columns
    )


def add_column_if_missing(
    conn,
    table_name,
    column_name,
    definition
):

    if not column_exists(
        conn,
        table_name,
        column_name
    ):

        conn.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {definition}
            """
        )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    conn = get_db()

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            category TEXT NOT NULL,

            price REAL DEFAULT 0,

            quantity INTEGER DEFAULT 0,

            unit TEXT DEFAULT 'Piece',

            description TEXT DEFAULT '',

            created_at TEXT

        )
    """)

    # --------------------------------------------------------
    # SALES
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id INTEGER,

            product_name TEXT DEFAULT '',

            quantity INTEGER DEFAULT 0,

            price REAL DEFAULT 0,

            total REAL DEFAULT 0,

            customer TEXT DEFAULT '',

            sale_date TEXT,

            FOREIGN KEY(product_id)
            REFERENCES products(id)

        )
    """)

    # ========================================================
    # PRODUCTS MIGRATION
    # ========================================================

    add_column_if_missing(
        conn,
        "products",
        "name",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "products",
        "category",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "products",
        "price",
        "REAL DEFAULT 0"
    )

    add_column_if_missing(
        conn,
        "products",
        "quantity",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        conn,
        "products",
        "unit",
        "TEXT DEFAULT 'Piece'"
    )

    add_column_if_missing(
        conn,
        "products",
        "description",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "products",
        "created_at",
        "TEXT"
    )

    # ========================================================
    # SALES MIGRATION
    # ========================================================

    add_column_if_missing(
        conn,
        "sales",
        "product_id",
        "INTEGER"
    )

    add_column_if_missing(
        conn,
        "sales",
        "product_name",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "sales",
        "quantity",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        conn,
        "sales",
        "price",
        "REAL DEFAULT 0"
    )

    add_column_if_missing(
        conn,
        "sales",
        "total",
        "REAL DEFAULT 0"
    )

    add_column_if_missing(
        conn,
        "sales",
        "customer",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "sales",
        "sale_date",
        "TEXT"
    )

    # ========================================================
    # FIX NULL VALUES
    # ========================================================

    conn.execute("""
        UPDATE products
        SET quantity = 0
        WHERE quantity IS NULL
    """)

    conn.execute("""
        UPDATE products
        SET price = 0
        WHERE price IS NULL
    """)

    conn.execute("""
        UPDATE products
        SET unit = 'Piece'
        WHERE unit IS NULL
        OR unit = ''
    """)

    conn.execute("""
        UPDATE sales
        SET quantity = 0
        WHERE quantity IS NULL
    """)

    conn.execute("""
        UPDATE sales
        SET price = 0
        WHERE price IS NULL
    """)

    conn.execute("""
        UPDATE sales
        SET total = price * quantity
        WHERE total IS NULL
        OR total = 0
    """)

    # ========================================================
    # REBUILD OLD PRODUCT NAMES
    # ========================================================

    try:

        conn.execute("""
            UPDATE sales

            SET product_name = (

                SELECT name

                FROM products

                WHERE products.id =
                sales.product_id

            )

            WHERE
                (product_name IS NULL
                OR product_name = '')

                AND product_id IS NOT NULL
        """)

    except Exception:

        pass

    conn.commit()
    conn.close()


# ============================================================
# OWNER LOGIN DETAILS
# ============================================================

OWNER_USERNAME = "rizwan"
OWNER_PASSWORD = "902820"


# ============================================================
# OWNER LOGIN PROTECTION
# ============================================================

def owner_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get(
            "owner_logged_in"
        ):

            return redirect(
                url_for("owner_login")
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# PUBLIC WEBSITE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# OWNER LOGIN
# ============================================================

@app.route(
    "/owner-login",
    methods=["GET", "POST"]
)
def owner_login():

    if session.get(
        "owner_logged_in"
    ):

        return redirect(
            url_for("owner_dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == OWNER_USERNAME
            and password == OWNER_PASSWORD
        ):

            session[
                "owner_logged_in"
            ] = True

            session[
                "owner_username"
            ] = username

            return redirect(
                url_for(
                    "owner_dashboard"
                )
            )

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# OWNER LOGOUT
# ============================================================

@app.route("/owner-logout")
def owner_logout():

    session.clear()

    return redirect(
        url_for("owner_login")
    )


# ============================================================
# OWNER DASHBOARD
# ============================================================

@app.route("/owner-dashboard")
@owner_required
def owner_dashboard():

    conn = get_db()

    total_products = conn.execute("""
        SELECT COUNT(*)
        FROM products
    """).fetchone()[0]

    total_stock = conn.execute("""
        SELECT COALESCE(
            SUM(quantity),
            0
        )
        FROM products
    """).fetchone()[0]

    inventory_value = conn.execute("""
        SELECT COALESCE(
            SUM(price * quantity),
            0
        )
        FROM products
    """).fetchone()[0]

    total_sales = conn.execute("""
        SELECT COALESCE(
            SUM(total),
            0
        )
        FROM sales
    """).fetchone()[0]

    total_sale_entries = conn.execute("""
        SELECT COUNT(*)
        FROM sales
    """).fetchone()[0]

    low_stock = conn.execute("""
        SELECT *
        FROM products
        WHERE quantity <= 5
        ORDER BY quantity ASC, name ASC
    """).fetchall()

    recent_sales = conn.execute("""
        SELECT *
        FROM sales
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    return render_template(
        "owner_dashboard.html",

        total_products=total_products,

        total_stock=total_stock,

        inventory_value=inventory_value,

        total_sales=total_sales,

        total_sale_entries=total_sale_entries,

        low_stock=low_stock,

        recent_sales=recent_sales
    )


# ============================================================
# PRODUCTS
# ============================================================

@app.route(
    "/products",
    methods=["GET", "POST"]
)
@owner_required
def products():

    conn = get_db()

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        price_raw = request.form.get(
            "price",
            "0"
        )

        quantity_raw = (
            request.form.get(
                "quantity"
            )
            or request.form.get(
                "stock"
            )
            or "0"
        )

        unit = request.form.get(
            "unit",
            "Piece"
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:

            price = float(
                price_raw
            )

        except (
            ValueError,
            TypeError
        ):

            price = 0

        try:

            quantity = int(
                quantity_raw
            )

        except (
            ValueError,
            TypeError
        ):

            quantity = 0

        if not name:

            flash(
                "Product name is required.",
                "error"
            )

        elif not category:

            flash(
                "Category is required.",
                "error"
            )

        elif price < 0:

            flash(
                "Price cannot be negative.",
                "error"
            )

        elif quantity < 0:

            flash(
                "Stock quantity cannot be negative.",
                "error"
            )

        else:

            conn.execute("""
                INSERT INTO products
                (
                    name,
                    category,
                    price,
                    quantity,
                    unit,
                    description,
                    created_at
                )

                VALUES (?, ?, ?, ?, ?, ?, ?)

            """, (

                name,

                category,

                price,

                quantity,

                unit or "Piece",

                description,

                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            ))

            conn.commit()

            flash(
                "Product added successfully.",
                "success"
            )

    product_list = conn.execute("""
        SELECT

            id,

            name,

            category,

            price,

            quantity,

            quantity AS stock,

            unit,

            description,

            created_at

        FROM products

        ORDER BY id DESC

    """).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=product_list
    )


# ============================================================
# ADD PRODUCT
# ============================================================

@app.route(
    "/add-product",
    methods=["GET", "POST"]
)
@owner_required
def add_product():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        price_raw = request.form.get(
            "price",
            "0"
        )

        quantity_raw = (
            request.form.get(
                "quantity"
            )
            or request.form.get(
                "stock"
            )
            or "0"
        )

        unit = request.form.get(
            "unit",
            "Piece"
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:

            price = float(
                price_raw
            )

        except (
            ValueError,
            TypeError
        ):

            price = 0

        try:

            quantity = int(
                quantity_raw
            )

        except (
            ValueError,
            TypeError
        ):

            quantity = 0

        if not name or not category:

            flash(
                "Please fill all required fields.",
                "error"
            )

            return render_template(
                "add_product.html"
            )

        if price < 0:

            flash(
                "Price cannot be negative.",
                "error"
            )

            return render_template(
                "add_product.html"
            )

        if quantity < 0:

            flash(
                "Stock cannot be negative.",
                "error"
            )

            return render_template(
                "add_product.html"
            )

        conn = get_db()

        conn.execute("""
            INSERT INTO products
            (
                name,
                category,
                price,
                quantity,
                unit,
                description,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)

        """, (

            name,

            category,

            price,

            quantity,

            unit or "Piece",

            description,

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ))

        conn.commit()
        conn.close()

        flash(
            f"Product added successfully. Stock: {quantity}",
            "success"
        )

        return redirect(
            url_for("products")
        )

    return render_template(
        "add_product.html"
    )


# ============================================================
# EDIT PRODUCT
# ============================================================

@app.route(
    "/edit-product/<int:product_id>",
    methods=["GET", "POST"]
)
@owner_required
def edit_product(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT

            id,

            name,

            category,

            price,

            quantity,

            quantity AS stock,

            unit,

            description,

            created_at

        FROM products

        WHERE id = ?

    """, (
        product_id,
    )).fetchone()

    if product is None:

        conn.close()

        flash(
            "Product not found.",
            "error"
        )

        return redirect(
            url_for("products")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        price_raw = request.form.get(
            "price",
            "0"
        )

        quantity_raw = (
            request.form.get(
                "quantity"
            )
            or request.form.get(
                "stock"
            )
            or "0"
        )

        unit = request.form.get(
            "unit",
            "Piece"
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:

            price = float(
                price_raw
            )

        except (
            ValueError,
            TypeError
        ):

            price = 0

        try:

            quantity = int(
                quantity_raw
            )

        except (
            ValueError,
            TypeError
        ):

            quantity = 0

        if not name or not category:

            flash(
                "Name and category are required.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_product.html",
                product=product
            )

        if price < 0 or quantity < 0:

            flash(
                "Price and stock cannot be negative.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_product.html",
                product=product
            )

        conn.execute("""
            UPDATE products

            SET

                name = ?,

                category = ?,

                price = ?,

                quantity = ?,

                unit = ?,

                description = ?

            WHERE id = ?

        """, (

            name,

            category,

            price,

            quantity,

            unit or "Piece",

            description,

            product_id

        ))

        conn.commit()
        conn.close()

        flash(
            "Product updated successfully.",
            "success"
        )

        return redirect(
            url_for("products")
        )

    conn.close()

    return render_template(
        "edit_product.html",
        product=product
    )


# ============================================================
# DELETE PRODUCT
# ============================================================

@app.route(
    "/delete-product/<int:product_id>",
    methods=["POST"]
)
@owner_required
def delete_product(product_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM products
        WHERE id = ?
    """, (
        product_id,
    ))

    conn.commit()
    conn.close()

    flash(
        "Product deleted successfully.",
        "success"
    )

    return redirect(
        url_for("products")
    )


# ============================================================
# SALES
# ============================================================

@app.route(
    "/sales",
    methods=["GET", "POST"]
)
@owner_required
def sales():

    conn = get_db()

    if request.method == "POST":

        product_id_raw = request.form.get(
            "product_id",
            ""
        )

        quantity_raw = request.form.get(
            "quantity",
            ""
        )

        customer = request.form.get(
            "customer",
            ""
        ).strip()

        try:

            product_id = int(
                product_id_raw
            )

            quantity = int(
                quantity_raw
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Invalid sale details.",
                "error"
            )

            conn.close()

            return redirect(
                url_for("sales")
            )

        product = conn.execute("""
            SELECT

                id,

                name,

                category,

                price,

                quantity,

                unit

            FROM products

            WHERE id = ?

        """, (
            product_id,
        )).fetchone()

        if product is None:

            flash(
                "Product not found.",
                "error"
            )

        elif quantity <= 0:

            flash(
                "Quantity must be greater than zero.",
                "error"
            )

        elif product["quantity"] <= 0:

            flash(
                "This product is out of stock.",
                "error"
            )

        elif quantity > product["quantity"]:

            flash(
                f"Not enough stock. Available: {product['quantity']}",
                "error"
            )

        else:

            sale_price = float(
                product["price"] or 0
            )

            total = (
                sale_price
                * quantity
            )

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            conn.execute("""
                INSERT INTO sales
                (
                    product_id,
                    product_name,
                    quantity,
                    price,
                    total,
                    customer,
                    sale_date
                )

                VALUES (?, ?, ?, ?, ?, ?, ?)

            """, (

                product["id"],

                product["name"],

                quantity,

                sale_price,

                total,

                customer,

                now

            ))

            conn.execute("""
                UPDATE products

                SET quantity =
                    quantity - ?

                WHERE id = ?

            """, (

                quantity,

                product_id

            ))

            conn.commit()

            flash(
                "Sale recorded successfully and stock updated.",
                "success"
            )

    products_list = conn.execute("""
        SELECT

            id,

            name,

            category,

            price,

            quantity,

            quantity AS stock,

            unit,

            description,

            created_at

        FROM products

        ORDER BY name COLLATE NOCASE

    """).fetchall()

    recent_sales = conn.execute("""
        SELECT *

        FROM sales

        ORDER BY id DESC

        LIMIT 10

    """).fetchall()

    total_sales = conn.execute("""
        SELECT COALESCE(
            SUM(total),
            0
        )

        FROM sales

    """).fetchone()[0]

    total_sale_entries = conn.execute("""
        SELECT COUNT(*)

        FROM sales

    """).fetchone()[0]

    conn.close()

    return render_template(

        "sales.html",

        products=products_list,

        recent_sales=recent_sales,

        total_sales=total_sales,

        total_sale_entries=total_sale_entries

    )


# ============================================================
# SALES HISTORY
# ============================================================

@app.route("/sales-history")
@owner_required
def sales_history():

    conn = get_db()

    sales_list = conn.execute("""
        SELECT

            id,

            product_id,

            product_name,

            quantity,

            price,

            total,

            customer,

            sale_date

        FROM sales

        ORDER BY id DESC

    """).fetchall()

    total_sales = conn.execute("""
        SELECT COALESCE(
            SUM(total),
            0
        )

        FROM sales

    """).fetchone()[0]

    total_sale_entries = conn.execute("""
        SELECT COUNT(*)

        FROM sales

    """).fetchone()[0]

    total_units_sold = conn.execute("""
        SELECT COALESCE(
            SUM(quantity),
            0
        )

        FROM sales

    """).fetchone()[0]

    conn.close()

    return render_template(

        "sales_history.html",

        sales_history=sales_list,

        sales=sales_list,

        total_sales=total_sales,

        total_sale_entries=total_sale_entries,

        total_units_sold=total_units_sold

    )


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
@owner_required
def reports():

    conn = get_db()

    total_products = conn.execute("""
        SELECT COUNT(*)
        FROM products
    """).fetchone()[0]

    total_stock = conn.execute("""
        SELECT COALESCE(
            SUM(quantity),
            0
        )
        FROM products
    """).fetchone()[0]

    inventory_value = conn.execute("""
        SELECT COALESCE(
            SUM(price * quantity),
            0
        )
        FROM products
    """).fetchone()[0]

    total_sales = conn.execute("""
        SELECT COALESCE(
            SUM(total),
            0
        )
        FROM sales
    """).fetchone()[0]

    total_items_sold = conn.execute("""
        SELECT COALESCE(
            SUM(quantity),
            0
        )
        FROM sales
    """).fetchone()[0]

    category_rows = conn.execute("""
        SELECT

            category,

            COUNT(*) AS count,

            COALESCE(
                SUM(quantity),
                0
            ) AS stock,

            COALESCE(
                SUM(price * quantity),
                0
            ) AS value

        FROM products

        GROUP BY category

        ORDER BY category

    """).fetchall()

    categories = []

    for row in category_rows:

        categories.append({

            "category":
                row["category"]
                or "General",

            "count":
                row["count"]
                or 0,

            "stock":
                row["stock"]
                or 0,

            "value":
                row["value"]
                or 0

        })

    low_stock_rows = conn.execute("""
        SELECT

            id,

            name,

            category,

            price,

            quantity,

            quantity AS stock,

            unit

        FROM products

        WHERE quantity <= 5

        ORDER BY
            quantity ASC,
            name ASC

    """).fetchall()

    low_stock = []

    for row in low_stock_rows:

        low_stock.append({

            "id":
                row["id"],

            "name":
                row["name"]
                or "Product",

            "product_name":
                row["name"]
                or "Product",

            "category":
                row["category"]
                or "General",

            "price":
                row["price"]
                or 0,

            "quantity":
                row["quantity"]
                or 0,

            "stock":
                row["stock"]
                or 0,

            "unit":
                row["unit"]
                or "Piece"

        })

    recent_sale_rows = conn.execute("""
        SELECT

            id,

            product_id,

            product_name,

            quantity,

            price,

            total,

            customer,

            sale_date

        FROM sales

        ORDER BY id DESC

        LIMIT 20

    """).fetchall()

    recent_sales = []

    for row in recent_sale_rows:

        recent_sales.append({

            "id":
                row["id"],

            "product_id":
                row["product_id"],

            "product_name":
                row["product_name"]
                or "Product",

            "name":
                row["product_name"]
                or "Product",

            "quantity":
                row["quantity"]
                or 0,

            "quantity_sold":
                row["quantity"]
                or 0,

            "price":
                row["price"]
                or 0,

            "total":
                row["total"]
                or 0,

            "total_amount":
                row["total"]
                or 0,

            "customer":
                row["customer"]
                or "",

            "sale_date":
                row["sale_date"]
                or ""

        })

    conn.close()

    return render_template(

        "reports.html",

        total_products=total_products,

        total_stock=total_stock,

        inventory_value=inventory_value,

        total_sales=total_sales,

        total_items_sold=total_items_sold,

        categories=categories,

        low_stock=low_stock,

        recent_sales=recent_sales

    )


# ============================================================
# ABOUT / OWNER ABOUT PAGE
# ============================================================

@app.route("/about")
@owner_required
def about():

    return render_template(
        "about.html"
    )


# ============================================================
# AUTOMATIC BROWSER OPEN
# ============================================================

def open_browser():

    try:

        webbrowser.open(
            "http://127.0.0.1:5000"
        )

    except Exception:

        pass


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    init_db()

    print("")
    print("================================================")
    print("        NATIONAL STEEL MANAGEMENT SYSTEM")
    print("================================================")
    print("Server starting...")
    print("")
    print("Website:")
    print("http://127.0.0.1:5000")
    print("")
    print("Owner Login:")
    print("http://127.0.0.1:5000/owner-login")
    print("")
    print("Username: rizwan")
    print("Password: 902820")
    print("================================================")
    print("")

    # Open browser automatically after server starts.
    # Only the reloader-disabled process is used for EXE.
    threading.Timer(
        2.0,
        open_browser
    ).start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )