# Aziza Bakery: wholesale ordering bot

Telegram bot for wholesale clients (warehouses, shops) of Aziza Bakery.
The client opens an order page inside Telegram, picks how many 1 kg / 2 kg boxes
of each product they need, and sends the order. The bakery gets it in a Telegram
chat with **Accept / Reject** buttons, and the client is notified of the decision.

```
Client: /start ──► bot shows "🛒 Buyurtma berish" button
        tap    ──► order page opens inside Telegram (webapp/, hosted on GitHub Pages)
        send   ──► Telegram.WebApp.sendData(order JSON) ──► bot
Bot:    validate ──► save to SQLite ──► send to ADMIN_CHAT_ID with buttons ──► confirm to client
Admin:  ✅ / ❌ ──► status saved ──► client notified
```

## Project structure

```
aziza_bot_v2/
├── run.py                 entry point: python run.py
├── requirements.txt
├── .env.example           template for secrets (copy to .env)
├── bot/
│   ├── app.py             builds Bot + Dispatcher, starts polling
│   ├── config.py          settings from .env (pydantic-settings)
│   ├── catalog.py         loads webapp/catalog.json
│   ├── models.py          shape of the data the page sends (pydantic)
│   ├── orders.py          order rules: totals, minimum, unknown products (no Telegram code)
│   ├── storage.py         SQLite storage: data/orders.sqlite3
│   ├── texts.py           every message text (Uzbek) + HTML escaping
│   ├── keyboards.py       buttons and callback data
│   └── handlers/
│       ├── common.py      /start, /help, /id
│       ├── orders.py      receives orders from the page
│       ├── admin.py       Accept / Reject buttons
│       └── fallback.py    any other message
├── tests/test_orders.py   tests for the order rules
└── webapp/                the order page (upload this to GitHub Pages)
    ├── index.html, style.css, app.js
    ├── catalog.json       products, prices, minimum order  ← edit this
    └── *.jpg, *.png       photos, logo, mascot
```

Design decisions:
- **Reply-keyboard button + `sendData`.** Telegram only allows `sendData` from Mini Apps opened by a
  reply-keyboard button. No web server of our own is needed: the page is static, and the order
  arrives at the bot as a message.
- **The bot never trusts the page.** Products, box sizes, the minimum and prices are re-checked
  against the bot's own copy of `catalog.json` (`bot/orders.py`).
- **Save first, then notify.** Each order is written to SQLite before it is sent, so nothing is lost
  if sending fails.
- **One catalog file.** `webapp/catalog.json` is used by both the page and the bot.
- **Shared objects through the Dispatcher.** `catalog`, `order_db`, `settings` and `webapp_link`
  are passed to `Dispatcher(...)` once and arrive in handlers as arguments (aiogram dependency injection).
- **The webapp folder is flat** (no subfolders), because GitHub's web upload often drops folders.

## Setup

### 1. Install (Python 3.10+)
```
python -m pip install -r requirements.txt
```

### 2. Put the page online (GitHub Pages)
1. On GitHub create a new **Public** repository, e.g. `aziza`.
2. Click **uploading an existing file**, open the `webapp` folder and drag **all files inside it** in.
   Check that the list shows `index.html` exactly (not `index (2).html`). Click **Commit changes**.
3. **Settings → Pages → Branch: main, / (root) → Save.** After 1–2 minutes the page is at
   `https://YOUR-NAME.github.io/aziza/`. Open it in a browser and check that the photos show.

### 3. Create .env
Copy `.env.example`, name the copy exactly `.env`, and fill in:

| Name | What |
|---|---|
| `BOT_TOKEN` | token from @BotFather |
| `ADMIN_CHAT_ID` | chat where orders arrive (step 5) |
| `WEBAPP_URL` | address from step 2 |

### 4. Run
```
python run.py
```
If a value in `.env` is wrong, the bot prints which one and stops.

### 5. Set who receives the orders
A bot cannot find a person by phone number, and it cannot write to someone who never started it.
So the person who receives orders must:
1. open the bot in Telegram and press **Start**,
2. send `/id` — the bot replies with a number,
3. give that number to whoever runs the bot, who puts it into `ADMIN_CHAT_ID` and restarts.

On start the bot logs `Orders go to: <name>` if it can reach that chat, or a warning if it cannot.

## Everyday changes

**Products, prices, minimum order: `webapp/catalog.json`**
```json
{ "id": "medovik", "name": "Medovik", "category": "pirojniy",
  "description": "...", "image": "medovik.jpg",
  "price": { "1": 45000, "2": 88000 } }
```
- `price`: price per box in so'm for the 1 kg and 2 kg box. `null` = "Narx kelishiladi".
- `min_boxes`: minimum boxes per order.
- New product: put the photo next to `catalog.json`, add an entry, keep `id` unique (latin letters and `_`).

After editing: upload the new `catalog.json` (and photos) to GitHub **and** restart the bot.
The page link contains the catalog version, so Telegram shows the new page right away.

**Texts the bot sends:** `bot/texts.py`.

## Regular customers
In the order form the client can tick **"Doimiy mijozman"**. Their company, phone and address are then
saved in Telegram CloudStorage (tied to their Telegram account, works on phone and computer).
Next time the form shows a "⭐ Doimiy mijoz" card instead of empty fields, and they only pick boxes.
Unticking the box deletes the saved details. Orders from regular customers are marked ⭐ for the admin.

## Orders
All orders are in `data/orders.sqlite3` (table `orders`). Open it with "DB Browser for SQLite"
or any SQLite tool; it can export to Excel.

## Tests
```
python -m pip install pytest
python -m pytest
```

## Running 24/7
On your computer the bot works only while `python run.py` is running.
For the bakery, run it on a small Linux VPS as a service, for example
`/etc/systemd/system/aziza-bot.service`:
```
[Unit]
Description=Aziza Bakery bot
After=network-online.target

[Service]
WorkingDirectory=/opt/aziza_bot_v2
ExecStart=/opt/aziza_bot_v2/.venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Then `sudo systemctl enable --now aziza-bot`.
