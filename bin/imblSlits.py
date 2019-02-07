#!/usr/bin/env python3

import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi
from enum import Enum
import epics

binPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep
sharePath = binPath + "../share/imblSlits/"
sys.path.append(sharePath)
from slits import Slits, MR, QRectF


class SHmode(QObject):

  class Mode(Enum):
    NONE = 'Unknown'
    PINK = 'Pink'
    MONO = 'Mono'
    MRTS = 'Mrt'

  pinkPV = epics.PV('SR08ID01PSS01:HU01A_NOM_SHT_MOD_PERM_STS')
  mrtsPV = epics.PV('SR08ID01PSS01:HU01A_FST_SHT_MOD_PERM_STS')
  monoPV = epics.PV('SR08ID01PSS01:HU01A_MON_SHT_MOD_PERM_STS')

  updated = pyqtSignal(str)

  def __init__(self):
    super(SHmode, self).__init__()
    def onUpdate(**kw):
      self.updated.emit(self.mode().value)
    self.pinkPV.add_callback(onUpdate)
    self.monoPV.add_callback(onUpdate)
    self.mrtsPV.add_callback(onUpdate)

  def mode(self):
    if self.pinkPV.value == None or self.monoPV.value == None or self.mrtsPV.value == None \
       or 1 != self.pinkPV.value + self.monoPV.value + self.mrtsPV.value :
      return self.Mode.NONE
    elif self.pinkPV.value :
      return self.Mode.PINK
    elif self.monoPV.value :
      return self.Mode.MONO
    elif self.mrtsPV.value :
      return self.Mode.MRTS


class BLmode(QObject):

  class Mode(Enum):
    NONE = 'OFF'
    MOD1 = '1'
    MOD2 = '2'
    MOD3 = '3'

  m1PV = epics.PV('SR08ID01PSS01:HU01B_ENABLE_STS')
  m2PV = epics.PV('SR08ID01PSS01:HU02B_ENABLE_STS')
  m3PV = epics.PV('SR08ID01PSS01:HU03B_ENABLE_STS')

  updated = pyqtSignal(str)

  def __init__(self):
    super(BLmode, self).__init__()
    def onUpdate(**kw):
      self.updated.emit(self.mode().value)
    self.m1PV.add_callback(onUpdate)
    self.m2PV.add_callback(onUpdate)
    self.m3PV.add_callback(onUpdate)

  def mode(self):
    if self.m3PV.value :
      return self.Mode.MOD3
    elif self.m2PV.value :
      return self.Mode.MOD2
    elif self.m1PV.value :
      return self.Mode.MOD1
    else :
      return self.Mode.NONE






class MainWindow(QtWidgets.QMainWindow):

  shMode = SHmode()
  blMode = BLmode()
  slitNames = {'panda': 'HHLS',
               'baby' : 'Baby bear',
               'mama' : 'Mama bear',
               'papa' : 'Papa bear'}


  def __init__(self):

    super(MainWindow, self).__init__()
    self.ui = loadUi(sharePath + 'imblSlitsMainWindow.ui', self)
    self.ui.famWidget.hide()

    self.bears  = {}
    self.synbts = {}
    for nslt in self.slitNames.keys() :
      self.bears[nslt] = eval('self.ui.'+nslt+'Bear')
      self.synbts[nslt] = eval('self.ui.'+nslt+'Synch')

    self.ui.mashaBear.face.set(sharePath+'masha.png', 'Detector')
    for nslt, desc in self.slitNames.items() :
      self.bears[nslt].face.set(sharePath+nslt+'.png', desc)
      self.synbts[nslt].setText(desc)
      self.synbts[nslt].setIcon(QtGui.QIcon(sharePath+nslt+'.png'))

    tab = self.ui.tabWidget.tabBar()
    tab.setExpanding(True)
    for itab in range(0, tab.count()):
      slt = self.ui.tabWidget.widget(itab).findChild(Slits)
      slt.layFaceTab.layout().addWidget(slt.face)
      tab.setTabButton(itab,  QtWidgets.QTabBar.LeftSide, slt.layFaceTab)

    self.ui.pandaBear.setDistance(14)
    self.ui.pandaBear.setMotors( {MR.VP : 'SR08ID01SLW01:VPOS',
                                  MR.VS : 'SR08ID01SLW01:VOPEN',
                                  MR.LF : 'SR08ID01SLW01:RIGHT', # left/right are swapped
                                  MR.RT : 'SR08ID01SLW01:LEFT'} )

    self.ui.babyBear.setDistance(20)
    self.ui.babyBear.setMotors(  {MR.VP : 'SR08ID01SLM12:VCENTRE',
                                  MR.VS : 'SR08ID01SLM12:VSIZE',
                                  MR.HP : 'SR08ID01SLM12:HCENTRE',
                                  MR.HS : 'SR08ID01SLM12:HSIZE'} )
                                  #MR.LF : 'SR08ID01SLM12:IN',
                                  #MR.RT : 'SR08ID01SLM12:OUT',
                                  #MR.BT : 'SR08ID01SLM12:BOT',
                                  #MR.TP : 'SR08ID01SLM12:TOP'} )

    self.ui.mamaBear.setDistance(31)
    self.ui.mamaBear.setMotors(  {MR.VP : 'SR08ID01SLM21:Z',
                                  MR.VS : 'SR08ID01SLM21:ZGAP',
                                  MR.HP : 'SR08ID01SLM21:Y',
                                  MR.HS : 'SR08ID01SLM21:YGAP'} )

    self.ui.papaBear.setDistance(136)
    self.ui.papaBear.setMotors(  {MR.VP : 'SR08ID01SLM03:ZCENTRE',
                                  MR.VS : 'SR08ID01SLM03:ZGAP',
                                  MR.HP : 'SR08ID01SLM03:YCENTRE',
                                  MR.HS : 'SR08ID01SLM03:YGAP'} )

    self.ui.statusbar.addPermanentWidget(QtWidgets.QLabel('Show: ', self))
    uimode = QtWidgets.QPushButton('All', self)
    uimode.clicked.connect(self.uiModeSwap)
    self.ui.statusbar.addPermanentWidget(uimode);

    self.ui.statusbar.addPermanentWidget(QtWidgets.QWidget(), 1)

    self.ui.statusbar.addPermanentWidget(QtWidgets.QLabel('Shutter mode: ', self))
    modeLabel = QtWidgets.QLabel('...', self)
    self.shMode.updated.connect(modeLabel.setText)
    self.shMode.updated.connect(self.updateBase)
    self.ui.statusbar.addPermanentWidget(modeLabel)

    modeLabel = QtWidgets.QLabel('    ', self)
    self.ui.statusbar.addPermanentWidget(modeLabel)
    self.ui.statusbar.addPermanentWidget(QtWidgets.QLabel('Beamline mode: ', self))
    modeLabel = QtWidgets.QLabel('...', self)
    self.blMode.updated.connect(modeLabel.setText)
    self.ui.statusbar.addPermanentWidget(modeLabel)

    distances = QtWidgets.QMenu(self)
    for nslt, desc in self.slitNames.items() :
      distances.addAction(QtGui.QIcon(sharePath+nslt+'.png'), desc, self.distancePicked)
    self.ui.distances.setMenu(distances)
    self.ui.distance.valueChanged.connect(self.ui.mashaBear.setDistance)

    synchs = QtWidgets.QMenu(self)
    synchs.addAction('Seen in any', self.synchPicked)
    synchs.addAction('Seen in all', self.synchPicked)
    for nslt, desc in self.slitNames.items() :
      synchs.addAction(QtGui.QIcon(sharePath+nslt+'.png'), desc, self.synchPicked)
    self.ui.synchMasha.setMenu(synchs)

    self.blMode.updated.connect(self.initMasha)
    for slt in self.ui.findChildren(Slits) :
      slt.changedConnection.connect(self.initMasha)

    self.ui.mashaBear.willMoveNow.connect(self.onMashaMove)


  @pyqtSlot()
  def updateBase(self):
    for slit in self.ui.babyBear, self.ui.papaBear, self.ui.mashaBear :
      slit.setBase(20 if self.shMode.mode() == SHmode.Mode.MONO else 0)


  @pyqtSlot()
  def uiModeSwap(self):
    toTab = self.ui.famWidget.isVisible()
    self.ui.famWidget.setVisible(not toTab)
    self.ui.tabWidget.setVisible(toTab)
    wslt = 'Tab' if toTab else 'Fam'
    eval('self.ui.masha'+wslt).layout().addWidget(self.ui.masha)
    for nslt in self.slitNames.keys():
      eval('self.ui.'+nslt+wslt).layout().addWidget(eval('self.ui.'+nslt))
    for slt in self.ui.findChildren(Slits) :
      eval('slt.layFace'+wslt).layout().addWidget(slt.face)
    self.sender().setText('All' if toTab else 'In tabs')
    QtCore.QTimer.singleShot(0, (lambda: self.resize(self.minimumSizeHint())))


  @pyqtSlot()
  def distancePicked(self):
    sndtxt = self.sender().text().replace('&','')
    nslt = [ns for ns,desc in self.slitNames.items() if sndtxt == desc][0]
    self.ui.distance.setValue(self.bears[nslt].dist)


  @pyqtSlot()
  def synchPicked(self):
    sndtxt = self.sender().text().replace('&','')
    recf = QtCore.QRectF()
    bearL = [self.bears[ns] for ns,desc in self.slitNames.items() if sndtxt == desc]
    if len(bearL) :
      recf = bearL[0].rectDRV()
    else:
      recfS = []
      for nslt in self.slitNames.keys() :
        if self.synbts[nslt].isChecked() :
          recfS.append(self.bears[nslt].rectDRV())
      if not len(recfS) :
        return
      elif 'any' in sndtxt :
        recf.setCoords(min(rf.left() for rf in recfS), min(rf.top() for rf in recfS),
                       max( rf.right() for rf in recfS ), max( rf.bottom() for rf in recfS ) )
      elif 'all' in sndtxt :
        recf.setCoords(max(rf.left() for rf in recfS), max(rf.top() for rf in recfS),
                       min( rf.right() for rf in recfS ), min( rf.bottom() for rf in recfS ) )
      else:
        print('Error! Unknown synchPicked.')
        return
    self.ui.mashaBear.setPositions(recf)


  @pyqtSlot()
  def initMasha(self) :
    def execonmod(slt):
      if slt.isConnected:
        self.ui.distance.setValue(slt.dist)
        self.ui.mashaBear.setPositions(slt.rectDRV())
        self.ui.mashaBear.ui.step.setValue(slt.ui.step.value())
        self.mashainited = True
    if hasattr(self, 'mashainited') or self.blMode.mode() is BLmode.Mode.NONE :
      return
    elif self.blMode.mode() is BLmode.Mode.MOD1 :
      execonmod(self.ui.babyBear)
    elif self.blMode.mode() is BLmode.Mode.MOD2 :
      execonmod(self.ui.mamaBear)
    elif self.blMode.mode() is BLmode.Mode.MOD3 :
      execonmod(self.ui.papaBear)


  @pyqtSlot(QRectF, dict)
  def onMashaMove(self, abs, rel) :
    for nslt in self.slitNames.keys() :
      if self.synbts[nslt].isChecked() :
        self.bears[nslt].onMoveOrder(rel)





app = QtWidgets.QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
