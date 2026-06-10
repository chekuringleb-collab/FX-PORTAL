import sys
import os
import threading
import time
import webbrowser

# Определяем базовый путь (для PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    # БД храним рядом с exe, не внутри него
    DATA_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = BASE_DIR

# Устанавливаем переменные окружения до импорта app
os.environ['DATABASE_URL'] = f"sqlite:///{os.path.join(DATA_DIR, 'users.db')}"
os.environ['FLASK_ENV'] = 'production'

# Добавляем BASE_DIR в путь чтобы Flask нашёл templates/static
sys.path.insert(0, BASE_DIR)

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QSplashScreen, QLabel
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
    from PyQt6.QtCore import QUrl, Qt, QTimer
    from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False

PORT = 5123

def run_flask():
    """Запускает Flask в отдельном потоке"""
    # Меняем папку шаблонов и статики на BASE_DIR
    import app as flask_app
    flask_app.app.template_folder = os.path.join(BASE_DIR, 'templates')
    flask_app.app.static_folder = os.path.join(BASE_DIR, 'static')
    flask_app.app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)

def wait_for_flask():
    """Ждём пока Flask поднимется"""
    import urllib.request
    for _ in range(30):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{PORT}/login', timeout=1)
            return True
        except:
            time.sleep(0.3)
    return False

if HAS_QT:
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('FX Portal — Курсы валют')
            self.setMinimumSize(1200, 750)
            self.resize(1400, 850)

            # Иконка
            icon_path = os.path.join(BASE_DIR, 'static', 'favicon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))

            # WebView
            self.browser = QWebEngineView()
            profile = QWebEngineProfile.defaultProfile()
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
            )
            settings = self.browser.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

            self.setCentralWidget(self.browser)
            self.browser.load(QUrl(f'http://127.0.0.1:{PORT}/login'))

        def closeEvent(self, event):
            os._exit(0)

    def make_splash():
        pixmap = QPixmap(400, 200)
        pixmap.fill(QColor('#0d1526'))
        painter = QPainter(pixmap)
        painter.setPen(QColor('#4f8ef7'))
        font = QFont('Arial', 22, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, '💱 FX Portal\nЗагрузка...')
        painter.end()
        splash = QSplashScreen(pixmap)
        return splash

    app_qt = QApplication(sys.argv)
    app_qt.setApplicationName('FX Portal')
    app_qt.setOrganizationName('FXPortal')

    # Сплэш-экран
    splash = make_splash()
    splash.show()
    app_qt.processEvents()

    # Запускаем Flask в фоне
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Ждём Flask
    ready = wait_for_flask()

    splash.close()

    if ready:
        window = MainWindow()
        window.show()
    else:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, 'Ошибка', 'Не удалось запустить сервер.\nПроверьте что порт 5123 свободен.')
        sys.exit(1)

    sys.exit(app_qt.exec())

else:
    # Fallback — просто открываем в браузере
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    wait_for_flask()
    webbrowser.open(f'http://127.0.0.1:{PORT}')
    print(f'FX Portal запущен: http://127.0.0.1:{PORT}')
    print('Закройте это окно чтобы остановить приложение.')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
