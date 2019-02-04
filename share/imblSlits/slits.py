import sys, os, copy
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QRectF, QLineF
from PyQt5.QtGui import  QPen, QBrush, QColor
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


class Face(QWidget):

  def __init__(self, parent):
    super(Face, self).__init__(parent)
    lyt = QtWidgets.QVBoxLayout(self)
    lyt.setContentsMargins(0, 0, 0, 0)
    lyt.setSpacing(0)
    self.labImg = QtWidgets.QLabel(self)
    lyt.addWidget(self.labImg)
    self.labTxt = QtWidgets.QLabel(self)
    szpol = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self.labTxt.setSizePolicy(szpol)
    lyt.addWidget(self.labTxt)
    lyt.setAlignment(self.labTxt, QtCore.Qt.AlignHCenter)

  def set(self, image, text):
    self.labImg.setStyleSheet('image: url(' + image + ');')
    self.labTxt.setText(text)


class BeamGeometry() :

  def  __init__(self):
    self.hp = 0
    self.hs = 0
    self.vp = 0
    self.vs = 0
    self.base = 0

  def getGeom(self, rol) :
    if   rol is MotoRole.BT :
      return self.vs/2 - self.vp
    elif rol is MotoRole.TP :
      return self.vs/2 + self.vp
    elif rol is MotoRole.LF :
      return self.hs/2 - self.hp
    elif rol is MotoRole.RT :
      return self.hs/2 + self.hp
    elif rol is MotoRole.HS :
      return self.hs
    elif rol is MotoRole.HP :
      return self.hp
    elif rol is MotoRole.VS :
      return self.vs
    elif rol is MotoRole.VP :
      return self.vp

  def setMot(self, rol, pos):
    if   rol is MotoRole.BT :
      tpo = self.getGeom(MotoRole.TP)
      self.vp = (tpo - pos)/2 - self.base
      self.vs = tpo + pos
    elif rol is MotoRole.TP :
      bto = self.getGeom(MotoRole.BT)
      self.vp = (pos - bto) / 2 - self.base
      self.vs = pos + bto
    elif rol is MotoRole.LF :
      rto = self.getGeom(MotoRole.RT)
      self.hp = (rto - pos)/2
      self.hs = rto + pos
    elif rol is MotoRole.RT :
      lfo = self.getGeom(MotoRole.LF)
      self.hp = (pos - lfo) / 2
      self.hs = pos + lfo
    elif rol is MotoRole.HS :
      self.hs = pos
    elif rol is MotoRole.HP :
      self.hp = pos
    elif rol is MotoRole.VS :
      self.vs = pos
    elif rol is MotoRole.VP :
      self.vp = pos - self.base

  def getMot(self, rol):
    if rol in [ MotoRole.BT, MotoRole.TP, MotoRole.VP ] :
      return self.getGeom(rol) + self.base
    else :
      return self.getGeom(rol)

  def scaled(self, scale=1) :
    newGeom = BeamGeometry()
    newGeom.hp = scale * self.hp
    newGeom.hs = scale * self.hs
    newGeom.vp = scale * self.vp
    newGeom.vs = scale * self.vs
    newGeom.base = self.base
    return newGeom



class SlitsVis(QWidget) :
  beamVw = 4.85714
  beamVh = 0.28571

  def __init__(self, parent):
    super(SlitsVis, self).__init__(parent) # parent is supposed to be Slits
    self.setMinimumWidth(100)
    self.setMinimumHeight( self.minimumWidth() * self.beamVh / self.beamVw );
    szpol = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored);
    szpol.setHeightForWidth(True);
    self.setSizePolicy(szpol);


  def heightForWidth(self, w) :
    return w * self.beamVh / self.beamVw


  def paintEvent(self, event):


    fw = self.beamVw
    fh = self.beamVh
    fw2 = fw/2.0
    fh2 = fh/2.0

    painter = QtGui.QPainter(self)

    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.translate( self.width()/2.0 , self.height()/2.0)
    scale = self.height() / fh \
            if self.width() / self.height() > fw/fh else \
            self.width() / fw
    painter.scale(scale, -scale)

    # beam
    #painter.drawRect(QRectF(-fw2, -fh2, fw, fh));

    # coordinates
    painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0,0,0)), 0, QtCore.Qt.DotLine))
    painter.drawLine(QtCore.QLineF(-fw2,0,fw2,0))
    painter.drawLine(QtCore.QLineF(0,-fh2,0,fh2))

    geom = self.parent().geometry.scaled(1/self.parent().distance)

    # slits box
    painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(227,121,38)), 0))
    painter.drawRect(QRectF(-geom.getGeom(MotoRole.LF), -geom.getGeom(MotoRole.BT),
                             geom.getGeom(MotoRole.HS),  geom.getGeom(MotoRole.VS) ))

    painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(227,121,38,50)), 0))
    painter.setBrush(QColor(227,121,38,50))
    painter.drawRect(QRectF(-fw2, -fh2, fw, fh2 - geom.getGeom(MotoRole.BT) ) ) # bottom
    painter.drawRect(QRectF(-fw2,  fh2, fw, geom.getGeom(MotoRole.TP) - fh2 ) ) # top
    painter.drawRect(QRectF(-fw2, -fh2, fw2 - geom.getGeom(MotoRole.LF), fh ) ) # left
    painter.drawRect(QRectF( fw2, -fh2, geom.getGeom(MotoRole.RT) - fw2, fh ) ) # right


class Slits(QWidget) :

  warnSS='background-color: rgb(128, 0, 0);'

  changedMotion     = pyqtSignal(bool)
  changedConnection = pyqtSignal(bool)
  changedLimits     = pyqtSignal(bool)
  changedGeometry   = pyqtSignal(BeamGeometry)

  def __init__(self, parent):
    super(Slits, self).__init__(parent)
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

    self.distance = 1
    self.isMoving = False
    self.isConnected = False
    self.isOnLimit = False
    self.geometry = BeamGeometry()
    self.motors = {}
    self.drivers = {}
    for rol in list(MotoRole) :
      exec('self.drivers[MotoRole.'+rol.name+'] = self.ui.d'+rol.name)

    self.ui.stack.lock(True)
    self.ui.stack.hide()
    self.ui.showStack.hide()
    self.ui.lineBot.hide()
    self.ui.showStack.toggled.connect(self.ui.stack.setVisible)
    self.ui.showStack.toggled.connect(self.ui.spacer.setHidden)

    self.ui.limitW.hide()
    self.ui.linkW.hide()

    self.ui.changedGeometry.connect(self.ui.visual.update)


  def setMotors(self, motorsDictionary={}) :

    if len(self.motors) :
      print('slits error: redefinition of the motors.')
      return
    if not len(motorsDictionary) :
      return

    for motoRole, motoPV in motorsDictionary.items() :
      mot = self.ui.stack.addMotor(motoPV).motor()
      mot.changedMoving       .connect(self.onStatusChange)
      mot.changedConnected    .connect(self.onStatusChange)
      mot.changedHiLimitStatus.connect(self.onStatusChange)
      mot.changedHiLimitStatus.connect(self.drivers[motoRole].setHiLimit)
      mot.changedLoLimitStatus.connect(self.onStatusChange)
      mot.changedLoLimitStatus.connect(self.drivers[motoRole].setLoLimit)
      mot.changedUserPosition .connect(self.onPositionChange)
      self.ui.stop.clicked.connect(mot.stop)
      self.motors[motoRole] = mot

    self.ui.showStack.setVisible(len(self.motors))
    self.ui.lineBot.setVisible(len(self.motors))
    self.onStatusChange()


  @pyqtSlot(float)
  def setBase(self, base) :
    self.geometry.vp -= base - self.geometry.base
    self.geometry.base = base
    self.onPositionChange()
    for rol in self.drivers.keys() :
      self.drivers[rol].setPosition(self.geometry.getGeom(rol))
    self.changedGeometry.emit(self.geometry)


  @pyqtSlot()
  def onPositionChange(self):
    newGeometry = self.geometry.scaled()
    for rol in self.motors.keys() :
      pos = self.motors[rol].getUserPosition()
      newGeometry.setMot(rol, pos)
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





