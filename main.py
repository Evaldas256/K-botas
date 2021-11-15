import pickle
from coin_base_functions import cbpGetHistoricRates, HA, ema, get_currrency_list, plot_rsi
import finplot as fplt
import pandas as pd
import ssl
import smtplib
from PyQt5.QtWidgets import QDesktopWidget, QMainWindow, QAction, QGraphicsView, \
    QTabWidget, QTableWidget, QPushButton
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QComboBox, QGridLayout, QMessageBox,
                             QLabel, QLineEdit,
                             QTableWidgetItem,
                             QWidget)
from PyQt5 import QtWidgets
from Langai import Ui

laikas=30
valiuta = 'ADA-EUR'
lenteles_eilute = 0
einama_eilute = 0
sekamos_valiutos = []
plots = {}
axs_dic = {}
flag = {}
strategiju_sarasas = ['Pagal_RSI', 'Pagal_kaina']

try:
    with open('sekamos_valiutos.pkl', 'rb') as pickle_in:
        sekamos_valiutos = pickle.load(pickle_in)
except:
    sekamos_valiutos = ['BTC-EUR']

try:
    with open('el_pasto_duomenys.pkl', 'rb') as pickle_in:
        el_pasto_duomenys = pickle.load(pickle_in)
        sender_email = el_pasto_duomenys[0]
        password = el_pasto_duomenys[1]
        outgoing_server = el_pasto_duomenys[2]
        port = int(el_pasto_duomenys[3])
except:
    sender_email = ''
    password = ''
    outgoing_server = ''
    port = ''

print(sekamos_valiutos)
# For SSL
context = ssl.create_default_context()

message_reikia_pirkti = """\
Subject: Reikia pirkti

This message is sent from Python."""
message_reikia_parduoti = """\
Subject: Reikia parduoti

This message is sent from Python."""




class AnotherWindow(QWidget):
    FROM, SUBJECT, DATE = range(3)
    Valiuta, Strategija, El_pastas, Pirkimo_kaina, Pardavimo_kaina, Close_price, RSI, EMA = range(8)

    def __init__(self, valiuta):
        super().__init__()
        self.title = 'Kripto boto nustatymai'
        self.left = 10
        self.top = 10
        self.width = 960
        self.height = 400
        self.valiuta = valiuta
        self.initUI(valiuta)

    def initUI(self, valiuta):
        global lenteles_eilute

        desktop = QDesktopWidget()
        rect = desktop.availableGeometry(desktop.primaryScreen())
        center = rect.center()
        self.left = center.x() - (self.width // 2)
        self.top = center.y() - (self.height // 2)
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.timer = QTimer()
        self.timer.timeout.connect(self.atnaujinti_grafikus)
        self.msg = QMessageBox()
        self.msg.setWindowTitle("Kripto botas")
        # self.table = QtWidgets.QTableView()

        self.column_headers = ['Valiuta', 'Strategija', 'El_pastas', 'Pirkimo_kaina', 'Pardavimo_kaina', 'Close_price',
                               'RSI', 'EMA']
        self.model = QStandardItemModel()
        # self.table = QTableView()
        self.table = QTableWidget()
        self.table.setRowCount(len(sekamos_valiutos))
        self.table.setColumnCount(8)
        self.table.clicked.connect(self.nuskaityti_kursoriaus_pozicija)
        self.atnaujinti_lentele()

        self.valiutu_sarasas_combo = QComboBox(self)
        for i in valiuta:
            self.valiutu_sarasas_combo.addItem(i)
        self.valiutu_sarasas_label = QLabel('Valiuta', self)

        self.strategiju_sarasas_combo = QComboBox(self)
        for i in strategiju_sarasas:
            self.strategiju_sarasas_combo.addItem(i)

        self.strategiju_sarasas_label = QLabel('Strategija', self)
        self.Pirkimo_kaina_textbox = QLineEdit(self)
        self.Pirkimo_kaina_label = QLabel('Pirkimo kaina', self)
        self.Pardavimo_kaina_label = QLabel('Pardavimo kaina', self)
        self.Pardavimo_kaina_textbox = QLineEdit(self)
        self.El_pastas_label = QLabel('El_pastas', self)
        self.El_pastas_textbox = QLineEdit(self)

        self.ivesti_button = QPushButton('Ivesti', self)
        self.ivesti_button.clicked.connect(self.on_click_ivesti_button)
        self.redaguoti_button = QPushButton('Redaguoti', self)
        self.redaguoti_button.clicked.connect(self.on_click_redaguoti_button)
        self.istrinti_button = QPushButton('Istrinti', self)
        self.istrinti_button.clicked.connect(self.on_click_istrinti_button)

        self.start_button = QPushButton('Pradeti sekima', self)
        self.start_button.clicked.connect(self.startTimer)
        self.end_button = QPushButton('Baigti sekima', self)
        self.end_button.clicked.connect(self.endTimer)



        entry_layout = QGridLayout()
        entry_layout.addWidget(self.valiutu_sarasas_label, 0, 0)
        entry_layout.addWidget(self.valiutu_sarasas_combo, 0, 1)
        entry_layout.addWidget(self.strategiju_sarasas_label, 0, 2)
        entry_layout.addWidget(self.strategiju_sarasas_combo, 0, 3)

        entry_layout.addWidget(self.Pirkimo_kaina_label, 1, 0)
        entry_layout.addWidget(self.Pirkimo_kaina_textbox, 1, 1)
        entry_layout.addWidget(self.Pardavimo_kaina_label, 1, 2)

        entry_layout.addWidget(self.Pardavimo_kaina_textbox, 1, 3)
        entry_layout.addWidget(self.El_pastas_label, 2, 0)
        entry_layout.addWidget(self.El_pastas_textbox, 2, 1)
        entry_layout.addWidget(self.ivesti_button, 0, 4)
        entry_layout.addWidget(self.redaguoti_button, 0, 5)
        entry_layout.addWidget(self.istrinti_button, 0, 6)
        entry_layout.addWidget(self.start_button, 0, 7)
        entry_layout.addWidget(self.end_button, 0, 8)

        entry_layout.addWidget(self.table, 3, 0, 1, 8)
        self.setLayout(entry_layout)


        self.show()

    def nuskaityti_kursoriaus_pozicija(self):
        global sekamos_valiutos
        global einama_eilute
        global valiuta
        einama_eilute = self.table.currentRow()
        pasirinkta_valiuta = sekamos_valiutos[einama_eilute][0]
        valiutos_indeksas = valiuta.index(pasirinkta_valiuta)
        self.valiutu_sarasas_combo.setCurrentIndex(valiutos_indeksas)
        pasirinkta_startegija = sekamos_valiutos[einama_eilute][1]
        strategijos_indeksas = strategiju_sarasas.index(pasirinkta_startegija)

        self.strategiju_sarasas_combo.setCurrentIndex(strategijos_indeksas)
        self.El_pastas_textbox.setText(sekamos_valiutos[einama_eilute][2])
        self.Pirkimo_kaina_textbox.setText(sekamos_valiutos[einama_eilute][3])
        self.Pardavimo_kaina_textbox.setText(sekamos_valiutos[einama_eilute][4])

    def atnaujinti_lentele(self):
        global lenteles_eilute
        lenteles_eilute = 0
        self.table.setRowCount(len(sekamos_valiutos))
        self.table.setColumnCount(8)
        self.model.clear()
        w = 0
        for x in self.column_headers:
            self.item = QTableWidgetItem()
            self.item.setText(x)

            self.table.setHorizontalHeaderItem(w, self.item)
            w += 1

        for x in sekamos_valiutos:

            for c in range(len(x)):
                self.tekstas = QTableWidgetItem(x[c])

                self.table.setItem(lenteles_eilute, c, self.tekstas)
            lenteles_eilute += 1

    def on_click_ivesti_button(self):
        global lenteles_eilute
        laikinas = []
        valiuta = str(self.valiutu_sarasas_combo.currentText())
        strategija = str(self.strategiju_sarasas_combo.currentText())
        el_pastas = str(self.El_pastas_textbox.text())
        if self.check_if_email_valid(el_pastas) == False:
            self.show_message("Blogas el_pasto formatas", 'critical')
            return
        pirkimo_kaina = str(self.Pirkimo_kaina_textbox.text())
        pardavimo_kaina = str(self.Pardavimo_kaina_textbox.text())
        if self.check_price_valid(pirkimo_kaina, pardavimo_kaina, strategija) == False:
            return
        close_price = ''
        rsi = ''
        ema = ''
        laikinas.append(valiuta)
        laikinas.append(strategija)
        laikinas.append(el_pastas)
        laikinas.append(pirkimo_kaina)
        laikinas.append(pardavimo_kaina)
        sekamos_valiutos.append(laikinas)
        self.atnaujinti_lentele()
        atnaujinti_tabus()
        with open('sekamos_valiutos.pkl', 'wb') as pickle_out:
            pickle.dump(sekamos_valiutos, pickle_out)
        self.show_message("Duomenys sėkmingai įvesti", 'information')

    def on_click_redaguoti_button(self):

        global lenteles_eilute
        laikinas = []
        valiuta = str(self.valiutu_sarasas_combo.currentText())
        strategija = str(self.strategiju_sarasas_combo.currentText())
        el_pastas = str(self.El_pastas_textbox.text())
        if self.check_if_email_valid(el_pastas) == False:
            self.show_message("Blogas el_pasto formatas", 'critical')
            return
        pirkimo_kaina = str(self.Pirkimo_kaina_textbox.text())
        pardavimo_kaina = str(self.Pardavimo_kaina_textbox.text())
        if self.check_price_valid(pirkimo_kaina, pardavimo_kaina, strategija) == False:
            return

        close_price = ''
        rsi = ''
        ema = ''
        laikinas.append(valiuta)
        laikinas.append(strategija)
        laikinas.append(el_pastas)
        laikinas.append(pirkimo_kaina)
        laikinas.append(pardavimo_kaina)
        sekamos_valiutos[einama_eilute] = laikinas
        self.atnaujinti_lentele()
        atnaujinti_tabus()
        with open('sekamos_valiutos.pkl', 'wb') as pickle_out:
            pickle.dump(sekamos_valiutos, pickle_out)
        self.show_message("Duomenys atnaujinti sėkmingai", 'information')

    def check_price_valid(self, buy_price, sel_price, strategy):
        atsakymas = True
        buy = 0
        sel = 0
        try:
            buy = float(buy_price)
        except:
            self.show_message('Pirkimo kaina netinkamo formato', 'critical')
            atsakymas = False

        try:
            sel = float(sel_price)
        except:
            self.show_message('Pardavimo kaina netinkamo formato', 'critical')
            atsakymas = False
        if buy >= sel:
            self.show_message('Pirkimo kaina turi būti mažesnė už pardavimo', 'critical')
            atsakymas = False
        return atsakymas

    def show_message(self, message, type):
        self.msg.setText(message)
        if type == 'critical':
            self.msg.setIcon(QMessageBox.Critical)
        if type == 'information':
            self.msg.setIcon(QMessageBox.Information)
        x = self.msg.exec_()  # this will show our messagebox

    def check_if_email_valid(self, email):
        result = email.find('@')
        result2 = email.find('.')
        if result > -1 and result2 > -1:
            atsakymas = True
        else:
            atsakymas = False
        return atsakymas

    def on_click_istrinti_button(self):
        global sekamos_valiutos
        sekamos_valiutos.pop(einama_eilute)
        with open('sekamos_valiutos.pkl', 'wb') as pickle_out:
            pickle.dump(sekamos_valiutos, pickle_out)
        self.atnaujinti_lentele()
        atnaujinti_tabus()
        self.show_message("Duomenys sėkmingai ištrinti", 'information')

    def atnaujinti_grafikus(self):
        global laikas
        if laikas==0:
            qw.myMessage.setText(f" Atnaujinami duomenys ")
            valiutos_duomenys = []
            global axs_dic
            global plots
            for key in plots:
                currency = key.split()[0]

                df = get_crypto_data(currency)

                if key.split()[1] == 'Candelstics':
                    plots[key].update_data(df[['Date', 'HA_Open', 'HA_Close', 'HA_High', 'HA_Low']])
                if key.split()[1] == 'Ema':
                    plots[key].update_data(df[['Date', 'EMA_200']])
                if key.split()[1] == 'Close':
                    plots[key].update_data(df[['Date', 'Close']])
                if key.split()[1] == 'Rsi':
                    plots[key].update_data(df[['Date', 'rsi']])

            a = 0

            for q in sekamos_valiutos:
                sutrumpinti_rezultatai = []
                df = get_crypto_data(q[0])
                lst_row = df.tail(1)

                close_value = lst_row['Close'].values

                rsi_value = lst_row['rsi'].values
                ema_200_value = lst_row['EMA_200'].values

                self.table.setItem(a, 5, QTableWidgetItem(str(close_value[0])))
                self.table.setItem(a, 6, QTableWidgetItem(str(rsi_value[0])))
                self.table.setItem(a, 7, QTableWidgetItem(str(ema_200_value[0])))
                sutrumpinti_rezultatai = [close_value[0], rsi_value[0], ema_200_value[0]]
                self.ar_reikia_informuoti(sutrumpinti_rezultatai, q)
                a += 1
                laikas=30

        else:
            laikas-=1
            qw.myMessage.setText(f"Iki atnaujinimo liko {laikas} s ")


    def ar_reikia_informuoti(self, sutrumpinti_rezultatai, valiutos_duomenys):
        global flag

        valiuta = valiutos_duomenys[0]
        el_pastas = valiutos_duomenys[2]
        pirkimas = float(valiutos_duomenys[3])
        pardavimas = float(valiutos_duomenys[4])

        close = sutrumpinti_rezultatai[0]
        rsi = sutrumpinti_rezultatai[1]
        ema_200 = sutrumpinti_rezultatai[2]

        if valiutos_duomenys[1] == 'Pagal_RSI':
            if rsi < pirkimas:
                if flag[valiuta] == 0 or flag[valiuta] == -1:
                    self.send_email(el_pastas, 1, valiuta, close)
                    flag[valiuta] = 1

            if rsi > pardavimas:
                if flag[valiuta] == 0 or flag[valiuta] == 1:
                    self.send_email(el_pastas, -1, valiuta, close)

                flag[valiuta] = -1
        if valiutos_duomenys[1] == 'Pagal_kaina':
            if close < pirkimas:
                if flag[valiuta] == 0 or flag[valiuta] == -1:
                    self.send_email(el_pastas, 1, valiuta, close)
                    flag[valiuta] = 1

            if close > pardavimas:
                if flag[valiuta] == 0 or flag[valiuta] == 1:
                    self.send_email(el_pastas, -1, valiuta, close)
                    flag[valiuta] = -1

    def send_email(self, el_pastas, email_theme, valiuta, close):
        global sender_email
        global outgoing_server
        global port
        global password
        global context
        message_reikia_pirkti = f"""\
        Subject: Reikia pirkti {valiuta}

        Kaina {close}"""

        message_reikia_parduoti = f"""\
        Subject: Reikia parduoti {valiuta}

        Kaina {close}."""

        if email_theme == 1:
            with smtplib.SMTP_SSL(outgoing_server, port, context=context) as server:
                server.login(el_pastas, password)
                server.sendmail(sender_email, el_pastas, message_reikia_pirkti)

        if email_theme - 1:
            with smtplib.SMTP_SSL(outgoing_server, port, context=context) as server:
                server.login(el_pastas, password)
                server.sendmail(sender_email, el_pastas, message_reikia_parduoti)

    def startTimer(self):
        self.timer.start(1000)
        self.start_button.setEnabled(False)
        self.end_button.setEnabled(True)
        qw.myMessage.setText("Duomenų atnaujinimas kas 30s")
        self.show_message('Duomenų atnaujinimas pradėtas', 'information')

    def endTimer(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.end_button.setEnabled(False)
        qw.myMessage.setText("Duomenų atnaujinimas sustabdytas")
        self.show_message('Duomenų atnaujinimas sustabdytas', 'information')


def onMyToolBarButtonClick():
    global w

    if w is None:
        w = AnotherWindow(valiuta)
    else:
        w.show()


def onMyToolBarButtonClick2():
    global el_pasto_nustatymo_langas

    if el_pasto_nustatymo_langas is None:
        el_pasto_nustatymo_langas = Ui()
        el_pasto_nustatymo_langas.show()
    else:
        el_pasto_nustatymo_langas.show()


def get_crypto_data(crypto):
    q = cbpGetHistoricRates(crypto, 3600)
    df = pd.DataFrame.from_records(q, columns=['Date', 'Low', 'High', 'Open', 'Close', 'Volume'])
    df = df.astype({'Date': 'datetime64[ns]'})
    HA(df)
    ema(df, 200)
    plot_rsi(df)
    return df


class Grafikas(QGraphicsView):
    def __init__(self):
        super().__init__()

    def update(self, df, ax, ax2, curency):
        global plots

        ax.reset()  # remove previous plots
        # remove previous plots
        ax2.reset()

        candles = df[['Date', 'HA_Open', 'HA_Close', 'HA_High', 'HA_Low']]

        plot1 = fplt.candlestick_ochl(candles, ax=ax)

        plot2 = fplt.plot(df['Date'], df['EMA_200'], ax=ax, legend='ema-200')
        plot3 = fplt.plot(df['Date'], df['Close'], ax=ax, legend='Close')
        plot4 = fplt.plot(df['Date'], df['rsi'], ax=ax2, legend='RSI')
        plots[curency + ' Candelstics'] = plot1
        plots[curency + ' Ema'] = plot2
        plots[curency + ' Close'] = plot3
        plots[curency + ' Rsi'] = plot4

        fplt.set_y_range(0, 100, ax=ax2)
        fplt.add_band(30, 70, ax=ax2)
        fplt.refresh()
        lst_row = df.tail(1)

        close_value = lst_row['Close'].values
        rsi_value = lst_row['rsi'].values
        ema_200_value = lst_row['EMA_200'].values
        print(f'Close value:{close_value[0]}')
        print(f'RSI values: {rsi_value[0]}')
        print(f'EMA_200 values: {ema_200_value[0]}')
        valiutos_duomenys = [close_value[0], rsi_value[0], ema_200_value[0]]
        return valiutos_duomenys


def atnaujinti_tabus():
    global tabs
    global flag
    vaizdas = Grafikas()

    kiek_yra_tabu = tabs.count()

    for x in range(kiek_yra_tabu):
        tabs.setCurrentIndex(x)
        tabs.removeTab(tabs.currentIndex())

    for tabas in sekamos_valiutos:
        duomenys = get_crypto_data(tabas[0])
        tab1 = QWidget()
        tab_layout = QGridLayout()
        ax, ax2 = fplt.create_plot(tabas[0], rows=2)
        win.axs = [ax, ax2]  # finplot requres this property
        tab_layout.addWidget(ax.vb.win, 0, 0, 1, 2)
        tab_layout.addWidget(ax2.vb.win, 0, 0, 1, 2)
        tab1.setLayout(tab_layout)
        tabs.addTab(tab1, tabas[0])
        axs_dic[tabas[0]] = [ax, ax2]
        vaizdas.update(duomenys, ax, ax2, tabas[0])
        flag[tabas[0]] = 0
    layout.addWidget(tabs, 4, 0, 1, 2)

app = QApplication([])
qw = QMainWindow()

win = QGraphicsView()

qw.setWindowTitle('Kripto botas')

layout = QGridLayout()
win.setLayout(layout)
win.resize(600, 500)
centralwidget = win
qw.setCentralWidget(centralwidget)
qw.resize(600, 500)

valiuta = get_currrency_list()
w = None
el_pasto_nustatymo_langas = None
menu = qw.menuBar()
button_action = QAction("&Sekimo nustatymai")
button_action.triggered.connect(onMyToolBarButtonClick)

button_action2 = QAction("&El_pasto nustatymai")
button_action2.triggered.connect(onMyToolBarButtonClick2)

file_menu = menu.addMenu("&Nustatymai")
file_menu.addAction(button_action)
file_menu.addAction(button_action2)
file_menu.addSeparator()

qw.myMessage = QtWidgets.QLabel()
qw.myMessage.setText("Pasirušęs")
qw.statusBar().addWidget(qw.myMessage)

tabs = QTabWidget()
tabs.resize(300, 200)
atnaujinti_tabus()

fplt.show(qt_exec=False)
qw.show()
win.show()

app.exec_()
