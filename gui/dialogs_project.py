# gui/dialogs_project.py (унифицированный путь к setup.ini, исправление ошибки несохранения)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel,
    QListWidgetItem, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
import configparser
import os

class ProjectSelectDialog(QDialog):
    def __init__(self, ini_path, parent=None):
        super().__init__(parent)
        if parent:
            self.setWindowIcon(parent.windowIcon())
        self.setWindowTitle("Выбор проекта")
        self.setMinimumSize(600, 400)

        self.ini_path = ini_path
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config.read(self.ini_path, encoding='utf-8')

        self.project_list = QListWidget()
        self.details_label = QLabel("Выберите проект слева, чтобы увидеть настройки")
        self.details_label.setTextInteractionFlags(self.details_label.textInteractionFlags() | Qt.TextSelectableByMouse)
        self.current_selection = None

        self.project_list.currentItemChanged.connect(self.update_preview)
        self.project_list.itemDoubleClicked.connect(self.accept_project)

        self.load_projects()

        # Кнопки
        btn_create = QPushButton("Создать")
        btn_delete = QPushButton("Удалить")
        btn_select = QPushButton("Выбрать")
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Отмена")

        btn_create.clicked.connect(self.create_project)
        btn_delete.clicked.connect(self.delete_project)
        btn_select.clicked.connect(self.accept_project)
        btn_ok.clicked.connect(self.accept_project)
        btn_cancel.clicked.connect(self.reject)

        # Layout
        main_layout = QVBoxLayout(self)
        hbox = QHBoxLayout()
        hbox.addWidget(self.project_list, 1)
        hbox.addWidget(self.details_label, 2)
        main_layout.addLayout(hbox)

        btns = QHBoxLayout()
        btns.addWidget(btn_create)
        btns.addWidget(btn_delete)
        btns.addWidget(btn_select)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        main_layout.addLayout(btns)

    def load_projects(self):
        self.project_list.clear()
        current = self.config.get("global", "current_project", fallback="")

        selected_item = None
        for section in self.config.sections():
            if section != "global":
                item = QListWidgetItem(section)
                self.project_list.addItem(item)
                if section == current:
                    selected_item = item

        if selected_item:
            self.project_list.setCurrentItem(selected_item)

    def update_preview(self):
        item = self.project_list.currentItem()
        if not item:
            self.details_label.setText("Нет проекта")
            self.current_selection = None
            return

        name = item.text()
        self.current_selection = name

        if not self.config.has_section(name):
            self.details_label.setText("Раздел не найден.")
            return

        data = self.config.items(name)
        summary = [f"Текущий проект: {name}", ""]
        file_counter = 0
        for k, v in data:
            if k == "output_folder":
                summary.append(f"Папка сохранения PDF: {v}")
            elif k == "merged_pdf_path":
                summary.append(f"Итоговый PDF: {v}")
            elif k.startswith("source_files_"):
                file_counter += 1
                filepath = v.split("|")[0].strip()
                summary.append(f"Файл: {filepath}")
        if file_counter == 0:
            summary.append("\nНет файлов в проекте.")
        self.details_label.setText("\n".join(summary))

    def create_project(self):
        self.config.read(self.ini_path, encoding="utf-8")

        name, ok = QInputDialog.getText(self, "Новый проект", "Введите имя проекта:")
        if not ok or not name.strip():
            return
        name = name.strip()

        if self.config.has_section(name):
            QMessageBox.warning(self, "Ошибка", "Проект с таким именем уже существует.")
            return

        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "template.ini"))
        template_config = configparser.ConfigParser()
        template_config.optionxform = str
        template_config.read(template_path, encoding="utf-8")

        if not template_config.has_section("template"):
            QMessageBox.warning(self, "Ошибка", "В template.ini отсутствует секция [template].")
            return

        self.config.add_section(name)

        input_folder = template_config.get("template", "input_folder", fallback="").replace("\\", "/").rstrip("/")

        for key, value in template_config.items("template"):
            if key == "input_folder":
                self.config.set(name, key, input_folder)
                continue
            value = value.replace("TEMPLATE", name)
            value = value.replace("_input_folder_", input_folder)
            value = value.replace("\\", "/")
            self.config.set(name, key, value)

        output_folder = self.config.get(name, "output_folder", fallback="")
        if output_folder:
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось создать папку:\n{output_folder}\n\n{e}")

        with open(self.ini_path, "w", encoding="utf-8") as f:
            self.config.write(f)

        self.project_list.addItem(name)
        self.project_list.setCurrentRow(self.project_list.count() - 1)

    def delete_project(self):
        item = self.project_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Нет выбора", "Выберите проект для удаления.")
            return

        name = item.text()

        if QMessageBox.question(self, "Удалить", f"Удалить проект {name}?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read(self.ini_path, encoding="utf-8")

        parser.remove_section(name)

        if parser.get("global", "current_project", fallback="") == name:
            parser.set("global", "current_project", "")

        with open(self.ini_path, "w", encoding="utf-8") as f:
            parser.write(f)

        self.config = parser
        self.project_list.takeItem(self.project_list.row(item))
        self.update_preview()

        # QMessageBox.information(self, "Удалено", f"Проект '{name}' удалён.")

    def accept_project(self):
        if not self.current_selection:
            QMessageBox.warning(self, "Нет выбора", "Выберите проект.")
            return

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(self.ini_path, encoding="utf-8")

        if not config.has_section("global"):
            config.add_section("global")

        config.set("global", "current_project", self.current_selection)

        with open(self.ini_path, "w", encoding="utf-8") as f:
            config.write(f)

        self.config = config
        self.accept()

    def get_selected_project(self):
        return self.project_list.currentItem().text() if self.project_list.currentItem() else None
