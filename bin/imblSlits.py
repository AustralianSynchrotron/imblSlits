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
      #self.updated.emit(self.encl().value+'-'+self.shut().value)
      self.updated.emit(self.Encl.MOD3.value+'-'+self.Shut.MONO.value)
    self.m1PV.add_callback(onUpdate)
    self.m2PV.add_callback(onUpdate)
    self.m3PV.add_callback(onUpdate)
    self.pinkPV.add_callback(onUpdate)
    self.monoPV.add_callback(onUpdate)
    self.mrtsPV.add_callback(onUpdate)

  def encl(self):
    if self.m3PV.value :
      return self.Encl.MOD3
    elif self.m2PV.value :
      return self.Encl.MOD2
    elif self.m1PV.value :
      return self.Encl.MOD1
    else :
      return self.Encl.NONE

  def shut(self):
    if self.pinkPV.value == None or self.monoPV.value == None or self.mrtsPV.value == None \
       or 1 != self.pinkPV.value + self.monoPV.value + self.mrtsPV.value :
      return self.Shut.NONE
    elif self.pinkPV.value :
      return self.Shut.PINK
    elif self.monoPV.value :
      return self.Shut.MONO
    elif self.mrtsPV.value :
      return self.Shut.MRTS
    else :
      return self.Shut.NONE






class MainWindow(QtWidgets.QMainWindow):

  blMode = BLmode()
  slitNames = {'panda': 'HHLS',
               'baby' : 'Baby bear',
               'mama' : 'Mama bear',
               'papa' : 'Papa bear'}


  def __init__(self):

    super(MainWindow, self).__init__()
    self.ui = loadUi(sharePath + 'imblSlitsMainWindow.ui', self)
    self.uiModeSwap(True)
    self.toggleConfigShow()

    self.bears  = {}
    self.synbts = {}
    for nslt in self.slitNames.keys() :
      self.bears[nslt] = eval('self.ui.'+nslt+'Bear')
      self.synbts[nslt] = eval('self.ui.'+nslt+'Synch')

    for nslt, desc in self.slitNames.items() :
      self.bears[nslt].face.set(sharePath+nslt+'.png', desc)
      self.synbts[nslt].setText(desc)
      self.synbts[nslt].setIcon(QtGui.QIcon(sharePath+nslt+'.png'))
    self.ui.mashaBear.face.set(sharePath+'masha.png', 'Detector')
    self.ui.xrayFace.set(sharePath+'xray.png', 'Config')
    self.ui.xrayFace.setMinimumSize(self.ui.mashaBear.face.minimumSize())
    self.ui.mashaBear.visual.heightChanged.connect(self.ui.fakeSlitsVis.setMinimumHeight)


    tab = self.ui.tabWidget.tabBar()
    tab.setExpanding(True)
    for itab in range(0, tab.count()):
      slt = self.ui.tabWidget.widget(itab).findChild(Slits)
      if slt:
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


    showcfg = QtWidgets.QPushButton('Show config', self)
    showcfg.clicked.connect(self.toggleConfigShow)
    self.ui.statusbar.addPermanentWidget(showcfg);
    self.ui.statusbar.addPermanentWidget(QtWidgets.QWidget(), 1)

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
    self.blMode.updated.connect(self.updateBase)

    self.ui.viewTab.clicked.connect(lambda: self.uiModeSwap(True))
    self.ui.viewFam.clicked.connect(lambda: self.uiModeSwap(False))
    self.uiModeSwap(True)

    self.ui.mashaBear.willMoveNow.connect(self.onMashaMove)




  @pyqtSlot()
  def updateBase(self):
    for slit in self.ui.babyBear, self.ui.papaBear, self.ui.mashaBear :
      slit.setBase(20 if self.blMode.shut() == BLmode.Shut.MONO else 0)

  @pyqtSlot()
  def toggleConfigShow(self):
    toShow = self.ui.tabWidget.widget(0) is not self.ui.configTab
    if self.sender() :
      self.sender().setText('Hide config' if toShow else 'Show config')
    if toShow :
      self.ui.tabWidget.insertTab(0, self.ui.configTab, '')
      # Have to create and use this new widget as home for self.ui.layXrayFaceTab
      # instead of using self.ui.layXrayFaceTab itself
      # because it is always deleted when removing tab - even if reparented
      layXrayFaceTab = QtWidgets.QWidget()
      QtWidgets.QVBoxLayout(layXrayFaceTab).setContentsMargins(0, 0, 0, 0)
      layXrayFaceTab.layout().addWidget(self.ui.layXrayFaceTab)
      self.ui.tabWidget.tabBar().setTabButton(
        0,  QtWidgets.QTabBar.LeftSide, layXrayFaceTab)
      self.ui.tabWidget.setCurrentWidget(self.ui.configTab)
    else :
      self.ui.config.layout().addWidget(self.ui.layXrayFaceTab) # to keep from delete
      self.ui.tabWidget.removeTab(0)
    self.configFam.setVisible(toShow)
    for i in range(0, 10):
      QtWidgets.QApplication.processEvents()
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
    for slt in self.ui.findChildren(Slits) :
      eval('slt.layFace'+wslt).layout().addWidget(slt.face)

    self.ui.fakeSlitsVis.setVisible(not toTab)
    self.ui.layXrayFaceFam.setVisible(not toTab)
    eval('self.ui.layXrayFace'+wslt).layout().addWidget(self.ui.xrayFace)
    eval('self.ui.layXrayFace'+wslt).setMinimumSize(self.ui.xrayFace.minimumSize())
    QtCore.QTimer.singleShot(0, (lambda: self.resize(self.minimumSizeHint())))


  @pyqtSlot()
  def distancePicked(self):
    sndtxt = self.sender().text().replace('&','')
    nslt = [ns for ns,desc in self.slitNames.items() if sndtxt == desc][0]
    self.ui.distance.setValue(self.bears[nslt].dist)


  @pyqtSlot()
  def synchPicked(self):
    sndtxt = self.sender().text().replace('&','')
    posf = {}
    bearL = [self.bears[ns] for ns,desc in self.slitNames.items() if sndtxt == desc]
    if len(bearL) :
      posf = bearL[0].posDRV()
    else:
      posS = []
      for nslt in self.slitNames.keys() :
        if self.synbts[nslt].isChecked() :
          posS.append(self.bears[nslt].posDRV())
      if not len(posS) :
        return
      elif 'any' in sndtxt :
        for rol in (MR.LF, MR.RT, MR.TP, MR.BT) :
          posf[rol] = max( pos[rol] for pos in posS )
      elif 'all' in sndtxt :
        for rol in (MR.LF, MR.RT, MR.TP, MR.BT) :
          posf[rol] = min( pos[rol] for pos in posS )
    self.ui.mashaBear.setPos(posf)


  @pyqtSlot()
  def initMasha(self) :
    encl = self.blMode.encl()
    def execonmod(slt):
      if slt.isConnected:
        self.ui.distance.setValue(slt.dist)
        self.ui.mashaBear.setPos(slt.posDRV())
        self.ui.mashaBear.ui.step.setValue(slt.ui.step.value())
        self.mashainited = True
    if hasattr(self, 'mashainited') or encl is BLmode.Encl.NONE :
      return
    elif encl is BLmode.Encl.MOD1 :
      execonmod(self.ui.babyBear)
    elif encl is BLmode.Encl.MOD2 :
      execonmod(self.ui.mamaBear)
    elif encl is BLmode.Encl.MOD3 :
      execonmod(self.ui.papaBear)


  @pyqtSlot(dict, dict)
  def onMashaMove(self, orig, dest) :
    for nslt in self.slitNames.keys() :
      if self.synbts[nslt].isChecked() :
        self.bears[nslt].onMoveOrder(dest)





app = QtWidgets.QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
