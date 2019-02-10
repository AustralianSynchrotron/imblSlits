import sys, os, copy
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QLineF
from PyQt5.QtGui import  QPen, QBrush, QColor
from PyQt5.uic import loadUi
from enum import Enum, auto
from qcamotorgui import QCaMotorGUI

filePath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

from driver import Driver


class MR(Enum) :
  HP = auto()
  VP = auto()
  HS = auto()
  VS = auto()
  LF = auto()
  RT = auto()
  TP = auto()
  BT = auto()



def posFill(pos) :

  if   MR.VP     in pos or MR.VS     in pos :
    if MR.VP not in pos or MR.VS not in pos :
      return False
    pos[MR.BT] = pos[MR.VS]/2 + pos[MR.VP]
    pos[MR.TP] = pos[MR.VS]/2 - pos[MR.VP]
  elif MR.BT     in pos or MR.TP     in pos :
    if MR.BT not in pos or MR.TP not in pos :
      return False
    pos[MR.VP] = pos[MR.TP]/2 - pos[MR.BT]/2
    pos[MR.VS] = pos[MR.TP]   + pos[MR.BT]

  if   MR.HP     in pos or MR.HS     in pos :
    if MR.HP not in pos or MR.HS not in pos :
      return False
    pos[MR.RT] = pos[MR.HS]/2 + pos[MR.HP]
    pos[MR.LF] = pos[MR.HS]/2 - pos[MR.HP]
  elif MR.LF     in pos or MR.RT     in pos :
    if MR.LF not in pos or MR.RT not in pos :
      return False
    pos[MR.HP] = pos[MR.RT]/2 - pos[MR.LF]/2
    pos[MR.HS] = pos[MR.RT] + pos[MR.LF]
  return True


def pos2pos(pos) :
  fpos = pos.copy()
  return fpos if posFill(fpos) else None


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




class SlitsVis(QWidget) :

  beamVw = 4.85714
  beamVh = 0.28571

  heightChanged = pyqtSignal(int)

  def __init__(self, parent):

    super(SlitsVis, self).__init__(parent) # parent is supposed to be Slits
    self.setMinimumWidth(100)
    self.setMinimumHeight( self.minimumWidth() * self.beamVh / self.beamVw )
    szpol = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
    szpol.setHeightForWidth(True)
    self.setSizePolicy(szpol)


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

    # destination geometry
    pos = self.parent().posGLV() if self.parent().isMoving else self.parent().posDRV()
    painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(227,121,38)), 0))
    painter.drawRect(QtCore.QRectF(-pos[MR.LF], -pos[MR.BT], pos[MR.HS], pos[MR.VS]))

    # read back geometry
    pos = self.parent().posRBV()
    painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(227,121,38,50)), 0))
    painter.setBrush(QColor(227,121,38,50))
    painter.drawRect(QtCore.QRectF(-fw2,  fh2, fw, pos[MR.TP] - fh2)) # top
    painter.drawRect(QtCore.QRectF(-fw2, -fh2, fw, fh2 - pos[MR.BT])) # bot
    painter.drawRect(QtCore.QRectF(-fw2, -fh2, fw2 - pos[MR.LF], fh)) # left
    painter.drawRect(QtCore.QRectF( fw2, -fh2, pos[MR.RT] - fw2, fh)) # right

    self.heightChanged.emit(self.height())


class Slits(QWidget) :

  warnSS='background-color: rgb(128, 0, 0);'

  changedMotion     = pyqtSignal(bool)
  changedConnection = pyqtSignal(bool)
  changedLimits     = pyqtSignal(bool)
  changedGeometry   = pyqtSignal()
  willMoveNow       = pyqtSignal(dict, dict) # from, to


  def __init__(self, parent):
    super(Slits, self).__init__(parent)
    self.ui = loadUi(filePath + 'slits.ui', self)

    self.ui.sd2.clicked.connect(lambda: self.ui.step.setValue(self.ui.step.value() / 2))
    self.ui.sd0.clicked.connect(lambda: self.ui.step.setValue(self.ui.step.value() / 10))
    self.ui.sm2.clicked.connect(lambda: self.ui.step.setValue(self.ui.step.value() * 2))
    self.ui.sm0.clicked.connect(lambda: self.ui.step.setValue(self.ui.step.value() * 10))

    # ↔↕⇔⇕
    self.ui.dHP.label.setText('↔ position')
    self.ui.dVP.label.setText('↕ position')
    self.ui.dHS.label.setText('↔ size')
    self.ui.dVS.label.setText('↕ size')
    self.ui.dLF.label.setText('left')
    self.ui.dRT.label.setText('right')
    self.ui.dTP.label.setText('top')
    self.ui.dBT.label.setText('bottom')

    self.ui.sizeLabel    .setStyleSheet('image: url(' + filePath + 'labplot-auto-scale-all.svg);')
    self.ui.positionLabel.setStyleSheet('image: url(' + filePath + 'labplot-transform-move.svg);')

    self.dist = 1
    self.base = 0
    self.isMoving = False
    self.isConnected = False
    self.isOnLimit = False
    self.motors = {}
    self.motGeom = {rol : 0 for rol in MR}
    self.drivers = {}
    for rol in MR:
      self.drivers[rol] = eval('self.ui.d'+rol.name)

    minDriverWidth = self.ui.stepWidget.sizeHint().width()
    minSide = min(minDriverWidth, self.ui.dVP.sizeHint().height())
    self.ui.face.setMinimumSize(minSide, minSide)

    for drv in self.drivers.values():
      drv.vChng.connect(self.synchDrivers)
      drv.goToP.connect(self.onMoveOrder)
      drv.setMinimumWidth(minDriverWidth)
      self.changedMotion.connect(drv.setDisabled)

    self.ui.stack.lock(True)
    self.ui.stack.hide()
    self.ui.showStack.hide()
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
      mot.changedUserGoal     .connect(self.onPositionChange)
      self.ui.stop.clicked.connect(mot.stop)
      self.motors[motoRole] = mot

    self.ui.showStack.setVisible(len(self.motors))
    self.onStatusChange()


  def _motorsPos(self, rbv=True) :
    if not len(self.motors) :
      return self.motGeom
    pos = {}
    for rol, mot in self.motors.items() :
      ps = mot.getUserPosition() if rbv else mot.getUserGoal()
      pos[rol] = ps/self.dist
      if rol in (MR.BT, MR.TP, MR.VP) :
        pos[rol] -= self.base/self.dist
    posFill(pos)
    return pos


  def posRBV(self) :
    return self._motorsPos(True)


  def posGLV(self) :
    return self._motorsPos(False)


  def posDRV(self) :
    return { rol : drv.pos()/self.dist for rol, drv in self.drivers.items() }


  def setPos(self, pos):
    posFill(pos)
    for rol, drv in self.drivers.items() :
      drv.setPos(self.dist * pos[rol])
    self.motGeom = self.posDRV()
    self.changedGeometry.emit()


  @pyqtSlot(float)
  def setBase(self, base) :
    self.base = base
    self.onPositionChange()


  @pyqtSlot(float)
  def setDistance(self, dist) :
    oldDrvs = self.posDRV()
    self.dist = dist
    self.setPos(oldDrvs)


  @pyqtSlot()
  def onPositionChange(self):
    drvP = self.posRBV() if self.isMoving else self.posGLV()
    self.setPos(drvP)


  @pyqtSlot()
  def onStatusChange(self, newConnected=True, newMoving=False, newLimit=False):

    if len(self.motors):
      for rol, mot in self.motors.items() :
        newConnected &= mot.isConnected()
        newMoving |= mot.isMoving()
        newLimit |= mot.getHiLimitStatus() & mot.getLoLimitStatus()

    if newConnected != self.isConnected :
      self.isConnected = newConnected
      self.setEnabled(self.isConnected)
      self.ui.linkW.setVisible(not self.isConnected)
      if self.isConnected :
        self.onPositionChange()
        step = max(mot.getStep() for mot in self.motors.values())
        self.ui.step.setValue(step)
      self.changedConnection.emit(self.isConnected)

    if newMoving != self.isMoving :
      self.isMoving = newMoving
      self.ui.stop.setEnabled(self.isMoving)
      self.ui.stop.setStyleSheet(self.warnSS if self.isMoving else '')
      self.changedMotion.emit(self.isMoving)
      self.update()

    if newLimit != self.isOnLimit :
      self.isOnLimit = newLimit
      self.ui.limitW.setVisible(self.isOnLimit)
      self.changedLimits.emit(self.isOnLimit)


  @pyqtSlot()
  def onMoveOrder(self, dest=None):
    orig = self.posRBV()
    if dest is None :
      dest = self.posDRV()
    else :
      posFill(dest)
    self.willMoveNow.emit(orig, dest)
    if not len(self.motors) :
      self.motGeom = dest
    else :
      for rol, mot in self.motors.items() :
        mot.goUserPosition(dest[rol]*self.dist)
    self.changedGeometry.emit()


  @pyqtSlot()
  def synchDrivers(self):

    drv = self.sender()
    if drv not in self.drivers.values() :
      return

    rol = [rl for rl,dr in self.drivers.items() if dr == drv][0]
    if   rol == MR.BT or rol == MR.TP:
      tp, bt = self.drivers[MR.TP].pos(), self.drivers[MR.BT].pos()
      self.drivers[MR.VS].setPos(tp + bt, True)
      self.drivers[MR.VP].setPos(tp/2 - bt/2, True)
    elif rol == MR.VS or rol == MR.VP:
      vs, vp = self.drivers[MR.VS].pos(), self.drivers[MR.VP].pos()
      self.drivers[MR.TP].setPos(vs/2 + vp, True)
      self.drivers[MR.BT].setPos(vs/2 - vp, True)
    elif rol == MR.LF or rol == MR.RT:
      lf, rt = self.drivers[MR.LF].pos(), self.drivers[MR.RT].pos()
      self.drivers[MR.HS].setPos(rt+lf, True)
      self.drivers[MR.HP].setPos(rt/2 - lf/2, True)
    elif rol == MR.HS or rol == MR.HP:
      hs, hp = self.drivers[MR.HS].pos(), self.drivers[MR.HP].pos()
      self.drivers[MR.RT].setPos(hs/2 + hp, True)
      self.drivers[MR.LF].setPos(hs/2 - hp, True)

    self.changedGeometry.emit()













