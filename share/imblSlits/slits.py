import sys, os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi

execPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

from driver import Driver

class Slits(QWidget) :    
  def __init__(self, parent):
    super(QWidget, self).__init__(parent)
    self.ui = loadUi(execPath + 'slits.ui', self)
    #for drv in self.ui.findChildren(Driver) :
    #  drv.label.setText(drv.toolTip())
