#!/usr/bin/env python3

import sys, os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.uic import loadUi
from enum import Enum
import epics

execPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep
sys.path.append(execPath + "../share/imblSlits")
#import imblSlits


class BLmode(QObject):
  
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
    super(BLmode, self).__init__()    
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
  




class MainWindow(QtWidgets.QMainWindow):
  
  blMode = BLmode()
  
  def __init__(self):
      
    super(MainWindow, self).__init__()
    self.ui = loadUi(execPath + '../share/imblSlits/imblSlitsMainWindow.ui', self)
    #self.ui = ui_slits.Ui_MainWindow()
    #self.ui.setupUi(self)
    
    tab = self.ui.tabWidget.tabBar()
    for itab in range(0, tab.count()):
    #  print(tab.tabIcon(itab).name())
      lab = QtWidgets.QLabel(tab.tabText(itab))
      #lab.setPixmap(tab.tabIcon(itab).pixmap())
      tab.setTabText(itab,'')
      #tab.setTabIcon(itab, None)
      tab.setTabButton(itab,  QtWidgets.QTabBar.LeftSide, lab )
    w = self.ui.tabWidget.tabBar().width()
    tab = self.ui.tabWidget.setIconSize(QtCore.QSize(w,w))
    

    
    
    self.ui.statusbar.addPermanentWidget(QtWidgets.QLabel('Shutter mode: ', self));
    modeLabel = QtWidgets.QLabel('Init', self)
    self.blMode.updated.connect(modeLabel.setText)
    self.ui.statusbar.addPermanentWidget(modeLabel);
    
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
  

  
app = QtWidgets.QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
