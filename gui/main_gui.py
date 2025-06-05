# PDFConvertProject v2.0.0-alpha
# Дата: 2025-06-03 19:00
# - исправлен обратный слеш при записи в setup.ini
# - подключено окно Список заданий к меню и кнопке
# - подключена обработка меню Справка

import sys, os, subprocess
import configparser
import datetime
import webbrowser
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QAction,
    QMenu, QMenuBar,
    QDialog, QFileDialog, QInputDialog,
    QVBoxLayout, QHBoxLayout,
    QGroupBox, QGridLayout,
    QLabel, QPushButton, QRadioButton,
    QProgressBar, QStatusBar,
    QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap, QBrush
from gui.dialogs_project import ProjectSelectDialog
from gui.dialogs_list import TaskListDialog
from gui.dialogs_excel import ExcelSheetsDialog
from core.converter_runner import ConvertWorker
from gui.dialogs_page_numbering import PageNumberingDialog

class MainWindow(QMainWindow):
    # ui_main_window
    def __init__(self):
        super().__init__()
        self.log_message(" Старт", divider=True)
        self.setWindowTitle(f"PDFConvert {read_version()}")
        self.setMinimumSize(350, 250)

        icon_path = os.path.join(os.path.dirname(__file__), "..", "logo_ps.png")
        self.app_icon = QIcon(icon_path)
        self.setWindowIcon(self.app_icon)

        self.ini_path = os.path.join(os.getcwd(), "setup.ini")

        # Логирование старта
        ini_path = self.ini_path.replace("\\", "/")
        self.log_message(f" Программа запущена. Файл конфигурации: {self.ini_path}")

        if not os.path.isfile(self.ini_path):
            self.log_message("ОШИБКА: setup.ini не найден.")  # Логирование отсутствия setup.ini
            QMessageBox.critical(self, "Ошибка", f"Файл setup.ini не найден в:\n{self.ini_path}")
            QTimer.singleShot(100, self.close)  # Завершает окно после показа
            return

        # Загрузка конфигурации
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.load_config()

        # Инициализация интерфейса
        self.setup_menu()
        self.setup_ui()
        self.sync_ui_with_config()


    # Универсальый метод (функция) логирования
    def log_message(self, text, divider=False):
        """Записывает строку в message.log с меткой времени; divider=True — добавляет разделитель"""
        log_path = os.path.join(os.getcwd(), "message.log")
        with open(log_path, "a", encoding="utf-8") as f:
            if divider:
                f.write("\n" + "-" * 50 + "\n")
            timestamp = datetime.datetime.now().strftime("[%d.%m.%Y %H:%M:%S] ")
            f.write(timestamp + text + "\n")


    def load_config(self):
        if os.path.exists(self.ini_path):
            self.config.read(self.ini_path, encoding="utf-8")
        if not self.config.has_section("global"):
            self.config.add_section("global")

    def save_mode_to_config(self, key, value):
        self.config.set("global", key, value)
        with open(self.ini_path, "w", encoding="utf-8") as f:
            self.config.write(f)

    def setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Файл")
        file_menu.addAction("Выбрать проект...", self.select_project)
        file_menu.addAction("Выбрать папку с исходными файлами", self.select_source_folder)
        file_menu.addAction("Выбрать исходные файлы", self.select_source_files)
        file_menu.addSeparator()
        file_menu.addAction("Выбрать папку для сохранения локальных PDF", self.select_output_folder)
        file_menu.addAction("Выбрать папку для сохранения итогового PDF", self.select_merged_pdf)
        file_menu.addAction("Изменить имя итогового PDF", self.rename_merged_pdf)
        file_menu.addSeparator()
        file_menu.addAction("Выход", self.close)

        edit_menu = menubar.addMenu("Редактирование")
        
        edit_menu.addAction("Список заданий", self.open_task_list_dialog)

        self.excel_all_action = QAction("Все", self, checkable=True)
        self.excel_selected_action = QAction("Выделенные", self, checkable=True)
        self.excel_all_action.setChecked(True)

        excel_sheet_menu = QMenu("Листы таблицы Excel", self)
        excel_sheet_menu.addAction(self.excel_all_action)
        excel_sheet_menu.addAction(self.excel_selected_action)
        edit_menu.addMenu(excel_sheet_menu)

        self.excel_all_action.triggered.connect(lambda: self.update_excel_mode("all"))
        self.excel_selected_action.triggered.connect(lambda: self.update_excel_mode("selected"))

        self.compass_all_action = QAction("Все", self, checkable=True)
        self.compass_selected_action = QAction("Выделенные", self, checkable=True)
        self.compass_all_action.setChecked(True)

        compass_sheet_menu = QMenu("Листы Компас", self)
        compass_sheet_menu.addAction(self.compass_all_action)
        compass_sheet_menu.addAction(self.compass_selected_action)
        edit_menu.addMenu(compass_sheet_menu)

        self.compass_all_action.triggered.connect(lambda: self.update_compass_mode("all"))
        self.compass_selected_action.triggered.connect(lambda: self.update_compass_mode("selected"))

        help_menu = menubar.addMenu("Справка")
        help_menu.addAction("Руководство пользователя", self.open_manual)
        help_menu.addAction("О программе", self.open_about)
        help_menu.addAction("Открыть ToDo", self.open_todo)

    def select_project(self):
        dialog = ProjectSelectDialog(ini_path=self.ini_path, parent=self)
        dialog.setWindowIcon(self.app_icon)
        if dialog.exec_() == QDialog.Accepted:

            self.config = configparser.ConfigParser()
            self.config.optionxform = str

            self.config.read(self.ini_path, encoding="utf-8")
            self.sync_ui_with_config()
            self.log_message("Проект выбран через диалог")


    # ui_select_source_folder
    def select_source_folder(self):
        from PyQt5.QtWidgets import QFileDialog
        import configparser
        import os

        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с исходными файлами")
        if not folder:
            return

        folder = folder.replace("\\", "/")  # нормализуем путь
        # ui_source_folder_chosen
        self.status.showMessage(f"Выбрана папка с исходными документами: {folder}", 3000)


        # Чтение конфигурации
        ini_path = os.path.join(os.getcwd(), "setup.ini")
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(ini_path, encoding="utf-8")

        section = config.get("global", "current_project", fallback="files")
        if not config.has_section(section):
            config.add_section(section)

        # Добавление файлов
        def list_source_files(folder_path):
            exts = (".docx", ".xlsx", ".cdw", ".pdf")
            return [
                os.path.join(folder_path, f).replace("\\", "/")
                for f in sorted(os.listdir(folder_path))
                if f.lower().endswith(exts)
            ]

        def add_files_to_project(config, section_name, files):
            for index, filepath in enumerate(files, start=1):
                ext = os.path.splitext(filepath)[1].lower()
                default_param = "-"  # может быть лист, если xlsx или cdw

                value = f"{filepath} | {default_param} | enabled | merge"
                config.set(section_name, f"source_files_{index}", value)

        source_files = list_source_files(folder)
        add_files_to_project(config, section, source_files)

        # Сохраняем setup.ini
        with open(ini_path, "w", encoding="utf-8") as f:
            config.write(f)

        # Обновим статус
        self.status.showMessage(f"Добавлено файлов: {len(source_files)}", 3000)




    def select_source_files(self):
        project = self.config.get("global", "current_project", fallback=None)
        if not project:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите проект.")
            return

        project = self.config.get("global", "current_project", fallback=None)

        default_path = self.config.get(project, "source_folder", fallback=os.getcwd())
        default_path = default_path.replace("\\", "/")

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выбор исходных файлов",
            directory=default_path,
            filter="Документы и чертежи (*.docx *.xlsx *.cdw *.pdf)"
        )

        if files:
            # Удаляем старые source_files_*
            keys_to_remove = [k for k in self.config[project] if k.startswith("source_files_")]
            for key in keys_to_remove:
                self.config.remove_option(project, key)

            # Записываем новые
            for idx, file in enumerate(files, start=1):
                normalized = file.replace("\\", "/")
                self.config.set(project, f"source_files_{idx}", f"{normalized} | all | enabled | merge")

            with open(self.ini_path, "w", encoding="utf-8") as f:
                self.config.write(f)

            self.log_message(f"Выбрано файлов: {len(files)}")
            for f in files:
                normalized = f.replace("\\", "/")
                self.log_message(f" - {normalized}")

            QMessageBox.information(self, "Файлы выбраны", "\n".join(files))

    def select_output_folder(self):
        import os

        project = self.config.get("global", "current_project", fallback=None)
        if not project:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите проект.")
            return

        default_path = self.config.get(project, "source_folder", fallback=os.getcwd())
        pdf_path = os.path.join(default_path, "pdf").replace("\\", "/")

        if not os.path.exists(pdf_path):
            os.makedirs(pdf_path)

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выбор папки для сохранения локальных PDF",
            directory=pdf_path
        )
        if folder:
            folder = folder.replace("\\", "/").rstrip("/")
            self.config.set(project, "output_folder", folder)
            with open(self.ini_path, "w", encoding="utf-8") as f:
                self.config.write(f)
            self.log_message(f"Изменена папка сохранения PDF: {folder}")

    def select_merged_pdf(self):
        import os

        project = self.config.get("global", "current_project", fallback=None)
        if not project:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите проект.")
            return

        default_path = self.config.get(project, "source_folder", fallback=os.getcwd())
        pdf_path = os.path.join(default_path, "pdf").replace("\\", "/")

        if not os.path.exists(pdf_path):
            os.makedirs(pdf_path)

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выбор папки сохранения итогового PDF",
            directory=pdf_path
        )

        if folder:
            folder = folder.replace("\\", "/").rstrip("/")
            project_name = os.path.basename(folder)
            merged_path = folder + "/" + project_name + ".pdf"

            self.config.set(project, "merged_pdf_path", merged_path)
            with open(self.ini_path, "w", encoding="utf-8") as f:
                self.config.write(f)

            self.log_message(f"Выбрана папка для итогового PDF: {folder}")
            self.log_message(f"merged_pdf_path → {merged_path}")

            QMessageBox.information(self, "Итоговый PDF", f"Файл будет сохранён как:\n{merged_path}")

    def rename_merged_pdf(self):
        project = self.config.get("global", "current_project", fallback=None)
        if not project:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите проект.")
            return

        from PyQt5.QtWidgets import QInputDialog
        current_path = self.config.get(project, "merged_pdf_path", fallback="")
        default_name = os.path.basename(current_path) if current_path else "Объединенный.pdf"
        new_name, ok = QInputDialog.getText(self, "Имя итогового PDF", "Введите новое имя файла:", text=default_name)

        if ok and new_name:
            new_name = os.path.splitext(new_name)[0] + ".pdf"
            folder = os.path.dirname(current_path) if current_path else os.getcwd()
            new_path = os.path.join(folder, new_name)
            new_path = new_path.replace("\\", "/").rstrip("/")
            self.config.set(project, "merged_pdf_path", new_path)
            with open(self.ini_path, "w", encoding="utf-8") as f:
                self.config.write(f)
            # QMessageBox.information(self, "Имя изменено", new_path)
        # QMessageBox.information(self, "Изменить имя", "Здесь будет реализация смены имени PDF.")

    def update_excel_mode(self, mode):
        self.excel_all_radio.setChecked(mode == "all")
        self.excel_selected_radio.setChecked(mode == "selected")
        self.excel_all_action.setChecked(mode == "all")
        self.excel_selected_action.setChecked(mode == "selected")
        self.save_mode_to_config("excel_sheet_mode", mode)

    def update_compass_mode(self, mode):
        self.compass_all_radio.setChecked(mode == "all")
        self.compass_selected_radio.setChecked(mode == "selected")
        self.compass_all_action.setChecked(mode == "all")
        self.compass_selected_action.setChecked(mode == "selected")
        self.save_mode_to_config("compass_sheet_mode", mode)

    def sync_ui_with_config(self):
        current_project = self.config.get("global", "current_project", fallback=None)
        if current_project:
            self.project_label.setText(f"Текущий проект: {current_project}")
        else:
            self.project_label.setText("Текущий проект: (не выбран)")
        compass_mode = self.config.get("global", "compass_sheet_mode", fallback="all")
        excel_mode = self.config.get("global", "excel_sheet_mode", fallback="all")
        self.update_excel_mode(excel_mode)
        self.update_compass_mode(compass_mode)

    def open_task_list_dialog(self):
        try:
            from gui.dialogs_list import TaskListDialog
            dialog = TaskListDialog(self)
            dialog.setWindowIcon(self.app_icon)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть диалог заданий:\n{e}")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        grid = QGridLayout()
        layout.addLayout(grid)

        # === Блок Excel ===
        excel_group = QGroupBox("Листы таблиц Excel:")
        excel_layout = QVBoxLayout()
        self.excel_all_radio = QRadioButton("Все")
        self.excel_selected_radio = QRadioButton("Выделенные")
        excel_layout.addWidget(self.excel_all_radio)
        excel_layout.addWidget(self.excel_selected_radio)
        excel_group.setLayout(excel_layout)
        grid.addWidget(excel_group, 0, 0)

        # === Блок Компас ===
        compass_group = QGroupBox("Листы чертежей Компас:")
        compass_layout = QVBoxLayout()
        self.compass_all_radio = QRadioButton("Все")
        self.compass_selected_radio = QRadioButton("Выделенные")
        compass_layout.addWidget(self.compass_all_radio)
        compass_layout.addWidget(self.compass_selected_radio)
        compass_group.setLayout(compass_layout)
        grid.addWidget(compass_group, 1, 0)

        # === Привязка сигналов после инициализации кнопок ===
        self.excel_all_radio.toggled.connect(
            lambda checked: (self.excel_all_action.setChecked(checked),
                            self.save_mode_to_config("excel_sheet_mode", "all") if checked else None))
        self.excel_selected_radio.toggled.connect(
            lambda checked: (self.excel_selected_action.setChecked(checked),
                            self.save_mode_to_config("excel_sheet_mode", "selected") if checked else None))
        self.compass_all_radio.toggled.connect(
            lambda checked: (self.compass_all_action.setChecked(checked),
                            self.save_mode_to_config("compass_sheet_mode", "all") if checked else None))
        self.compass_selected_radio.toggled.connect(
            lambda checked: (self.compass_selected_action.setChecked(checked),
                            self.save_mode_to_config("compass_sheet_mode", "selected") if checked else None))

        # === Боковая панель справа ===
        button_column = QVBoxLayout()
        button_column.addStretch()
        self.project_label = QLabel("Текущий проект: (не выбран)")
        change_button = QPushButton("Изменить проект")
        change_button.clicked.connect(self.select_project)
        button_column.addWidget(self.project_label)
        button_column.addWidget(change_button)

        tasklist_button = QPushButton("Список заданий")
        tasklist_button.clicked.connect(self.open_task_list_dialog)
        convert_button = QPushButton("Конвертировать")
        convert_button.clicked.connect(self.start_conversion)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.close)
        button_column.addWidget(tasklist_button)
        button_column.addWidget(convert_button)
        button_column.addWidget(cancel_button)
        button_column.addStretch()
        grid.addLayout(button_column, 0, 2, 2, 1)

        # ui_progress_bar

        # Создаём прогресс-бар
        self.progress = QProgressBar()
        self.progress.setVisible(False)          # Скрыт по умолчанию
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.reset_progress_style_to_background()

        # Добавляем на layout — например, под кнопками
        layout.addWidget(self.progress)
        # main_layout.addWidget(self.progress)
        # или другой layout, подходящий по месту
        

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Готов к работе")

        central_widget.setLayout(layout)
        
    def open_task_list_dialog(self):
        from gui.dialogs_list import TaskListDialog
        import configparser
        import os

        ini_path = os.path.join(os.getcwd(), "setup.ini")
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(ini_path, encoding="utf-8")

        from gui.dialogs_list import TaskListDialog
        dialog = TaskListDialog(self, config, ini_path)
        dialog.setWindowIcon(self.app_icon)
        dialog.exec_()

    def open_manual(self):
        manual_path = os.path.abspath("manual.html")
        if os.path.exists(manual_path):
            webbrowser.open(f"file:///{manual_path}")
        else:
            QMessageBox.warning(self, "Ошибка", "Файл manual.html не найден.")

    # ui_about_dialog
    def open_about(self):
        version = read_version()

        readme_path = os.path.join(os.path.dirname(__file__), "..", "readme.txt")
        readme_path = os.path.abspath(readme_path)
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read().strip()
        except FileNotFoundError:
            readme_content = "Файл readme.txt не найден."

        message = (
            f"PDFConvert {version}\n"
            f"© 2025, psiv\n"
            f"Все права защищены.\n"
            f"{'-'*40}\n"
            f"{readme_content}"
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("О программе")
        dialog.setWindowIcon(self.app_icon)
        dialog.resize(400, 300)

        bg_path = os.path.join(os.path.dirname(__file__), "..", "logo_spp.png")
        bg_pixmap = QPixmap(bg_path)

        def update_background():
            scaled = bg_pixmap.scaled(
                dialog.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            palette = dialog.palette()
            palette.setBrush(dialog.backgroundRole(), QBrush(scaled))
            dialog.setPalette(palette)

        def on_resize(event):
            update_background()
            QDialog.resizeEvent(dialog, event)

        dialog.resizeEvent = on_resize
        update_background()

        layout = QVBoxLayout(dialog)
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            "background-color: rgba(255, 255, 255, 200); padding: 10px;"
        )
        layout.addWidget(label, alignment=Qt.AlignCenter)

        dialog.exec_()


    def open_todo(self):
        todo_path = os.path.join(os.path.dirname(__file__), "..", "ToDo.md")
        if os.path.exists(todo_path):
            subprocess.Popen(["notepad.exe", todo_path])
        else:
            QMessageBox.warning(self, "Файл не найден", f"ToDo.md не найден:\n{todo_path}")
            
    def start_conversion(self):
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.set_progress_with_border()
        self.status.showMessage("Начинаем...")


        # Логирование начала
        log_path = os.path.join(os.path.dirname(__file__), "..", "message.log")
        log_path = os.path.abspath(log_path)
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now():%d.%m.%Y %H:%M:%S}] Начало работы: {os.path.abspath(__file__)}\n")
        except Exception:
            pass


        # Создание и запуск потока
        self.worker = ConvertWorker(
            ini_path=os.path.join(os.path.dirname(__file__), "..", "setup.ini")
        )

        # Подключения сигналов
        self.worker.update_status.connect(self.handle_status_message)
        self.worker.update_progress.connect(self.progress.setValue)
        self.worker.done.connect(self.conversion_finished)
        self.worker.show_info.connect(self.show_info_dialog)
        self.worker.show_blocking_dialog.connect(self.show_blocked_file_message)

        self.worker.start()

    def conversion_finished(self):
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.status.showMessage("Конвертация завершена", 2000)
        self.reset_progress_style_to_background()
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
    
    def reset_progress_style_to_background(self):
        bg_color = self.palette().color(self.backgroundRole()).name()
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {bg_color};
            }}
        """)

    def set_progress_with_border(self):
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #999;
                border-radius: 3px;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #3399ff;
                width: 10px;
            }
        """)

    def show_info_dialog(self, text):
        QMessageBox.information(self, "Информация", text)

    def show_blocked_file_message(self, message):
        QMessageBox.critical(self, "Файлы заблокированы", message)
        QApplication.quit()

    
     # ui_status_message_handler
    def handle_status_message(self, text):
        from PyQt5.QtWidgets import QMessageBox
        import os
        from datetime import datetime

        # Путь к log-файлу рядом со скриптом
        log_path = os.path.join(os.path.dirname(__file__), "..", "message.log")
        log_path = os.path.abspath(log_path)

        def log(message):
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now():%d.%m.%Y %H:%M:%S}] {message}\n")
            except Exception:
                pass  # Не мешаем GUI работать даже при ошибке логирования

        # --- Обработка особых сообщений
        if text.startswith("[BLOCKED]"):
            filename = text.replace("[BLOCKED] ", "")
            QMessageBox.critical(
                self,
                "Ошибка доступа",
                f"Файл «{filename}» заблокирован!\nВозможно, он открыт в другой программе.",
                QMessageBox.Ok
            )
            log(f"[ОШИБКА] Блокировка файла: {filename}")
        else:
            self.status.showMessage(text, 3000)
            log(text)
   
    
# config_read_version
def read_version():
    try:
        with open("version.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "v?.?.?"

    

def run_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
