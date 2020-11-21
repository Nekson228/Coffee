import sqlite3
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.setWindowTitle('Кофе')
        self.con = sqlite3.connect('coffee.sqlite')
        self.add_coffee_button.clicked.connect(self.create_coffee)
        self.change_coffee_button.clicked.connect(self.change_coffee)
        self.update_coffee()

    def update_coffee(self):
        cur = self.con.cursor()
        result = cur.execute('''
        SELECT coffee.id, coffee.name, roastings.roasting, types.type, coffee.taste, coffee.price, coffee.extent 
        FROM coffee INNER JOIN roastings ON coffee.roasting_id = roastings.id, types ON coffee.type_id = types.id
        ''').fetchall()
        self.coffee_table.setRowCount(len(result))
        self.coffee_table.setColumnCount(len(result[0]))
        title = ['ID', 'Название сорта', 'Обжарка', 'Молотый/Зерновой', 'Вкус', 'Цена (руб)', 'Объем (г)']
        self.coffee_table.setHorizontalHeaderLabels(title)
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.coffee_table.setItem(i, j, QTableWidgetItem(str(val)))
        self.coffee_table.resizeColumnsToContents()

    def create_coffee(self):
        coffee_settings = CoffeeDialog().exec_()
        if not coffee_settings:
            return
        cur = self.con.cursor()
        id = cur.execute('SELECT id FROM coffee').fetchall()[-1][0] + 1
        coffee_settings.insert(0, id)
        cur.execute(f'''INSERT INTO coffee VALUES {tuple(coffee_settings)}''')
        self.con.commit()
        self.update_coffee()

    def change_coffee(self):
        rows = list(set([i.row() for i in self.coffee_table.selectedItems()]))
        if len(rows) > 1:
            self.statusBar().showMessage('Изменить можно только один элемент за раз')
            return
        elif len(rows) == 0:
            self.statusBar().showMessage('Элементов для изменеия не выбрано')
            return
        parameters = []
        for i in range(7):
            parameters.append(self.coffee_table.item(rows[0], i).text())
        item_id = parameters.pop(0)
        cur = self.con.cursor()
        settings = CoffeeDialog(*parameters).exec_()
        settings[1] = cur.execute(f'SELECT id FROM roastings WHERE roasting = "{settings[1]}"').fetchone()[0]
        settings[2] = cur.execute(f'SELECT id FROM types WHERE type = "{settings[2]}"').fetchone()[0]
        cur.execute(f'''
        UPDATE coffee SET name = ?, roasting_id = ?, type_id = ?, taste = ?, price = ?, extent = ?
        WHERE id = {item_id}''', [*settings])
        self.con.commit()
        self.update_coffee()


class CoffeeDialog(QDialog):
    def __init__(self, *parameters):
        super(CoffeeDialog, self).__init__()
        uic.loadUi("addEditCoffeeForm.ui", self)
        self.setWindowTitle('Добавить/изменить кофе')
        self.buttonBox.accepted.connect(self.check_settings)
        self.buttonBox.rejected.connect(self.reject)
        self.fill_roastings()
        self.fill_types()
        self.roastings_list.activated[str].connect(self.set_roasting)
        self.types_list.activated[str].connect(self.set_type)

        self.roasting = 1
        self.type = 1

        if parameters:
            self.name_line.setText(parameters[0])
            self.roasting = parameters[1]
            self.type = parameters[2]
            self.roastings_list.setCurrentText(self.roasting)
            self.types_list.setCurrentText(self.type)
            self.taste_line.setText(parameters[3])
            self.price_line.setText(parameters[4])
            self.extent_line.setText(parameters[5])

    def fill_roastings(self):
        database = sqlite3.connect('coffee.sqlite')
        cursor = database.cursor()
        roastings = cursor.execute('SELECT roasting FROM roastings').fetchall()
        roastings = [i[0] for i in roastings]
        self.roastings_list.addItems(roastings)

    def set_roasting(self, name):
        database = sqlite3.connect('coffee.sqlite')
        cursor = database.cursor()
        self.roasting = cursor.execute(f'''SELECT id FROM roastings WHERE roasting = "{name}"''').fetchone()[0]

    def fill_types(self):
        database = sqlite3.connect('coffee.sqlite')
        cursor = database.cursor()
        types = cursor.execute('SELECT type FROM types').fetchall()
        types = [i[0] for i in types]
        self.types_list.addItems(types)

    def set_type(self, name):
        database = sqlite3.connect('coffee.sqlite')
        cursor = database.cursor()
        self.type = cursor.execute(f'''SELECT id FROM types WHERE type = "{name}"''').fetchone()[0]

    def check_settings(self):
        if all([self.name_line.text(), self.taste_line.text(), self.price_line.text(), self.extent_line.text()]):
            self.accept()
        else:
            self.status_label.setText('Неправильно заполнена форма')

    def exec_(self) -> list:
        super(CoffeeDialog, self).exec_()
        if not all([self.name_line.text(), self.taste_line.text(), self.price_line.text(), self.extent_line.text()]):
            return []
        return [self.name_line.text(), self.roasting, self.type, self.taste_line.text(), self.price_line.text(),
                self.extent_line.text()]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec())
