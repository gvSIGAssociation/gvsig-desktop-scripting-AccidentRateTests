# encoding: utf-8

import gvsig

import os
from java.io import FileInputStream
from java.lang import StringBuilder

from java.util import Properties

from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.dispose import DisposeUtils

from org.gvsig.fmap.dal import DALLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.fmap.dal.swing.searchpanel import  FeatureStoreSearchPanel 

from org.gvsig.scripting.app.extension.ScriptingUtils import log, INFO, WARN

STATUS_OK = "Ok"
STATUS_UNKNOWN = "Unknown"


class SearchBookmark(object):
  def __init__(self, pathname):
    self.__pathname = pathname
    self.__searchParameters = None
    self.__name = "unknown"
    self.__lastExecutionStatus = "unknown"
    try:
      self.__name = os.path.basename(pathname).split("!")[2]
    except:
      pass
    self.__enabled = True
    
    self.__table_name = None
    self.__result_should_have_rows = "true"
    self.__first_row_of_results_must_have_values = "true"

  def getName(self):
    return self.__name

  def getSearchParameters(self):
    return self.__searchParameters

  def getTableName(self):
    return self.__table_name

  def __str__(self):
    return self.__name

  def getLastExecutionStatus(self):
    return self.__lastExecutionStatus

  def setEnabled(self, enabled):
    self.__enabled = enabled

  def isEnabled(self):
    return self.__enabled
    
  def load(self):
    persistenceManager = ToolsLocator.getPersistenceManager()
    fname = os.path.splitext(self.__pathname)[0]
    self.__name = os.path.basename(fname).split("!")[2]

    stream = FileInputStream(fname)
    self.__searchParameters = persistenceManager.getObject(stream)
    stream.close()
    
    stream = FileInputStream(self.__pathname)
    props = Properties()
    props.load(stream)
    stream.close()
    self.__table_name = props.getProperty("table_name")
    self.__result_should_have_rows = props.getProperty("result_should_have_rows", "true").lower()
    self.__first_row_of_results_must_have_values = props.getProperty("first_row_of_results_must_have_values", "true").lower()
    self.__enabled = props.getProperty("enabled", "true").lower()
    if self.__enabled == "true":
      self.__enabled = True
    else:
      self.__enabled = False
    if self.__searchParameters.getQuery().getLimit() == 0:
      self.__searchParameters.getQuery().clearLimit()

  def getStore(self):
    dataManager = DALLocator.getDataManager()
    try:
      store = dataManager.getStoresRepository().getStore(self.__table_name)
    except:
        return None
    return store
      
  def run(self):
    if not self.__enabled:
      self.__lastExecutionStatus = STATUS_UNKNOWN
      return
    dataManager = DALLocator.getDataManager()
    dataSwingManager = DALSwingLocator.getDataSwingManager()
    store = None
    searchPanel = None
    model = None
    try:
      store = dataManager.getStoresRepository().getStore(self.__table_name)
      if store == None:
        self.__lastExecutionStatus = "Table not found"
        log(WARN,self.__lastExecutionStatus,None)
        return
    except:
        self.__lastExecutionStatus = "Table not open"
        log(WARN,self.__lastExecutionStatus,None)
        return
    
    validationMessage = ""
    try:
      searchParameters = self.__searchParameters.getCopy()
      featureType = store.getDefaultFeatureType()
      errMessage = StringBuilder()
      if not searchParameters.isValid(featureType,errMessage):
        self.__lastExecutionStatus = errMessage.toString()
        log(WARN,self.__lastExecutionStatus,None)
        validationMessage = "\nValidation failed:\n" + self.__lastExecutionStatus 
        #return
      searchPanel = dataSwingManager.createFeatureStoreSearchPanel(store)
      searchPanel.setAutomaticallySearch(False)
      #searchPanel.asJComponent() #Fuerza a inicializar el panel
      st = searchPanel.search(searchParameters)
      if st != FeatureStoreSearchPanel.STATUS_OK:
        self.__lastExecutionStatus = "Failed"+validationMessage
        return
      model = searchPanel.getResultsTableModel()
      n = model.getColumnCount()
      if model.hasErrors():
          self.__lastExecutionStatus = "Failed, error getting number of columns"+validationMessage
          return
      if n<1:
          self.__lastExecutionStatus = "Failed, no columns"+validationMessage
          return
      if self.__result_should_have_rows == "true":
        n = model.getRowCount()
        if model.hasErrors():
          self.__lastExecutionStatus = "Failed, error getting number of rows"+validationMessage
          return
        if n<1:
          self.__lastExecutionStatus = "Failed, no rows"+validationMessage
          return
      if self.__first_row_of_results_must_have_values == "true":
        ok = False
        for columnIndex in range(0,model.getColumnCount()):
          x = model.getValueAt(0, columnIndex)
          if x!=None:
            ok = True
        if model.hasErrors():
          self.__lastExecutionStatus = "Failed, error getting cells of first row"+validationMessage
          return
        if not ok:
          self.__lastExecutionStatus = "Failed, first row empty"+validationMessage
          return
      if model.hasErrors():
          self.__lastExecutionStatus = "Failed, error getting data"+validationMessage
          return
      self.__lastExecutionStatus = STATUS_OK+validationMessage
    except:
      self.__lastExecutionStatus = "Error"+validationMessage
    finally:
      DisposeUtils.disposeQuietly(searchPanel)
      DisposeUtils.disposeQuietly(model)
      DisposeUtils.disposeQuietly(store)

  def isFailed(self):
    return  self.__lastExecutionStatus != STATUS_OK and self.__lastExecutionStatus != STATUS_UNKNOWN
    
def getSearchBookmarks(taskStatus = None):
  if taskStatus == None:
    taskStatus = ToolsLocator.getTaskStatusManager().createDefaultSimpleTaskStatus("Cargando tests")
  searchBookmarks = list()
  folder = gvsig.getResource(__file__,"..","data","searchbookmarks")
  files = os.listdir(folder)
  taskStatus.setRangeOfValues(0,len(files))
  for f in files:
    if taskStatus.isCancellationRequested():
      taskStatus.cancel()
      return
    if f.endswith(".properties") :
      s = os.path.basename(f)
      if len(s)>60:
        s = s[:60] + "..."
      taskStatus.message(s)
      searchBookmark = SearchBookmark(os.path.join(folder,f))
      taskStatus.message(searchBookmark.getName())
      searchBookmark .load()
      searchBookmarks.append(searchBookmark)
    taskStatus.incrementCurrentValue()
  taskStatus.terminate()
  searchBookmarks.sort(key=lambda e:e.getName())
  return searchBookmarks
  
def main(*args):
    for x in getSearchBookmarks():
      print x.getName(), x.getTableName(), x.isEnabled()
