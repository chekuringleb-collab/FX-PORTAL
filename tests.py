"""
Тесты для FX Portal — запуск: python tests.py
Тестируются: авторизация, регистрация, API курсов, история, экспорт CSV/Excel.
"""
import unittest
import json
from app import app, db, User

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def _register(self, username='testuser', password='password123'):
        return self.client.post('/register', data={
            'username': username,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)

    def _login(self, username='testuser', password='password123'):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)


# ── Тесты модуля авторизации ──────────────────────────────────────────────────
class TestAuth(BaseTestCase):

    def test_register_success(self):
        """Успешная регистрация"""
        r = self._register()
        self.assertEqual(r.status_code, 200)
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)

    def test_first_user_is_admin(self):
        """Регистрация через секретный роут даёт роль admin"""
        self.client.post('/admin-register/fx-admin-2026', data={
            'username': 'testuser', 'password': 'password123', 'confirm_password': 'password123'
        }, follow_redirects=True)
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.role, 'admin')

    def test_second_user_is_not_admin(self):
        """Второй пользователь — обычный"""
        self._register('user1', 'password123')
        self._register('user2', 'password456')
        with app.app_context():
            u = User.query.filter_by(username='user2').first()
            self.assertEqual(u.role, 'user')

    def test_register_short_username(self):
        """Короткий логин — ошибка валидации"""
        r = self.client.post('/register', data={
            'username': 'ab', 'password': 'password123', 'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn('символ', r.data.decode('utf-8').lower())

    def test_register_short_password(self):
        """Короткий пароль — ошибка"""
        r = self.client.post('/register', data={
            'username': 'validuser', 'password': '123', 'confirm_password': '123'
        }, follow_redirects=True)
        self.assertIn('пароль', r.data.decode('utf-8').lower())

    def test_register_password_mismatch(self):
        """Пароли не совпадают — ошибка"""
        r = self.client.post('/register', data={
            'username': 'validuser', 'password': 'password123', 'confirm_password': 'different'
        }, follow_redirects=True)
        self.assertIn('совпад', r.data.decode('utf-8').lower())

    def test_register_duplicate(self):
        """Повторная регистрация с тем же логином — ошибка"""
        self._register()
        r = self._register()
        self.assertIn('существует', r.data.decode('utf-8').lower())

    def test_login_success(self):
        """Успешный вход"""
        self._register()
        r = self._login()
        self.assertEqual(r.status_code, 200)

    def test_login_wrong_password(self):
        """Неверный пароль"""
        self._register()
        r = self.client.post('/login', data={
            'username': 'testuser', 'password': 'wrong'
        }, follow_redirects=True)
        self.assertIn('неверный', r.data.decode('utf-8').lower())

    def test_logout(self):
        """Выход из системы"""
        self._register(); self._login()
        r = self.client.post('/logout', follow_redirects=True)
        self.assertEqual(r.status_code, 200)


# ── Тесты доступа к страницам ─────────────────────────────────────────────────
class TestAccess(BaseTestCase):

    def test_index_requires_login(self):
        """Главная страница — только для авторизованных"""
        r = self.client.get('/', follow_redirects=False)
        self.assertEqual(r.status_code, 302)

    def test_index_accessible_after_login(self):
        """После входа главная доступна"""
        self._register(); self._login()
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)

    def test_admin_requires_admin_role(self):
        """Админ-панель недоступна обычному пользователю"""
        self._register('user1', 'pass1234'); self._login('user1', 'pass1234')
        # создаём второго пользователя и логинимся под ним
        self.client.post('/logout')
        self._register('user2', 'pass5678')
        self._login('user2', 'pass5678')
        r = self.client.get('/admin')
        self.assertEqual(r.status_code, 403)

    def test_history_page(self):
        """Страница истории курса"""
        self._register(); self._login()
        r = self.client.get('/history/EUR')
        self.assertEqual(r.status_code, 200)

    def test_history_unknown_currency(self):
        """Несуществующая валюта — 404"""
        self._register(); self._login()
        r = self.client.get('/history/XXX')
        self.assertEqual(r.status_code, 404)


# ── Тесты API курсов ──────────────────────────────────────────────────────────
class TestRatesAPI(BaseTestCase):

    def test_rates_requires_login(self):
        """API курсов — только для авторизованных"""
        r = self.client.get('/api/rates')
        self.assertIn(r.status_code, [302, 401])

    def test_rates_returns_json(self):
        """API возвращает JSON со списком валют"""
        self._register(); self._login()
        r = self.client.get('/api/rates')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIn('rates', data)
        self.assertIsInstance(data['rates'], list)
        if data['rates']:
            first = data['rates'][0]
            self.assertIn('code', first)
            self.assertIn('rate', first)
            self.assertIn('name', first)
            self.assertIn('flag', first)

    def test_history_api_returns_json(self):
        """API истории возвращает данные"""
        self._register(); self._login()
        r = self.client.get('/api/history/EUR')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIn('labels', data)
        self.assertIn('rates', data)
        self.assertEqual(len(data['labels']), len(data['rates']))

    def test_history_api_period_filter(self):
        """API истории принимает параметр period"""
        self._register(); self._login()
        for period in ['1w', '1m', '3m', '6m', '1y']:
            r = self.client.get(f'/api/history/EUR?period={period}')
            self.assertEqual(r.status_code, 200)

    def test_history_unknown_currency(self):
        """API истории — неизвестная валюта — 404"""
        self._register(); self._login()
        r = self.client.get('/api/history/ZZZ')
        self.assertEqual(r.status_code, 404)


# ── Тесты экспорта ────────────────────────────────────────────────────────────
class TestExport(BaseTestCase):

    def test_csv_download(self):
        """Скачивание CSV"""
        self._register(); self._login()
        r = self.client.get('/download')
        self.assertIn(r.status_code, [200, 302])
        if r.status_code == 200:
            self.assertIn('text/csv', r.content_type)

    def test_xlsx_download(self):
        """Скачивание Excel"""
        self._register(); self._login()
        r = self.client.get('/download_xlsx')
        self.assertIn(r.status_code, [200, 302])
        if r.status_code == 200:
            self.assertIn('spreadsheetml', r.content_type)


# ── Тесты безопасности ────────────────────────────────────────────────────────
class TestSecurity(BaseTestCase):

    def test_password_hashed(self):
        """Пароль хранится в хешированном виде"""
        self._register()
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertNotEqual(user.password, 'password123')
            self.assertTrue(user.password.startswith('pbkdf2'))

    def test_open_redirect_blocked(self):
        """Открытый редирект заблокирован"""
        self._register(); 
        r = self.client.post('/login?next=https://evil.com', data={
            'username': 'testuser', 'password': 'password123'
        }, follow_redirects=False)
        if r.status_code == 302:
            self.assertFalse(r.location.startswith('https://evil.com'))


if __name__ == '__main__':
    print("=" * 60)
    print("  FX Portal — Тесты модулей")
    print("=" * 60)
    unittest.main(verbosity=2)
