# encoding: utf-8

import gvsig

import os
from java.io import FileInputStream
from java.util import Properties

from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.dispose import DisposeUtils

from org.gvsig.fmap.dal import DALLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.fmap.dal.swing.searchpanel import  FeatureStoreSearchPanel 

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
      
  def run(self):
    if not self.__enabled:
      self.__lastExecutionStatus = "unknown"
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
        return
    except:
        self.__lastExecutionStatus = "Table not open"
        return
    
    try:
      searchPanel = dataSwingManager.createFeatureStoreSearchPanel(store)
      st = searchPanel.search(self.__searchParameters)
      if st != FeatureStoreSearchPanel.STATUS_OK:
        self.__lastExecutionStatus = "Failed"
        return
      model = searchPanel.getResultsTableModel()
      if model.getColumnCount()<1:
          self.__lastExecutionStatus = "Failed, no columns"
          return
      if self.__result_should_have_rows == "true":
        if model.getRowCount()<1:
          self.__lastExecutionStatus = "Failed, no rows"
          return
      if self.__first_row_of_results_must_have_values == "true":
        ok = False
        for columnIndex in range(0,model.getColumnCount()):
          x = model.getValueAt(0, columnIndex)
          if x!=None:
            ok = True
        if not ok:
          self.__lastExecutionStatus = "Failed, first row empty"
          return
      self.__lastExecutionStatus = "Ok"
    except:
      self.__lastExecutionStatus = "Error"
    finally:
      DisposeUtils.dispose(model)
      DisposeUtils.dispose(store)
      DisposeUtils.dispose(store)


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
  return searchBookmarks
  
def main(*args):
    for x in getSearchBookmarks():
      print x.getName(), x.getTableName(), x.isEnabled()
