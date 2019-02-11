#!/usr/bin/env python3

import sys
import os
from enum import Enum
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import *
import epics

binPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep
sharePath = binPath + "../share/imblSlits/"
sys.path.append(sharePath)

from slits import Slits, MR, Face



class BLmode(QObject):

  class Encl(Enum):
    NONE = 'OFF'
    MOD1 = '1'
    MOD2 = '2'
    MOD3 = '3'

  m1PV = epics.PV('SR08ID01PSS01:HU01B_ENABLE_STS')
  m2PV = epics.PV('SR08ID01PSS01:HU02B_ENABLE_STS')
  m3PV = epics.PV('SR08ID01PSS01:HU03B_ENABLE_STS')

  class Shut(Enum):
    NONE = 'Unknown'
    PINK = 'Pink'
    MONO = 'Mono'
    MRTS = 'Mrt'

  pinkPV = epics.PV('SR08ID01PSS01:HU01A_NOM_SHT_MOD_PERM_STS')
  mrtsPV = epics.PV('SR08ID01PSS01:HU01A_FST_SHT_MOD_PERM_STS')
  monoPV = epics.PV('SR08ID01PSS01:HU01A_MON_SHT_MOD_PERM_STS')

  updated = pyqtSignal(str)


  def __init__(self):
    super(BLmode, self).__init__()

    def onUpdate(**kw):
      self.updated.emit(str(self))
    self.m1PV.add_callback(onUpdate)
    self.m2PV.add_callback(onUpdate)
    self.m3PV.add_callback(onUpdate)
    self.pinkPV.add_callback(onUpdate)
    self.monoPV.add_callback(onUpdate)
    self.mrtsPV.add_callback(onUpdate)

  def __str__(self):
    return self.encl().value+'-'+self.shut().value


  def encl(self):
    if self.m3PV.get(timeout=0) is None or \
       self.m2PV.get(timeout=0) is None or \
       self.m1PV.get(timeout=0) is None :
      return self.Encl.NONE
    elif self.m3PV.value:
      return self.Encl.MOD3
    elif self.m2PV.value:
      return self.Encl.MOD2
    elif self.m1PV.value:
      return self.Encl.MOD1
    else:
      return self.Encl.NONE


  def shut(self):
    if self.pinkPV.get(timeout=0) is None or \
       self.monoPV.get(timeout=0) is None or \
       self.mrtsPV.get(timeout=0) is None or \
       1 != self.pinkPV.value + self.monoPV.value + self.mrtsPV.value:
      return self.Shut.NONE
    elif self.pinkPV.value:
      return self.Shut.PINK
    elif self.monoPV.value:
      return self.Shut.MONO
    elif self.mrtsPV.value:
      return self.Shut.MRTS
    else:
      return self.Shut.NONE



class MainWindow(QMainWindow):

  blMode = BLmode()
  slitNames = {'panda': 'HHLS',
               'baby' : 'Baby bear',
               'mama' : 'Mama bear',
               'papa' : 'Papa bear'}


  def __init__(self):

    super(MainWindow, self).__init__()
    self.ui = loadUi(sharePath + 'imblSlits.ui', self)
    self.uiModeSwap(True)
    self.toggleConfigShow()

    self.bears = {}
    self.synbts = {}
    for nslt in self.slitNames.keys():
      self.bears[nslt] = eval('self.ui.'+nslt+'Bear')
      self.synbts[nslt] = eval('self.ui.'+nslt+'Synch')

    for nslt, desc in self.slitNames.items():
      self.bears[nslt].face.set(sharePath+nslt+'.png', desc)
      self.synbts[nslt].setText(desc)
      self.synbts[nslt].setIcon(QtGui.QIcon(sharePath+nslt+'.png'))
    self.ui.mashaBear.face.set(sharePath+'masha.png', 'Detector')
    self.ui.xrayFace.set(sharePath+'xray.png', 'Config')
    self.ui.xrayFace.setMinimumSize(self.ui.mashaBear.face.minimumSize())
    self.ui.mashaBear.visual.heightChanged.connect(
      self.ui.fakeSlitsVis.setMinimumHeight)

    tab = self.ui.tabWidget.tabBar()
    tab.setExpanding(True)
    for itab in range(0, tab.count()):
      slt = self.ui.tabWidget.widget(itab).findChild(Slits)
      if slt:
        slt.layFaceTab.layout().addWidget(slt.face)
        tab.setTabButton(itab,  QTabBar.LeftSide, slt.layFaceTab)

    self.ui.pandaBear.setDistance(14)
    self.ui.pandaBear.setMotors({MR.VP : 'SR08ID01SLW01:VPOS',
                                 MR.VS : 'SR08ID01SLW01:VOPEN',
                                 MR.LF : 'SR08ID01SLW01:RIGHT', # left/right are swapped
                                 MR.RT : 'SR08ID01SLW01:LEFT'})

    self.ui. babyBear.setDistance(20)
    self.ui. babyBear.setMotors({MR.VP : 'SR08ID01SLM12:VCENTRE',
                                 MR.VS : 'SR08ID01SLM12:VSIZE',
                                 MR.HP : 'SR08ID01SLM12:HCENTRE',
                                 MR.HS : 'SR08ID01SLM12:HSIZE'},
                                'SR08ID01SLM12:VCENTRE',
                                ['SR08ID01SLM12:IN',
                                 'SR08ID01SLM12:OUT',
                                 'SR08ID01SLM12:BOT',
                                 'SR08ID01SLM12:TOP'])

    self.ui. mamaBear.setDistance(31)
    self.ui. mamaBear.setMotors({MR.VP : 'SR08ID01SLM21:Z',
                                 MR.VS : 'SR08ID01SLM21:ZGAP',
                                 MR.HP : 'SR08ID01SLM21:Y',
                                 MR.HS : 'SR08ID01SLM21:YGAP'},
                                'SR08ID01TBL21:Z')

    self.ui.papaBear.setDistance(136)
    self.ui.papaBear.setMotors(  {MR.VP : 'SR08ID01SLM03:ZCENTRE',
                                  MR.VS : 'SR08ID01SLM03:ZGAP',
                                  MR.HP : 'SR08ID01SLM03:YCENTRE',
                                  MR.HS : 'SR08ID01SLM03:YGAP'},
                                 'SR08ID01SLM03:ZCENTRE')

    showcfg = QPushButton('Show config', self)
    showcfg.clicked.connect(self.toggleConfigShow)
    self.ui.statusbar.addPermanentWidget(showcfg)
    self.ui.statusbar.addPermanentWidget(QWidget(), 1)

    self.ui.statusbar.addPermanentWidget(QLabel('Beamline mode: ', self))
    modeLabel = QLabel(str(self.blMode), self)
    self.blMode.updated.connect(modeLabel.setText)
    self.ui.statusbar.addPermanentWidget(modeLabel)

    distances = QMenu(self)
    for nslt, desc in self.slitNames.items():
      distances.addAction(QtGui.QIcon(sharePath+nslt+'.png'),
                          desc, self.distancePicked)
    self.ui.distances.setMenu(distances)
    self.ui.distance.valueChanged.connect(self.ui.mashaBear.setDistance)

    synchs = QMenu(self)
    synchs.addAction('Seen in any', self.synchPicked)
    synchs.addAction('Seen in all', self.synchPicked)
    for nslt, desc in self.slitNames.items():
      synchs.addAction(QtGui.QIcon(sharePath+nslt+'.png'),
                       desc, self.synchPicked)
    self.ui.synchMasha.setMenu(synchs)

    self.blMode.updated.connect(self.initMasha)
    for slt in self.ui.findChildren(Slits):
      slt.changedConnection.connect(self.initMasha)
    self.blMode.updated.connect(self.updateBase)
    QtCore.QTimer.singleShot(0, self.updateBase)


    self.ui.viewTab.clicked.connect(lambda: self.uiModeSwap(True))
    self.ui.viewFam.clicked.connect(lambda: self.uiModeSwap(False))
    self.uiModeSwap(True)

    self.ui.save.clicked.connect(self.onSave)
    self.ui.load.clicked.connect(self.onLoad)

    self.ui.goWhite.clicked.connect(self.moveToBlMode)
    self.ui.goMono .clicked.connect(self.moveToBlMode)

    self.ui.mashaBear.willMoveNow.connect(self.onMashaMove)
    for slt in self.bears.values():
      self.ui.mashaBear.ui.stop.clicked.connect(slt.stop.clicked.emit)
      slt.changedConnection.connect(self.setMashaStatus)
      slt.changedMotion    .connect(self.setMashaStatus)
      slt.changedLimits    .connect(self.setMashaStatus)


  @pyqtSlot()
  def updateBase(self):
    for slt in self.bears.values():
      slt.setBase(20 if self.blMode.shut() == BLmode.Shut.MONO else 0)


  def moveToBlMode(self):
    if self.sender() not in (self.ui.goWhite, self.ui.goMono):
      return
    for nslt in self.slitNames.keys():
      slt = self.bears[nslt]
      if self.synbts[nslt].isChecked() and slt.baseMotor is not None:
        if self.ui.driveAbs.isChecked():
          slt.baseMotor.goUserPosition(0 if self.sender() is self.ui.goWhite else 20)
        else:
          slt.baseMotor.goRelative(-20 if self.sender() is self.ui.goWhite else 20)



  @pyqtSlot()
  def toggleConfigShow(self):
    tbwg = self.ui.tabWidget
    toShow = tbwg.widget(tbwg.count()-1) is not self.ui.configTab
    if self.sender():
      self.sender().setText('Hide config' if toShow else 'Show config')
    if toShow:
      tbwg.addTab(self.ui.configTab, '')
      # Have to create and use this new widget as home for
      # self.ui.layXrayFaceTab instead of using it itself
      # because it is always deleted when removing tab - even if reparented
      layXrayFaceTab = QWidget()
      QVBoxLayout(layXrayFaceTab).setContentsMargins(0, 0, 0, 0)
      layXrayFaceTab.layout().addWidget(self.ui.layXrayFaceTab)
      tbwg.tabBar().setTabButton(
        tbwg.count()-1,  QTabBar.LeftSide, layXrayFaceTab)
      tbwg.setCurrentWidget(self.ui.configTab)
    else:
      self.ui.config.layout().addWidget(self.ui.layXrayFaceTab)  # to keep from delete
      tbwg.removeTab(tbwg.count()-1)
    self.configFam.setVisible(toShow)
    for i in range(0, 10):
      QApplication.processEvents()
    if not toShow and self.ui.famWidget.isVisible():
      QtCore.QTimer.singleShot(0, (lambda: self.resize(self.minimumSizeHint())))


  @pyqtSlot()
  def uiModeSwap(self, toTab):

    (self.ui.viewTab if toTab else self.ui.viewFam).setChecked(True)
    self.ui.famWidget.setVisible(not toTab)
    self.ui.tabWidget.setVisible(toTab)

    wslt = 'Tab' if toTab else 'Fam'

    eval('self.ui.masha'+wslt).layout().addWidget(self.ui.masha)
    eval('self.ui.config'+wslt).layout().addWidget(self.ui.config)
    for nslt in self.slitNames.keys():
      eval('self.ui.'+nslt+wslt).layout().addWidget(eval('self.ui.'+nslt))
    for slt in self.ui.findChildren(Slits):
      eval('slt.layFace'+wslt).layout().addWidget(slt.face)

    self.ui.fakeSlitsVis.setVisible(not toTab)
    self.ui.layXrayFaceFam.setVisible(not toTab)
    layXF = eval('self.ui.layXrayFace'+wslt)
    layXF.layout().addWidget(self.ui.xrayFace)
    layXF.setMinimumSize(self.ui.xrayFace.minimumSize())
    QtCore.QTimer.singleShot(0, (lambda: self.resize(self.minimumSizeHint())))


  @pyqtSlot()
  def distancePicked(self):
    sndtxt = self.sender().text().replace('&', '')
    nslt = [ns for ns, desc in self.slitNames.items() if sndtxt == desc][0]
    self.ui.distance.setValue(self.bears[nslt].dist)


  @pyqtSlot()
  def synchPicked(self):
    sndtxt = self.sender().text().replace('&', '')
    posf = {}
    bearL = [self.bears[ns]
             for ns, desc in self.slitNames.items() if sndtxt == desc]
    if len(bearL):
      posf = bearL[0].posDRV()
    else:
      posS = []
      for nslt in self.slitNames.keys():
        if self.synbts[nslt].isChecked():
          posS.append(self.bears[nslt].posDRV())
      if not len(posS):
        return
      elif 'any' in sndtxt:
        for rol in MR.LF, MR.RT, MR.TP, MR.BT:
          posf[rol] = max(pos[rol] for pos in posS)
      elif 'all' in sndtxt:
        for rol in MR.LF, MR.RT, MR.TP, MR.BT:
          posf[rol] = min(pos[rol] for pos in posS)
    self.ui.mashaBear.setPos(posf)


  @pyqtSlot()
  def initMasha(self):

    def execonmod(slt):
      if slt.isConnected:
        self.ui.distance.setValue(slt.dist)
        self.ui.mashaBear.setPos(slt.posDRV())
        self.ui.mashaBear.ui.step.setValue(slt.ui.step.value())
        self.mashainited = True

    encl = self.blMode.encl()
    if hasattr(self, 'mashainited') or encl is BLmode.Encl.NONE:
      return
    elif encl is BLmode.Encl.MOD1:
      execonmod(self.ui.babyBear)
    elif encl is BLmode.Encl.MOD2:
      execonmod(self.ui.mamaBear)
    elif encl is BLmode.Encl.MOD3:
      execonmod(self.ui.papaBear)


  @pyqtSlot(dict, dict)
  def onMashaMove(self, orig, dest):
    for nslt in self.slitNames.keys():
      if self.synbts[nslt].isChecked():
        slt = self.bears[nslt]
        if self.ui.driveAbs.isChecked():
          slt.onMoveOrder(dest)
        else:
          sorig = slt.posRBV()
          sdest = {rol : sorig[rol] + dest[rol] - orig[rol] for rol in MR}
          slt.onMoveOrder(sdest)


  @pyqtSlot()
  def setMashaStatus(self):
    newConnected = True
    newMoving = False
    newLimit = False
    for slt in self.bears.values():
      newConnected &= slt.isConnected
      newMoving |= slt.isMoving
      newLimit |= slt.isOnLimit
    self.ui.mashaBear.onStatusChange(newConnected, newMoving, newLimit)


  @pyqtSlot()
  def onSave(self, fileName=None):

    if fileName is None:
      fileName = QtWidgets.QFileDialog.getSaveFileName(self,
        'Save configuration', QtCore.QDir.currentPath(),
        filter="Slits (*.slits);;All Files (*)")[0]
    if not fileName:
      return

    config = QtCore.QSettings(fileName, QtCore.QSettings.IniFormat)

    config.setValue('distance', self.ui.distance.value())
    config.setValue('tabbedui', self.ui.viewTab.isChecked())
    config.setValue('driverel', self.ui.driveRel.isChecked())

    for nslt in self.slitNames.keys():
      config.beginGroup(nslt)
      config.setValue('undercontrol', self.synbts[nslt].isChecked())
      for mot in self.bears[nslt].motors.values():
        config.setValue(mot.getPv(), mot.getUserPosition())
      config.endGroup()


  @pyqtSlot()
  def onLoad(self, fileName=None):
    pass


app = QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
