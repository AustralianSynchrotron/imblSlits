import sys, os, copy
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, QRectF, QPointF, pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi
from enum import Enum, auto
from qcamotorgui import QCaMotorGUI

filePath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

from driver import Driver

class MotoRole(Enum) :
  HP = auto()
  VP = auto()
  HS = auto()
  VS = auto()
  LF = auto()
  RT = auto()
  TP = auto()
  BT = auto()

class BeamGeometry() :

  def  __init__(self):
    self.base = 0
    self.gm = QRectF()
    self.tr = {MotoRole.HP :  1,
               MotoRole.VP :  1,
               MotoRole.HS :  1,
               MotoRole.VS :  1,
               MotoRole.LF :  1,
               MotoRole.RT :  1,
               MotoRole.TP :  1,
               MotoRole.BT :  1 }

  def getGeom(self, rol) :
    ret = 0
    if   rol is MotoRole.BT :
      ret = -1 * (self.gm.top() - self.base)
    elif rol is MotoRole.TP :
      ret = self.gm.bottom() - self.base
    elif rol is MotoRole.LF :
      ret = -1 * self.gm.left()
    elif rol is MotoRole.RT :
      ret = self.gm.right()
    elif rol is MotoRole.HS :
      ret = self.gm.width()
    elif rol is MotoRole.HP :
      ret = self.gm.center().x()
    elif rol is MotoRole.VS :
      ret = self.gm.height()
    elif rol is MotoRole.VP :
      ret = self.gm.center().y() - self.base
    #return self.tr[rol] * ret
    return ret

  def setRole(self, rol, pos):
    pos *= self.tr[rol]
    if   rol is MotoRole.BT :
      self.gm.setTop(pos)
    elif rol is MotoRole.TP :
      self.gm.setBottom(pos)
    elif rol is MotoRole.LF :
      self.gm.setLeft(pos)
    elif rol is MotoRole.RT :
      self.gm.setRight(pos)
    elif rol is MotoRole.HS :
      cent = self.gm.center()
      self.gm.setWidth(pos)
      self.gm.moveCenter(cent)
    elif rol is MotoRole.HP :
      self.gm.moveCenter(QPointF(pos, self.gm.center().y()))
    elif rol is MotoRole.VS :
      cent = self.gm.center()
      self.gm.setHeight(pos)
      self.gm.moveCenter(cent)
    elif rol is MotoRole.VP :
      self.gm.moveCenter(QPointF(self.gm.center().x(), pos))


class Slits(QWidget) :

  warnSS='background-color: rgb(128, 0, 0);'

  changedMotion     = pyqtSignal(bool)
  changedConnection = pyqtSignal(bool)
  changedLimits     = pyqtSignal(bool)
  changedGeometry   = pyqtSignal(BeamGeometry)

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
    self.geometry = BeamGeometry()
    self.motors = {}
    self.drivers = { MotoRole.HP : self.ui.dHP,
                     MotoRole.HS : self.ui.dHS,
                     MotoRole.VP : self.ui.dVP,
                     MotoRole.VS : self.ui.dVS,
                     MotoRole.LF : self.ui.dLF,
                     MotoRole.RT : self.ui.dRT,
                     MotoRole.TP : self.ui.dTP,
                     MotoRole.BT : self.ui.dBT }

    self.ui.stack.lock(True)
    self.ui.stack.hide()
    self.ui.showStack.hide()
    self.ui.lineBot.hide()
    self.ui.showStack.toggled.connect(self.ui.stack.setVisible)
    self.ui.showStack.toggled.connect(self.ui.spacer.setHidden)

    self.ui.limitW.hide()
    self.ui.linkW.hide()

  def setMotors(self, motorsDictionary={}, translateMotors={}) :

    if len(self.motors) :
      print('slits error: redefinition of the motors.')
      return
    if not len(motorsDictionary) :
      return

    for motoRole, trans in translateMotors.items() :
      self.geometry.tr[motoRole] = trans

    for motoRole, motoPV in motorsDictionary.items() :
      mot = self.ui.stack.addMotor(motoPV).motor()
      mot.changedMoving       .connect(self.onStatusChange)
      mot.changedConnected    .connect(self.onStatusChange)
      mot.changedHiLimitStatus.connect(self.onStatusChange)
      mot.changedHiLimitStatus.connect(self.drivers[motoRole].setHiLimit)
      mot.changedLoLimitStatus.connect(self.onStatusChange)
      mot.changedLoLimitStatus.connect(self.drivers[motoRole].setLoLimit)
      mot.changedUserPosition .connect(self.onPositionChange)
      self.motors[motoRole] = mot

    self.ui.showStack.setVisible(len(self.motors))
    self.ui.lineBot.setVisible(len(self.motors))
    self.onStatusChange()

  @pyqtSlot(float)
  def setBase(self, base) :
    self.geometry.base = base
    self.onPositionChange()

  @pyqtSlot()
  def onPositionChange(self):
    newGeometry = copy.deepcopy(self.geometry)
    for rol in self.motors.keys() :
      pos = self.motors[rol].getUserPosition()
      newGeometry.setRole(rol, pos)
    if newGeometry != self.geometry :
      self.geometry = newGeometry
      for rol in self.drivers.keys() :
        self.drivers[rol].setPosition(self.geometry.getGeom(rol))
      self.changedGeometry.emit(self.geometry)

  @pyqtSlot()
  def onStatusChange(self):

    if not len(self.motors) :
      return

    newConnected = True
    newMoving = False
    newOnLimit = False

    for rol, mot in self.motors.items() :
      newConnected &= mot.isConnected()
      newMoving |= mot.isMoving()
      newOnLimit |= mot.getHiLimitStatus() & mot.getLoLimitStatus()

    if newConnected != self.isConnected :
      self.isConnected = newConnected
      self.setEnabled(self.isConnected)
      self.ui.linkW.setVisible(not self.isConnected)
      if self.isConnected :
        self.onPositionChange()
      self.changedConnection.emit(self.isConnected)

    if newMoving != self.isMoving :
      self.isMoving = newMoving
      self.ui.stop.setEnabled(self.isMoving)
      self.ui.stop.setStyleSheet(self.warnSS if self.isMoving else '')
      self.changedMotion.emit(self.isMoving)

    if newOnLimit != self.isOnLimit :
      self.isOnLimit = newOnLimit
      self.ui.limitW.setVisible(self.isOnLimit)
      self.changedLimits.emit(self.isOnLimit)







