"""
Module of helper functions for building the menus in the menu bar of the MDI (Weasel GUI)
using the definition in an XML file. It calls the `XMLMenuReader.py` in order to read the XML menu file.
"""

from PyQt5.QtWidgets import QAction, QToolTip 
from PyQt5.QtGui import QCursor, QIcon
import os
import sys
import importlib
import logging
logger = logging.getLogger(__name__)

from CoreModules.XMLMenuReader import XMLMenuReader


def setupMenus(weasel, menuXMLFile):
    """Builds the menus in the menu bar of the MDI"""
    try:
        logger.info("Menus.setupMenus")
        mainMenu = weasel.menuBar()
        objXMLMenuReader = XMLMenuReader(menuXMLFile) 
        menus = objXMLMenuReader.getMenus()
        for menu in menus:
            menuName = menu.attrib['name']
            topMenu = mainMenu.addMenu(menuName)
            topMenu.hovered.connect(_actionHovered)
            weasel.menuBuilder.listMenus.append(topMenu)
            for item in menu:
                buildUserDefinedToolsMenuItem(weasel, topMenu, item)
    except Exception as e:
            print('Error in Menus.setupMenus: ' + str(e)) 
            logger.exception('Error in Menus.setupMenus: ' + str(e)) 


def buildUserDefinedToolsMenuItem(weasel, topMenu, item):
    """This method creates one button (`item`) in the `topMenu`."""
    try:
        #create action button on the fly
        logger.info("Menus.buildUserDefinedToolsMenuItem called.")
        if item.find('separator') is not None:
            topMenu.addSeparator()
        else:
            if item.find('icon') is not None:
                icon = item.find('icon').text
                if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                    if os.path.exists(os.path.join(sys._MEIPASS, icon)): icon_path = os.path.join(sys._MEIPASS, icon)
                    else: icon_path = icon
                else: icon_path = icon
                weasel.menuItem = QAction(QIcon(icon_path), item.find('label').text, weasel)
            else:
                weasel.menuItem = QAction(item.find('label').text, weasel)
            if item.find('shortcut') is not None:
                weasel.menuItem.setShortcut(item.find('shortcut').text)
            if item.find('tooltip') is not None:
                weasel.menuItem.setToolTip(item.find('tooltip').text)

            moduleName = item.find('module').text

            if item.find('function') is not None:
                function = item.find('function').text
            else:
                function = "main"
                
            #Walk the directory structure until the modules defined the menu XML are found
            #moduleFileName = [os.path.join(dirpath, moduleName+".py") 
            #    for dirpath, dirnames, filenames in os.walk(pathlib.Path().absolute().parent) if moduleName+".py" in filenames][0]
            moduleFileName = [pythonFilePath for pythonFilePath in weasel.menuBuilder.listPythonFiles if moduleName+".py" in pythonFilePath][0]
            spec = importlib.util.spec_from_file_location(moduleName, moduleFileName)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            objFunction = getattr(module, function)
            weasel.menuItem.triggered.connect(lambda : objFunction(weasel))
            #weasel.menuItem.triggered.connect(lambda : weasel.refresh())

            weasel.menuItem.setEnabled(True)
            weasel.menuItem.setData(module)
          
            topMenu.addAction(weasel.menuItem)
    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        #filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        print('Error in function Menus.buildUserDefinedToolsMenuItem at line number {} when {}: '.format(line_number, item.find('label').text) + str(e))
        logger.exception('Error in Menus.buildUserDefinedToolsMenuItem at line number {} when {}: '.format(line_number, item.find('label').text) + str(e)) 


def buildContextMenuItem(weasel, context, item):
    """This method creates one button (`item`) in the `context`, i.e. in the right-click submenu."""
    try:
        menuItem = QAction(item.find('label').text, weasel)
        menuItem.setEnabled(True)
        moduleName = item.find('module').text
    
        if item.find('function') is not None:
            function = item.find('function').text
        else:
            function = "main"
    
        #moduleFileName = [os.path.join(dirpath, moduleName+".py") 
        #    for dirpath, dirnames, filenames in os.walk(pathlib.Path().absolute()) if moduleName+".py" in filenames][0]
        moduleFileName = [pythonFilePath for pythonFilePath in weasel.menuBuilder.listPythonFiles if moduleName+".py" in pythonFilePath][0]
        spec = importlib.util.spec_from_file_location(moduleName, moduleFileName)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        objFunction = getattr(module, function)
        menuItem.triggered.connect(lambda : objFunction(weasel))
        #menuItem.triggered.connect(lambda : weasel.refresh())
    
        menuItem.setEnabled(True)
        menuItem.setData(module)

        context.addAction(menuItem)
    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        #filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        print('Error in function Menus.buildContextMenuItem at line number {} when {}: '.format(line_number, item.find('label').text) + str(e))
        logger.exception('Error in Menus.buildContextMenuItem at line number {} when {}: '.format(line_number, item.find('label').text) + str(e)) 


def _actionHovered(action):
        """
        Allows a menu item to display a tool tip when the mouse
        pointer hovers over it.
        """
        tip = action.toolTip()
        QToolTip.showText(QCursor.pos(), tip)


def __repr__(self):
       """Represents this class's objects as a string"""
       return '{}, {!r}'.format(
           self.__class__.__name__,
           self.fullFilePath)


def buildContextMenu(weasel, menuXMLFile):
    logger.info("Menus.buildContextMenu called")
    try:
        weasel.menuBuilder.context.hovered.connect(_actionHovered)

        objXMLMenuReader = XMLMenuReader(menuXMLFile) 
        items = objXMLMenuReader.getContextMenuItems()
        for item in items:
            buildContextMenuItem(weasel, weasel.menuBuilder.context, item)

    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        #filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        print('Error in function Menus.buildContextMenu at line number {}: '.format(line_number) + str(e))
        logger.exception('Error in function Menus.buildContextMenu at line number {}: '.format(line_number) + str(e))