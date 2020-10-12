import os
import numpy as np
import random
import pydicom
import itertools
from ast import literal_eval # Convert strings to their actual content. Eg. "[a, b]" becomes the actual list [a, b]
import CoreModules.WEASEL.readDICOM_Image as readDICOM_Image
import CoreModules.WEASEL.saveDICOM_Image as saveDICOM_Image
import CoreModules.WEASEL.TreeView as treeView
import CoreModules.WEASEL.DisplayImageColour as displayImageColour
import CoreModules.WEASEL.MessageWindow as messageWindow
import CoreModules.WEASEL.InterfaceDICOMXMLFile as interfaceDICOMXMLFile
import CoreModules.WEASEL.InputDialog as inputDialog


def NestedDictValues(dictionary):
    """
    This function gets a list of all the values inside a python dictionary,
    regardless of the number of levels present in the dictionary.
    """
    for value in dictionary.values():
        if isinstance(value, dict):
            yield from NestedDictValues(value)
        else:
            yield value


class UserInterfaceTools:
    """
    This class contains functions that read the items selected in the User Interface
    and return variables that are used in processing pipelines. It also contains functions
    that allow the user to insert inputs and give an update of the pipeline steps through
    message windows. 
    """
    @staticmethod 
    def getSelectedStudyID(self):
        """
        Returns the Study ID of the item selected in the Treeview.
        """
        return self.selectedStudy
    

    @staticmethod 
    def getSelectedSeriesID(self):
        """
        Returns the Series ID of the item selected in the Treeview.
        """
        return self.selectedSeries
    

    @staticmethod 
    def getSelectedImage(self):
        """
        Returns a string with the path of the selected image.
        """
        return self.selectedImagePath
    
    
    def getCheckedSeriesIDs(self):
        """
        Returns a list with the Series IDs of the items checked in the Treeview.
        """
        return treeView.returnSelectedSeries(self)
    
    
    def getAllCheckedImages(self):
        """
        Returns a list of strings with the paths of all images checked in the Treeview.
        """
        imagesDict = treeView.returnSelectedImages(self)
        pathsList = list(itertools.chain(*NestedDictValues(imagesDict)))
        if len(pathsList) == 1:
            pathsList = pathsList[0]
        return pathsList
    

    @staticmethod
    def getAllSelectedImages(self):
        """
        Returns a list of strings with the paths of all images selected in the Treeview.
        It includes all images that belong to a selected series.
        """
        studyID = self.selectedStudy
        seriesID = self.selectedSeries
        if len(self.objXMLReader.getImagePathList(studyID, seriesID)) == 1:
            return self.objXMLReader.getImagePathList(studyID, seriesID)[0]
        else:
            return self.objXMLReader.getImagePathList(studyID, seriesID)

    
    def showMessageWindow(self, msg="Please insert message in the function call", title="Message Window Title"):
        """
        Displays a window in the User Interface with the title in "title" and
        with the message in "msg". The 2 strings in the arguments are the input by default.
        """
        messageWindow.displayMessageSubWindow(self, "<H4>" + msg + "</H4>", title)


    def closeMessageWindow(self):
        """
        Closes any message window present in the User Interface.
        """
        messageWindow.closeMessageSubWindow(self)


    def startProgressBar(self, maxNumber=1, msg="Total of {} iterations", title="Progress Bar"):
        """
        Starts and displays a progress bar with a number of units equal to "maxNumber".
        Arguments "title" and "msg" are the title and message to be incorporated in the new window.
        The 2 strings in the arguments are the input by default.
        """
        messageWindow.displayMessageSubWindow(self, ("<H4>" + msg + "</H4>").format(maxNumber), title)
        messageWindow.setMsgWindowProgBarMaxValue(self, maxNumber)


    def incrementProgressBar(self, index=0, msg="Iteration Number {}", title="Progress Bar"):
        """
        Updates the ProgressBar to the unit set in "index".
        """
        messageWindow.displayMessageSubWindow(self, ("<H4>" + msg + "</H4>").format(index), title)
        messageWindow.setMsgWindowProgBarValue(self, index)
    
    
    @staticmethod
    def inputWindow(paramDict, title="Input Parameters", helpText="", lists=None):
        """
        Display a window and prompts the user to insert inputs. The input variables
        and respective types are defined in "paramDict". See below for examples.
        Variable "title" is the title of the window and "helpText" is the text
        displayed inside the window. It should be used to give important notes or 
        tips regarding the input process.

        Eg. of paramDict:
            paramDict = {"Tag":"string", "Value":"string"}
            The variable types are int, float and string.
            The user may add extra validation of the parameters. Read the file
            thresholdDICOM_Image.py as it contains a good example of validation.
        Other eg. of paramDict:
            inputDict = {"Algorithm":"dropdownlist", "Nature":"listview"}
            algorithmList = ["B0", "T2*", "T1 Molli"]
            natureList = ["Animals", "Plants", "Trees"]
            inputWindow(paramDict, ..., lists=[algorithmList, natureList])
        """
        try:
            inputDlg = inputDialog.ParameterInputDialog(paramDict, title=title, helpText=helpText, lists=lists)
            # Return None if the user hits the Cancel button
            if inputDlg.closeInputDialog() == True:
                return None
            listParams = inputDlg.returnListParameterValues()
            outputList = []
            # Sometimes the values parsed could be list or hexadecimals in strings
            for param in listParams:
                try:
                    outputList.append(literal_eval(param))
                except:
                    outputList.append(param)
            return outputList
        except Exception as e:
            print('Error in function #.inputWindow: ' + str(e))


    def displayImage(self, inputPath):
        """
        Display the PixelArray in "inputPath" in the User Interface.
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                _, studyID, seriesID = treeView.getPathParentNode(self, inputPath)
                displayImageColour.displayImageSubWindow(self, studyID, seriesID, derivedImagePath=inputPath)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                _, studyID, seriesID = treeView.getPathParentNode(self, inputPath[0])
                displayImageColour.displayMultiImageSubWindow(self, inputPath, studyID, seriesID)
        except Exception as e:
            print('Error in function #.displayImage: ' + str(e))


class GenericDICOMTools:

    def copyDICOM(self, inputPath, series_id=None, series_uid=None, suffix="_Copy"):
        """
        Creates a DICOM copy of all files in "inputPath" (1 or more) into a new series.
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                if series_id is None:
                    series_id = int(str(readDICOM_Image.getDicomDataset(inputPath).SeriesNumber) + str(random.randint(0, 9999)))
                if series_uid is None:
                    series_uid = pydicom.uid.generate_uid()
                newDataset = readDICOM_Image.getDicomDataset(inputPath)
                derivedPath = saveDICOM_Image.returnFilePath(inputPath, suffix)
                saveDICOM_Image.saveDicomToFile(newDataset, output_path=derivedPath)
                # The next lines perform an overwrite operation over the copied images
                saveDICOM_Image.overwriteDicomFileTag(derivedPath, "SeriesInstanceUID", series_uid)
                saveDICOM_Image.overwriteDicomFileTag(derivedPath, "SeriesNumber", series_id)
                saveDICOM_Image.overwriteDicomFileTag(derivedPath, "SeriesDescription", str(newDataset.SeriesDescription + suffix))
                newSeriesID = interfaceDICOMXMLFile.insertNewImageInXMLFile(self,
                                             derivedPath, suffix)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                derivedPath = []
                if series_id is None:
                    series_id = int(str(readDICOM_Image.getDicomDataset(inputPath[0]).SeriesNumber) + str(random.randint(0, 9999)))
                if series_uid is None:
                    series_uid = pydicom.uid.generate_uid()
                for path in inputPath:
                    newDataset = readDICOM_Image.getDicomDataset(path)
                    newFilePath = saveDICOM_Image.returnFilePath(path, suffix)
                    saveDICOM_Image.saveDicomToFile(newDataset, output_path=newFilePath)
                    derivedPath.append(newFilePath)
                    # The next lines perform an overwrite operation over the copied images
                    saveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesInstanceUID", series_uid)
                    saveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesNumber", series_id)
                    saveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesDescription", str(newDataset.SeriesDescription + suffix))
                newSeriesID = interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self,
                                inputPath, derivedPath, suffix)
            treeView.refreshDICOMStudiesTreeView(self, newSeriesID) 
            return derivedPath
        except Exception as e:
            print('Error in function #.copyDICOM: ' + str(e))


    def deleteDICOM(self, inputPath):
        """
        A window is prompted asking the user if it wishes to delete all images in "inputPath".
        It performs the file removal upon affirmative answer.
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                inputDict = {"Confirmation":"string"}
                paramList = UserInterfaceTools.inputWindow(inputDict, title="Are you sure you want to delete this image?", helpText="Type YES to delete selected images")
                reply = paramList[0]
                if reply=="YES":
                    os.remove(inputPath)
                    interfaceDICOMXMLFile.removeImageFromXMLFile(self, inputPath)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                inputDict = {"Confirmation":"string"}
                paramList = UserInterfaceTools.inputWindow(inputDict, title="Are you sure you want to delete these images?", helpText="Type YES to delete selected images")
                reply = paramList[0]
                if reply=="YES":
                    for path in inputPath:
                        os.remove(path)
                        interfaceDICOMXMLFile.removeMultipleImagesFromXMLFile(self, inputPath)   
            treeView.refreshDICOMStudiesTreeView(self) 
        except Exception as e:
            print('Error in function #.deleteDICOM: ' + str(e))


    def mergeDicomIntoOneSeries(self, imagePathList, series_description="New Series", series_uid=None, series_id=None, suffix="_Merged", overwrite=False):
        """
        Merges all DICOM files in "imagePathList" into 1 series.
        It creates a copy if "overwrite=False" (default).
        """
        try:
            if os.path.exists(imagePathList[0]):
                if series_id is None:
                    series_id = int(str(readDICOM_Image.getDicomDataset(imagePathList[0]).SeriesNumber) + str(random.randint(0, 9999)))
                if series_uid is None:
                    series_uid = pydicom.uid.generate_uid()
            newImagePathList = []
            if overwrite:
                for path in imagePathList:
                    saveDICOM_Image.overwriteDicomFileTag(path, "SeriesInstanceUID", series_uid)
                    saveDICOM_Image.overwriteDicomFileTag(path, "SeriesNumber", series_id)
                    saveDICOM_Image.overwriteDicomFileTag(path, "SeriesDescription", series_description + suffix)
                newImagePathList = imagePathList
                newSeriesID = interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self,
                                imagePathList, newImagePathList, suffix)
                interfaceDICOMXMLFile.removeMultipleImagesFromXMLFile(self, imagePathList)     
            else:
                for path in imagePathList:
                    newDataset = readDICOM_Image.getDicomDataset(path)
                    newFilePath = saveDICOM_Image.returnFilePath(path, suffix)
                    saveDICOM_Image.saveDicomToFile(newDataset, output_path=newFilePath)
                    # The next lines perform an overwrite operation over the copied images
                    saveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesInstanceUID", series_uid)
                    saveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesNumber", series_id)
                    saveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesDescription", series_description + suffix)
                    newImagePathList.append(newFilePath)
                # CAN WE UPDATE THE XML FILE WITHOUT THE SUFFIX AND IMAGE PATH LIST???
                newSeriesID = interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self,
                                imagePathList, newImagePathList, suffix)
            treeView.refreshDICOMStudiesTreeView(self, newSeriesID)
            return newImagePathList
        except Exception as e:
            print('Error in #.mergeDicomIntoOneSeries: ' + str(e))


    @staticmethod
    def editDICOMTag(inputPath, dicomTag, newValue):
        """
        Overwrites all "dicomTag" of the DICOM files in "inputPath"
        with "newValue".
        """
        # CONSIDER THE CASES WHERE SERIES NUMBER, NAME AND UID ARE CHANGED - UPDATE XML
        try:
            saveDICOM_Image.overwriteDicomFileTag(inputPath, dicomTag, newValue)
        except Exception as e:
            print('Error in function #.editDICOMTag: ' + str(e))

    #def generateUIDForDICOM():
        #return 

class PixelArrayDICOMTools:
    
    @staticmethod
    def getPixelArrayFromDICOM(inputPath):
        """
        Returns the PixelArray of the DICOM file(s) in "inputPath".
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                pixelArray = readDICOM_Image.returnPixelArray(inputPath)
                return pixelArray
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                pixelArray = readDICOM_Image.returnSeriesPixelArray(inputPath)
                return pixelArray
            else:
                return None
        except Exception as e:
            print('Error in function #.getPixelArrayFromDICOM: ' + str(e))


    @staticmethod
    def getDICOMobject(inputPath):
        """
        Returns the DICOM object (or list of DICOM objects) of the file(s) in "inputPath".
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                dataset = readDICOM_Image.getDicomDataset(inputPath)
                return dataset
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                dataset = readDICOM_Image.getSeriesDicomDataset(inputPath)
                return dataset
            else:
                return None
        except Exception as e:
            print('Error in function #.getDICOMobject: ' + str(e))


    def writeNewPixelArray(self, pixelArray, inputPath, suffix):
        # OPTIONAL FLAGS OF SERIES / CREATE A GENERATE_UID FUNCTION
        """
        Saves the "pixelArray" into new DICOM files with a new series, based
        on the "inputPath" and on the "suffix".
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                numImages = 1
                derivedImageList = [pixelArray]
                derivedImageFilePath = saveDICOM_Image.returnFilePath(inputPath, suffix)
                derivedImagePathList = [derivedImageFilePath]

            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                if hasattr(readDICOM_Image.getDicomDataset(inputPath[0]), 'PerFrameFunctionalGroupsSequence'):
                    # If it's Enhanced MRI
                    numImages = 1
                    derivedImageList = [pixelArray]
                    derivedImageFilePath = saveDICOM_Image.returnFilePath(inputPath[0], suffix)
                    derivedImagePathList = [derivedImageFilePath]
                else:
                    # Iterate through list of images (slices) and save the resulting Map for each DICOM image
                    numImages = (1 if len(np.shape(pixelArray)) < 3 else np.shape(pixelArray)[0])
                    derivedImagePathList = []
                    derivedImageList = []
                    for index in range(numImages):
                        derivedImageFilePath = saveDICOM_Image.returnFilePath(inputPath[index], suffix)
                        derivedImagePathList.append(derivedImageFilePath)
                        if numImages==1:
                            derivedImageList.append(pixelArray)
                        else:
                            derivedImageList.append(pixelArray[index, ...])
                    if len(inputPath) > len(derivedImagePathList):
                        inputPath = inputPath[:len(derivedImagePathList)]

            if numImages == 1:    
                saveDICOM_Image.saveNewSingleDicomImage(derivedImagePathList[0], inputPath, derivedImageList[0], suffix, list_refs_path=[inputPath])
                # Record derived image in XML file
                newSeriesID = interfaceDICOMXMLFile.insertNewImageInXMLFile(self,
                                derivedImagePathList[0], suffix)
            else:
                saveDICOM_Image.saveDicomNewSeries(derivedImagePathList, inputPath, derivedImageList, suffix, list_refs_path=[inputPath])
                # Insert new series into the DICOM XML file
                newSeriesID = interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self,
                                inputPath, derivedImagePathList, suffix)
            treeView.refreshDICOMStudiesTreeView(self, newSeriesID)
            return derivedImagePathList

        except Exception as e:
            print('Error in function #.writePixelArrayToDicom: ' + str(e))


    @staticmethod
    def overwritePixelArray(pixelArray, inputPath):
        """
        Overwrites the DICOM files in the "pixelArray" into new DICOM files with a new series, based
        on the "inputPath" and on the "suffix".
        """
        try:
            if isinstance(inputPath, list):
                datasetList = readDICOM_Image.getSeriesDicomDataset(inputPath)
                for index, dataset in enumerate(datasetList):
                    modifiedDataset = saveDICOM_Image.createNewPixelArray(pixelArray, dataset)
                    saveDICOM_Image.saveDicomToFile(modifiedDataset, output_path=inputPath[index])
            else:
                dataset = readDICOM_Image.getDicomDataset(inputPath)
                modifiedDataset = saveDICOM_Image.createNewPixelArray(pixelArray, dataset)
                saveDICOM_Image.saveDicomToFile(modifiedDataset, output_path=inputPath)
            return
        except Exception as e:
            print('Error in #.overwritePixelArray: ' + str(e))

