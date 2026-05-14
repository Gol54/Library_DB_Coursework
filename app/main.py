import sys
import os

# Путь к PostgreSQL
pg_dir = r"C:\Program Files\PostgreSQL\18\bin"
os.environ["PATH"] = pg_dir + os.pathsep + os.environ["PATH"]

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableView, QLineEdit, 
                             QLabel, QMessageBox, QDialog, QComboBox, 
                             QFormLayout, QDateEdit, QSpinBox, QGroupBox, QHeaderView)
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQueryModel
from PyQt6.QtCore import Qt, QDate

# ==============================================================================
# 1. ДИАЛОГ ПАРАМЕТРОВ ОТЧЕТА (Фильтры + Сортировка)
# ==============================================================================
class ReportParamsDialog(QDialog):
    def __init__(self, fields_config, sort_options, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        self.inputs = {}
        
        filter_group = QGroupBox("Фильтры")
        filter_form = QFormLayout()
        for label, key, input_type in fields_config:
            if input_type == "text": widget = QLineEdit()
            elif input_type == "number": 
                widget = QSpinBox()
                widget.setRange(0, 1000000)
            elif input_type == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate().addYears(-1))
            filter_form.addRow(label, widget)
            self.inputs[key] = (widget, input_type)
        filter_group.setLayout(filter_form)
        layout.addWidget(filter_group)

        sort_group = QGroupBox("Сортировка")
        sort_layout = QHBoxLayout()
        self.sort_combo = QComboBox()
        for label, sql_field in sort_options:
            self.sort_combo.addItem(label, sql_field)
        sort_layout.addWidget(QLabel("Сортировать по:"))
        sort_layout.addWidget(self.sort_combo)
        sort_group.setLayout(sort_layout)
        layout.addWidget(sort_group)

        btn_ok = QPushButton("Сформировать отчет")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

    def get_values(self):
        results = {}
        for key, (widget, itype) in self.inputs.items():
            if itype == "text":
                val = widget.text().strip()
                results[key] = val if val else None
            elif itype == "number":
                val = widget.value()
                results[key] = val if val > 0 else None
            elif itype == "date":
                results[key] = widget.date().toString("yyyy-MM-dd")
        results["order_by"] = self.sort_combo.currentData()
        return results

# ==============================================================================
# 2. ОКНО ВЫВОДА ОТЧЕТА
# ==============================================================================
class ReportWindow(QDialog):
    def __init__(self, query_sql, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 450)
        layout = QVBoxLayout(self)

        self.view = QTableView()
        self.model = QSqlQueryModel()
        self.model.setQuery(query_sql)
        self.view.setModel(self.model)
        
        # Исправлено: обращение к self.view, настройка авто-ширины
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.view)
        layout.addWidget(QLabel(f"Итого строк: {self.model.rowCount()}"))

# ==============================================================================
# 3. ФОРМА МАСТЕР-ДЕТАЛЬ 1:М
# ==============================================================================
class LibraryBooksForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление фондами (1:М)")
        self.resize(900, 500)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Выберите библиотеку:"))
        self.lib_combo = QComboBox()
        self.lib_model = QSqlTableModel()
        self.lib_model.setTable("libraries")
        self.lib_model.select()
        self.lib_combo.setModel(self.lib_model)
        self.lib_combo.setModelColumn(1) 
        layout.addWidget(self.lib_combo)
        
        layout.addWidget(QLabel("Книги в этой библиотеке:"))
        self.books_view = QTableView()
        self.books_model = QSqlTableModel()
        self.books_model.setTable("books")
        self.books_model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.books_view.setModel(self.books_model)
        
        # Исправлено: настройка ширины ПОСЛЕ создания books_view
        self.books_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.books_view)
        
        btns = QHBoxLayout()
        b_add = QPushButton("Добавить строку")
        b_add.clicked.connect(self.add_book)
        b_save = QPushButton("СОХРАНИТЬ")
        b_save.clicked.connect(self.save_all)
        btns.addWidget(b_add)
        btns.addWidget(b_save)
        layout.addLayout(btns)
        
        self.lib_combo.currentIndexChanged.connect(self.load_books)
        self.load_books()
        
    def load_books(self):
        idx = self.lib_combo.currentIndex()
        if idx < 0: return
        lib_id = self.lib_model.index(idx, 0).data()
        self.books_model.setFilter(f"library_id = {lib_id}")
        self.books_model.select()
        
    def add_book(self):
        idx = self.lib_combo.currentIndex()
        lib_id = self.lib_model.index(idx, 0).data()
        r = self.books_model.rowCount()
        self.books_model.insertRow(r)
        self.books_model.setData(self.books_model.index(r, 1), lib_id)
        self.books_model.setData(self.books_model.index(r, 2), 1)
        self.books_model.setData(self.books_model.index(r, 3), 1)

    def save_all(self):
        if self.books_model.submitAll(): QMessageBox.information(self, "ОК", "Сохранено")
        else: QMessageBox.warning(self, "Ошибка", self.books_model.lastError().text())

# ==============================================================================
# 4. ГЛАВНОЕ ОКНО (Твой стиль)
# ==============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Информационная система Библиотеки")
        self.resize(1100, 650)
        self.connect_db()

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)

        # Слева меню
        self.setup_menu()

        # Справа контент
        self.right_panel = QVBoxLayout()
        self.main_layout.addLayout(self.right_panel, stretch=4)

        self.setup_toolbar()
        
        self.model = QSqlTableModel(self)
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.right_panel.addWidget(self.table_view)

        self.setup_buttons()
        self.load_table("publishers")

    def connect_db(self):
        self.db = QSqlDatabase.addDatabase("QPSQL")
        self.db.setHostName("localhost")
        self.db.setDatabaseName("postgres")
        self.db.setUserName("postgres")
        self.db.setPassword("123456789") 
        if not self.db.open():
            QMessageBox.critical(self, "БД", "Ошибка подключения")
            sys.exit(1)

    def setup_menu(self):
        menu = QVBoxLayout()
        menu.addWidget(QLabel("<b>ТАБЛИЦЫ</b>"))
        tabs = [("Издательства", "publishers"), ("Тематики", "topics"), 
                ("Библиотеки", "libraries"), ("Читатели", "readers"), 
                ("Книги", "books"), ("Абонементы", "subscriptions")]
        for n, t in tabs:
            btn = QPushButton(n)
            btn.clicked.connect(lambda ch, tbl=t: self.load_table(tbl))
            menu.addWidget(btn)

        menu.addSpacing(20)
        menu.addWidget(QLabel("<b>ОТЧЕТЫ И ФОРМЫ</b>"))
        
        btn_md = QPushButton("Управление (1:М)")
        btn_md.clicked.connect(lambda: LibraryBooksForm(self).exec())
        menu.addWidget(btn_md)

        btn_r1 = QPushButton("Отчет: Фонд"); btn_r1.clicked.connect(self.rep_1); menu.addWidget(btn_r1)
        btn_r2 = QPushButton("Отчет: Издатели"); btn_r2.clicked.connect(self.rep_2); menu.addWidget(btn_r2)
        btn_r3 = QPushButton("Отчет: Читатели"); btn_r3.clicked.connect(self.rep_3); menu.addWidget(btn_r3)

        menu.addStretch()
        self.main_layout.addLayout(menu, stretch=1)

    def setup_toolbar(self):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Поиск по полю:"))
        self.search_col_combo = QComboBox()
        layout.addWidget(self.search_col_combo)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self.apply_filter)
        layout.addWidget(self.search_input)
        self.right_panel.addLayout(layout)

    def setup_buttons(self):
        layout = QHBoxLayout()
        b_add = QPushButton("Добавить"); b_add.clicked.connect(self.add_record)
        b_del = QPushButton("Удалить"); b_del.clicked.connect(self.delete_record)
        layout.addWidget(b_add); layout.addWidget(b_del)
        self.right_panel.addLayout(layout)

    def load_table(self, table_name):
        self.current_table = table_name
        self.model.setTable(table_name)
        self.model.select()
        self.search_col_combo.clear()
        for i in range(self.model.columnCount()):
            h = self.model.headerData(i, Qt.Orientation.Horizontal)
            f = self.model.record().fieldName(i)
            self.search_col_combo.addItem(str(h), f)
        self.search_input.clear()
    
    def apply_filter(self):
        txt = self.search_input.text().strip(); fld = self.search_col_combo.currentData()
        if not txt or not fld: self.model.setFilter(""); self.model.select(); return
        self.model.setFilter(f"CAST({fld} AS TEXT) ILIKE '%{txt}%'")
        self.model.select()

    def add_record(self): self.model.insertRow(self.model.rowCount())

    def delete_record(self):
        sel = self.table_view.selectionModel().selectedRows()
        if sel: self.model.removeRow(sel[0].row()); self.model.select()

    # --- ОТЧЕТЫ ---
    def rep_1(self):
        f = [("Автор:", "a", "text"), ("Год от:", "y", "number")]
        s = [("Тема", "t.name"), ("Кол-во", "total DESC")]
        dlg = ReportParamsDialog(f, s, "Отчет по фондам", self)
        if dlg.exec():
            v = dlg.get_values(); c = []
            if v['a']: c.append(f"b.author ILIKE '%{v['a']}%'")
            if v['y']: c.append(f"b.release_year >= {v['y']}")
            wh = "WHERE " + " AND ".join(c) if c else ""
            sql = f"SELECT t.name, COUNT(b.book_id) as total FROM topics t JOIN books b ON t.topic_id = b.topic_id {wh} GROUP BY t.name ORDER BY {v['order_by']}"
            ReportWindow(sql, "Фонд по тематикам", self).exec()

    def rep_2(self):
        f = [("Город:", "c", "text")]; s = [("Название", "name")]
        dlg = ReportParamsDialog(f, s, "Издательства", self)
        if dlg.exec():
            v = dlg.get_values(); wh = f"WHERE city ILIKE '%{v['c']}%'" if v['c'] else ""
            sql = f"SELECT city, name FROM publishers {wh} ORDER BY {v['order_by']}"
            ReportWindow(sql, "Список издательств", self).exec()

    def rep_3(self):
        f = [("Выдано после:", "d", "date"), ("Мин. залог:", "m", "number")]
        s = [("Сумма", "total DESC")]
        dlg = ReportParamsDialog(f, s, "Активность читателей", self)
        if dlg.exec():
            v = dlg.get_values(); c = []
            if v['d']: c.append(f"s.issue_date >= '{v['d']}'")
            if v['m']: c.append(f"s.deposit >= {v['m']}")
            wh = "WHERE " + " AND ".join(c) if c else ""
            sql = f"SELECT r.last_name, SUM(s.deposit) as total FROM readers r JOIN subscriptions s ON r.reader_id = s.reader_id {wh} GROUP BY r.reader_id, r.last_name ORDER BY {v['order_by']}"
            ReportWindow(sql, "Статистика залогов", self).exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(); window.show()
    sys.exit(app.exec())