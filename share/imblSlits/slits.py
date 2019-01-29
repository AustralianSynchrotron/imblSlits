import sys, os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, QRectF, pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi
from enum import Enum, auto

from qcamotorgui import QCaMotorGUI

execPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

from driver import Driver

class Slits(QWidget) :

  class MotoRole(Enum) :
    HP = auto()
    VP = auto()
    HS = auto()
    VS = auto()
    LF = auto()
    RT = auto()
    TP = auto()
    BT = auto()

  changedMotion     = pyqtSignal(bool)
  changedConnection = pyqtSignal(bool)
  changedLimits     = pyqtSignal(bool)
  cahngedGeometry   = pyqtSignal(QRectF)

  def __init__(self, parent):
    super(QWidget, self).__init__(parent)
    self.ui = loadUi(execPath + 'slits.ui', self)
    # ↔↕⇔⇕
    self.ui.HPos.label.setText('↔ position')
    self.ui.VPos.label.setText('↕ position')
    self.ui.HSize.label.setText('↔ size')
    self.ui.VSize.label.setText('↕ size')
    self.ui.Left.label.setText('left')
    self.ui.Right.label.setText('right')
    self.ui.Top.label.setText('top')
    self.ui.Bottom.label.setText('bottom')

    minDriverWidth = self.ui.stepWidget.sizeHint().width()
    for drv in self.ui.findChildren(Driver):
      drv.setMinimumWidth(minDriverWidth)

    self.isMoving = False
    self.isConnected = False
    self.isOnLimit = False
    self.geometry = QRectF()
    self.motors = {}

    self.ui.stack.lock(True)
    self.ui.stack.hide()
    self.ui.showStack.hide()
    self.ui.lineBot.hide()
    self.ui.showStack.toggled.connect(self.ui.stack.setVisible)
    self.ui.showStack.toggled.connect(self.ui.spacer.setHidden)

  def setMotors(self, motorsDictionary={}) :

    if len(self.motors) :
      print('slits error: redefinition of the motors.')
      return
    if type(motorsDictionary) is not dict or not len(motorsDictionary) :
      return

    for motoRole in motorsDictionary.keys() :
      motoPV = motorsDictionary[motoRole]
      if type(motoRole) is self.MotoRole and \
         type(motoPV) is str and \
         len(motoPV) :
        mot = self.ui.stack.addMotor(motoPV).motor()
        mot.changedMoving       .connect(self.onStatusChange)
        mot.changedConnected    .connect(self.onStatusChange)
        mot.changedHiLimitStatus.connect(self.onStatusChange)
        mot.changedLoLimitStatus.connect(self.onStatusChange)
        #mot.changedPrecision    .connect(self.onStatusChange)
        #mot.changedUnits        .connect(self.onStatusChange)
        mot.changedUserPosition .connect(self.onPositionChange)
        self.motors[motoRole] = mot

    self.ui.showStack.setVisible(len(self.motors))
    self.ui.lineBot.setVisible(len(self.motors))

  @pyqtSlot()
  def onPositionChange(self):
    return 1

  @pyqtSlot()
  def onStatusChange(self):
    newConnected = True
    newMoving = False
    newOnLimit = False
    #maxPrec=0
    #units=''
    for mot in self.motors.values():
      newConnected &= mot.isConnected()
      newMoving |= mot.isMoving()
      newOnLimit |= mot.getHiLimitStatus() & mot.getLoLimitStatus()
      #maxPrec = max(maxPrec, mot.getPrecision())
      #newUnits = mot.getUnits()
      #if newConnected and units and newUnits != units:
      #  print('slits warning: different units on motors.')
      #units = newUnits

    if newConnected != self.isConnected :
      self.isConnected = newConnected
      self.changedConnection.emit(self.isConnected)
    if newMoving != self.isMoving :
      self.isMoving = newMoving
      self.changedMotion.emit(self.isMoving)
    if newOnLimit != self.isOnLimit :
      self.isOnLimit = newOnLimit
      self.changedLimits.emit(self.isOnLimit)
    #if self.ui.step.decimals() != maxPrec :
    #  self.ui.step.setDecimals(maxPrec)
    #  for drv in self.ui.findChildren(Driver):
    #    drv.position.setDecimals(maxPrec)
    #if self.ui.step.suffix() != units :
    #  self.ui.step.setSuffix(units)
    #  for drv in self.ui.findChildren(Driver):
    #    drv.position.setSuffix(units)







