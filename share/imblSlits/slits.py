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




class SlitsVis(QWidget) :

  beamVw = 4.85714
  beamVh = 0.28571

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
    geom = self.parent().rectGLV(True) if self.parent().isMoving else self.parent().rectDRV(True)
    painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(227,121,38)), 0))
    painter.drawRect(geom)
    #def printRect(recf) :
    #  print("%f x %f %+f %+f" % (recf.width(), recf.height(),
    #                             recf.center().x(), recf.center().y() ) )


    # read back geometry
    geom = self.parent().rectRBV(True)
    painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(227,121,38,50)), 0))
    painter.setBrush(QColor(227,121,38,50))
    painter.drawRect(QRectF(-fw2, geom.bottom() , fw, fh2 - geom.bottom() ) ) # top
    painter.drawRect(QRectF(-fw2, geom.top(), fw, geom.top() - fh2 ) ) # bot
    painter.drawRect(QRectF(-fw2, -fh2, fw2 + geom.left(), fh ) ) # left
    painter.drawRect(QRectF( fw2, -fh2, geom.right() - fw2, fh ) ) # right


class Slits(QWidget) :

  warnSS='background-color: rgb(128, 0, 0);'

  changedMotion     = pyqtSignal(bool)
  changedConnection = pyqtSignal(bool)
  changedLimits     = pyqtSignal(bool)
  changedGeometry   = pyqtSignal()

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

    minDriverWidth = self.ui.stepWidget.sizeHint().width()
    for drv in self.ui.findChildren(Driver):
      drv.setMinimumWidth(minDriverWidth)
    minSide = min(minDriverWidth, self.ui.dVP.sizeHint().height())
    self.ui.face.setMinimumSize(minSide, minSide)

    self.ui.sizeLabel.setStyleSheet('image: url(' + filePath + 'labplot-auto-scale-all.svg);')
    self.ui.positionLabel.setStyleSheet('image: url(' + filePath + 'labplot-transform-move.svg);')

    self.dist = 1
    self.base = 0
    self.isMoving = False
    self.isConnected = False
    self.isOnLimit = False
    self.motors = {}
    self.drivers = {}
    for rol in MotoRole :
      exec('self.drivers[rol] = self.ui.d'+rol.name)
      self.drivers[rol].vChng.connect(self.synchDrivers)

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
      mot.changedUserGoal     .connect(self.onPositionChange)
      self.ui.stop.clicked.connect(mot.stop)
      self.motors[motoRole] = mot

    self.ui.showStack.setVisible(len(self.motors))
    self.ui.lineBot.setVisible(len(self.motors))
    self.onStatusChange()


  @pyqtSlot(float)
  def setBase(self, base) :
    self.base = base
    self.onPositionChange()


  @pyqtSlot()
  def onPositionChange(self):
    drvP = self.rectRBV() if self.isMoving else self.rectGLV()
    posS = self.position(drvP)
    for rol, drv in self.drivers.items() :
      drv.setPos(posS[rol])
    self.changedGeometry.emit()


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
        step = max(mot.getStep() for mot in self.motors.values())
        self.ui.step.setValue(step)
      self.changedConnection.emit(self.isConnected)

    if newMoving != self.isMoving :
      self.isMoving = newMoving
      self.ui.stop.setEnabled(self.isMoving)
      self.ui.stop.setStyleSheet(self.warnSS if self.isMoving else '')
      self.changedMotion.emit(self.isMoving)
      self.update()

    if newOnLimit != self.isOnLimit :
      self.isOnLimit = newOnLimit
      self.ui.limitW.setVisible(self.isOnLimit)
      self.changedLimits.emit(self.isOnLimit)


  @pyqtSlot()
  def synchDrivers(self):

    drv = self.sender()
    if drv not in self.drivers.values() :
      return
    rol = [rl for rl,dr in self.drivers.items() if dr == drv][0]

    if   rol == MotoRole.BT or rol == MotoRole.TP:
      tp, bt = self.drivers[MotoRole.TP].pos(), self.drivers[MotoRole.BT].pos()
      self.drivers[MotoRole.VS].setPos(tp + bt, True)
      self.drivers[MotoRole.VP].setPos(tp/2 - bt/2, True)
    elif rol == MotoRole.VS or rol == MotoRole.VP:
      vs, vp = self.drivers[MotoRole.VS].pos(), self.drivers[MotoRole.VP].pos()
      self.drivers[MotoRole.TP].setPos(vs/2 + vp/2, True)
      self.drivers[MotoRole.BT].setPos(vs/2 - vp/2, True)
    elif rol == MotoRole.LF or rol == MotoRole.RT:
      lf, rt = self.drivers[MotoRole.LF].pos(), self.drivers[MotoRole.RT].pos()
      self.drivers[MotoRole.HS].setPos(rt+lf, True)
      self.drivers[MotoRole.HP].setPos(rt/2 - lf/2, True)
    elif rol == MotoRole.HS or rol == MotoRole.HP:
      hs, hp = self.drivers[MotoRole.HS].pos(), self.drivers[MotoRole.HP].pos()
      self.drivers[MotoRole.RT].setPos(hs/2 + hp/2, True)
      self.drivers[MotoRole.LF].setPos(hs/2 - hp/2, True)

    self.ui.visual.update()


  def _motorsRectF(self, rbv=True, norm=False) :
    hp = hs = vp = vs = 0
    for rol, mot in self.motors.items() :
      pos = mot.getUserPosition() if rbv else mot.getUserGoal()
      if   rol is MotoRole.BT :
        tpo = vs/2 + vp
        vp = (tpo - pos)/2 - self.base
        vs = tpo + pos
      elif rol is MotoRole.TP :
        bto = vs/2 - vp
        vp = (pos - bto) / 2 - self.base
        vs = pos + bto
      elif rol is MotoRole.LF :
        rto = hs/2 + hp
        hp = (rto - pos)/2
        hs = rto + pos
      elif rol is MotoRole.RT :
        lfo = hs/2 - hp
        hp = (pos - lfo) / 2
        hs = pos + lfo
      elif rol is MotoRole.HS :
        hs = pos
      elif rol is MotoRole.HP :
        hp = pos
      elif rol is MotoRole.VS :
        vs = pos
      elif rol is MotoRole.VP :
        vp = pos - self.base
    if norm :
      (hp, hs, vp, vs) = [x/self.dist for x in (hp, hs, vp, vs)]
    return QRectF(hp-hs/2, vp-vs/2, hs, vs)


  def rectRBV(self, norm=False) :
    return self._motorsRectF(True, norm)


  def rectGLV(self, norm=False) :
    return self._motorsRectF(False, norm)


  def rectDRV(self, norm=False) :
    scl = 1/self.dist if norm else 1
    return QRectF(-scl*self.drivers[MotoRole.LF].pos(), -scl*self.drivers[MotoRole.BT].pos(),
                   scl*self.drivers[MotoRole.HS].pos(),  scl*self.drivers[MotoRole.VS].pos())


  def position(self, rf, rol=None, norm=False) :
    ret = 0

    if rol is None :
      positions = {}
      for rl in MotoRole :
        positions[rl] = self.position(rf, rl, norm)
      return positions

    elif rol is MotoRole.BT :
      ret = -rf.top()
    elif rol is MotoRole.TP :
      ret = rf.bottom()
    elif rol is MotoRole.LF :
      ret = -rf.left()
    elif rol is MotoRole.RT :
      ret = rf.right()
    elif rol is MotoRole.HS :
      ret = rf.width()
    elif rol is MotoRole.HP :
      ret = rf.center().x()
    elif rol is MotoRole.VS :
      ret = rf.height()
    elif rol is MotoRole.VP :
      ret = rf.center().y()

    if norm :
      ret *= self.dist
    return ret










