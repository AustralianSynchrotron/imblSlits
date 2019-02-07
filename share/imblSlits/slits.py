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



class QRectF(QtCore.QRectF) :
  def __mul__(self,flt):
    return QRectF(self.x()*flt, self.y()*flt, self.width()*flt, self.height()*flt)
  __rmul__ = __mul__
  def __truediv__(self,flt):
    return QRectF(self.x()/flt, self.y()/flt, self.width()/flt, self.height()/flt)
  def __str__(self):
    return "%f x %f %+f %+f" % (self.width(), self.height(), self.center().x(), self.center().y() )


class MR(Enum) :
  HP = auto()
  VP = auto()
  HS = auto()
  VS = auto()
  LF = auto()
  RT = auto()
  TP = auto()
  BT = auto()



def pos2pos(pos, strict=False) :

  fpos = {}

  def badin(rol) :
    return rol in pos and pos[rol] != fpos[rol] and strict

  if MR.BT in pos or MR.TP in pos :
    if MR.BT not in pos or MR.TP not in pos :
      return None
    fpos[MR.BT] = pos[MR.BT]
    fpos[MR.TP] = pos[MR.TP]
    fpos[MR.VP] = pos[MR.TP]/2 - pos[MR.BT]/2
    fpos[MR.VS] = pos[MR.TP] + pos[MR.BT]
    if badin(MR.VP) or badin(MR.VS) :
      return None

  if MR.VP in pos or MR.VS in pos :
    if MR.VP not in pos or MR.VS not in pos :
      return None
    fpos[MR.BT] = pos[MR.VS]/2 + pos[MR.VP]
    fpos[MR.TP] = pos[MR.VS]/2 - pos[MR.VP]
    fpos[MR.VP] = pos[MR.VP]
    fpos[MR.VS] = pos[MR.VS]
    if badin(MR.BT) or badin(MR.TP) :
      return None

  if MR.LF in pos or MR.RT in pos :
    if MR.LF not in pos or MR.RT not in pos :
      return None
    fpos[MR.RT] = pos[MR.RT]
    fpos[MR.LF] = pos[MR.LF]
    fpos[MR.HP] = pos[MR.RT]/2 - pos[MR.LF]/2
    fpos[MR.HS] = pos[MR.RT] + pos[MR.LF]
    if badin(MR.HP) or badin(MR.HS) :
      return None

  if MR.HP in pos or MR.HS in pos :
    if MR.HP not in pos or MR.HS not in pos :
      return None
    fpos[MR.RT] = pos[MR.HS]/2 + pos[MR.HP]
    fpos[MR.LF] = pos[MR.HS]/2 - pos[MR.HP]
    fpos[MR.HP] = pos[MR.HP]
    fpos[MR.HS] = pos[MR.HS]
    if badin(MR.RT) or badin(MR.LF) :
      return None

  return fpos


def pos2rct(pos) :
  pos = pos2pos(pos)
  return QRectF(pos[MR.HP] - pos[MR.HS]/2,
                pos[MR.VP] - pos[MR.VS]/2,
                pos[MR.HS],
                pos[MR.VS])

def rct2pos(rct) :
  return {MR.BT : -rct.top(),
          MR.TP :  rct.bottom(),
          MR.LF : -rct.left(),
          MR.RT :  rct.right(),
          MR.HS :  rct.width(),
          MR.HP :  rct.center().x(),
          MR.VS :  rct.height(),
          MR.VP :  rct.center().y()}



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
    geom = self.parent().rectGLV() if self.parent().isMoving else self.parent().rectDRV()
    painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(227,121,38)), 0))
    painter.drawRect(geom)
    #def printRect(recf) :
    #  print("%f x %f %+f %+f" % (recf.width(), recf.height(),
    #                             recf.center().x(), recf.center().y() ) )


    # read back geometry
    geom = self.parent().rectRBV()
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
  willMoveNow       = pyqtSignal(QRectF, dict) #abs and rel


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
    self.motGeom = QRectF()
    self.drivers = {}
    for rol in MR :
      drv = eval('self.ui.d'+rol.name)
      self.drivers[rol] = drv
      drv.vChng.connect(self.synchDrivers)
      drv.goToP.connect(self.onMoveOrder)

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


  def _motorsRectF(self, rbv=True) :
    if not len(self.motors) :
      return self.motGeom
    pos = {}
    for rol, mot in self.motors.items() :
      ps = mot.getUserPosition() if rbv else mot.getUserGoal()
      pos[rol] = ps
      if rol in (MR.BT, MR.TP, MR.VP) :
        pos[rol] -= self.base
    return pos2rct(pos)/self.dist


  def rectRBV(self) :
    return self._motorsRectF(True)


  def rectGLV(self) :
    return self._motorsRectF(False)


  def rectDRV(self) :
    pos = { rol : drv.pos() for rol, drv in self.drivers.items() }
    return pos2rct(pos)/self.dist


  def setPositions(self, rf):
    posS = rct2pos(rf)
    for rol, drv in self.drivers.items() :
      drv.setPos(self.dist * posS[rol])
    self.motGeom = self.rectDRV()
    self.changedGeometry.emit()


  @pyqtSlot(float)
  def setBase(self, base) :
    self.base = base
    self.onPositionChange()


  @pyqtSlot(float)
  def setDistance(self, dist) :
    oldDrvs = self.rectDRV()
    self.dist = dist
    self.setPositions(oldDrvs)


  @pyqtSlot()
  def onPositionChange(self):
    drvP = self.rectRBV() if self.isMoving else self.rectGLV()
    self.setPositions(drvP)


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
  def onMoveOrder(self, absORrel=None):

    orig = rct2pos(self.rectRBV())
    dest = {}
    if not absORrel: # self-induced motion
      dest = rct2pos(self.rectDRV())
    elif isinstance(absORrel, QRectF): # absolute
      dest = rct2pos(absORrel)
    elif isinstance(absORrel, dict): # relative
      dest = { rol : orig[rol] + absORrel[rol] for rol in MR }
    else : # should never happen
      return

    shft = { rol : dest[rol] - orig[rol] for rol in MR }
    self.willMoveNow.emit(pos2rct(dest), shft)

    if not len(self.motors) :
      self.motGeom = pos2rct(dest)
    else :
      for rol, mot in self.motors.items() :
        mot.goUserPosition(dest[rol])
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













