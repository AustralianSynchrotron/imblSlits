import sys, os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, QRectF, pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi
from enum import Enum, auto

from qcamotorgui import QCaMotorGUI

filePath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

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
    self.ui = loadUi(filePath + 'slits.ui', self)
    # ↔↕⇔⇕
    self.ui.dHP.label.setText('↔ position')
    self.ui.dVP.label.setText('↕ position')
    self.ui.dHS.label.setText('↔ size')
    self.ui.dVS.label.setText('↕ size')
    self.ui.dLF.label.setText('left')
    self.ui.dRT.label.setText('right')
    self.ui.dTP.label.setText('top')
    self.ui.dBT.label.setText('bottom')

    minDriverWidth = self.ui.stepWidget.sizeHint().width()
    for drv in self.ui.findChildren(Driver):
      drv.setMinimumWidth(minDriverWidth)
    minSide = min(minDriverWidth, self.ui.dVP.sizeHint().height())
    self.ui.face.setMinimumSize(minSide, minSide)


    self.ui.sizeLabel.setStyleSheet('image: url(' + filePath + 'labplot-auto-scale-all.svg);')
    self.ui.positionLabel.setStyleSheet('image: url(' + filePath + 'labplot-transform-move.svg);')

    self.isMoving = False
    self.isConnected = False
    self.isOnLimit = False
    self.geometry = QRectF()
    self.motors = {}
    self.dirvers = { self.MotoRole.HP : self.ui.dHP,
                     self.MotoRole.HS : self.ui.dHS,
                     self.MotoRole.VP : self.ui.dVP,
                     self.MotoRole.VS : self.ui.dVS,
                     self.MotoRole.LF : self.ui.dLF,
                     self.MotoRole.RT : self.ui.dRT,
                     self.MotoRole.TP : self.ui.dTP,
                     self.MotoRole.BT : self.ui.dBT }

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







