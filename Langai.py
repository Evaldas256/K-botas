from PyQt5 import QtWidgets, uic
import sys
import pickle
from PyQt5.QtWidgets import (QApplication, QComboBox, QGridLayout,QMessageBox,
                             QLabel, QLineEdit,
                             QTableWidgetItem,
                             QWidget)
class Ui(QtWidgets.QDialog):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('el_pasto_nustatymo_langas.ui', self) # Load the .ui file
        self.okButton.clicked.connect(self.issaugoti_nustatymus)
        self.cancelButton.clicked.connect(self.iseiti_is_formos)
        self.msg = QMessageBox()
        self.msg.setWindowTitle("Kripto botas")
        try:
            with open('el_pasto_duomenys.pkl', 'rb') as pickle_in:
                self.el_pasto_duomenys = pickle.load(pickle_in)
                self.email_lineEdit.setText(self.el_pasto_duomenys[0])
                self.password_lineEdit.setText(self.el_pasto_duomenys[1])
                self.outgoing_server_lineEdit.setText(self.el_pasto_duomenys[2])
                self.port_lineEdit.setText(self.el_pasto_duomenys[3])
        except:
            self.email_lineEdit.setText('')
            self.password_lineEdit.setText('')
            self.outgoing_server_lineEdit.setText('')
            self.port_lineEdit.setText('')

    def iseiti_is_formos(self):
        self.close()
    def issaugoti_nustatymus(self):
        self.el_pastas=self.email_lineEdit.text()
        if self.check_if_email_valid(self.el_pastas)==False:
            self.show_message('Neteisinngas el_pašto formatas','critical')
            return
        self.slaptazodis=self.password_lineEdit.text()
        self.iseinantis_serveris=self.outgoing_server_lineEdit.text()
        self.portas=self.port_lineEdit.text()
        if self.check_if_port_valid(self.portas)==False:
            self.show_message('Porto numeris netinkamo formato arba reikšmės', 'critical')
            return
        self.el_pasto_duomenys=[self.el_pastas,self.slaptazodis,self.iseinantis_serveris,self.portas]
        with open('el_pasto_duomenys.pkl', 'wb') as pickle_out:
            pickle.dump(self.el_pasto_duomenys, pickle_out)
        self.show_message('Duomenys sėkmingai išsaugoti','information')
    def show_message(self,message,type):
        self.msg.setText(message)
        if type=='critical':
            self.msg.setIcon(QMessageBox.Critical)
        if type=='information':
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
    def check_if_port_valid (self,port):
        atsakymas=False
        try:
            portas=int(port)
            if portas>=0 and portas<=65536:
                atsakymas=True
        except:
            atsakymas=False
        return atsakymas