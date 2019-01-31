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

  warnSS='background-color: rgb(128, 0, 0);'

  def __init__(self, parent):
    super(QWidget, self).__init__(parent)
    self.ui = loadUi(execPath + 'driver.ui', self)
    self.ui.negative.clicked.connect(self.goNeg)
    self.ui.positive.clicked.connect(self.goPos)
    @pyqtSlot()
    def onEditingFinished() :
      self.goToP.emit(self.ui.position.value())
    self.ui.position.editingFinished.connect(onEditingFinished)

  @pyqtSlot(bool)
  def setHiLimit(self, lms) :
    self.ui.positive.setStyleSheet(self.warnSS if lms else '')

  @pyqtSlot(bool)
  def setLoLimit(self, lms) :
    self.ui.negative.setStyleSheet(self.warnSS if lms else '')

  @pyqtSlot(bool)
  def setMoving(self, mvs) :
    self.ui.position.setStyleSheet(self.warnSS if lms else '')

  @pyqtSlot(float)
  def setPosition(self, pos) :
    self.ui.position.setValue(pos)



