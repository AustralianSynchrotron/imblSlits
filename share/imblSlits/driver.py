import sys, os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi

execPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

class Driver(QWidget) :
  
  goNeg = pyqtSignal()
  goPos = pyqtSignal()
  goToP = pyqtSignal(float)
  
  def __init__(self, parent):
    super(QWidget, self).__init__(parent)
    self.ui = loadUi(execPath + 'driver.ui', self)
    self.ui.negative.clicked.connect(self.goNeg)
    self.ui.positive.clicked.connect(self.goPos)
    @pyqtSlot()
    def onEditingFinished() :
      self.goToP.emit(self.ui.position.value())
    self.ui.position.editingFinished.connect(onEditingFinished)
    
