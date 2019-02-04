#!/usr/bin/env python3

import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, qDebug, pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi
from enum import Enum
import epics

binPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep
sharePath = binPath + "../share/imblSlits/"
sys.path.append(sharePath)
from slits import Slits, MotoRole


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
               'papa' : 'Papa bear',
               'masha': 'Detector' }

  def __init__(self):

    super(MainWindow, self).__init__()
    self.ui = loadUi(sharePath + 'imblSlitsMainWindow.ui', self)
    #self.ui = ui_slits.Ui_MainWindow()
    #self.ui.setupUi(self)

    for nslt in self.slitNames.keys() :
      eval('self.ui.'+nslt+'Bear.face.set(sharePath+nslt+\'.png\', self.slitNames[nslt])')

    tab = self.ui.tabWidget.tabBar()
    tab.setExpanding(True)
    for itab in range(0, tab.count()):
      slt = self.ui.tabWidget.widget(itab).findChild(Slits)
      slt.layFaceTab.layout().addWidget(slt.face)
      tab.setTabButton(itab,  QtWidgets.QTabBar.LeftSide, slt.layFaceTab)


    #w = self.ui.tabWidget.tabBar().width()
    #tab = self.ui.tabWidget.setIconSize(QtCore.QSize(w,w))
    self.ui.famWidget.hide()


    self.ui.pandaBear.ui.visual.dist = 14
    self.ui.pandaBear.setMotors( {MotoRole.VP : 'SR08ID01SLW01:VPOS',
                                  MotoRole.VS : 'SR08ID01SLW01:VOPEN',
                                  MotoRole.LF : 'SR08ID01SLW01:LEFT',
                                  MotoRole.RT : 'SR08ID01SLW01:RIGHT'} )

    self.ui.babyBear.ui.visual.dist = 20
    self.ui.babyBear.setMotors(  {MotoRole.VP : 'SR08ID01SLM12:VCENTRE',
                                  MotoRole.VS : 'SR08ID01SLM12:VSIZE',
                                  MotoRole.HP : 'SR08ID01SLM12:HCENTRE',
                                  MotoRole.HS : 'SR08ID01SLM12:HSIZE'} )
                                  #MotoRole.LF : 'SR08ID01SLM12:IN',
                                  #MotoRole.RT : 'SR08ID01SLM12:OUT',
                                  #MotoRole.BT : 'SR08ID01SLM12:BOT',
                                  #MotoRole.TP : 'SR08ID01SLM12:TOP'} )

    self.ui.mamaBear.ui.visual.dist = 31
    self.ui.mamaBear.setMotors(  {MotoRole.VP : 'SR08ID01SLM21:Z',
                                  MotoRole.VS : 'SR08ID01SLM21:ZGAP',
                                  MotoRole.HP : 'SR08ID01SLM21:Y',
                                  MotoRole.HS : 'SR08ID01SLM21:YGAP'} )

    self.ui.papaBear.ui.visual.dist = 136
    self.ui.papaBear.setMotors(  {MotoRole.VP : 'SR08ID01SLM03:ZCENTRE',
                                  MotoRole.VS : 'SR08ID01SLM03:ZGAP',
                                  MotoRole.HP : 'SR08ID01SLM03:YCENTRE',
                                  MotoRole.HS : 'SR08ID01SLM03:YGAP'} )

    @pyqtSlot()
    def updateBase():
      for slit in self.ui.babyBear, self.ui.papaBear, self.ui.mashaBear :
        slit.setBase(20 if self.shMode.mode() == SHmode.Mode.MONO else 0)
    self.shMode.updated.connect(updateBase)

    @pyqtSlot()
    def uiModeSwap():
      toTab = self.ui.famWidget.isVisible()
      self.ui.famWidget.setVisible(not toTab)
      self.ui.tabWidget.setVisible(toTab)
      wslt = 'Tab' if toTab else 'Fam'
      for nslt in self.slitNames.keys():
        eval('self.ui.'+nslt+wslt+'.layout().addWidget(self.ui.'+nslt+')')
      for slt in self.ui.findChildren(Slits) :
        eval('slt.layFace'+wslt+'.layout().addWidget(slt.face)')
      self.sender().setText('All' if toTab else 'In tabs')
      QtCore.QTimer.singleShot(0, (lambda: self.resize(self.minimumSizeHint())))

    self.ui.statusbar.addPermanentWidget(QtWidgets.QLabel('Show: ', self))
    uimode = QtWidgets.QPushButton('All', self)
    uimode.clicked.connect(uiModeSwap)
    self.ui.statusbar.addPermanentWidget(uimode);

    self.ui.statusbar.addPermanentWidget(QtWidgets.QWidget(), 1)

    self.ui.statusbar.addPermanentWidget(QtWidgets.QLabel('Shutter mode: ', self))
    modeLabel = QtWidgets.QLabel('...', self)
    self.shMode.updated.connect(modeLabel.setText)
    self.ui.statusbar.addPermanentWidget(modeLabel)

    modeLabel = QtWidgets.QLabel('    ', self)
    self.ui.statusbar.addPermanentWidget(modeLabel)

    self.ui.statusbar.addPermanentWidget(QtWidgets.QLabel('Beamline mode: ', self))
    modeLabel = QtWidgets.QLabel('...', self)
    self.blMode.updated.connect(modeLabel.setText)
    self.ui.statusbar.addPermanentWidget(modeLabel)


    distances = QtWidgets.QMenu(self)

    @pyqtSlot()
    def distancePicked():
      if self.sender() not in distances.actions() :
        return
      elif '1A' in self.sender().text() :
        self.ui.distance.setValue(self.ui.pandaBear.ui.visual.dist)
      elif '1B' in self.sender().text() :
        self.ui.distance.setValue(self.ui.babyBear.ui.visual.dist)
      elif '2B' in self.sender().text() :
        self.ui.distance.setValue(self.ui.mamaBear.ui.visual.dist)
      elif '3B' in self.sender().text() :
        self.ui.distance.setValue(self.ui.papaBear.ui.visual.dist)

    distances.addAction('Enclosure 1A', distancePicked)
    distances.addAction('Enclosure 1B', distancePicked)
    distances.addAction('Enclosure 2B', distancePicked)
    distances.addAction('Enclosure 3B', distancePicked)
    self.ui.distances.setMenu(distances)






app = QtWidgets.QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
