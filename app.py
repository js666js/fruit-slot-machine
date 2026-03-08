
from flask import Flask, render_template, request, redirect, url_for, session
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

BASIC_FRUITS = {"🍎", "🍒", "🍇", "🍐"}
WEIGHTED_SYMBOLS = [
    "🍎", "🍎", "🍎",
    "🍒", "🍒", "🍒",
    "🍇", "🍇", "🍇",
    "🍐", "🍐", "🍐",
    "🍉", "🍉",
    "🔔",
    "7"
]

LINES = [
    ([(0, 0), (0, 1), (0, 2)], "第1横线"),
    ([(1, 0), (1, 1), (1, 2)], "第2横线"),
    ([(2, 0), (2, 1), (2, 2)], "第3横线"),
    ([(0, 0), (1, 1), (2, 2)], "主对角线"),
    ([(0, 2), (1, 1), (2, 0)], "副对角线"),
]

def init_state():
    session.setdefault("balance", 0)
    session.setdefault("bet", 1)
    session.setdefault("cells", [["❔" for _ in range(3)] for _ in range(3)])
    session.setdefault("message", "欢迎游玩！")
    session.setdefault("message_color", "#2563eb")
    session.setdefault("winning_positions", [])

def get_line_payout(symbol):
    if symbol in BASIC_FRUITS:
        return 2
    if symbol == "🍉":
        return 5
    if symbol == "🔔":
        return 10
    if symbol == "7":
        return 50
    return 0

def calculate_payout(cells, bet):
    payout = 0
    winning_lines = []

    for positions, name in LINES:
        vals = [cells[r][c] for r, c in positions]
        if vals[0] == vals[1] == vals[2]:
            symbol = vals[0]
            money = get_line_payout(symbol) * bet
            if money > 0:
                payout += money
                winning_lines.append((positions, name, symbol, money))

    all_symbols = [cells[r][c] for r in range(3) for c in range(3)]
    special = len(set(all_symbols)) == 1 and all_symbols[0] in BASIC_FRUITS
    if special:
        payout += 20 * bet

    return payout, winning_lines, special

@app.route("/")
def index():
    init_state()
    return render_template(
        "index.html",
        balance=session["balance"],
        bet=session["bet"],
        cells=session["cells"],
        message=session["message"],
        message_color=session["message_color"],
        winning_positions=session["winning_positions"],
        symbols=WEIGHTED_SYMBOLS,
    )

@app.post("/recharge")
def recharge():
    init_state()
    try:
        amount = int(request.form.get("amount", "").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        session["message"] = "请输入大于 0 的整数金额"
        session["message_color"] = "#dc2626"
        return redirect(url_for("index"))

    session["balance"] += amount
    session["message"] = f"充值成功：£{amount}"
    session["message_color"] = "#15803d"
    return redirect(url_for("index"))

@app.post("/quick_recharge/<int:amount>")
def quick_recharge(amount):
    init_state()
    session["balance"] += amount
    session["message"] = f"充值成功：£{amount}"
    session["message_color"] = "#15803d"
    return redirect(url_for("index"))

@app.post("/bet/increase")
def increase_bet():
    init_state()
    if session["bet"] < 10 and session["bet"] < session["balance"]:
        session["bet"] += 1
    return redirect(url_for("index"))

@app.post("/bet/decrease")
def decrease_bet():
    init_state()
    if session["bet"] > 1:
        session["bet"] -= 1
    return redirect(url_for("index"))

@app.post("/spin")
def spin():
    init_state()

    if session["balance"] < session["bet"]:
        session["message"] = "余额不足，请先充值"
        session["message_color"] = "#dc2626"
        return redirect(url_for("index"))

    session["balance"] -= session["bet"]
    cells = [[random.choice(WEIGHTED_SYMBOLS) for _ in range(3)] for _ in range(3)]
    payout, winning_lines, special = calculate_payout(cells, session["bet"])

    session["balance"] += payout
    session["cells"] = cells

    winning_positions = []
    for positions, _, _, _ in winning_lines:
        for pos in positions:
            pos_list = [pos[0], pos[1]]
            if pos_list not in winning_positions:
                winning_positions.append(pos_list)
    session["winning_positions"] = winning_positions

    if payout > 0:
        parts = [f"总奖金 £{payout}"]
        for _, name, symbol, money in winning_lines:
            parts.append(f"{name} {symbol}{symbol}{symbol} = £{money}")
        if special:
            parts.append("满屏同一种水果奖励 = £20")
        session["message"] = " | ".join(parts)
        session["message_color"] = "#15803d"
    else:
        session["message"] = "这次没有中奖"
        session["message_color"] = "#dc2626"

    return redirect(url_for("index"))

@app.post("/reset")
def reset():
    session["balance"] = 0
    session["bet"] = 1
    session["cells"] = [["❔" for _ in range(3)] for _ in range(3)]
    session["message"] = "游戏已重置"
    session["message_color"] = "#2563eb"
    session["winning_positions"] = []
    return redirect(url_for("index"))

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
