from copy import deepcopy
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QMessageBox,
    QFileDialog,
    QTableWidgetItem,
    QApplication,
    QProgressBar,
)
from tools.ui.mainWindow.Ui_mainWindow import Ui_MainWindow
from tools.ui.systemTray.Ui_systemTray import SystemTrayIcon
from tools.db.DBtools import MyDB


class MyMainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, app: QApplication, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.app = app
        self._bound()
        self.__initialization__()
        self.__init_systemTray(app)

    def _bound(self):
        """
        绑定事件
        """
        self.importtxt.triggered.connect(self.import_txt)
        self.importxls.triggered.connect(self.import_xls)
        self.exporttxt.triggered.connect(self.export_txt)
        self.exportxls.triggered.connect(self.export_xls)
        self.actionSetAutoOpen.triggered.connect(self.set_auto_open)
        self.actionRegister.triggered.connect(self.register_right_click)
        self.actionExit.triggered.connect(self.exit_app)

        self.pushButtonmodify.clicked.connect(self.modify)
        self.pushButtondelete.clicked.connect(self.delete)
        self.pushButtonclear.clicked.connect(self.clear)
        self.pushButtonquery.clicked.connect(self.query)

        self.tableWidget.cellClicked.connect(self.cell_clicked)

    def __initialization__(self):
        # 菜单
        self.importtxt: QAction
        self.importxls: QAction
        self.exporttxt: QAction
        self.exportxls: QAction
        self.actionSetAutoOpen: QAction
        self.actionRegister: QAction
        self.actionExit: QAction
        # Button
        self.pushButtonmodify: QPushButton
        self.pushButtondelete: QPushButton
        self.pushButtonclear: QPushButton
        self.pushButtonquery: QPushButton
        # lineEdit
        self.lineEdituuid: QLineEdit
        self.lineEditname: QLineEdit
        self.lineEditremarks: QLineEdit
        self.lineEditaccount: QLineEdit
        self.lineEditpassword: QLineEdit
        # tableWidget
        self.tableWidget: QTableWidget
        # 进度条
        self.progressBar: QProgressBar
        self.progressBar.setVisible(False)
        # 记录当前数据库中的数据
        self.data: list = None
        # 数据库对象
        self.__init_db__()
        # 初始化数据库中数据加入tableWidget
        self._refresh_tableWidget(self._refresh_all_info())

    def __init_db__(self):
        self.db = MyDB()

    def __init_systemTray(self, app):
        """
        初始化系统托盘
        """
        self.tray = SystemTrayIcon(self)

    def _refresh_tableWidget(self, data: list = None):
        """
        初始化tableWidget
        """
        self.tableWidget.setRowCount(len(data))
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(["名称", "账号", "密码", "备注"])
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                if j == 0:
                    continue
                t = str(value) if value else ""
                self.tableWidget.setItem(i, j - 1, QTableWidgetItem(t))

    def _choose_file(self, info: str, file_type_choose, filter: str):
        """
        选择文件
        """
        m = QMessageBox.warning(self, "警告", info, QMessageBox.Yes | QMessageBox.No)
        if m == QMessageBox.Yes:
            file_name, _ = QFileDialog.getOpenFileName(self, "选择文件", "", filter)
            if file_name:
                flag = file_type_choose(file_name.rsplit(".", 1)[-1])
                if flag:
                    return file_name
                else:
                    QMessageBox.critical(self, "错误", "请选择对应文件", QMessageBox.Yes)
                    return False
        elif m == QMessageBox.No:
            return False
        else:
            return False
        return False

    def _choose_dir(self):
        """
        选择文件夹
        """
        dir_name = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_name:
            return dir_name
        else:
            return False

    def _refresh_all_info(self, uuid: bool = True):
        """
        获取所有数据库表中的数据
        """
        self.data = self.db.fetch_all()
        if uuid:
            return deepcopy(self.data)
        else:
            return [i[1:] for i in deepcopy(self.data)]

    def _get_lineEdit_data(self):
        """
        获取输入框数据
        """
        uuid = self.lineEdituuid.text()
        name = self.lineEditname.text()
        account = self.lineEditaccount.text()
        password = self.lineEditpassword.text()
        remarks = self.lineEditremarks.text()
        return (uuid, name, account, password, remarks)

    def _change_visible(self, qwidget):
        """
        设置控件显示
        """
        qwidget.setVisible(not qwidget.isVisible())

    def import_txt(self):
        """
        导入txt
        """
        file_name = self._choose_file(
            "导入会覆盖之前保存的记录!\n\n每行数据从左至右顺序应为(名称,账号,密码,备注)\n数据之间用TAB分开",
            lambda x: x == "txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_name:
            return

        try:
            tmp_info = []
            try:
                f = open(file_name, "r", encoding="utf-8")
                tmp_data = f.readlines()
            except:
                f = open(file_name, "r", encoding="gbk")
                tmp_data = f.readlines()
            finally:
                f.close()
                for i in tmp_data:
                    t = i.split("\t")
                    t = [t.strip() for t in t]
                    tmp_info.append(tuple(t))
            self.db.clear_table()
            self.db.insert_many_data(tmp_info)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e), QMessageBox.Yes)
        finally:
            self._refresh_tableWidget(self._refresh_all_info())

    def import_xls(self):
        """
        导入xls
        """
        file_name = self._choose_file(
            '导入会覆盖之前保存的记录!\n\n每行数据从左至右顺序应为(名称,账号,密码,备注) \n"备注"一列可为空',
            lambda x: x in ["xls", "xlsx"],
            "Excel Files (*.xls *.xlsx);;All Files (*)",
        )
        if not file_name:
            return

        try:
            import xlrd

            tmp_info = []
            book = xlrd.open_workbook(file_name)
            sheet = book.sheet_by_index(0)
            head_dict = {
                "名称": -1,
                "账号": -1,
                "密码": -1,
                "备注": -1,
            }
            # 遍历列名，获取列名对应的列索引
            for i in range(sheet.ncols):
                if sheet.cell_value(0, i) in head_dict:
                    head_dict[sheet.cell_value(0, i)] = i
            # 遍历所有行，获取对应列的数据
            for i in range(1, sheet.nrows):
                tmp = []
                for j in ["名称", "账号", "密码", "备注"]:
                    if head_dict[j] == -1:
                        tmp.append("")
                    else:
                        tmp.append(sheet.cell_value(i, head_dict[j]).strip())
                tmp_info.append(tuple(tmp))

            self.db.clear_table()
            self.db.insert_many_data(tmp_info)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e), QMessageBox.Yes)
        finally:
            self._refresh_tableWidget(self._refresh_all_info())

    def export_txt(self):
        """
        导出txt
        """
        dir: str = self._choose_dir()
        if not dir:
            return
        try:
            import os

            flag = ""
            file_name = dir + "/data{}.txt"
            while os.path.exists(file_name.format(flag)):
                flag = flag + 1 if flag else 1

            with open(file_name.format(flag), "w", encoding="utf-8") as f:
                tmp_data = self._refresh_all_info(False)
                for i in tmp_data:
                    f.write("\t".join(i) + "\n")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e), QMessageBox.Yes)

    def export_xls(self):
        """
        导出xls
        """
        dir = self._choose_dir()
        if not dir:
            return
        try:
            import os
            import xlwt

            flag = ""
            file_name = dir + "/data{}.xls"
            while os.path.exists(file_name.format(flag)):
                flag = flag + 1 if flag else 1

            book = xlwt.Workbook()
            sheet1 = book.add_sheet("账号信息")
            # 表头
            sheet1.row(0).height_mismatch = True  # 允许行高自定义
            sheet1.row(0).height = 20 * 15  # 行高以 1/20 个点为单位
            head_list = ["名称", "账号", "密码", "备注"]
            for i in range(len(head_list)):
                sheet1.write(0, i, head_list[i])
                sheet1.col(i).width = 256 * 50
            # 表内容
            tmp_data = self._refresh_all_info(False)
            for i in range(1, len(tmp_data) + 1):
                for j in range(4):
                    sheet1.write(i, j, tmp_data[i - 1][j])
                sheet1.row(i).height_mismatch = True
                sheet1.row(i).height = 20 * 15
            book.save(file_name.format(flag))

        except Exception as e:
            QMessageBox.critical(self, "错误", str(e), QMessageBox.Yes)

    def set_auto_open(self): ...

    def register_right_click(self): ...

    def exit_app(self):
        self.app.quit()

    def modify(self):
        """
        修改或新增
        """
        data = self._get_lineEdit_data()
        if not any(data):
            return
        self._change_visible(self.progressBar)
        self.progressBar.setValue(20)
        if data[0]:
            self.db.update_data(data[0], data[1:])
        else:
            self.db.insert_data(data[1:])
        self.progressBar.setValue(40)
        self._refresh_tableWidget(self._refresh_all_info())
        self.progressBar.setValue(65)
        self.clear()
        self.progressBar.setValue(100)
        self._change_visible(self.progressBar)

    def delete(self):
        """
        删除
        """
        self._change_visible(self.progressBar)
        self.progressBar.setValue(5)
        t = self.tableWidget.selectedItems()
        rows = []
        for i in t:
            rows.append(i.row())
        self.progressBar.setValue(15)
        rows = list(set(rows))
        uuid_list = [self.data[i][0] for i in rows]
        self.progressBar.setValue(35)
        for i in uuid_list:
            self.db.delete_data(i)
        self.progressBar.setValue(75)
        self._refresh_tableWidget(self._refresh_all_info())
        self.progressBar.setValue(95)
        self.clear()
        self.progressBar.setValue(100)
        self._change_visible(self.progressBar)

    def clear(self):
        """
        清空lineEdit
        """
        self.lineEdituuid.clear()
        self.lineEditname.clear()
        self.lineEditremarks.clear()
        self.lineEditaccount.clear()
        self.lineEditpassword.clear()
        self._refresh_tableWidget(self._refresh_all_info())

    def query(self):
        """
        查询并显示
        """
        data = self._get_lineEdit_data()
        if not any(data):
            return
        self._change_visible(self.progressBar)
        self.progressBar.setValue(5)
        ans = self.db.fetch(*data)
        self.progressBar.setValue(45)
        all_info = self._refresh_all_info()
        for i in ans:
            if i in all_info:
                all_info.remove(i)
        self.progressBar.setValue(70)
        self.data = [*ans, *all_info]
        self._refresh_tableWidget(self.data)
        self.progressBar.setValue(85)
        l_ans = len(ans)
        for i in range(l_ans):
            self.tableWidget.selectRow(i)
        self.progressBar.setValue(100)
        self._change_visible(self.progressBar)

    def cell_clicked(self, row, col):
        # 获取当前tablewidget中所有被选中的单元格
        t = self.tableWidget.selectedItems()
        rows = []
        for i in t:
            rows.append(i.row())
        rows = list(set(rows))
        if len(rows) != 1:
            return
        else:
            row = rows[0]
            self.lineEdituuid.setText(self.data[row][0])
            self.lineEditname.setText(self.data[row][1])
            self.lineEditaccount.setText(self.data[row][2])
            self.lineEditpassword.setText(self.data[row][3])
            self.lineEditremarks.setText(self.data[row][4])
