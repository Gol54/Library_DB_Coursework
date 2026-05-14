import sys
import os

# Путь к PostgreSQL (твой путь)
pg_dir = r"C:\Program Files\PostgreSQL\18\bin"
os.environ["PATH"] = pg_dir + os.pathsep + os.environ["PATH"]

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableView, QLineEdit, 
                             QLabel, QMessageBox, QDialog, QComboBox, QInputDialog,
                             QFormLayout, QDateEdit, QSpinBox, QGroupBox)
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQueryModel, QSqlQuery
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QHeaderView 


# ==============================================================================
# 1. НОВЫЙ ДИАЛОГ ПАРАМЕТРОВ ОТЧЕТА (Фильтры + Сортировка)
# ==============================================================================
class ReportParamsDialog(QDialog):
    """Окно для ввода множества фильтров и параметров сортировки"""
    def __init__(self, fields_config, sort_options, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        
        self.inputs = {}
        
        # Секция фильтров
        filter_group = QGroupBox("Фильтры (пустые поля не учитываются)")
        filter_form = QFormLayout()
        
        for label, key, input_type in fields_config:
            if input_type == "text":
                widget = QLineEdit()
            elif input_type == "number":
                widget = QSpinBox()
                widget.setRange(0, 1000000)
                widget.setValue(0)
            elif input_type == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate().addYears(-1)) # По умолчанию за прошлый год
            
            filter_form.addRow(label, widget)
            self.inputs[key] = (widget, input_type)
        
        filter_group.setLayout(filter_form)
        layout.addWidget(filter_group)

        # Секция сортировки
        sort_group = QGroupBox("Параметры сортировки")
        sort_layout = QHBoxLayout()
        self.sort_combo = QComboBox()
        for label, sql_field in sort_options:
            self.sort_combo.addItem(label, sql_field)
        sort_layout.addWidget(QLabel("Сортировать по:"))
        sort_layout.addWidget(self.sort_combo)
        sort_group.setLayout(sort_layout)
        layout.addWidget(sort_group)

        # Кнопки
        btns = QHBoxLayout()
        btn_ok = QPushButton("Сформировать отчет")
        btn_ok.setStyleSheet("background-color: #d1e7dd; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_values(self):
        """Собирает введенные параметры в словарь"""
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
# 2. ОКНО ВЫВОДА ОТЧЕТА (С итогами)
# ==============================================================================
class ReportWindow(QDialog):
    def __init__(self, query_sql, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(900, 500)
        layout = QVBoxLayout(self)

        self.view = QTableView()
        self.model = QSqlQueryModel()
        self.model.setQuery(query_sql)
        self.view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.view.setSortingEnabled(True) 
        self.view.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.view)
        
        total_rows = self.model.rowCount()
        lbl_totals = QLabel(f"<b>Итого в отчете:</b> найдено строк — {total_rows}")
        layout.addWidget(lbl_totals)


# ==============================================================================
# 3. ФОРМА МАСТЕР-ДЕТАЛЬ 1:М
# ==============================================================================
class LibraryBooksForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление фондами библиотек (Форма 1:М)")
        self.resize(950, 550)
        
        layout = QVBoxLayout(self)
        
        # МАСТЕР: Библиотека
        layout.addWidget(QLabel("<b>Шаг 1: Выберите библиотеку (Главная таблица)</b>"))
        self.lib_combo = QComboBox()
        self.lib_model = QSqlTableModel()
        self.lib_model.setTable("libraries")
        self.lib_model.select()
        self.lib_combo.setModel(self.lib_model)
        self.books_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.lib_combo.setModelColumn(1) 
        layout.addWidget(self.lib_combo)
        
        # ДЕТАЛЬ: Книги
        layout.addWidget(QLabel("<b>Шаг 2: Книги в этой библиотеке (Подчиненная таблица)</b>"))
        self.books_view = QTableView()
        self.books_model = QSqlTableModel()
        self.books_model.setTable("books")
        
        # !!! МЕНЯЕМ СТРАТЕГИЮ НА OnManualSubmit !!!
        self.books_model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        
        self.books_view.setModel(self.books_model)
        layout.addWidget(self.books_view)
        
        # КНОПКИ
        btn_layout = QHBoxLayout()
        
        btn_add = QPushButton("Добавить пустую строку")
        btn_add.clicked.connect(self.add_book)
        btn_layout.addWidget(btn_add)

        btn_save = QPushButton("СОХРАНИТЬ ВСЕ ИЗМЕНЕНИЯ")
        btn_save.setStyleSheet("background-color: #d1e7dd; font-weight: bold;")
        btn_save.clicked.connect(self.save_all)
        btn_layout.addWidget(btn_save)

        btn_cancel = QPushButton("Отменить ввод")
        btn_cancel.clicked.connect(self.books_model.revertAll)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        self.lib_combo.currentIndexChanged.connect(self.load_books)
        self.load_books()
        
    def load_books(self):
        # Предупреждаем пользователя, если есть несохраненные данные
        if self.books_model.isDirty():
            res = QMessageBox.question(self, "Внимание", "У вас есть несохраненные изменения. Сохранить их?")
            if res == QMessageBox.StandardButton.Yes:
                self.save_all()
            else:
                self.books_model.revertAll()

        idx = self.lib_combo.currentIndex()
        if idx < 0: return
        lib_id = self.lib_model.index(idx, 0).data()
        self.books_model.setFilter(f"library_id = {lib_id}")
        self.books_model.select()
        
    def add_book(self):
        idx = self.lib_combo.currentIndex()
        lib_id = self.lib_model.index(idx, 0).data()
        
        row = self.books_model.rowCount()
        self.books_model.insertRow(row)
        # Устанавливаем ID библиотеки
        self.books_model.setData(self.books_model.index(row, 1), lib_id)
        # ВАЖНО: нужно также проставить дефолтные ID для темы и издательства, 
        # если они не могут быть NULL в БД
        self.books_model.setData(self.books_model.index(row, 2), 1) # Например, ID темы = 1
        self.books_model.setData(self.books_model.index(row, 3), 1) # Например, ID издательства = 1
        
        self.books_view.setCurrentIndex(self.books_model.index(row, 4))

    def save_all(self):
        if self.books_model.submitAll():
            QMessageBox.information(self, "Успех", "Данные успешно сохранены в БД!")
        else:
            QMessageBox.critical(self, "Ошибка сохранения", 
                                f"База данных отклонила изменения:\n{self.books_model.lastError().text()}")
            
# ==============================================================================
# 4. ГЛАВНОЕ ОКНО
# ==============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Информационная система Библиотеки")
        self.resize(1100, 650)
        self.connect_db()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)

        self.setup_menu()

        self.right_panel = QVBoxLayout()
        self.main_layout.addLayout(self.right_panel, stretch=4)

        self.setup_toolbar()
        
        self.model = QSqlTableModel(self)
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setSortingEnabled(True)
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
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось подключиться:\n{self.db.lastError().text()}")
            sys.exit(1)

    def setup_menu(self):
        menu_layout = QVBoxLayout()
        menu_layout.addWidget(QLabel("<b>ТАБЛИЦЫ</b>"))
        tables = [("Издательства", "publishers"), ("Тематики", "topics"), 
                  ("Библиотеки", "libraries"), ("Читатели", "readers"), 
                  ("Книги", "books"), ("Абонементы", "subscriptions")]
        for name, table in tables:
            btn = QPushButton(name)
            btn.clicked.connect(lambda ch, t=table: self.load_table(t))
            menu_layout.addWidget(btn)

        menu_layout.addSpacing(20)
        menu_layout.addWidget(QLabel("<b>ОТЧЕТЫ И ФОРМЫ</b>"))
        
        btn_md = QPushButton("Управление фондами ")
        btn_md.setStyleSheet("background-color: #d1e7dd;")
        btn_md.clicked.connect(lambda: LibraryBooksForm(self).exec())
        menu_layout.addWidget(btn_md)

        # Кнопки новых отчетов
        btn_rep1 = QPushButton("Отчет: Фонд по тематикам")
        btn_rep1.clicked.connect(self.report_books_by_topic)
        menu_layout.addWidget(btn_rep1)

        btn_rep2 = QPushButton("Отчет: Анализ издательств")
        btn_rep2.clicked.connect(self.report_publishers_by_city)
        menu_layout.addWidget(btn_rep2)

        btn_rep3 = QPushButton("Отчет: Финансы читателей")
        btn_rep3.clicked.connect(self.report_reader_deposits)
        menu_layout.addWidget(btn_rep3)

        menu_layout.addStretch()
        self.main_layout.addLayout(menu_layout, stretch=1)

    def setup_toolbar(self):
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(QLabel("Поиск по полю:"))
        self.search_col_combo = QComboBox()
        toolbar_layout.addWidget(self.search_col_combo)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите значение...")
        self.search_input.textChanged.connect(self.apply_filter)
        toolbar_layout.addWidget(self.search_input)
        self.right_panel.addLayout(toolbar_layout)

    def setup_buttons(self):
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить запись")
        btn_add.clicked.connect(self.add_record)
        btn_layout.addWidget(btn_add)
        btn_del = QPushButton("Удалить выбранную")
        btn_del.clicked.connect(self.delete_record)
        btn_layout.addWidget(btn_del)
        self.right_panel.addLayout(btn_layout)

    def load_table(self, table_name):
        self.current_table = table_name
        self.model.setTable(table_name)
        self.model.select()
        self.search_col_combo.clear()
        
        if table_name == "publishers":
            headers, fields = ["ID", "Название", "Город"], ["publisher_id", "name", "city"]
        elif table_name == "topics":
            headers, fields = ["ID", "Тема"], ["topic_id", "name"]
        elif table_name == "libraries":
            headers, fields = ["ID", "Название", "Адрес"], ["library_id", "name", "address"]
        elif table_name == "readers":
            headers, fields = ["ID", "Фамилия", "Имя", "Отчество", "Адрес", "Телефон", "Дата рождения"], ["reader_id", "last_name", "first_name", "patronymic", "address", "phone", "birth_date"]
        elif table_name == "books":
            headers, fields = ["ID", "Lib ID", "Topic ID", "Pub ID", "Название", "Автор", "Год", "Кол-во"], ["book_id", "library_id", "topic_id", "publisher_id", "title", "author", "release_year", "quantity"]
        elif table_name == "subscriptions":
            headers, fields = ["ID", "Lib ID", "Book ID", "Reader ID", "Выдача", "Возврат", "Залог"], ["sub_id", "library_id", "book_id", "reader_id", "issue_date", "return_date", "deposit"]

        for i, h in enumerate(headers):
            self.model.setHeaderData(i, Qt.Orientation.Horizontal, h)
            self.search_col_combo.addItem(h, fields[i])
        self.search_input.clear()
    
    def apply_filter(self):
        txt = self.search_input.text().strip()
        fld = self.search_col_combo.currentData()
        if not txt or not fld:
            self.model.setFilter(""); self.model.select(); return
        self.model.setFilter(f"CAST({fld} AS TEXT) ILIKE '%{txt}%'")
        self.model.select()

    def add_record(self):
        self.model.insertRow(self.model.rowCount())

    def delete_record(self):
        sel = self.table_view.selectionModel().selectedRows()
        if sel: self.model.removeRow(sel[0].row()); self.model.select()

    # ==========================================================================
    # ОБНОВЛЕННЫЕ ОТЧЕТЫ С МНОЖЕСТВЕННЫМИ ПАРАМЕТРАМИ
    # ==========================================================================
    
    def report_books_by_topic(self):
        """Отчет 1: Группировка книг по темам с фильтрами по автору и году"""
        fields = [
            ("Автор содержит:", "auth", "text"),
            ("Издано после года:", "yr", "number")
        ]
        sorts = [("По названию темы", "t.name"), ("По количеству книг", "total_books DESC")]
        
        dlg = ReportParamsDialog(fields, sorts, "Параметры отчета по фондам", self)
        if dlg.exec():
            v = dlg.get_values()
            conds = []
            if v['auth']: conds.append(f"b.author ILIKE '%{v['auth']}%'")
            if v['yr']:   conds.append(f"b.release_year >= {v['yr']}")
            
            wh = "WHERE " + " AND ".join(conds) if conds else ""
            
            sql = f"""
                SELECT t.name as "Тематика", 
                       COUNT(b.book_id) as "total_books",
                       SUM(b.quantity) as "Всего экземпляров",
                       ROUND(AVG(b.release_year), 0) as "Средний год издания"
                FROM topics t
                JOIN books b ON t.topic_id = b.topic_id
                {wh}
                GROUP BY t.name
                ORDER BY {v['order_by']}
            """
            ReportWindow(sql, "Отчет: Книги по темам", self).exec()

    def report_publishers_by_city(self):
        """Отчет 2: Статистика издательств с фильтрами по городу и названию"""
        fields = [
            ("Город издания:", "city", "text"),
            ("Название содержит:", "name", "text")
        ]
        sorts = [("По городу", "city"), ("По названию", "name")]
        
        dlg = ReportParamsDialog(fields, sorts, "Параметры отчета по издательствам", self)
        if dlg.exec():
            v = dlg.get_values()
            conds = []
            if v['city']: conds.append(f"city ILIKE '%{v['city']}%'")
            if v['name']: conds.append(f"name ILIKE '%{v['name']}%'")
            
            wh = "WHERE " + " AND ".join(conds) if conds else ""
            
            sql = f"""
                SELECT city as "Город", 
                       name as "Издательство",
                       (SELECT COUNT(*) FROM books WHERE publisher_id = publishers.publisher_id) as "Книг в базе"
                FROM publishers
                {wh}
                ORDER BY {v['order_by']}
            """
            ReportWindow(sql, "Отчет: Список издательств", self).exec()

    def report_reader_deposits(self):
        """Отчет 3: Финансы читателей с фильтрами по дате выдачи и сумме залога"""
        fields = [
            ("Выдано после:", "dt", "date"),
            ("Минимальный залог:", "min_dep", "number")
        ]
        sorts = [("По сумме залога", "total_dep DESC"), ("По фамилии", "r.last_name")]
        
        dlg = ReportParamsDialog(fields, sorts, "Параметры активности читателей", self)
        if dlg.exec():
            v = dlg.get_values()
            conds = []
            if v['dt']:      conds.append(f"s.issue_date >= '{v['dt']}'")
            if v['min_dep']: conds.append(f"s.deposit >= {v['min_dep']}")
            
            wh = "WHERE " + " AND ".join(conds) if conds else ""
            
            sql = f"""
                SELECT r.last_name || ' ' || r.first_name as "Читатель",
                       COUNT(s.sub_id) as "Кол-во книг",
                       SUM(s.deposit) as "total_dep",
                       MAX(s.issue_date) as "Последняя выдача"
                FROM readers r
                JOIN subscriptions s ON r.reader_id = s.reader_id
                {wh}
                GROUP BY r.reader_id, r.last_name, r.first_name
                ORDER BY {v['order_by']}
            """
            ReportWindow(sql, "Отчет: Финансовая активность читателей", self).exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())