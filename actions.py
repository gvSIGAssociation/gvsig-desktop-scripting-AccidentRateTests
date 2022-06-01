# encoding: utf-8

import gvsig

from gvsig import getResource

from java.io import File
from org.gvsig.andami import PluginsLocator
from org.gvsig.app import ApplicationLocator
from org.gvsig.scripting.app.extension import ScriptingExtension
from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator

from addons.AccidentRateTests.searchbookmarkspanel import TestSearchBookmarsPanel

class AccidentRateTestsExtension(ScriptingExtension):
  def __init__(self):
    pass

  def canQueryByAction(self):
    return True

  def isEnabled(self,action):
    return True

  def isVisible(self,action):
    return True
    
  def execute(self,actionCommand, *args):
    actionCommand = actionCommand.lower()
    if actionCommand == "tools-accidentrate-testsearchbookmars":
      TestSearchBookmarsPanel().showWindow("Test favoritos de la ficha de busqueda"))

def selfRegister():
  application = ApplicationLocator.getManager()

  #
  # Registramos las traducciones
  i18n = ToolsLocator.getI18nManager()
  i18n.addResourceFamily("text",File(getResource(__file__,"i18n")))

  #
  # Registramos los iconos en el tema de iconos
  icon = File(getResource(__file__,"images","testsearchbookmars.png")).toURI().toURL()
  iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
  iconTheme.registerDefault("scripting.AccidentRateTestsExtension", "action", "tools-accidentrate-testsearchbookmars", None, icon)

  #
  # Creamos la accion 
  extension = SQLWorkbenchJExtension()
  actionManager = PluginsLocator.getActionInfoManager()
  action = actionManager.createAction(
    extension, 
    "tools-accidentrate-testsearchbookmars", # Action name
    u"TestSearchBookmars", # Text
    "tools-accidentrate-testsearchbookmars", # Action command
    "tools-accidentrate-testsearchbookmars", # Icon name
    None, # Accelerator
    650700601, # Position 
    u"TestSearchBookmars" # Tooltip
  )
  action = actionManager.registerAction(action)
  application.addMenu(action, u"tools/TestSearchBookmars")
      
def main(*args):
   #selfRegister()
   pass
   
   