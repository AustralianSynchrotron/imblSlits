#!/usr/bin/env python3

import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, qDebug, pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi
from enum import Enum
import epics

binPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep
sharePath = binPath + "../share/imblSlits"
sys.path.append(sharePath)
from slits import Slits


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

  def __init__(self):

    super(MainWindow, self).__init__()
    self.ui = loadUi(sharePath + '/imblSlitsMainWindow.ui', self)
    #self.ui = ui_slits.Ui_MainWindow()
    #self.ui.setupUi(self)

    rotTrans = QtGui.QTransform().rotate(-90)
    tab = self.ui.tabWidget.tabBar()
    tab.setExpanding(True)
    for itab in range(0, tab.count()):
      lab = QtWidgets.QLabel(tab.tabText(itab))
      tab.setTabText(itab,'')
      tab.setTabButton(itab,  QtWidgets.QTabBar.LeftSide, lab )
      icon = tab.tabIcon(itab)
      slt = self.ui.tabWidget.widget(itab).findChild(Slits)
      if slt :
        slt.face.setPixmap( icon.pixmap(slt.face.minimumSize()).transformed(rotTrans) )
        slt.face.hide()

    w = self.ui.tabWidget.tabBar().width()
    tab = self.ui.tabWidget.setIconSize(QtCore.QSize(w,w))
    self.ui.famWidget.hide()

    tabLay = { self.ui.panda : self.ui.pandaTab.layout(),
               self.ui.baby  : self.ui.babyTab .layout(),
               self.ui.mama  : self.ui.mamaTab .layout(),
               self.ui.papa  : self.ui.papaTab .layout(),
               self.ui.masha : self.ui.mashaTab.layout()  }
    famLay = { self.ui.panda : self.ui.pandaFam.layout(),
               self.ui.baby  : self.ui.babyFam .layout(),
               self.ui.mama  : self.ui.mamaFam .layout(),
               self.ui.papa  : self.ui.papaFam .layout(),
               self.ui.masha : self.ui.mashaFam.layout()  }

    @pyqtSlot()
    def uiModeSwap():
      if self.ui.mashaFam.layout().count() :
        self.ui.famWidget.hide()
        for slt in tabLay.keys() :
          tabLay[slt].addWidget(slt)
          slt.findChild(Slits).face.hide()
        self.ui.tabWidget.show()
        self.sender().setText('In tabs')
      else :
        self.ui.tabWidget.hide()
        for slt in famLay.keys() :
          famLay[slt].addWidget(slt)
          slt.findChild(Slits).face.show()
        self.ui.famWidget.show()
        self.sender().setText('All')
      for slt in famLay.keys() :
        slt.show()
      QtCore.QTimer.singleShot(0, (lambda: self.resize(self.minimumSizeHint())))

    self.ui.statusbar.addPermanentWidget(QtWidgets.QLabel('View: ', self))
    uimode = QtWidgets.QPushButton('all', self)
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
        self.ui.distance.setValue(14)
      elif '1B' in self.sender().text() :
        self.ui.distance.setValue(20)
      elif '2B' in self.sender().text() :
        self.ui.distance.setValue(31)
      elif '3B' in self.sender().text() :
        self.ui.distance.setValue(136)

    distances.addAction('Enclosure 1A', distancePicked)
    distances.addAction('Enclosure 1B', distancePicked)
    distances.addAction('Enclosure 2B', distancePicked)
    distances.addAction('Enclosure 3B', distancePicked)
    self.ui.distances.setMenu(distances)

    self.ui.pandaBear.setMotors( {Slits.MotoRole.VP : 'SR08ID01SLW01:VPOS',
                                  Slits.MotoRole.VS : 'SR08ID01SLW01:VOPEN',
                                  Slits.MotoRole.LF : 'SR08ID01SLW01:LEFT',
                                  Slits.MotoRole.RT : 'SR08ID01SLW01:RIGHT'} )

    self.ui.babyBear.setMotors(  {Slits.MotoRole.VP : 'SR08ID01SLM12:VCENTRE',
                                  Slits.MotoRole.VS : 'SR08ID01SLM12:VSIZE',
                                  Slits.MotoRole.HP : 'SR08ID01SLM12:HCENTRE',
                                  Slits.MotoRole.HS : 'SR08ID01SLM12:HSIZE',
                                  Slits.MotoRole.LF : 'SR08ID01SLM12:IN',
                                  Slits.MotoRole.RT : 'SR08ID01SLM12:OUT',
                                  Slits.MotoRole.BT : 'SR08ID01SLM12:BOT',
                                  Slits.MotoRole.TP : 'SR08ID01SLM12:TOP'} )

    self.ui.mamaBear.setMotors(  {Slits.MotoRole.VP : 'SR08ID01SLM21:Z',
                                  Slits.MotoRole.VS : 'SR08ID01SLM21:ZGAP',
                                  Slits.MotoRole.HP : 'SR08ID01SLM21:Y',
                                  Slits.MotoRole.HS : 'SR08ID01SLM21:YGAP'} )

    self.ui.papaBear.setMotors(  {Slits.MotoRole.VP : 'SR08ID01SLM03:ZCENTRE',
                                  Slits.MotoRole.VS : 'SR08ID01SLM03:ZGAP',
                                  Slits.MotoRole.HP : 'SR08ID01SLM03:YCENTRE',
                                  Slits.MotoRole.HS : 'SR08ID01SLM03:YGAP'} )







app = QtWidgets.QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
