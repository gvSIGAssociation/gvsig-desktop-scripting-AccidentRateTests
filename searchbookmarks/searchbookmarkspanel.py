# encoding: utf-8

import gvsig
import thread
from time import sleep

from java.lang import Boolean, String

from javax.swing.table import AbstractTableModel
from javax.swing import SwingUtilities

from gvsig.libs.formpanel import FormPanel

from org.gvsig.tools.swing.api import ToolsSwingUtils, ToolsSwingLocator
from org.gvsig.tools import ToolsLocator

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
    self.__tests = list() 
    self.initComponents()

  def initComponents(self):
    self.taskStatusController = ToolsSwingLocator.getTaskStatusSwingManager().createTaskStatusController(
      None,
      self.lblStatusTitle,
      self.lblStatusMessage,
      self.pbStatus,
      self.btnStatusCancel,
      None
    )
    self.__tableModel = TestSearchBookmarsTableModel(self.__tests)
    self.tblTests.setModel(self.__tableModel)
    self.tblTests.setAutoCreateRowSorter(True)
    ToolsSwingUtils.ensureRowsCols(self.asJComponent(), 25, 100, 30, 150)

    thread.start_new_thread(lambda : self.__loadBookmarks(), tuple())

  def __loadBookmarks(self):
    taskStatus = ToolsLocator.getTaskStatusManager().createDefaultSimpleTaskStatus("Cargando favoritos")
    self.taskStatusController.bind(taskStatus)
    self.taskStatusController.setVisible(True)
    tests = getSearchBookmarks(taskStatus)
    self.taskStatusController.setVisible(False)
    self.setTableModel(tests)

  def setTableModel(self, tests):
    if not SwingUtilities.isEventDispatchThread():
      SwingUtilities.invokeLater(lambda : self.setTableModel( tests))
      return
    self.__tests = tests
    self.__tableModel = TestSearchBookmarsTableModel(self.__tests)
    self.tblTests.setModel(self.__tableModel)
    self.lblMessage.setText("Cargados %s favoritos." % len(self.__tests))
    
  def btnSelectAll_click(self, *args):
    for test in self.__tests:
      test.setEnabled(True)
    self.__tableModel.fireTableDataChanged()

  def btnDeselectAll_click(self, *args):
    for test in self.__tests:
      test.setEnabled(False)
    self.__tableModel.fireTableDataChanged()
   
  def btnExecuteTests_click(self,*args):
    thread.start_new_thread(lambda : self.__runtests(), tuple())

  def __runtests(self):
    taskStatus = ToolsLocator.getTaskStatusManager().createDefaultSimpleTaskStatus("Ejecutando tests")
    self.taskStatusController.bind(taskStatus)
    taskStatus.setRangeOfValues(0,len(self.__tests))
    self.taskStatusController.setVisible(True)
    for test in self.__tests:
      if taskStatus.isCancellationRequested():
        taskStatus.cancel()
        break
      taskStatus.message(test.getName())
      test.run()
      taskStatus.incrementCurrentValue()
      sleep(0.01)
    taskStatus.terminate()
    self.taskStatusController.setVisible(False)
    SwingUtilities.invokeLater(lambda : self.__tableModel.fireTableDataChanged())
  

def main(*args):
  panel = TestSearchBookmarsPanel()
  panel.showWindow("Test favoritos de la ficha de busqueda")
  
