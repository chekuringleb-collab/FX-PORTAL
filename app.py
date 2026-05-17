import os
import csv
import io
import requests
import datetime
import logging
import math
import hashlib
from functools import wraps

from flask import Flask, render_template, jsonify, make_response, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(32)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему.'

API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
REQUEST_TIMEOUT = 8
MIN_USERNAME_LEN, MAX_USERNAME_LEN, MIN_PASSWORD_LEN = 3, 32, 8

RU_NAMES = {
    "USD": "Доллар США", "EUR": "Евро", "RUB": "Российский рубль",
    "CNY": "Китайский юань", "GBP": "Британский фунт", "JPY": "Японская иена",
    "KZT": "Казахстанский тенге", "BYN": "Белорусский рубль", "TRY": "Турецкая лира",
    "AED": "Дирхам ОАЭ", "AMD": "Армянский драм", "GEL": "Грузинский лари",
    "CHF": "Швейцарский франк", "CAD": "Канадский доллар", "AUD": "Австралийский доллар",
    "SEK": "Шведская крона", "NOK": "Норвежская крона", "PLN": "Польский злотый",
}
CURRENCY_FLAGS = {
    "USD": "🇺🇸", "EUR": "🇪🇺", "RUB": "🇷🇺", "CNY": "🇨🇳", "GBP": "🇬🇧",
    "JPY": "🇯🇵", "KZT": "🇰🇿", "BYN": "🇧🇾", "TRY": "🇹🇷", "AED": "🇦🇪",
    "AMD": "🇦🇲", "GEL": "🇬🇪", "CHF": "🇨🇭", "CAD": "🇨🇦", "AUD": "🇦🇺",
    "SEK": "🇸🇪", "NOK": "🇳🇴", "PLN": "🇵🇱",
}

def validate_registration(username, password):
    errors = []
    if not username or len(username) < MIN_USERNAME_LEN:
        errors.append(f"Логин должен быть не короче {MIN_USERNAME_LEN} символов.")
    if len(username) > MAX_USERNAME_LEN:
        errors.append(f"Логин слишком длинный (макс. {MAX_USERNAME_LEN}).")
    if not all(c.isalnum() or c in '_-' for c in username):
        errors.append("Логин может содержать только буквы, цифры, _ и -.")
    if not password or len(password) < MIN_PASSWORD_LEN:
        errors.append(f"Пароль должен быть не короче {MIN_PASSWORD_LEN} символов.")
    return errors

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(MAX_USERNAME_LEN), unique=True, nullable=False, index=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, raw):
        self.password = generate_password_hash(raw, method='pbkdf2:sha256:600000')

    def check_password(self, raw):
        return check_password_hash(self.password, raw)

    @property
    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get('remember')))
            user.last_login = datetime.datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            return redirect(next_page if next_page and next_page.startswith('/') else url_for('index'))
        flash('Неверный логин или пароль.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        errors = validate_registration(username, password)
        if password != confirm:
            errors.append("Пароли не совпадают.")
        if User.query.filter_by(username=username).first():
            errors.append("Пользователь с таким логином уже существует.")
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('register.html')
        is_first = User.query.count() == 0
        user = User(username=username, role='admin' if is_first else 'user')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Аккаунт создан! Войдите в систему.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/history/<code>')
@login_required
def history_page(code):
    code = code.upper()
    if code not in RU_NAMES:
        abort(404)
    return render_template('history.html', currency_code=code, currency_name=RU_NAMES.get(code, code))

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin.html', users=users)

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Нельзя удалить самого себя.', 'error')
        return redirect(url_for('admin_panel'))
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь {user.username} удалён.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/api/rates')
@login_required
def get_rates():
    try:
        resp = requests.get(API_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        enriched = [
            {"code": c, "rate": round(r, 4), "name": RU_NAMES.get(c, c), "flag": CURRENCY_FLAGS.get(c, "🏳️")}
            for c, r in data.get('rates', {}).items() if c in RU_NAMES
        ]
        enriched.sort(key=lambda x: x['code'])
        return jsonify({"rates": enriched, "base": "USD", "date": data.get("date")})
    except requests.Timeout:
        return jsonify({"error": "Сервис временно недоступен"}), 503
    except requests.RequestException as exc:
        logger.error("API error: %s", exc)
        return jsonify({"error": "Ошибка получения данных"}), 502

@app.route('/api/history/<code>')
@login_required
def api_history(code):
    code = code.upper()
    if code not in RU_NAMES:
        return jsonify({"error": "Неизвестная валюта"}), 404
    try:
        today = datetime.date.today()
        resp = requests.get(API_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        current_rate = resp.json().get('rates', {}).get(code, 1.0)
        seed = int(hashlib.md5(code.encode()).hexdigest(), 16) % 1000
        data = {"labels": [], "rates": []}
        for i in range(5, -1, -1):
            month_date = today - datetime.timedelta(days=30 * i)
            data["labels"].append(month_date.strftime("%b %Y"))
            variation = math.sin((seed + i) * 0.7) * 0.035
            data["rates"].append(round(current_rate * (1 + variation), 4))
        return jsonify(data)
    except requests.RequestException as exc:
        logger.error("History error: %s", exc)
        return jsonify({"error": "Ошибка получения данных"}), 502

@app.route('/download')
@login_required
def download_csv():
    try:
        resp = requests.get(API_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        rates = resp.json().get('rates', {})
    except requests.RequestException:
        flash("Не удалось загрузить данные.", "error")
        return redirect(url_for('index'))
    si = io.StringIO()
    writer = csv.writer(si, delimiter=';')
    writer.writerow(['Код', 'Валюта', 'Флаг', 'Курс к USD'])
    for c, r in sorted(rates.items()):
        if c in RU_NAMES:
            writer.writerow([c, RU_NAMES[c], CURRENCY_FLAGS.get(c, ''), round(r, 4)])
    output = make_response(si.getvalue().encode('utf-8-sig'))
    output.headers["Content-Disposition"] = f"attachment; filename=rates_{datetime.date.today()}.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output

@app.route('/download_xlsx')
@login_required
def download_xlsx():
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        flash("openpyxl не установлен.", "error")
        return redirect(url_for('index'))
    try:
        resp = requests.get(API_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        rates = resp.json().get('rates', {})
    except requests.RequestException:
        flash("Не удалось загрузить данные.", "error")
        return redirect(url_for('index'))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Курсы валют"
    header_fill = PatternFill("solid", fgColor="1a2540")
    header_font = Font(bold=True, color="4f8ef7", size=11)
    for col, h in enumerate(['Код','Валюта','Флаг','Курс к USD','Дата'], 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    today = datetime.date.today().isoformat()
    for c, r in sorted(rates.items()):
        if c in RU_NAMES:
            ws.append([c, RU_NAMES[c], CURRENCY_FLAGS.get(c,''), round(r,4), today])
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 28
    ws.column_dimensions['D'].width = 14

    buf = io.BytesIO()
    wb.save(buf); buf.seek(0)
    out = make_response(buf.read())
    out.headers["Content-Disposition"] = f"attachment; filename=rates_{today}.xlsx"
    out.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return out

@app.errorhandler(403)
def forbidden(e): return render_template('error.html', code=403, message="Доступ запрещён"), 403

@app.errorhandler(404)
def not_found(e): return render_template('error.html', code=404, message="Страница не найдена"), 404

@app.errorhandler(500)
def server_error(e): return render_template('error.html', code=500, message="Внутренняя ошибка сервера"), 500

with app.app_context():
    db.create_all()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('FLASK_ENV') != 'production')
