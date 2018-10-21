import sys

from PyQt5.QtWidgets import (QApplication, QWidget, QComboBox, QStyleFactory,
    QGridLayout, QHBoxLayout, QLabel)
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QTimer

import pyqtgraph as pg

from Bittrex import Bittrex

bittrex = Bittrex(APIKey='', Secret='')

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Crypto Trader'
        self.left = 10
        self.top = 10
        self.width = 1280
        self.height = 960
        self.table_rows_one_direction = 5
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # btn = QtGui.QPushButton('press me')
        # btn.clicked.connect(self.test)

        dropdown_base_curr = QComboBox()
        dropdown_base_curr.addItems(['BTC'])

        label_base_curr = QLabel("&Base:")
        label_base_curr.setBuddy(dropdown_base_curr)

        dropdown_curr_curr = QComboBox()
        dropdown_curr_curr.addItems(['XRP', 'SALT'])

        label_curr_curr = QLabel("&Currency:")
        label_curr_curr.setBuddy(dropdown_curr_curr)

        topLayout = QHBoxLayout()
        topLayout.addWidget(label_base_curr)
        topLayout.addWidget(dropdown_base_curr)
        # topLayout.addStretch(1)
        topLayout.addWidget(label_curr_curr)
        topLayout.addWidget(dropdown_curr_curr)

        self.tableWidget = QtGui.QTableWidget()
        self.tableWidget.setRowCount(2 * self.table_rows_one_direction)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(['Price','Quantity','XRP sum','BTC sum'])
        self.test()

        plot = pg.PlotWidget()

        mainLayout = QGridLayout()
        mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        # layout.addWidget(btn, 0, 0)
        mainLayout.addWidget(self.tableWidget, 2, 0)
        mainLayout.addWidget(plot, 2, 1)

        styleComboBox = QComboBox()
        styleComboBox.addItems(QStyleFactory.keys())
        styleComboBox.activated[str].connect(self.changeStyle)
        mainLayout.addWidget(styleComboBox, 1, 1)

        self.setLayout(mainLayout)

        if 'Fusion' in QStyleFactory.keys():
            self.changeStyle('Fusion')

        timer = QTimer(self)
        timer.timeout.connect(self.test)
        timer.start(1000)

        self.show()

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))

    def test(self):
        color_green = QtGui.QColor(40,167,69)
        color_red = QtGui.QColor(220,53,69)
        align_right = Qt.AlignRight

        results = bittrex.load_order_book("BTC-SALT")
        for cell_index in range(2 * self.table_rows_one_direction):
            self.tableWidget.setItem(cell_index,0, QtGui.QTableWidgetItem(""))
            self.tableWidget.setItem(cell_index,1, QtGui.QTableWidgetItem(""))
        sum_bid = 0
        sum_bid_base = 0
        for bid in results['Bid']:
            self.tableWidget.setItem(self.table_rows_one_direction + bid, 0, QtGui.QTableWidgetItem("{0:.8f}".format(results['Bid'][bid]['Price'])))
            self.tableWidget.setItem(self.table_rows_one_direction + bid, 1, QtGui.QTableWidgetItem("{0:.8f}".format(results['Bid'][bid]['Quantity'])))
            sum_bid += results['Bid'][bid]['Quantity']
            sum_bid_base += results['Bid'][bid]['Quantity'] * results['Bid'][bid]['Price']
            self.tableWidget.setItem(self.table_rows_one_direction + bid, 2, QtGui.QTableWidgetItem("{0:.8f}".format(sum_bid)))
            self.tableWidget.setItem(self.table_rows_one_direction + bid, 3, QtGui.QTableWidgetItem("{0:.8f}".format(sum_bid_base)))
            for i in range(4):
                self.tableWidget.item(self.table_rows_one_direction + bid, i).setBackground(color_green)
                self.tableWidget.item(self.table_rows_one_direction + bid, i).setTextAlignment(align_right)

        sum_ask = 0
        sum_ask_base = 0
        for ask in results['Ask']:
            self.tableWidget.setItem(self.table_rows_one_direction - 1 - ask, 0, QtGui.QTableWidgetItem("{0:.8f}".format(results['Ask'][ask]['Price'])))
            self.tableWidget.setItem(self.table_rows_one_direction - 1 - ask, 1, QtGui.QTableWidgetItem("{0:.8f}".format(results['Ask'][ask]['Quantity'])))
            sum_ask += results['Ask'][ask]['Quantity']
            sum_ask_base += results['Ask'][ask]['Quantity'] * results['Ask'][ask]['Price']
            self.tableWidget.setItem(self.table_rows_one_direction - 1 - ask, 2, QtGui.QTableWidgetItem("{0:.8f}".format(sum_ask)))
            self.tableWidget.setItem(self.table_rows_one_direction - 1 - ask, 3, QtGui.QTableWidgetItem("{0:.8f}".format(sum_ask_base)))
            for i in range(4):
                self.tableWidget.item(self.table_rows_one_direction - 1 - ask, i).setBackground(color_red)
                self.tableWidget.item(self.table_rows_one_direction - 1 - ask, i).setTextAlignment(align_right)

if __name__ == '__main__':
    app = QApplication([])
    ex = App()
    sys.exit(app.exec_())
