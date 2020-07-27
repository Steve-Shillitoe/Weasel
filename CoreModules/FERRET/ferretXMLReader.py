"""
This class module contains functionality for loading and 
parsing an XML configuration file that describes the model(s)
to be used for curve fitting time/concentration data.

It also contains functions for retrieving data from 
parsed XML tree held in memory.

It uses the functionality provided by the xml.etree.ElementTree
package.
"""
import xml.etree.ElementTree as ET  
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

FIRST_ITEM_MODEL_LIST = 'Select a model'
NO_MODELS_DEFINED_IN_CONFIG_FILE = 'No models defined in config file'

# User-defined exceptions
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ValueNotDefinedInConfigFile(Error):
   """Raised when no model constants are defined in 
   the XML configuration file."""
   pass

class CannotFormFullParameterName(Error):
   """Raised if the short and long names of a parameter 
   are not defined in the XML configuration file."""
   pass


class FerretXMLReader:
    def __init__(self): 
        try:
            self.hasXMLFileParsedOK = True
            self.fullFilePath = ""
            self.tree = None 
            self.root = None 

            logger.info('In module ' + __name__ + ' Created XML Reader Object')

        except Exception as e:
            print('Error in FerretXMLReader.__init__: ' + str(e)) 
            logger.error('Error in FerretXMLReader.__init__: ' + str(e)) 
            
    def parseXMLFile(self, fullFilePath): 
        """Loads and parses the XML configuration file at fullFilePath.
       After successful parsing, the XML tree and its root node
      is stored in memory."""
        try:
            self.hasXMLFileParsedOK = True
            self.fullFilePath = fullFilePath
            self.tree = ET.parse(fullFilePath)
            self.root = self.tree.getroot()
            return self.root
            # Uncomment to test XML file loaded OK
            #print(ET.tostring(self.root, encoding='utf8').decode('utf8'))
           
            logger.info('In module ' + __name__ 
                    + '.parseConfigFile ' + fullFilePath)

        except ET.ParseError as et:
            print('FerretXMLReader.parseConfigFile error: ' + str(et)) 
            logger.error('FerretXMLReader.parseConfigFile error: ' + str(et))
            self.hasXMLFileParsedOK = False
            
        except Exception as e:
            print('Error in FerretXMLReader.parseConfigFile: ' + str(e)) 
            logger.error('Error in FerretXMLReader.parseConfigFile: ' + str(e)) 
            self.hasXMLFileParsedOK = False

    def getImagePathListForSeries(self, studyID, seriesID):
        try:
            xPath = './study[@id=' + chr(34) + studyID + chr(34) + \
            ']/series[@id=' + chr(34) + seriesID + chr(34) + ']/image'
            images = self.root.findall(xPath)
            imageList = [image.find('name').text for image in images]
            return imageList
        except Exception as e:
            print('Error in getImagePathListForSeries: ' + str(e))


    def getListModelShortNames(self):
        """Returns a list of model short names for display
        in a combo dropdown list on the application GUI """
        try:
            tempList = []
            shortModelNames = self.root.findall('./model/name/short')

            if not shortModelNames:
                tempList.append(NO_MODELS_DEFINED_IN_CONFIG_FILE)
                raise ValueNotDefinedInConfigFile
            else:
                tempList = [name.text 
                        for name in shortModelNames]

            # Insert string 'Select a model' as the start of the list
            tempList.insert(0, FIRST_ITEM_MODEL_LIST)
            return tempList

        except ValueNotDefinedInConfigFile:
            warningString = 'Error - No models defined in the configuration file.'
            print(warningString)
            logger.error('FerretXMLReader.getListModelShortNames - ' + warningString)
            return tempList
        except ET.ParseError as et:
            print('FerretXMLReader.getListModelShortNames XPath error: ' + str(et)) 
            logger.error('FerretXMLReader.getListModelShortNames XPath error: ' + str(et))
        except Exception as e:
            print('Error in FerretXMLReader.getListModelShortNames: ' + str(e)) 
            logger.error('Error in FerretXMLReader.getListModelShortNames: ' + str(e)) 
    

    def getFunctionName(self, shortModelName):
        """Returns the name of the function that 
        contains the logic corresponding to the model
       with a short name in the string variable shortModelName"""
        try:
            logger.info('FerretXMLReader.getFunctionName called with short model name= ' + shortModelName)
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) +']..function'
                functionName = self.root.find(xPath)
                if functionName.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    logger.info('FerretXMLReader.getFunctionName found function name ' + functionName.text)
                    return functionName.text
            else:
                return None

        except ValueNotDefinedInConfigFile:
            warningString = 'Error - No function defined for model {}'.format(shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getFunctionName - ' + warningString)
            return None
        except Exception as e:
            print('Error in FerretXMLReader.getFunctionName when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getFunctionName when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            return None

    def getModuleName(self, shortModelName):
        """Returns the name of the module that 
        contains the function corresponding to the model
       with a short name in the string variable shortModelName"""
        try:
            logger.info('FerretXMLReader.getModuleName called with short model name= ' 
                        + shortModelName)
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) +']..module'
                moduleName = self.root.find(xPath)
                if moduleName.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    logger.info('FerretXMLReader.getModuleName found module name ' 
                                + moduleName.text)
                    return moduleName.text
            else:
                return None

        except ValueNotDefinedInConfigFile:
            warningString = 'Error - No module defined for model {}'.format(shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getFunctionName - ' + warningString)
            return None
        except Exception as e:
            print('Error in FerretXMLReader.getModuleName when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getModuleName when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            return None


    def getYAxisLabel(self):
        """Returns the text of the Y Axis Label use
       with the model with a short name 
        in the string variable shortModelName when
        its output is plotted against time."""
        try:
            logger.info('FerretXMLReader.getYAxisLabel called')
            
            xPath='./plot/y_axis_label'
            yAxisLabel = self.root.find(xPath)
            if yAxisLabel.text is None:
                raise ValueNotDefinedInConfigFile
            else:
                logger.info('FerretXMLReader.getYAxisLabel found Y Axis Label' 
                            + yAxisLabel.text)
                return yAxisLabel.text
            
        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - FerretXMLReader.getYAxisLabel - No Y axis label defined'
            print(warningString)
            logger.info(warningString)
            return 'No Y Axis Label defined in the configuration file.'
        except Exception as e:
            print('Error in FerretXMLReader.getYAxisLabel: ' + str(e)) 
            logger.error('Error in FerretXMLReader.getYAxisLabel: ' + str(e)) 
            return ''


    def getImageName(self, shortModelName):
        """Returns the name of the image that represents the model
       with a short name in the string variable shortModelName"""
        try:
            logger.info('FerretXMLReader.getImageName called with short model name= ' + shortModelName)
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) +']..image'
                imageName = self.root.find(xPath)
                if imageName.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    logger.info('FerretXMLReader.getImageName found image ' + imageName.text)
                    return imageName.text
            else:
                return None

        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - The name of an image describing model {}' \
                .format(shorModelName) +' is not defined in the configuration file.'
            print(warningString)
            logger.info('FerretXMLReader.getImageName - ' + waringString)
            return None
        except Exception as e:
            print('Error in FerretXMLReader.getImageName when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getImageName when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            return None


    def getLongModelName(self, shortModelName):
        """Returns the long name of the model
       with a short name in the string variable shortModelName"""
        try:
            logger.info('FerretXMLReader.getLongModelName called with short model name= ' + shortModelName)
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) +']/long'
                modelName = self.root.find(xPath)
                if modelName.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    logger.info('FerretXMLReader.getLongModelName found long model name ' + \
                        modelName.text)
                    return modelName.text
            else:
                return None
        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - No long name defined for this model in the configuration file'
            print(warningString)
            logger.info('FerretXMLReader.getLongModel - '   + NamewarningString)
            return 'No long name defined for this model'
        except Exception as e:
            print('Error in FerretXMLReader.getLongModelName when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getLongModelName when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            return None


    def getModelInletType(self, shortModelName):
        """Returns the inlet type (single or dual) of the model
       with a short name in the string variable shortModelName"""
        try:
            logger.info('FerretXMLReader.getModelInletType called with short model name= ' + shortModelName)
            if len(shortModelName) > 0 and \
                shortModelName != FIRST_ITEM_MODEL_LIST and \
                shortModelName != NO_MODELS_DEFINED_IN_CONFIG_FILE:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) +']..inlet_type'
                modelInletType= self.root.find(xPath)
                if modelInletType.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    logger.info('FerretXMLReader.getModelInletType found model inlet type ' + modelInletType.text)
                    return modelInletType.text
            else:
                return None

        except ValueNotDefinedInConfigFile:  
            warningString = 'Error - No model inlet type defined in the config file'
            print(warningString)
            logger.info('FerretXMLReader.getModelInletType - ' + warningString)
            return None
        except Exception as e:
            print('Error in FerretXMLReader.getModelInletType when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getModelInletType when shortModelName ={}: '.format(shortModelName) 
                  + str(e)) 
            return None


    def getNumberOfParameters(self, shortModelName) ->int:
        """Returns the number of input parameters to the model whose
       short name is stored in the string variable shortModelName."""
        try:
            logger.info('FerretXMLReader.getNumberOfParameters called with short model name= ' + shortModelName)
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) +']..parameters/parameter'
                parameters = self.root.findall(xPath)
                if parameters:
                    numParams = len(parameters)
                    return numParams
                else:
                    raise ValueNotDefinedInConfigFile
            else:
                return 0

        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - No parameters defined when shortModelName = {} and xPath= {}: '.format(shortModelName, xPath) 
            print(warningString)
            logger.info('FerretXMLReader.getNumberOfParameters - ' + warningString)
            return 0
        except Exception as e:
            print('Error in FerretXMLReader.getNumberOfParameters when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getNumberOfParameters when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return 0


    def getParameterLabel(self, shortModelName, positionNumber):
        """Returns the full name and units of the parameter to be
        displayed in the parameter label on the application GUI.

        Input Parameters
        ----------------
        shortModelName - Identifies the model.
        positionNumber - The ordinal position of the parameter in the 
                        model's parameter collection. Numbers from one."""
        try:
            logger.info('FerretXMLReader.getParameterLabel called with short model name= {} and position={} '.format(shortModelName,positionNumber) )
            isPercentage = False
            missingShortName = False
            missingLongName = False

            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/name/short'
               
                shortName = self.root.find(xPath)
                if shortName.text is None:
                    missingShortName = True
                    print('short name for parameter at position {} is missing.'.format(str(positionNumber)))

                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/name/long'
                longName = self.root.find(xPath)
                if longName.text is None:
                    missingLongName = True
                    print('Long name for parameter at position {} is missing.'.format(str(positionNumber)))

                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/units'
                units = self.root.find(xPath)
                if units.text is None:
                    print('Units for parameter at position {} are missing.'.format(str(positionNumber)))
                else:
                    if units.text == '%':
                        isPercentage = True
                
                if missingShortName and missingLongName:
                    raise CannotFormFullParameterName
                else:
                    fullName = longName.text + ', ' + \
                            shortName.text + \
                            '(' + units.text + ')'

                return isPercentage, fullName
        except CannotFormFullParameterName:
            warningString = 'Warning - Cannot form the full name for parameter at position {}'.format(str(positionNumber))
            print (warningString)
            logger.info('FerretXMLReader.getParameterLabel - ' + warningString)
            return False, 'Cannot form full parameter name'
        except Exception as e:
            print('Error in FerretXMLReader.getParameterLabel when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getParameterLabel when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return None, ''


    def getParameterShortName(self, shortModelName, positionNumber):
        """Returns the short name of a parameter.

        Input Parameters
        ----------------
        shortModelName - Identifies the model.
        positionNumber - The ordinal position of the parameter in the 
                        model's parameter collection. Numbers from one."""
        try:
            logger.info('FerretXMLReader.getParameterShortName called with short model name= {} and position={} '.format(shortModelName,positionNumber) )
            
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/name/short'
                shortName = self.root.find(xPath)
            else:
                return ''

            if shortName.text is None:
                raise ValueNotDefinedInConfigFile
            else:
                return shortName.text

        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - No short name defined for the parameter '  + \
                    'at position {} when the model short = {}'.format(positionNumber, shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getParameterShortName - ' + warningString)
            return ''
        except Exception as e:
            print('Error in FerretXMLReader.getParameterShortName when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getParameterShortName when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return ''


    def getParameterDefault(self, shortModelName, positionNumber)->float:
        """
        Returns the default value for parameter in ordinal position,
        positionNumber, of the parameter collection of the model whose
        short name is shortModelName.
        """
        try:
            logger.info('FerretXMLReader.getParameterDefault called with short model name= {} and position={} '.format(shortModelName,positionNumber) )
            
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/default'
                default = self.root.find(xPath)
                #print('Default ={} when position={}'.format(default.text, positionNumber))
                if default.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    return float(default.text)
            else:
                return 0.0

        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - No default value defined for the parameter '  + \
                    'at position {} when the model short = {}'.format(positionNumber, shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getParameterDefault - ' + warningString)
            return 0.0
        except Exception as e:
            print('Error in FerretXMLReader.getParameterDefault when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getParameterDefault when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return 0.0


    def getParameterStep(self, shortModelName, positionNumber)->float:
        """
        Returns the spinbox step value for parameter in ordinal position,
        positionNumber, of the parameter collection of the model whose
        short name is shortModelName. Parameter values are displayed in a
        spinbox on the application GUI. When the spinbox arrows are clicked,
        the parameter value is changed by the value of step.
        """
        try:
            logger.info('FerretXMLReader.getParameterStep called with short model name= {} and position={} '.format(shortModelName,positionNumber) )
            
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/step'
                step = self.root.find(xPath)

                if step.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    return float(step.text)
            else:
                return 0.0

        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - No increment/decrement step value defined for the parameter '  + \
                    'at position {} when the model short = {}'.format(positionNumber, shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getParameterStep - ' + warningString)
            return 0.0
        except Exception as e:
            print('Error in FerretXMLReader.getParameterStep when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getParameterStep when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return 0.0


    def getParameterPrecision(self, shortModelName, positionNumber)->int:
        """
        Returns the number of decimal places to be displayed in the spinbox 
        for parameter in ordinal position, positionNumber, of the parameter 
        collection of the model whose short name is shortModelName. 
        Parameter values are displayed in a spinbox on the application GUI.
        """
        try:
            logger.info('FerretXMLReader.getParameterPrecision called with short model name= {} and position={} '.format(shortModelName,positionNumber) )
            
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/precision'
                precision = self.root.find(xPath)

                if precision.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    return int(precision.text)
            else:
                return 0

        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - Number of decimal places is not defined for the parameter '  + \
                    'at position {} when the model short = {}'.format(positionNumber, shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getParameterPrecision - ' + warningString)
            return 0
        except Exception as e:
            print('Error in FerretXMLReader.getParameterPrecision when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getParameterPrecision when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return 0.0


    def getMaxParameterDisplayValue(self, shortModelName, positionNumber)->float:
        """
        Returns the maximum value allowed 
        in the spinbox for the parameter in ordinal position,
        positionNumber, of the parameter collection of the model whose
        short name is shortModelName. Parameter values are displayed in a
        spinbox on the application GUI.
        """
        try:
            logger.info('FerretXMLReader.getMaxParameterDisplayValue called with short model name= {} and position={} '.format(shortModelName,positionNumber) )
            
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/display_value/max'
                max = self.root.find(xPath)

                if max.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    return float(max.text)
                
        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - Maximum value allowed in the spinbox for the parameter '  + \
                    'at position {} when the model short = {} is not defined'.format(positionNumber, shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getMaxParameterDisplayValue - ' + warningString)
            return None
        except Exception as e:
            print('Error in FerretXMLReader.getMaxParameterDisplayValue when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getMaxParameterDisplayValue when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return None


    def getMinParameterDisplayValue(self, shortModelName, positionNumber)->float:
        """
        Returns the maximum value allowed 
        in the spinbox for the parameter in ordinal position,
        positionNumber, of the parameter collection of the model whose
        short name is shortModelName. Parameter values are displayed in a
        spinbox on the application GUI.
        """
        try:
            logger.info('FerretXMLReader.getMinParameterDisplayValue called with short model name= {} and position={} '.format(shortModelName,positionNumber) )
            
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/display_value/min'
                min = self.root.find(xPath)

                if min.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    return float(min.text)
                
        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - Minimum value allowed in the spinbox for the parameter '  + \
                    'at position {} when the model short = {} is not defined'.format(positionNumber, shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getMinParameterDisplayValue - ' + warningString)
            return None
        except Exception as e:
            print('Error in FerretXMLReader.getMinParameterDisplayValue when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getMinParameterDisplayValue when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return None
    

    def getUpperParameterConstraint(self, shortModelName, positionNumber)->float:
        """
        Returns the upper constraint value for curve fitting
        for the parameter in ordinal position,
        positionNumber, of the parameter collection of the model whose
        short name is shortModelName. Parameter values are displayed in a
        spinbox on the application GUI.
        """
        try:
            logger.info('FerretXMLReader.getUpperParameterConstraint called with short model name= {} and position={} '.format(shortModelName,positionNumber) )
            
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/constraints/upper'
                upper = self.root.find(xPath)

                if upper.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    return float(upper.text)
                
        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - Upper constraint for curve fitting for the parameter '  + \
                    'at position {} when the model short = {} is not defined'.format(positionNumber, shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getUpperParameterConstraint - ' + warningString)
            return None
        except Exception as e:
            print('Error in FerretXMLReader.getUpperParameterConstraint when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getUpperParameterConstraint when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return None


    def getLowerParameterConstraint(self, shortModelName, positionNumber)->float:
        """
        Returns the lower constraint value for curve fitting
        for the parameter in ordinal position,
        positionNumber, of the parameter collection of the model whose
        short name is shortModelName. Parameter values are displayed in a
        spinbox on the application GUI.
        """
        try:
            logger.info('FerretXMLReader.getLowerParameterConstraint called with short model name= {} and position={} '.format(shortModelName,positionNumber) )
            
            if len(shortModelName) > 0:
                xPath='./model/name[short=' + chr(34) + shortModelName + chr(34) + \
                    ']..parameters/parameter[' + str(positionNumber) + ']/constraints/lower'
                lower = self.root.find(xPath)

                if lower.text is None:
                    raise ValueNotDefinedInConfigFile
                else:
                    return float(lower.text)
                
        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - Lower constraint for curve fitting for the parameter '  + \
                    'at position {} when the model short = {} is not defined'.format(positionNumber, shortModelName)
            print(warningString)
            logger.info('FerretXMLReader.getLowerParameterConstraint - ' + warningString)
            return None
        except Exception as e:
            print('Error in FerretXMLReader.getLowerParameterConstraint when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getLowerParameterConstraint when shortModelName ={} and xPath={}: '.format(shortModelName, xPath) 
                  + str(e)) 
            return None


    def getDataFileFolder(self)->str:
        """ Returns the path to the folder where the data files are stored"""
        try:
            logger.info('FerretXMLReader.getDataFileFolder called')
           
            xPath='./data_file_path'
            dataFileFolder = self.root.find(xPath)

            if dataFileFolder.text is None:
                raise ValueNotDefinedInConfigFile
            else:
                return dataFileFolder.text

        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - Path to folder containing data files is not defined'
            print(warningString)
            logger.info('FerretXMLReader.getDataFileFolder - ' + warningString)
            return ''
        except Exception as e:
            print('Error in FerretXMLReader.getDataFileFolder:' 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getDataFileFolder:' 
                  + str(e)) 
            return ''
        

    def getStringOfConstants(self):
        """ Returns a string representation of a dictionary of
            model constant name:value pairs."""
        try:
            logger.info('FerretXMLReader.getStringOfConstants called')
           
            xPath='./constants/constant'
            collectionConstants = self.root.findall(xPath)

            if not collectionConstants:
                raise ValueNotDefinedInConfigFile
            else:
                constantsDict = {}
                for constant in collectionConstants:
                    name = constant.find('name').text
                    value = constant.find('value').text
                    constantsDict[name] = value

            #Return a string representation of the
            #dictionary
            return str(constantsDict)
        
        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - FerretXMLReader.getStringOfConstants - No model constants defined.'
            print(warningString)
            logger.info(warningString)
            return ''
        except Exception as e:
            print('Error in FerretXMLReader.getStringOfConstants:' 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getStringOfConstants:' 
                  + str(e)) 
            return ''

    def getNumBaselineScans(self):
        """ Gets the number of the baseline scans."""
        try:
            logger.info('FerretXMLReader.getNumBaselineScans called')
           
            xPath="./constants/constant[name ='baseline']/value"
            baselineValue = self.root.find(xPath)

            if baselineValue is None:
                raise ValueNotDefinedInConfigFile
            else:
                return int(baselineValue.text)
        
        except ValueNotDefinedInConfigFile:
            warningString = 'Warning - FerretXMLReader.getNumBaselineScans - No baseline value defined.'
            print(warningString)
            logger.info(warningString)
            return 1
        except Exception as e:
            print('Error in FerretXMLReader.getNumBaselineScans: ' 
                  + str(e)) 
            logger.error('Error in FerretXMLReader.getNumBaselineScans: ' 
                  + str(e)) 
            return 1