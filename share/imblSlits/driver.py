import sys, os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi

execPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

class Driver(QWidget) :

  goToP = pyqtSignal(float)
  vChng = pyqtSignal(float)

  warnSS='background-color: rgb(128, 0, 0);'

  def __init__(self, parent):
    super(Driver, self).__init__(parent)
    self.ui = loadUi(execPath + 'driver.ui', self)
    self.ui.negative.clicked.connect(lambda: self.goToP.emit(self.setPos(self.pos()-self.step())))
    self.ui.positive.clicked.connect(lambda: self.goToP.emit(self.setPos(self.pos()+self.step())))
    self.ui.position.valueEdited.connect(lambda: self.goToP.emit(self.pos()))
    self.ui.position.valueChanged.connect(self.vChng)

  @pyqtSlot(bool)
  def setHiLimit(self, lms) :
    self.ui.positive.setStyleSheet(self.warnSS if lms else '')

  @pyqtSlot(bool)
  def setLoLimit(self, lms) :
    self.ui.negative.setStyleSheet(self.warnSS if lms else '')

  @pyqtSlot(bool)
  def setMoving(self, mvs) :
    self.ui.position.setStyleSheet(self.warnSS if mvs else '')

  @pyqtSlot(float)
  def setPos(self, pos, blockSignal=False) :
    self.ui.position.blockSignals(blockSignal)
    self.ui.position.setValue(pos)
    self.ui.position.blockSignals(False)
    return self.pos()

  def pos(self) :
    return self.ui.position.value()

  def step(self) :
    return self.parent().ui.step.value()




