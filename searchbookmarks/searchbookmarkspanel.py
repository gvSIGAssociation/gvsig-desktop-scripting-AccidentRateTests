# encoding: utf-8

import gvsig
import thread
from time import sleep

from java.lang import Boolean, String

from javax.swing.table import AbstractTableModel
from javax.swing import SwingUtilities

from gvsig.libs.formpanel import FormPanel

from org.gvsig.tools.swing.api import ToolsSwingUtils, ToolsSwingLocator
from org.gvsig.tools.swing.api.windowmanager import WindowManager
from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.dispose import  DisposeUtils

from org.gvsig.scripting.app.extension.ScriptingUtils import log, INFO, WARN
from org.gvsig.fmap.dal import DALLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager

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

  def message(self,msg):
    if not SwingUtilities.isEventDispatchThread():
      SwingUtilities.invokeLater(lambda : self.message(msg))
      return
    self.lblMessage.setText(msg)
 
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
    self.tblTests.getSelectionModel().addListSelectionListener(self.tblTest_selectionChanged)
    self.message("Cargados %s favoritos." % len(self.__tests))

  def tblTest_selectionChanged(self, *args):
    row = self.tblTests.getSelectedRow()
    self.message("Linea %s de %s" % (row,len(self.__tests)))
    
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
    manager = ToolsLocator.getDisposableManager();
    taskStatus = ToolsLocator.getTaskStatusManager().createDefaultSimpleTaskStatus("Ejecutando tests")
    self.taskStatusController.bind(taskStatus)
    taskStatus.setRangeOfValues(0,len(self.__tests))
    self.taskStatusController.setVisible(True)
    failsCounter = 0
    for test in self.__tests:
      if taskStatus.isCancellationRequested():
        taskStatus.cancel()
        break
      taskStatus.message(test.getName())
      if test.isEnabled():
        log(INFO,"TEST: " + test.getName(),None)
        d1 = len(manager.getBoundDisposables())
        test.run()
        d2 = len(manager.getBoundDisposables())
        if test.isFailed():
          log(INFO,"\n"+test.getSearchParameters().toString(),None)
          failsCounter+=1
        if d2 > d1:
          log(INFO,u"No se han liberado todos los elementos usados en la búsqueda: " + test.getName(),None)
          #break
      taskStatus.incrementCurrentValue()
      sleep(0.01)
    taskStatus.terminate()
    self.taskStatusController.setVisible(False)
    SwingUtilities.invokeLater(lambda : self.__tableModel.fireTableDataChanged())
    self.message("Han fallado %s de %s" % (failsCounter, len(self.__tests)))
    
  def btnGoSearchPanel_click(self,*args):
    row = self.tblTests.getSelectedRow()

    if row<0 :
      self.message("Debera seleccionar un test")
      return
    row = self.tblTests.getRowSorter().convertRowIndexToModel(row);
    test = self.__tests[row]
    store = test.getStore()
    if store == None:
      self.message("Tabla no encontrada")
      return
    dataSwingManager = DALSwingLocator.getDataSwingManager()
    searchPanel = dataSwingManager.createFeatureStoreSearchPanel(store)
    searchPanel.setAutomaticallySearch(False)
    ToolsSwingLocator.getWindowManager().showWindow(
      searchPanel.asJComponent(), 
      "Buscar: %s [Favorito %s]" % (test.getTableName(), test.getName()), 
      WindowManager.MODE.WINDOW
    );
    SwingUtilities.invokeLater(lambda : searchPanel.put(test.getSearchParameters().getCopy()))
    

  def btnShowParameters_click(self, *args):
    toolsSwingManager = ToolsSwingLocator.getToolsSwingManager()
    row = self.tblTests.getSelectedRow()
    
    if row<0 :
      self.message("Debera seleccionar un test")
      return
    row = self.tblTests.getRowSorter().convertRowIndexToModel(row);
    test = self.__tests[row]
    toolsSwingManager .showZoomDialog(
      self.asJComponent(), 
      test.getName(), 
      "%s\n\n-------------------------------\n\n%s" % (
        test.getSearchParameters().toString(), 
        test.getLastExecutionStatus()
      ),
      False
      #, WindowManager.MODE.WINDOW
    )
    

  def btnExport_click(self, *args):
     thread.start_new_thread(lambda : self.export(), tuple())
   
  def export(self):
    name = "search_bookmark_tests"
    taskStatus = ToolsLocator.getTaskStatusManager().createDefaultSimpleTaskStatus("Exportando tests")
    self.taskStatusController.bind(taskStatus)
    self.taskStatusController.setVisible(True)   
    taskStatus.message("Creando tabla temporal")
    store = self.createTemporaryH2Store(name)
    taskStatus.setRangeOfValues(0,len(self.__tests))
    taskStatus.message("Guardando registros...")
    store.edit()
    pk = 1
    for test in self.__tests:
      if taskStatus.isCancellationRequested():
        taskStatus.cancel()
        break
      taskStatus.message(test.getName())
      f = store.createNewFeature()
      f.set("pk",pk)
      f.set("Activo",test.isEnabled())
      f.set("Nombre",test.getName())
      f.set("Tabla",test.getTableName())
      f.set("Estado",test.getLastExecutionStatus())
      f.set("Favorito",test.getSearchParameters().toString())
      store.insert(f)
      pk+=1
      taskStatus.incrementCurrentValue()
    if taskStatus.isCancellationRequested():
      store.cancelEditing()
    else:
      store.finishEditing()
      application = ApplicationLocator.getApplicationManager()
      taskStatus.message("Añadiendo la tabla al proyecto")
      project = application.getCurrentProject()
      doc = project.createDocument(TableManager.TYPENAME)
      doc.setStore(store)
      doc.setName(u"Pruebas de marcador de búsqueda")
      project.addDocument(doc)
      DisposeUtils.dispose(store)
      taskStatus.terminate()
    self.taskStatusController.setVisible(False)
 
  def createTemporaryH2Store(self, name):
    dataManager = DALLocator.getDataManager()
    foldersManager = ToolsLocator.getFoldersManager()
    
    tempFile = foldersManager.getUniqueTemporaryFile(name)
    featureType = dataManager.createFeatureType()
    featureType.add("pk","INTEGER").setIsPrimaryKey(True)
    featureType.add("Activo","BOOLEAN")
    featureType.add("Tabla","STRING",100)
    featureType.add("Nombre","STRING",255)
    featureType.add("Estado","STRING",10240)
    featureType.add("Favorito","STRING",10240)

    serverParameters = dataManager.createServerExplorerParameters("H2Spatial")
    serverParameters.setFile(tempFile)
    serverExplorer = dataManager.openServerExplorer("H2Spatial", serverParameters)

    newParametersTarget = serverExplorer.getAddParameters()
    newParametersTarget.setDynValue("Table", name)
    newParametersTarget.setDefaultFeatureType(featureType)
    serverExplorer.add("H2Spatial", newParametersTarget, True)

    openParametersTarget = dataManager.createStoreParameters("H2Spatial")
    openParametersTarget.setDynValue("database_file", tempFile)
    openParametersTarget.setDynValue("Table", name)

    storeResults = dataManager.openStore("H2Spatial", openParametersTarget)
    return storeResults

    
def main(*args):
  log(INFO,"Hola mundo",None)
  panel = TestSearchBookmarsPanel()
  panel.showWindow("Test favoritos de la ficha de busqueda")


  
