# 🧶 Thread & Bloom — Crochet Business Manager

A complete Flask web application for managing a handmade crochet business.
Features a **Whimsical Vintage Coquette** aesthetic with a custom CSS design system.

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Then visit: **http://127.0.0.1:5000**

The database is auto-created and seeded with sample products and members on first run.

## Features

| Module | What it does |
|---|---|
| **Dashboard** | Stats overview, quick actions, recent orders |
| **Members** | Register customers, view directory, duplicate email guard |
| **Catalog** | Add/edit/delete products, live search, sort by title/category/price |
| **Orders** | Place orders with stock validation, live price preview, full ledger |

## File Structure

```
crochet_app/
├── app.py                  # Flask backend + all routes
├── crochet.db              # SQLite database (auto-generated)
├── requirements.txt
├── static/
│   └── css/
│       └── style.css       # Full custom CSS design system
└── templates/
    ├── base.html           # Sidebar layout + flash messages
    ├── dashboard.html      # Home page
    ├── add_member.html     # Member registration form
    ├── view_members.html   # Member directory table
    ├── add_product.html    # Product creation form
    ├── catalog.html        # Product grid with search
    ├── edit_product.html   # Product edit form
    ├── order_form.html     # Order placement with live preview
    └── view_orders.html    # Order ledger with total revenue
```

## Color Palette

| Name | Hex | Usage |
|---|---|---|
| Cherry Blossom Pink | `#E4ACB2` | Primary accents, borders, highlights |
| Desert Sand | `#EABCA8` | Warm secondary structures, cards |
| Papaya Whip | `#FAEDCD` | Body background (vintage linen) |
| Tea Green | `#CCD5AE` | Badges, stock indicators, success states |
| Ash Gray | `#99BAB9` | Headings, table structure, muted elements |
