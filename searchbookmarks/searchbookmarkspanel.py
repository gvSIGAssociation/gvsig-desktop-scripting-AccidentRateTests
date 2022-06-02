# encoding: utf-8

import gvsig

from java.lang import Boolean, String

from javax.swing.table import AbstractTableModel

from gvsig.libs.formpanel import FormPanel

from org.gvsig.tools.swing.api import ToolsSwingUtils

import addons.AccidentRateTests.searchbookmarks.searchbookmarks
reload(addons.AccidentRateTests.searchbookmarks.searchbookmarks)
from addons.AccidentRateTests.searchbookmarks.searchbookmarks import getSearchBookmarks

class TestSearchBookmarsTableModel(AbstractTableModel):
  def __init__(self, tests):
    self.__tests = tests # list of SearchBookmark
    self.__columnNames = ("Activo","Tabla", "Nombre", "Estado")
    self.__columnClass = ( Boolean, String, String, String)

  def getRowCount(self):
    return len(self.__tests)

  def getColumnCount(self):
    return len(self.__columnNames)
    
  def getColumnName(self, columnIndex):
    return self.__columnNames[columnIndex]

  def getColumnClass(self, columnIndex):
    return self.__columnClass[columnIndex]
  
  def getValueAt(self, rowIndex, columnIndex):
    test = self.__tests[rowIndex]
    if columnIndex == 0:
      return test.isEnabled()
    if columnIndex == 1:
      return test.getTableName()
    if columnIndex == 2:
      return test.getName()
    if columnIndex == 3:
      return test.getLastExecutionStatus()

  def isCellEditable(self, rowIndex, columnIndex):
    if columnIndex==0:
      return True
    return False

  def setValueAt(self, value, rowIndex, columnIndex):
    test = self.__tests[rowIndex]
    if columnIndex == 0:
      return test.setEnabled(value)

class TestSearchBookmarsPanel(FormPanel):
  def __init__(self):
    FormPanel.__init__(self,gvsig.getResource(__file__,"searchbookmarkspanel.xml"))
    self.__tests = getSearchBookmarks()
    self.initComponents()

  def initComponents(self):
    self.__tableModel = TestSearchBookmarsTableModel(self.__tests)
    self.tblTests.setModel(self.__tableModel)
    ToolsSwingUtils.ensureRowsCols(self.asJComponent(), 25, 100, 30, 150)

  def btnExecuteTests_click(self,*args):
    for test in self.__tests:
     test.run()
    self.__tableModel.fireTableDataChanged()

def main(*args):
  panel = TestSearchBookmarsPanel()
  panel.showWindow("Test favoritos de la ficha de busqueda")
  
