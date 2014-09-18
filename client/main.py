import sys
from PyQt5.QtWidgets import QApplication
from GUI import GUI


app = QApplication(sys.argv)

ui = GUI('resources/gui.ui', app)

sys.exit(app.exec_())
