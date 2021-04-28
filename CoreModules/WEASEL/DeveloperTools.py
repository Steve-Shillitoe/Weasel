import os
import time
import numpy as np
import random
import pydicom
import nibabel as nib
import copy
import itertools
import logging
import warnings
from PyQt5.QtWidgets import (QMessageBox, QFileDialog)
from ast import literal_eval # Convert strings to their actual content. Eg. "[a, b]" becomes the actual list [a, b]
import CoreModules.WEASEL.ReadDICOM_Image as ReadDICOM_Image
import CoreModules.WEASEL.SaveDICOM_Image as SaveDICOM_Image
import CoreModules.WEASEL.TreeView as treeView
import CoreModules.WEASEL.DisplayImageColour as displayImageColour
import CoreModules.WEASEL.MessageWindow as messageWindow
import CoreModules.WEASEL.InterfaceDICOMXMLFile as interfaceDICOMXMLFile
import CoreModules.WEASEL.InputDialog as inputDialog
from CoreModules.WEASEL.ViewMetaData import displayMetaDataSubWindow

logger = logging.getLogger(__name__)

class UserInterfaceTools:
    """
    This class contains functions that read the items selected in the User Interface
    and return variables that are used in processing pipelines. It also contains functions
    that allow the user to insert inputs and give an update of the pipeline steps through
    message windows. 
    """

    def __init__(self, objWeasel):
        self.objWeasel = objWeasel

    # May be redundant
    def getCurrentSubject(self):
        """
        Returns the Subject ID of the latest item selected in the Treeview.
        """
        return self.objWeasel.selecteSubject

    # May be redundant
    def getCurrentStudy(self):
        """
        Returns the Study ID of the latest item selected in the Treeview.
        """
        return self.objWeasel.selectedStudy

    # May be redundant
    def getCurrentSeries(self):
        """
        Returns the Series ID of the latest item selected in the Treeview.
        """
        return self.objWeasel.selectedSeries
    
    # May be redundant
    def getCurrentImage(self):
        """
        Returns a string with the path of the latest selected image.
        """
        return self.objWeasel.selectedImagePath
    
    # Need to do one for subjects and to include treeView.buildListsCheckedItems(self)

    def getCheckedSubjects(self):
        """
        Returns a list with objects of class Subject of the items checked in the Treeview.
        """
        subjectList = []
        subjectsTreeViewList = treeView.returnCheckedSubjects(self.objWeasel)
        if subjectsTreeViewList == []:
            self.showMessageWindow(msg="Script didn't run successfully because"
                              " no subjects were checked in the Treeview.",
                              title="No Subjects Checked")
            return 
        else:
            for subject in subjectsTreeViewList:
                subjectList.append(Subject.fromTreeView(self.objWeasel, subject))
        return subjectList

    def getCheckedStudies(self):
        """
        Returns a list with objects of class Study of the items checked in the Treeview.
        """
        studyList = []
        studiesTreeViewList = treeView.returnCheckedStudies(self.objWeasel)
        if studiesTreeViewList == []:
            self.showMessageWindow(msg="Script didn't run successfully because"
                              " no studies were checked in the Treeview.",
                              title="No Studies Checked")
            return 
        else:
            for study in studiesTreeViewList:
                studyList.append(Study.fromTreeView(self.objWeasel, study))
        return studyList
    

    def getCheckedSeries(self):
        """
        Returns a list with objects of class Series of the items checked in the Treeview.
        """
        seriesList = []
        seriesTreeViewList = treeView.returnCheckedSeries(self.objWeasel)
        if seriesTreeViewList == []:
            self.showMessageWindow(msg="Script didn't run successfully because"
                              " no series were checked in the Treeview.",
                              title="No Series Checked")
            return 
        else:
            for series in seriesTreeViewList:
                seriesList.append(Series.fromTreeView(self.objWeasel, series))
        return seriesList
    

    def getCheckedImages(self):
        """
        Returns a list with objects of class Image of the items checked in the Treeview.
        """
        imagesList = []
        imagesTreeViewList = treeView.returnCheckedImages(self.objWeasel)
        if imagesTreeViewList == []:
            self.showMessageWindow(msg="Script didn't run successfully because"
                              " no images were checked in the Treeview.",
                              title="No Images Checked")
            return
        else:
            for images in imagesTreeViewList:
                imagesList.append(Image.fromTreeView(self.objWeasel, images))
        return imagesList

    
    def showMessageWindow(self, msg="Please insert message in the function call", title="Message Window Title"):
        """
        Displays a window in the User Interface with the title in "title" and
        with the message in "msg". The 2 strings in the arguments are the input by default.
        """
        messageWindow.displayMessageSubWindow(self.objWeasel, "<H4>" + msg + "</H4>", title)


    def showInformationWindow(self, title="Message Window Title", msg="Please insert message in the function call"):
        """
        Displays an information window in the User Interface with the title in "title" and
        with the message in "msg". The 2 strings in the arguments are the input by default.
        The user has to click "OK" in order to continue using the interface.
        """
        QMessageBox.information(self.objWeasel, title, msg)


    def showErrorWindow(self, msg="Please insert message in the function call"):
        """
        Displays an error window in the User Interface with the title in "title" and
        with the message in "msg". The 2 strings in the arguments are the input by default.
        The user has to click "OK" in order to continue using the interface.
        """
        QMessageBox.critical(self.objWeasel, title, msg)


    def showQuestionWindow(self, title="Message Window Title", question="You wish to proceed (OK) or not (Cancel)?"):
        """
        Displays a question window in the User Interface with the title in "title" and
        with the question in "question". The 2 strings in the arguments are the input by default.
        The user has to click either "OK" or "Cancel" in order to continue using the interface.

        It returns 0 if reply is "Cancel" and 1 if reply is "OK".
        """
        buttonReply = QMessageBox.question(self, title, question, 
                      QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
        if buttonReply == QMessageBox.Ok:
            return 1
        else:
            return 0


    def closeMessageWindow(self):
        """
        Closes any message window present in the User Interface.
        """
        messageWindow.hideProgressBar(self.objWeasel)
        messageWindow.closeMessageSubWindow(self.objWeasel)


    def progressBar(self, maxNumber=1, index=0, msg="Iteration Number {}", title="Progress Bar"):
        """
        Updates the ProgressBar to the unit set in "index".
        """
        index += 1
        messageWindow.displayMessageSubWindow(self.objWeasel, ("<H4>" + msg + "</H4>").format(index), title)
        messageWindow.setMsgWindowProgBarMaxValue(self.objWeasel, maxNumber)
        messageWindow.setMsgWindowProgBarValue(self.objWeasel, index)
        return index
    

    def selectFolder(self, title="Select the directory"):
        """Displays an open folder dialog window to allow the
        user to select afolder """
        scan_directory = QFileDialog.getExistingDirectory(self.objWeasel, title, self.objWeasel.weaselDataFolder, QFileDialog.ShowDirsOnly)
        return scan_directory


    @staticmethod
    def inputWindow(paramDict, title="Input Parameters", helpText="", lists=None):
        """
        Display a window and prompts the user to insert input values in the fields of the prompted window.
        The user has the option to choose what fields and variables are present in this input window.
        The input window variables and respective types are defined in "paramDict". See below for examples.
        Variable "title" is the title of the window and "helpText" is the text
        displayed inside the window. It should be used to give important notes or 
        tips regarding the input process.

        The user may add extra validation of the parameters. Read the file
        thresholdDICOM_Image.py as it contains a good example of validation of the input parameters.

        This function is a wrap of function "ParameterInputDialog" and you can consult it's detailed documentation
        in CoreModules/WEASEL/InputDialog.py.

        Parameters
        ----------
        paramDict: Dictionary containing the input variables. The key is the field/variable name and the value is the
                   type of the variable. There are 5 possible variable types - [int, float, string, dropdownlist, listview].
                   The dictionary doesn't have any limit of number of fields, the developer can insert as many as wished.
                   The order of the fields displayed in the window is the order set in the dictionary.
                   Eg. paramDict = {"NumberStaff":"int", "Password":"string", "Course":"dropdownlist"}.
                   "NumberStaff" comes first in the window and only accepts integers, then "Password" and then "Course", which is
                   a dropdown where the user can select an option from a set of options, which is given in the parameter "lists".
                   It's possible to assign default values to the input variables. Eg.paramDict = {"NumberStaff":"int,100"} sets the
                   variable "NumberStaff" value to 100.
                   
        title: String that contains the title of the input window that is prompted.

        helpText: String that contains any text that the developer finds useful. 
                  It's the introductory text that comes before the input fields.
                  This is a good variable to write instructions of what to do and how to fill in the fields.

        lists: If the values "dropdownlist" or/and "listview" are given in paramDict, then the developer provides the list of
               options to select in this parameter. This becomes a list of lists if there is more than one of "dropdownlist" or/and "listview".
               The order of the lists in this parameter should be respective to the order of the variables in paramDict. See examples below for
               more details.

        Output
        ------
        outputList: List with the values typed or selected by the user in the prompted window.
                    It returns "None" if the Cancel button or close window are pressed.
                    Eg: if param paramDict = {"Age":"int", "Name":"string"} and the user types 
                    "30" for Age and "Weasel" for Name, then the outputList will be [30, "Weasel"].
                    If "30" and "Weasel" are the default values, then paramDict = {"Age":"int,30", "Name":"string,Weasel"}

        Eg. of paramDict using string:
            paramDict = {"Threshold":"float,0.5", "Age":"int,30"}
            The variable types are float and int. "0.5" and "30" are the default values.

        Eg. of paramDict using string:
            paramDict = {"DicomTag":"string", "TagValue":"string"}
            This a good example where "helpText" can make a difference. 
            For eg., "DicomTag" should be written in the format (XXXX,YYYY).

        Eg. of paramDict using dropdownlist and listview:
            inputDict = {"Algorithm":"dropdownlist", "Nature":"listview"}
            algorithmList = ["B0", "T2*", "T1 Molli"]
            natureList = ["Animals", "Plants", "Trees"]
            inputWindow(paramDict, lists=[algorithmList, natureList])
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
            print('inputWindow: ' + str(e))


    def displayMetadata(self, inputPath):
        """
        Display the metadata in "inputPath" in the User Interface.
        If "inputPath" is a list, then it displays the metadata of the first image.
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                dataset = PixelArrayDICOMTools.getDICOMobject(inputPath)
                displayMetaDataSubWindow(self.objWeasel, "Metadata for image {}".format(inputPath), dataset)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                dataset = PixelArrayDICOMTools.getDICOMobject(inputPath[0])
                displayMetaDataSubWindow(self.objWeasel, "Metadata for image {}".format(inputPath[0]), dataset)
        except Exception as e:
            print('displayMetadata: ' + str(e))


    def displayImages(self, inputPath, subjectID, studyID, seriesID):
        """
        Display the PixelArray in "inputPath" in the User Interface.
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                displayImageColour.displayImageSubWindow(self.objWeasel, inputPath, subjectID, seriesID, studyID)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                if len(inputPath) == 1:
                    displayImageColour.displayImageSubWindow(self.objWeasel, inputPath[0], subjectID, seriesID, studyID)
                else:
                    displayImageColour.displayMultiImageSubWindow(self.objWeasel, inputPath, subjectID, studyID, seriesID)
            return
        except Exception as e:
            print('displayImages: ' + str(e))
        
    # Consider removing this and make it default for any pipeline
    def refreshWeasel(self, new_series_name=None):
        """
        Refresh the user interface screen.
        """
        try:
            logger.info("DeveloperTool.refreshWeasel")
            if new_series_name:
                treeView.refreshDICOMStudiesTreeView(self.objWeasel, newSeriesName=new_series_name)
            else:
                treeView.refreshDICOMStudiesTreeView(self.objWeasel)
        except Exception as e:
            print('refreshWeasel: ' + str(e))


class GenericDICOMTools:

    def copyDICOM(self, inputPath, series_id=None, series_uid=None, series_name=None, study_uid=None, study_name=None, patient_id=None, suffix="_Copy", output_dir=None):
        """
        Creates a DICOM copy of all files in "inputPath" (1 or more) into a new series.
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                if (series_id is None) and (series_uid is None):
                    series_id, series_uid = GenericDICOMTools.generateSeriesIDs(self, inputPath, studyUID=study_uid)
                elif (series_id is not None) and (series_uid is None):
                    _, series_uid = GenericDICOMTools.generateSeriesIDs(self, inputPath, seriesNumber=series_id, studyUID=study_uid)
                elif (series_id is None) and (series_uid is not None):
                    series_id = int(str(ReadDICOM_Image.getDicomDataset(inputPath).SeriesNumber) + str(random.randint(0, 9999)))
                newDataset = ReadDICOM_Image.getDicomDataset(inputPath)
                derivedPath = SaveDICOM_Image.returnFilePath(inputPath, suffix, output_folder=output_dir)
                SaveDICOM_Image.saveDicomToFile(newDataset, output_path=derivedPath)
                # The next lines perform an overwrite operation over the copied images
                if patient_id:
                        SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "PatientID", patient_id)
                if study_uid:
                    SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "StudyInstanceUID", study_uid)
                if study_name:
                    SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "StudyDescription", study_name)
                instance_uid = SaveDICOM_Image.generateUIDs(newDataset, seriesNumber=series_id, studyUID=study_uid)[2]
                SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "SOPInstanceUID", instance_uid)
                SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "SeriesInstanceUID", series_uid)
                SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "SeriesNumber", series_id)
                if series_name:
                    SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "SeriesDescription", series_name)
                else:
                    if hasattr(newDataset, "SeriesDescription"):
                        SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "SeriesDescription", str(newDataset.SeriesDescription + suffix))
                    elif hasattr(newDataset, "SequenceName"):
                        SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "SequenceName", str(newDataset.SequenceName + suffix))
                    elif hasattr(newDataset, "ProtocolName"):
                        SaveDICOM_Image.overwriteDicomFileTag(derivedPath, "ProtocolName", str(newDataset.ProtocolName + suffix))
                newSeriesID = interfaceDICOMXMLFile.insertNewImageInXMLFile(self, inputPath,
                                             derivedPath, suffix, newSeriesName=series_name, newStudyName=study_name, newSubjectName=patient_id)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                if (series_id is None) and (series_uid is None):
                    series_id, series_uid = GenericDICOMTools.generateSeriesIDs(self, inputPath, studyUID=study_uid)
                elif (series_id is not None) and (series_uid is None):
                    _, series_uid = GenericDICOMTools.generateSeriesIDs(self, inputPath, seriesNumber=series_id, studyUID=study_uid)
                elif (series_id is None) and (series_uid is not None):
                    series_id = int(str(ReadDICOM_Image.getDicomDataset(inputPath[0]).SeriesNumber) + str(random.randint(0, 9999)))
                derivedPath = []
                for path in inputPath:
                    newDataset = ReadDICOM_Image.getDicomDataset(path)
                    newFilePath = SaveDICOM_Image.returnFilePath(path, suffix, output_folder=output_dir)
                    SaveDICOM_Image.saveDicomToFile(newDataset, output_path=newFilePath)
                    derivedPath.append(newFilePath)
                    # The next lines perform an overwrite operation over the copied images
                    if patient_id:
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "PatientID", patient_id)
                    if study_uid:
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "StudyInstanceUID", study_uid)
                    if study_name:
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "StudyDescription", study_name)
                    instance_uid = SaveDICOM_Image.generateUIDs(newDataset, seriesNumber=series_id, studyUID=study_uid)[2]
                    SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SOPInstanceUID", instance_uid)
                    SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesInstanceUID", series_uid)
                    SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesNumber", series_id)
                    if series_name:
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesDescription", series_name)
                    else:
                        if hasattr(newDataset, "SeriesDescription"):
                            SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesDescription", str(newDataset.SeriesDescription + suffix))
                        elif hasattr(newDataset, "SequenceName"):
                            SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SequenceName", str(newDataset.SequenceName + suffix))
                        elif hasattr(newDataset, "ProtocolName"):
                            SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "ProtocolName", str(newDataset.ProtocolName + suffix))
                newSeriesID = interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self,
                                inputPath, derivedPath, suffix, newSeriesName=series_name, newStudyName=study_name, newSubjectName=patient_id)
            return derivedPath, newSeriesID
        except Exception as e:
            print('copyDICOM: ' + str(e))

    def deleteDICOM(self, inputPath):
        """
        This functions remove all files in inputhPath and updates the XML file accordingly.
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                os.remove(inputPath)
                interfaceDICOMXMLFile.removeImageFromXMLFile(self, inputPath)
                for displayWindow in self.mdiArea.subWindowList():
                    if displayWindow.windowTitle().split(" - ")[-1] == os.path.basename(inputPath):
                        displayWindow.close()
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                for path in inputPath:
                    os.remove(path)
                interfaceDICOMXMLFile.removeMultipleImagesFromXMLFile(self, inputPath)
                for displayWindow in self.mdiArea.subWindowList():
                    if displayWindow.windowTitle().split(" - ")[-1] in list(map(os.path.basename, inputPath)):
                        displayWindow.close()
        except Exception as e:
            print('deleteDICOM: ' + str(e))

    def mergeDicomIntoOneSeries(self, imagePathList, series_uid=None, series_id=None, series_name="New Series", study_uid=None, study_name=None, patient_id=None, suffix="_Merged", overwrite=False):
        """
        Merges all DICOM files in "imagePathList" into 1 series.
        It creates a copy if "overwrite=False" (default).
        """
        try:
            if os.path.exists(imagePathList[0]):
                if (series_id is None) and (series_uid is None):
                    series_id, series_uid = GenericDICOMTools.generateSeriesIDs(self, imagePathList, studyUID=study_uid)
                elif (series_id is not None) and (series_uid is None):
                    _, series_uid = GenericDICOMTools.generateSeriesIDs(self, imagePathList, seriesNumber=series_id, studyUID=study_uid)
                elif (series_id is None) and (series_uid is not None):
                    series_id = int(str(ReadDICOM_Image.getDicomDataset(imagePathList[0]).SeriesNumber) + str(random.randint(0, 9999)))
            newImagePathList = []
            messageWindow.displayMessageSubWindow(self, ("<H4>Merging {} images</H4>").format(len(imagePathList)), "Progress Bar - Merging")
            if overwrite:
                originalPathList = imagePathList
                messageWindow.setMsgWindowProgBarMaxValue(self, len(imagePathList))
                for index, path in enumerate(imagePathList):
                    messageWindow.setMsgWindowProgBarValue(self, index+1)
                    if patient_id:
                        SaveDICOM_Image.overwriteDicomFileTag(path, "PatientID", patient_id)
                    if study_uid:
                        SaveDICOM_Image.overwriteDicomFileTag(path, "StudyInstanceUID", study_uid)
                    if study_name:
                        SaveDICOM_Image.overwriteDicomFileTag(path, "StudyDescription", study_name)
                    SaveDICOM_Image.overwriteDicomFileTag(path, "SeriesInstanceUID", series_uid)
                    SaveDICOM_Image.overwriteDicomFileTag(path, "SeriesNumber", series_id)
                    dataset = ReadDICOM_Image.getDicomDataset(path)
                    if hasattr(dataset, "SeriesDescription"):
                        SaveDICOM_Image.overwriteDicomFileTag(path, "SeriesDescription", series_name)# + suffix)
                    elif hasattr(dataset, "SequenceName"):
                        SaveDICOM_Image.overwriteDicomFileTag(path, "SequenceName", series_name)# + suffix)
                    elif hasattr(dataset, "ProtocolName"):
                        SaveDICOM_Image.overwriteDicomFileTag(path, "ProtocolName", series_name)# + suffix)
                newImagePathList = imagePathList
                #messageWindow.displayMessageSubWindow(self, "<H4>Updating the XML File ...</H4>", "Progress Bar - Merging")
                newSeriesID = interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self,
                                originalPathList, newImagePathList, suffix, newSeriesName=series_name)
                interfaceDICOMXMLFile.removeMultipleImagesFromXMLFile(self, originalPathList)
            else:
                for index, path in enumerate(imagePathList):
                    messageWindow.setMsgWindowProgBarValue(self, index+1)
                    newDataset = ReadDICOM_Image.getDicomDataset(path)
                    newFilePath = SaveDICOM_Image.returnFilePath(path, suffix)
                    SaveDICOM_Image.saveDicomToFile(newDataset, output_path=newFilePath)
                    # The next lines perform an overwrite operation over the copied images
                    if patient_id:
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "PatientID", patient_id)
                    if study_uid:
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "StudyInstanceUID", study_uid)
                    if study_name:
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "StudyDescription", study_name)
                    instance_uid = SaveDICOM_Image.generateUIDs(newDataset, seriesNumber=series_id, studyUID=study_uid)[2]
                    SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SOPInstanceUID", instance_uid)
                    SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesInstanceUID", series_uid)
                    SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesNumber", series_id)
                    if hasattr(newDataset, "SeriesDescription"):
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SeriesDescription", series_name)# + suffix)
                    elif hasattr(newDataset, "SequenceName"):
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "SequenceName", series_name)# + suffix)
                    elif hasattr(newDataset, "ProtocolName"):
                        SaveDICOM_Image.overwriteDicomFileTag(newFilePath, "ProtocolName", series_name)# + suffix)
                    newImagePathList.append(newFilePath)
                #messageWindow.displayMessageSubWindow(self, "<H4>Updating the XML File ...</H4>", "Progress Bar - Merging")
                newSeriesID = interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self, imagePathList, newImagePathList, suffix, newSeriesName=series_name)
            return newImagePathList
        except Exception as e:
            print('mergeDicomIntoOneSeries: ' + str(e))

    def generateSeriesIDs(self, inputPath, seriesNumber=None, studyUID=None):
        """
        This function generates and returns a SeriesUID and an InstanceUID.
        The SeriesUID is generated based on the StudyUID and on seriesNumber (if provided)
        The InstanceUID is generated based on SeriesUID.
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                dataset = PixelArrayDICOMTools.getDICOMobject(inputPath)
                if seriesNumber is None:
                    #(subjectID, studyID, seriesID) = treeView.getPathParentNode(self, inputPath)
                    (subjectID, studyID, seriesID) = self.objXMLReader.getImageParentIDs(inputPath)
                    seriesNumber = str(int(self.objXMLReader.getStudy(subjectID, studyID)[-1].attrib['id'].split('_')[0]) + 1)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                dataset = PixelArrayDICOMTools.getDICOMobject(inputPath[0])
                if seriesNumber is None:
                    #(subjectID, studyID, seriesID) = treeView.getPathParentNode(self, inputPath[0])
                    (subjectID, studyID, seriesID) = self.objXMLReader.getImageParentIDs(inputPath[0])
                    seriesNumber = str(int(self.objXMLReader.getStudy(subjectID, studyID)[-1].attrib['id'].split('_')[0]) + 1)
            ids = SaveDICOM_Image.generateUIDs(dataset, seriesNumber=seriesNumber, studyUID=studyUID)
            seriesID = ids[0]
            seriesUID = ids[1]
            return seriesID, seriesUID
        except Exception as e:
            print('Error in DeveloperTools.generateSeriesIDs: ' + str(e))

    @staticmethod
    def editDICOMTag(inputPath, dicomTag, newValue):
        """
        Overwrites all "dicomTag" of the DICOM files in "inputPath"
        with "newValue".
        """
        # CONSIDER THE CASES WHERE SERIES NUMBER, NAME AND UID ARE CHANGED - UPDATE XML
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                SaveDICOM_Image.overwriteDicomFileTag(inputPath, dicomTag, newValue)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                for path in inputPath:
                    SaveDICOM_Image.overwriteDicomFileTag(path, dicomTag, newValue)
        except Exception as e:
            print('Error in DeveloperTools.editDICOMTag: ' + str(e))
        

class PixelArrayDICOMTools:
    
    @staticmethod
    def getPixelArrayFromDICOM(inputPath):
        """
        Returns the PixelArray of the DICOM file(s) in "inputPath".
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                pixelArray = ReadDICOM_Image.returnPixelArray(inputPath)
                return np.squeeze(pixelArray)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                pixelArray = ReadDICOM_Image.returnSeriesPixelArray(inputPath)
                return np.squeeze(pixelArray)
            else:
                return None
        except Exception as e:
            print('Error in DeveloperTools.getPixelArrayFromDICOM: ' + str(e))

    @staticmethod
    def getDICOMobject(inputPath):
        """
        Returns the DICOM object (or list of DICOM objects) of the file(s) in "inputPath".
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                dataset = ReadDICOM_Image.getDicomDataset(inputPath)
                return dataset
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                dataset = ReadDICOM_Image.getSeriesDicomDataset(inputPath)
                return dataset
            else:
                return None
        except Exception as e:
            print('Error in DeveloperTools.getDICOMobject: ' + str(e))

    def writeNewPixelArray(self, pixelArray, inputPath, suffix, series_id=None, series_uid=None, series_name=None, output_dir=None):
        """
        Saves the "pixelArray" into new DICOM files with a new series, based
        on the "inputPath" and on the "suffix".
        """
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                numImages = 1
                derivedImageList = [pixelArray]
                derivedImageFilePath = SaveDICOM_Image.returnFilePath(inputPath, suffix, output_folder=output_dir)
                derivedImagePathList = [derivedImageFilePath]

            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                if hasattr(ReadDICOM_Image.getDicomDataset(inputPath[0]), 'PerFrameFunctionalGroupsSequence'):
                    # If it's Enhanced MRI
                    numImages = 1
                    derivedImageList = [pixelArray]
                    derivedImageFilePath = SaveDICOM_Image.returnFilePath(inputPath[0], suffix, output_folder=output_dir)
                    derivedImagePathList = [derivedImageFilePath]
                else:
                    # Iterate through list of images (slices) and save the resulting Map for each DICOM image
                    numImages = (1 if len(np.shape(pixelArray)) < 3 else np.shape(pixelArray)[0])
                    derivedImagePathList = []
                    derivedImageList = []
                    for index in range(numImages):
                        derivedImageFilePath = SaveDICOM_Image.returnFilePath(inputPath[index], suffix, output_folder=output_dir)
                        derivedImagePathList.append(derivedImageFilePath)
                        if numImages==1:
                            derivedImageList.append(pixelArray)
                        else:
                            derivedImageList.append(pixelArray[index, ...])
                    if len(inputPath) > len(derivedImagePathList):
                        inputPath = inputPath[:len(derivedImagePathList)]

            if numImages == 1:
                if isinstance(inputPath, list):
                    inputPath = inputPath[0]
                SaveDICOM_Image.saveNewSingleDicomImage(derivedImagePathList[0], (''.join(inputPath)), derivedImageList[0], suffix, series_id=series_id, series_uid=series_uid, series_name=series_name, list_refs_path=[(''.join(inputPath))])
                # Record derived image in XML file
                interfaceDICOMXMLFile.insertNewImageInXMLFile(self, (''.join(inputPath)), derivedImagePathList[0], suffix, newSeriesName=series_name)
            else:
                SaveDICOM_Image.saveDicomNewSeries(derivedImagePathList, inputPath, derivedImageList, suffix, series_id=series_id, series_uid=series_uid, series_name=series_name, list_refs_path=[inputPath])
                # Insert new series into the DICOM XML file
                interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self, inputPath, derivedImagePathList, suffix, newSeriesName=series_name)            
                
            return derivedImagePathList

        except Exception as e:
            print('Error in DeveloperTools.writePixelArrayToDicom: ' + str(e))

    @staticmethod
    def overwritePixelArray(pixelArray, inputPath):
        """
        Overwrites the DICOM files in the "pixelArray" into new DICOM files with a new series, based
        on the "inputPath" and on the "suffix".
        """
        try:
            if isinstance(inputPath, list) and len(inputPath) > 1:
                datasetList = ReadDICOM_Image.getSeriesDicomDataset(inputPath)
                for index, dataset in enumerate(datasetList):
                    modifiedDataset = SaveDICOM_Image.createNewPixelArray(pixelArray[index], dataset)
                    SaveDICOM_Image.saveDicomToFile(modifiedDataset, output_path=inputPath[index])
            else:
                dataset = ReadDICOM_Image.getDicomDataset(inputPath)
                modifiedDataset = SaveDICOM_Image.createNewPixelArray(pixelArray, dataset)
                SaveDICOM_Image.saveDicomToFile(modifiedDataset, output_path=inputPath)
        except Exception as e:
            print('overwritePixelArray: ' + str(e))


class Project:
    def __init__(self, objWeasel):
        self.objWeasel = objWeasel

    @property
    def children(self):
        children = []
        rootXML = self.objWeasel.objXMLReader.getXMLRoot()
        for subjectXML in rootXML:
            subjectID = subjectXML.attrib['id']
            subject = Subject(self.objWeasel, subjectID)
            children.append(subject)
        return SubjectList(children)
    
    @property
    def numberChildren(self):
        return len(self.children)


class Subject:
    __slots__ = ('objWeasel', 'subjectID', 'suffix')
    def __init__(self, objWeasel, subjectID, suffix=None):
        self.objWeasel = objWeasel
        self.subjectID = subjectID
        self.suffix = '' if suffix is None else suffix
    
    @property
    def children(self, index=None):
        children = []
        subjectXML = self.objWeasel.objXMLReader.getSubject(self.subjectID)
        if subjectXML:
            for studyXML in subjectXML:
                studyID = studyXML.attrib['id']
                study = Study(self.objWeasel, self.subjectID, studyID)
                children.append(study)
        return StudyList(children)

    @property
    def parent(self):
        return Project(self.objWeasel)

    @property
    def numberChildren(self):
        return len(self.children)
    
    @property
    def allImages(self):
        listImages = []
        for study in self.children:
            listImages.extend(study.allImages)
        return ImagesList(listImages)

    @classmethod
    def fromTreeView(cls, objWeasel, subjectItem):
        subjectID = subjectItem.text(1).replace('Subject -', '').strip()
        return cls(objWeasel, subjectID)
    
    def new(self, suffix="_Copy", subjectID=None):
        if subjectID is None:
            subjectID = self.subjectID + suffix
        return Subject(self.objWeasel, subjectID)

    def copy(self, suffix="_Copy", output_dir=None):
        newSubjectID = self.subjectID + suffix
        for study in self.children:
            study.copy(suffix='', newSubjectID=newSubjectID, output_dir=output_dir)
        return Subject(self.objWeasel, newSubjectID)

    def delete(self):
        for study in self.children:
            study.delete()
        self.subjectID = ''
        #interfaceDICOMXMLFile.removeSubjectinXMLFile(self.objWeasel, self.subjectID)

    def add(self, study):
        study.subjectID = self.subjectID
        study["PatientID"] = series.subjectID
        #interfaceDICOMXMLFile.insertNewStudyInXMLFile(self, study.subjectID, study.studyID, study.suffix)

    @staticmethod
    def merge(listSubjects, newSubjectName=None, suffix='_Merged', overwrite=False, output_dir=None):
        if newSubjectName:
            outputSubject = Subject(listSubjects[0].objWeasel, newSubjectName)
        else:
            outputSubject = listSubjects[0].new(suffix=suffix)
        # Setup Progress Bar
        progressBarTitle = "Progress Bar - Merging " + str(len(listSubjects)) + " Subjects"
        messageWindow.displayMessageSubWindow(listSubjects[0].objWeasel, ("<H4>Merging {} Subjects</H4>").format(len(listSubjects)), progressBarTitle)
        messageWindow.setMsgWindowProgBarMaxValue(listSubjects[0].objWeasel, len(listSubjects))
        # Add new subject (outputSubject) to XML
        for index, subject in enumerate(listSubjects):
            # Increment progress bar
            subjMsg = "Merging subject " + subject.subjectID
            messageWindow.displayMessageSubWindow(listSubjects[0].objWeasel, ("<H4>" + subjMsg + "</H4>"), progressBarTitle)
            messageWindow.setMsgWindowProgBarMaxValue(listSubjects[0].objWeasel, len(listSubjects))
            messageWindow.setMsgWindowProgBarValue(listSubjects[0].objWeasel, index+1)
            # Overwrite or not?
            if overwrite == False:
                for study in subject.children:
                    # Create a copy of the study into the new subject
                    studyMsg = ", study " + study.studyID
                    messageWindow.displayMessageSubWindow(listSubjects[0].objWeasel, ("<H4>" + subjMsg + studyMsg + "</H4>"), progressBarTitle)
                    messageWindow.setMsgWindowProgBarMaxValue(listSubjects[0].objWeasel, len(listSubjects))
                    messageWindow.setMsgWindowProgBarValue(listSubjects[0].objWeasel, index+1)
                    study.copy(suffix=suffix, newSubjectID=outputSubject.subjectID, output_dir=None)
            else:
                for study in subject.children:
                    studyMsg = ", study " + study.studyID
                    messageWindow.displayMessageSubWindow(listSubjects[0].objWeasel, ("<H4>" + subjMsg + studyMsg + "</H4>"), progressBarTitle)
                    messageWindow.setMsgWindowProgBarMaxValue(listSubjects[0].objWeasel, len(listSubjects))
                    messageWindow.setMsgWindowProgBarValue(listSubjects[0].objWeasel, index+1)
                    seriesPathsList = []
                    for series in study.children:
                        series.Item('PatientID', outputSubject.subjectID)
                        seriesPathsList.append(series.images)
                    interfaceDICOMXMLFile.insertNewStudyInXMLFile(outputSubject.objWeasel, outputSubject.subjectID, study.studyID, suffix, seriesList=seriesPathsList) # Need new Study name situation
                    # Add study to new subject in the XML
                interfaceDICOMXMLFile.removeSubjectinXMLFile(subject.objWeasel, subject.subjectID)
        return outputSubject

    def get_value(self, tag):
        if len(self.children) > 0:
            studyOutputValuesList = []
            for study in self.children:
                studyOutputValuesList.append(study.get_value(tag)) # extend will allow long single list, while append creates list of lists
            return studyOutputValuesList
        else:
            return []

    def set_value(self, tag, newValue):
        if len(self.children) > 0:
            for study in self.children:
                study.set_value(tag, newValue)
    
    def __getitem__(self, tag):
        return self.get_value(tag)

    def __setitem__(self, tag, value):
        self.set_value(tag, value)


class Study:
    __slots__ = ('objWeasel', 'subjectID', 'studyID', 'studyUID', 'suffix')
    def __init__(self, objWeasel, subjectID, studyID, studyUID=None, suffix=None):
        self.objWeasel = objWeasel
        self.subjectID = subjectID
        self.studyID = studyID
        self.studyUID = self.StudyUID if studyUID is None else studyUID
        self.suffix = '' if suffix is None else suffix

    @property
    def children(self, index=None):
        children = []
        studyXML = self.objWeasel.objXMLReader.getStudy(self.subjectID, self.studyID)
        if studyXML:
            for seriesXML in studyXML:
                seriesID = seriesXML.attrib['id']
                images = []
                for imageXML in seriesXML:
                    images.append(imageXML.find('name').text)
                series = Series(self.objWeasel, self.subjectID, self.studyID, seriesID, listPaths=images)
                children.append(series)
        return SeriesList(children)
    
    @property
    def parent(self):
        return Subject(self.objWeasel, self.subjectID)

    @property
    def numberChildren(self):
        return len(self.children)

    @property
    def allImages(self):
        listImages = []
        for series in self.children:
            listImages.extend(series.children)
        return ImagesList(listImages)
    
    @classmethod
    def fromTreeView(cls, objWeasel, studyItem):
        subjectID = studyItem.parent().text(1).replace('Subject -', '').strip()
        studyID = studyItem.text(1).replace('Study -', '').strip()
        return cls(objWeasel, subjectID, studyID)

    def new(self, suffix="_Copy", studyID=None):
        if studyID is None:
            studyID = self.studyID + suffix
        prefixUID = '.'.join(self.studyUID.split(".", maxsplit=6)[:5]) + "." + str(random.randint(0, 9999)) + "."
        study_uid = pydicom.uid.generate_uid(prefix=prefixUID)
        return Study(self.objWeasel, self.subjectID, studyID, studyUID=study_uid, suffix=suffix)

    def copy(self, suffix="_Copy", newSubjectID=None, output_dir=None):
        if newSubjectID:
            prefixUID = '.'.join(self.studyUID.split(".", maxsplit=6)[:5]) + "." + str(random.randint(0, 9999)) + "."
            study_uid = pydicom.uid.generate_uid(prefix=prefixUID)
            newStudyInstance = Study(self.objWeasel, newSubjectID, self.studyID + suffix, studyUID=study_uid, suffix=suffix)
        else:
            newStudyInstance = self.new(suffix=suffix)
        seriesPathsList = []
        for series in self.children:
            copiedSeries = series.copy(suffix=suffix, series_id=series.seriesID.split('_', 1)[0], series_name=series.seriesID.split('_', 1)[1], study_uid=newStudyInstance.studyUID,
                                       study_name=newStudyInstance.studyID.split('_', 1)[1].split('_', 1)[1], patient_id=newSubjectID, output_dir=output_dir)
            seriesPathsList.append(copiedSeries.images)
        #interfaceDICOMXMLFile.insertNewStudyInXMLFile(newStudyInstance.objWeasel, newStudyInstance.subjectID, newStudyInstance.studyID, suffix, seriesList=seriesPathsList)
        return newStudyInstance

    def delete(self):
        for series in self.children:
            series.delete()
        #interfaceDICOMXMLFile.removeOneStudyFromSubject(self.objWeasel, self.subjectID, self.studyID)
        self.subjectID = self.studyID = ''
    
    def add(self, series):
        series.subjectID = self.subjectID
        series.studyID = self.studyID
        series.studyUID = self.studyUID
        series["PatientID"] = series.subjectID
        series["StudyDate"] = series.studyID.split("_")[0]
        series["StudyTime"] = series.studyID.split("_")[1]
        series["StudyDescription"] = series.studyID.split("_")[2]
        series["StudyInstanceUID"] = self.studyUID
        #if len(series.referencePathsList) > 0:
        #    interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self.objWeasel, series.referencePathsList, series.images, series.suffix)
        #else:
        #    interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self.objWeasel, series.images, series.images, series.suffix)

    @staticmethod
    def merge(listStudies, newStudyName=None, suffix='_Merged', overwrite=False, output_dir=None):
        if newStudyName:
            prefixUID = '.'.join(listStudies[0].studyUID.split(".", maxsplit=6)[:5]) + "." + str(random.randint(0, 9999)) + "."
            study_uid = pydicom.uid.generate_uid(prefix=prefixUID)
            newStudyID = listStudies[0].studyID.split('_')[0] + "_" + listStudies[0].studyID.split('_')[1] + "_" + newStudyName
            outputStudy = Study(listStudies[0].objWeasel, listStudies[0].subjectID, newStudyID, studyUID=study_uid)
        else:
            outputStudy = listStudies[0].new(suffix=suffix)
        # Set up Progress Bar
        progressBarTitle = "Progress Bar - Merging " + str(len(listStudies)) + " Studies"
        messageWindow.displayMessageSubWindow(listStudies[0].objWeasel, ("<H4>Merging {} Studies</H4>").format(len(listStudies)), progressBarTitle)
        messageWindow.setMsgWindowProgBarMaxValue(listStudies[0].objWeasel, len(listStudies))
        # Add new study (outputStudy) to XML
        seriesPathsList = []
        if overwrite == False:
            for index, study in enumerate(listStudies):
                messageWindow.displayMessageSubWindow(listStudies[0].objWeasel, ("<H4>Merging study " + study.studyID + "</H4>"), progressBarTitle)
                messageWindow.setMsgWindowProgBarMaxValue(listStudies[0].objWeasel, len(listStudies))
                messageWindow.setMsgWindowProgBarValue(listStudies[0].objWeasel, index+1)
                seriesNumber = 1
                for series in study.children:
                    copiedSeries = series.copy(suffix=suffix, series_id=seriesNumber, series_name=series.seriesID.split('_', 1)[1], study_uid=outputStudy.studyUID,
                                               study_name=outputStudy.studyID.split('_', 1)[1].split('_', 1)[1], patient_id=outputStudy.subjectID, output_dir=output_dir) # StudyID in InterfaceXML
                    seriesPathsList.append(copiedSeries.images)
                    seriesNumber =+ 1
        else:
            seriesNumber = 1
            for index, study in enumerate(listStudies):
                messageWindow.displayMessageSubWindow(listStudies[0].objWeasel, ("<H4>Merging study " + study.studyID + "</H4>"), progressBarTitle)
                messageWindow.setMsgWindowProgBarMaxValue(listStudies[0].objWeasel, len(listStudies))
                messageWindow.setMsgWindowProgBarValue(listStudies[0].objWeasel, index+1)
                for series in study.children:
                    series.Item('PatientID', outputStudy.subjectID)
                    series.Item('StudyInstanceUID', outputStudy.studyUID)
                    series.Item('StudyDescription', outputStudy.studyID.split('_', 1)[1].split('_', 1)[1])
                    series.Item('SeriesNumber', seriesNumber)
                    # Generate new series uid based on outputStudy.studyUID
                    _, new_series_uid = GenericDICOMTools.generateSeriesIDs(series.objWeasel, series.images, seriesNumber=seriesNumber, studyUID=outputStudy.studyUID)
                    series.Item('SeriesInstanceUID', new_series_uid)
                    seriesPathsList.append(series.images)
                    seriesNumber += 1
                interfaceDICOMXMLFile.removeOneStudyFromSubject(study.objWeasel, study.subjectID, study.studyID)
        interfaceDICOMXMLFile.insertNewStudyInXMLFile(outputStudy.objWeasel, outputStudy.subjectID, outputStudy.studyID, suffix, seriesList=seriesPathsList) # Need new Study name situation
        return outputStudy

    @property
    def StudyUID(self):
        if len(self.children) > 0:
            return self.children[0].studyUID
        else:
            return pydicom.uid.generate_uid(prefix=None)
    
    def get_value(self, tag):
        if len(self.children) > 0:
            seriesOutputValuesList = []
            for series in self.children:
                seriesOutputValuesList.append(series.get_value(tag)) # extend will allow long single list, while append creates list of lists
            return seriesOutputValuesList
        else:
            return []

    def set_value(self, tag, newValue):
        if len(self.children) > 0:
            for series in self.children:
                series.set_value(tag, newValue)
    
    def __getitem__(self, tag):
        return self.get_value(tag)

    def __setitem__(self, tag, value):
        self.set_value(tag, value)


class Series:
    __slots__ = ('objWeasel', 'subjectID', 'studyID', 'seriesID', 'studyUID', 'seriesUID', 
                 'images', 'suffix', 'referencePathsList')
    def __init__(self, objWeasel, subjectID, studyID, seriesID, listPaths=None, studyUID=None, seriesUID=None, suffix=None):
        self.objWeasel = objWeasel
        self.subjectID = subjectID
        self.studyID = studyID
        self.seriesID = seriesID
        self.images = [] if listPaths is None else listPaths
        self.studyUID = self.StudyUID if studyUID is None else studyUID
        self.seriesUID = self.SeriesUID if seriesUID is None else seriesUID
        self.suffix = '' if suffix is None else suffix
        self.referencePathsList = []
        # This is to deal with Enhanced MRI
        #if self.PydicomList and len(self.images) == 1:
        #    self.indices = list(np.arange(len(self.PydicomList[0].PerFrameFunctionalGroupsSequence))) if hasattr(self.PydicomList[0], 'PerFrameFunctionalGroupsSequence') else []
        #else:
        #    self.indices = []

    @property
    def children(self, index=None):
        children = []
        seriesXML = self.objWeasel.objXMLReader.getSeries(self.subjectID, self.studyID, self.seriesID)
        for imageXML in seriesXML:
            image = Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, imageXML.find('name').text)
            children.append(image)
        return ImagesList(children)
    
    @property
    def parent(self):
        return Study(self.objWeasel, self.subjectID, self.studyID, studyUID=self.studyUID)

    @property
    def numberChildren(self):
        return len(self.children)

    @classmethod
    def fromTreeView(cls, objWeasel, seriesItem):
        subjectID = seriesItem.parent().parent().text(1).replace('Subject -', '').strip()
        studyID = seriesItem.parent().text(1).replace('Study -', '').strip()
        seriesID = seriesItem.text(1).replace('Series -', '').strip()
        images = objWeasel.objXMLReader.getImagePathList(subjectID, studyID, seriesID)
        return cls(objWeasel, subjectID, studyID, seriesID, listPaths=images)
    
    def new(self, suffix="_Copy", series_id=None, series_name=None, series_uid=None):
        if series_id is None:
            series_id, _ = GenericDICOMTools.generateSeriesIDs(self.objWeasel, self.images)
        if series_name is None:
            series_name = self.seriesID.split('_', 1)[1] + suffix
        if series_uid is None:
            _, series_uid = GenericDICOMTools.generateSeriesIDs(self.objWeasel, self.images, seriesNumber=series_id)
        seriesID = str(series_id) + '_' + series_name
        newSeries = Series(self.objWeasel, self.subjectID, self.studyID, seriesID, seriesUID=series_uid, suffix=suffix)
        newSeries.referencePathsList = self.images
        return newSeries
    
    def copy(self, suffix="_Copy", newSeries=True, series_id=None, series_name=None, series_uid=None, study_uid=None, study_name=None, patient_id=None, output_dir=None):
        if newSeries == True:
            newPathsList, newSeriesID = GenericDICOMTools.copyDICOM(self.objWeasel, self.images, series_id=series_id, series_uid=series_uid, series_name=series_name,
                                                                    study_uid=study_uid, study_name=study_name, patient_id=patient_id, suffix=suffix, output_dir=output_dir)
            return Series(self.objWeasel, self.subjectID, self.studyID, newSeriesID, listPaths=newPathsList, suffix=suffix)
        else:
            series_id = self.seriesID.split('_', 1)[0]
            series_name = self.seriesID.split('_', 1)[1]
            series_uid = self.seriesUID
            suffix = self.suffix
            newPathsList, _ = GenericDICOMTools.copyDICOM(self.objWeasel, self.images, series_id=series_id, series_uid=series_uid, series_name=series_name, study_uid=study_uid,
                                                          study_name=study_name, patient_id=patient_id,suffix=suffix, output_dir=output_dir) # StudyID in InterfaceXML
            for newCopiedImagePath in newPathsList:
                newImage = Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, newCopiedImagePath)
                self.add(newImage)

    def delete(self):
        GenericDICOMTools.deleteDICOM(self.objWeasel, self.images)
        self.images = self.referencePathsList = []
        #self.children = self.indices = []
        #self.numberChildren = 0
        self.subjectID = self.studyID = self.seriesID = self.seriesUID = ''

    def add(self, Image):
        self.images.append(Image.path)
        # Might need XML functions
        #self.children.append(Image)
        #self.numberChildren = len(self.children)

    def remove(self, allImages=False, Image=None):
        if allImages == True:
            self.images = []
            # Might need XML functions
            #self.children = []
            #self.numberChildren = 0
        elif Image is not None:
            self.images.remove(Image.path)
            # Might need XML functions
            #self.children.remove(Image)
            #self.numberChildren = len(self.children)

    def write(self, pixelArray, output_dir=None):
        if self.images:
            PixelArrayDICOMTools.overwritePixelArray(pixelArray, self.images)
        else:
            series_id = self.seriesID.split('_', 1)[0]
            series_name = self.seriesID.split('_', 1)[1]
            inputReference = self.referencePathsList[0] if len(self.referencePathsList)==1 else self.referencePathsList
            outputPath = PixelArrayDICOMTools.writeNewPixelArray(self.objWeasel, pixelArray, inputReference, self.suffix, series_id=series_id, series_name=series_name, series_uid=self.seriesUID, output_dir=output_dir)
            self.images = outputPath
    
    def read(self):
        return self.PydicomList

    def save(self, PydicomList):
        newSubjectID = self.subjectID
        newStudyID = self.studyID
        newSeriesID = self.seriesID
        for index, dataset in enumerate(PydicomList):
            changeXML = False
            if dataset.SeriesDescription != self.PydicomList[index].SeriesDescription or dataset.SeriesNumber != self.PydicomList[index].SeriesNumber:
                changeXML = True
                newSeriesID = str(dataset.SeriesNumber) + "_" + str(dataset.SeriesDescription)
            if dataset.StudyDate != self.PydicomList[index].StudyDate or dataset.StudyTime != self.PydicomList[index].StudyTime or dataset.StudyDescription != self.PydicomList[index].StudyDescription:
                changeXML = True
                newStudyID = str(dataset.StudyDate) + "_" + str(dataset.StudyTime).split(".")[0] + "_" + str(dataset.StudyDescription)
            if dataset.PatientID != self.PydicomList[index].PatientID:
                changeXML = True
                newSubjectID = str(dataset.PatientID)
            SaveDICOM_Image.saveDicomToFile(dataset, output_path=self.images[index])
            if changeXML == True:
                interfaceDICOMXMLFile.moveImageInXMLFile(self.objWeasel, self.subjectID, self.studyID, self.seriesID, newSubjectID, newStudyID, newSeriesID, self.images[index], '')
        # Only after updating the Element Tree (XML), we can change the instance values and save the DICOM file
        self.subjectID = newSubjectID
        self.studyID = newStudyID
        self.seriesID = newSeriesID

    @staticmethod
    def merge(listSeries, series_id=None, series_name='NewSeries', series_uid=None, suffix='_Merged', overwrite=False):
        outputSeries = listSeries[0].new(suffix=suffix, series_id=series_id, series_name=series_name, series_uid=series_uid)
        pathsList = [image for series in listSeries for image in series.images]
        outputPathList = GenericDICOMTools.mergeDicomIntoOneSeries(outputSeries.objWeasel, pathsList, series_uid=series_uid, series_id=series_id, series_name=series_name, suffix=suffix, overwrite=overwrite)
        outputSeries.images = outputPathList
        outputSeries.referencePathsList = outputPathList
        return outputSeries
    
    #def sort(self, tagDescription, *argv):
    #    if self.Item(tagDescription) or self.Tag(tagDescription):
    #        imagePathList, _, _, indicesSorted = ReadDICOM_Image.sortSequenceByTag(self.images, tagDescription)
    #        self.images = imagePathList
    #        #if self.Multiframe: self.indices = sorted(set(indicesSorted) & set(self.indices), key=indicesSorted.index)
    #    for tag in argv:
    #        if self.Item(tag) or self.Tag(tag):
    #            imagePathList, _, _, indicesSorted = ReadDICOM_Image.sortSequenceByTag(self.images, tag)
    #            self.images = imagePathList
    #            #if self.Multiframe: self.indices = sorted(set(indicesSorted) & set(self.indices), key=indicesSorted.index)
    
    def sort(self, *argv, reverse=False):
        tuple_to_sort = []
        list_to_sort = []
        list_to_sort.append(self.images) # children? images?
        for tag in argv:
            if len(self.get_value(tag)) > 0:
                attributeList = self.get_value(tag)
                list_to_sort.append(attributeList)
        for index, _ in enumerate(self.images):
            individual_tuple = []
            for individual_list in list_to_sort:
                individual_tuple.append(individual_list[index])
            tuple_to_sort.append(tuple(individual_tuple))
        tuple_sorted = sorted(tuple_to_sort, key=lambda x: x[1:], reverse=reverse)
        list_sorted_images = []
        for individual in tuple_sorted:
            list_sorted_images.append(individual[0])
        list_sorted_paths = [img.path for img in list_sorted_images]
        self.images = list_sorted_paths
        return self
    
    def where(self, tag, condition, target):
        list_images = []
        list_paths = []
        for image in self.children:
            value = image[tag]
            statement = repr(value) + ' ' + repr(condition) + ' ' + repr(target)
            if eval(literal_eval(statement)) == True:
                list_images.append(image)
                list_paths.append(image.path)
        self.images = list_paths
        return self

    def display(self):
        UserInterfaceTools(self.objWeasel).displayImages(self.images, self.subjectID, self.studyID, self.seriesID)

    def Metadata(self):
        UserInterfaceTools(self.objWeasel).displayMetadata(self.images)

    @property
    def SeriesUID(self):
        if not self.images:
            self.seriesUID = None
        elif os.path.exists(self.images[0]):
            self.seriesUID = ReadDICOM_Image.getImageTagValue(self.images[0], 'SeriesInstanceUID')
        else:
            self.seriesUID = None
        return self.seriesUID

    @property
    def StudyUID(self):
        if not self.images:
            self.studyUID = None
        elif os.path.exists(self.images[0]):
            self.studyUID = ReadDICOM_Image.getImageTagValue(self.images[0], 'StudyInstanceUID')
        else:
            self.studyUID = None
        return self.studyUID

    @property
    def Magnitude(self):
        dicomList = self.PydicomList
        magnitudeSeries = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=self.images)
        magnitudeSeries.remove(allImages=True)
        magnitudeSeries.referencePathsList = self.images
        for index in range(len(self.images)):
            flagMagnitude, _, _, _, _ = ReadDICOM_Image.checkImageType(dicomList[index])
            if isinstance(flagMagnitude, list) and flagMagnitude:
                if len(flagMagnitude) > 1 and len(self.images) == 1:
                    magnitudeSeries.indices = flagMagnitude
                magnitudeSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
            elif flagMagnitude == True:
                magnitudeSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
        return magnitudeSeries

    @property
    def Phase(self):
        dicomList = self.PydicomList
        phaseSeries = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=self.images)
        phaseSeries.remove(allImages=True)
        phaseSeries.referencePathsList = self.images
        for index in range(len(self.images)):
            _, flagPhase, _, _, _ = ReadDICOM_Image.checkImageType(dicomList[index])
            if isinstance(flagPhase, list) and flagPhase:
                if len(flagPhase) > 1 and len(self.images) == 1:
                    phaseSeries.indices = flagPhase
                phaseSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
            elif flagPhase == True:
                phaseSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
        return phaseSeries

    @property
    def Real(self):
        dicomList = self.PydicomList
        realSeries = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=self.images)
        realSeries.remove(allImages=True)
        realSeries.referencePathsList = self.images
        for index in range(len(self.images)):
            _, _, flagReal, _, _ = ReadDICOM_Image.checkImageType(dicomList[index])
            if isinstance(flagReal, list) and flagReal:
                if len(flagReal) > 1 and len(self.images) == 1:
                    realSeries.indices = flagReal
                realSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
            elif flagReal:
                realSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
        return realSeries 

    @property
    def Imaginary(self):
        dicomList = self.PydicomList
        imaginarySeries = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=self.images)
        imaginarySeries.remove(allImages=True)
        imaginarySeries.referencePathsList = self.images
        for index in range(len(self.images)):
            _, _, _, flagImaginary, _ = ReadDICOM_Image.checkImageType(dicomList[index])
            if isinstance(flagImaginary, list) and flagImaginary:
                if len(flagImaginary) > 1 and len(self.images) == 1:
                    imaginarySeries.indices = flagImaginary
                imaginarySeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
            elif flagImaginary:
                imaginarySeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
        return imaginarySeries 

    @property
    def PixelArray(self, ROI=None):
        pixelArray = PixelArrayDICOMTools.getPixelArrayFromDICOM(self.images)
        #if self.Multiframe:    
        #    tempArray = []
        #    for index in self.indices:
        #        tempArray.append(pixelArray[index, ...])
        #    pixelArray = np.array(tempArray)
        #    del tempArray
        if isinstance(ROI, Series):
            mask = np.zeros(np.shape(pixelArray))
            coords = ROI.ROIindices
            mask[tuple(zip(*coords))] = list(np.ones(len(coords)).flatten())
            #pixelArray = pixelArray * mask
            pixelArray = np.extract(mask.astype(bool), pixelArray)
        elif ROI == None:
            pass
        else:
            warnings.warn("The input argument ROI should be a Series instance.") 
        return pixelArray

    @property
    def ListAffines(self):
        return [ReadDICOM_Image.returnAffineArray(image) for image in self.images]
    
    @property
    def ROIindices(self):
        tempImage = self.PixelArray
        tempImage[tempImage != 0] = 1
        return np.transpose(np.where(tempImage == 1))

    @property
    def NumberOfSlices(self):
        #numSlices = 0
        #if self.Multiframe:
        #    numSlices = int(self.Item("NumberOfFrames"))
        #else:
        numSlices = len(np.unique(self.SliceLocations))
        return numSlices

    @property
    def SliceLocations(self):
        #slices = []
        #if self.Multiframe:
        #    #slices = self.indices
        #    slices = self.Item("PerFrameFunctionalGroupsSequence.FrameContentSequence.InStackPositionNumber")
        #else:
        slices = self.Item("SliceLocation")
        return slices
    
    @property
    def EchoTimes(self):
        echoList = []
        #if not self.Multiframe:
            #echoList = self.Item("EchoTime")
        #else:
            #for dataset in self.PydicomList:
                #for index in self.indices:
                    #echoList.append(dataset.PerFrameFunctionalGroupsSequence[index].MREchoSequence[0].EffectiveEchoTime)
        if self.Item("PerFrameFunctionalGroupsSequence.MREchoSequence.EffectiveEchoTime"):
            echoList = self.Item("PerFrameFunctionalGroupsSequence.MREchoSequence.EffectiveEchoTime")
        elif self.Item("EchoTime"):
            echoList = self.Item("EchoTime")
        return echoList

    @property
    def InversionTimes(self):
        inversionList = []
        #if not self.Multiframe:
        if self.Item("InversionTime"):
            inversionList = self.Item("InversionTime")
        elif self.Item(0x20051572):
            inversionList = self.Item(0x20051572)
        else:
            inversionList = []
        #else:
            #inversionList = self.Item("InversionTime")
            #for dataset in self.PydicomList:
                #for index in self.indices:
                    #inversionList.append(dataset.PerFrameFunctionalGroupsSequence[index].MREchoSequence[0].EffectiveInversionTime) # InversionTime
        return inversionList
    
    def get_value(self, tag):
        if self.images:
            if isinstance(tag, list):
                outputValuesList = []
                for ind_tag in tag:
                    outputValuesList.append(ReadDICOM_Image.getSeriesTagValues(self.images, ind_tag)[0])
                return outputValuesList
            else:
                return ReadDICOM_Image.getSeriesTagValues(self.images, tag)[0]
        else:
            return []

    def set_value(self, tag, newValue):
        if self.images:
            comparisonDicom = self.PydicomList
            oldSubjectID = self.subjectID
            oldStudyID = self.studyID
            oldSeriesID = self.seriesID
            if isinstance(tag, list) and isinstance(newValue, list):
                for index, ind_tag in enumerate(tag):
                    GenericDICOMTools.editDICOMTag(self.images, ind_tag, newValue[index])
            else:
                GenericDICOMTools.editDICOMTag(self.images, tag, newValue)
            # Consider the case where other XML fields are changed
            for index, dataset in enumerate(comparisonDicom):
                changeXML = False
                if dataset.SeriesDescription != self.PydicomList[index].SeriesDescription or dataset.SeriesNumber != self.PydicomList[index].SeriesNumber:
                    changeXML = True
                    newSeriesID = str(self.PydicomList[index].SeriesNumber) + "_" + str(self.PydicomList[index].SeriesDescription)
                    self.seriesID = newSeriesID
                else:
                    newSeriesID = oldSeriesID
                if dataset.StudyDate != self.PydicomList[index].StudyDate or dataset.StudyTime != self.PydicomList[index].StudyTime or dataset.StudyDescription != self.PydicomList[index].StudyDescription:
                    changeXML = True
                    newStudyID = str(self.PydicomList[index].StudyDate) + "_" + str(self.PydicomList[index].StudyTime).split(".")[0] + "_" + str(self.PydicomList[index].StudyDescription)
                    self.studyID = newStudyID
                else:
                    newStudyID = oldStudyID
                if dataset.PatientID != self.PydicomList[index].PatientID:
                    changeXML = True
                    newSubjectID = str(self.PydicomList[index].PatientID)
                    self.subjectID = newSubjectID
                else:
                    newSubjectID = oldSubjectID
                if changeXML == True:
                    interfaceDICOMXMLFile.moveImageInXMLFile(self.objWeasel, oldSubjectID, oldStudyID, oldSeriesID, newSubjectID, newStudyID, newSeriesID, self.images[index], '')
    
    def __getitem__(self, tag):
        return self.get_value(tag)

    def __setitem__(self, tag, value):
        self.set_value(tag, value)

    def Item(self, tagDescription, newValue=None):
        if self.images:
            if newValue:
                GenericDICOMTools.editDICOMTag(self.images, tagDescription, newValue)
                if (tagDescription == 'SeriesDescription') or (tagDescription == 'SequenceName') or (tagDescription == 'ProtocolName'):
                    interfaceDICOMXMLFile.renameSeriesinXMLFile(self.objWeasel, self.images, series_name=newValue)
                elif tagDescription == 'SeriesNumber':
                    interfaceDICOMXMLFile.renameSeriesinXMLFile(self.objWeasel, self.images, series_id=newValue)
            itemList, _ = ReadDICOM_Image.getSeriesTagValues(self.images, tagDescription)
            #if self.Multiframe: 
            #    tempList = [itemList[index] for index in self.indices]
            #    itemList = tempList
            #    del tempList
        else:
            itemList = []
        return itemList

    def Tag(self, tag, newValue=None):
        try:
            hexTag = '0x' + tag.split(',')[0] + tag.split(',')[1]
        except:
            # Print message about how to provide tag
            return []
        if self.images:
            if newValue:
                GenericDICOMTools.editDICOMTag(self.images, literal_eval(hexTag), newValue)
            itemList, _ = ReadDICOM_Image.getSeriesTagValues(self.images, literal_eval(hexTag))
            #if self.Multiframe: 
            #    tempList = [itemList[index] for index in self.indices]
            #    itemList = tempList
            #    del tempList
        else:
            itemList = []
        return itemList
    
    @property
    def PydicomList(self):
        if self.images:
            return PixelArrayDICOMTools.getDICOMobject(self.images)
        else:
            return []
    
    #@property
    #def Multiframe(self):
    #    if self.indices:
    #        return True
    #    else:
    #        return False

    def export_as_nifti(self, directory=None, filename=None):
        if directory is None: directory=os.path.dirname(self.images[0])
        if filename is None: filename=self.seriesID
        dicomHeader = nib.nifti1.Nifti1DicomExtension(2, self.PydicomList[0])
        niftiObj = nib.Nifti1Image(np.transpose(self.PixelArray), affine=self.ListAffines[0])
        niftiObj.header.extensions.append(dicomHeader)
        nib.save(niftiObj, directory + '/' + filename + '.nii.gz')


class Image:
    __slots__ = ('objWeasel', 'subjectID', 'studyID', 'seriesID', 'path', 'seriesUID',
                 'studyUID', 'suffix', 'referencePath')
    def __init__(self, objWeasel, subjectID, studyID, seriesID, path, suffix=None):
        self.objWeasel = objWeasel
        self.subjectID = subjectID
        self.studyID = studyID
        self.seriesID = seriesID
        self.path = path
        self.seriesUID = self.SeriesUID
        self.studyUID = self.StudyUID
        self.suffix = '' if suffix is None else suffix
        self.referencePath = ''

    @property
    def parent(self):
        temp_series = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, studyUID=self.studyUID, seriesUID=self.seriesUID)
        paths = []
        images_of_series = temp_series.children
        for image in images_of_series:
            paths.append(image.path)
        del temp_series, images_of_series
        return Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=paths, studyUID=self.studyUID, seriesUID=self.seriesUID)

    @classmethod
    def fromTreeView(cls, objWeasel, imageItem):
        subjectID = imageItem.parent().parent().parent().text(1).replace('Subject -', '').strip()
        studyID = imageItem.parent().parent().text(1).replace('Study -', '').strip()
        seriesID = imageItem.parent().text(1).replace('Series -', '').strip()
        path = imageItem.text(4)
        return cls(objWeasel, subjectID, studyID, seriesID, path)
    
    @staticmethod
    def newSeriesFrom(listImages, suffix='_Copy', series_id=None, series_name=None, series_uid=None):
        pathsList = [image.path for image in listImages]
        if series_id is None:
            series_id, _ = GenericDICOMTools.generateSeriesIDs(listImages[0].objWeasel, pathsList)
        if series_name is None:
            series_name = listImages[0].seriesID.split('_', 1)[1] + suffix
        if series_uid is None:
            _, series_uid = GenericDICOMTools.generateSeriesIDs(listImages[0].objWeasel, pathsList, seriesNumber=series_id)
        seriesID = str(series_id) + '_' + series_name
        newSeries = Series(listImages[0].objWeasel, listImages[0].subjectID, listImages[0].studyID, seriesID, seriesUID=series_uid, suffix=suffix)
        newSeries.referencePathsList = pathsList
        return newSeries

    def new(self, suffix='_Copy', series=None):
        if series is None:
            newImage = Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, '', suffix=suffix)
        else:
            newImage = Image(series.objWeasel, series.subjectID, series.studyID, series.seriesID, '', suffix=suffix)
        newImage.referencePath = self.path
        return newImage

    def copy(self, suffix='_Copy', series=None, output_dir=None):
        if series is None:
            series_id = self.seriesID.split('_', 1)[0]
            series_name = self.seriesID.split('_', 1)[1]
            series_uid = self.seriesUID
            #suffix = self.suffix
        else:
            series_id = series.seriesID.split('_', 1)[0]
            series_name = series.seriesID.split('_', 1)[1]
            series_uid = series.seriesUID
            suffix = series.suffix
        newPath, newSeriesID = GenericDICOMTools.copyDICOM(self.objWeasel, self.path, series_id=series_id, series_uid=series_uid, series_name=series_name, suffix=suffix, output_dir=output_dir)
        copiedImage = Image(self.objWeasel, self.subjectID, self.studyID, newSeriesID, newPath, suffix=suffix)
        if series: series.add(copiedImage)
        return copiedImage

    def delete(self):
        GenericDICOMTools.deleteDICOM(self.objWeasel, self.path)
        self.path = []
        self.referencePath = []
        self.subjectID = self.studyID = self.seriesID = ''
        # Delete the instance, such as del self???

    def write(self, pixelArray, series=None, output_dir=None):
        if os.path.exists(self.path):
            PixelArrayDICOMTools.overwritePixelArray(pixelArray, self.path)
        else:
            if series is None:
                series_id = self.seriesID.split('_', 1)[0]
                series_name = self.seriesID.split('_', 1)[1]
                series_uid = self.seriesUID
            else:
                series_id = series.seriesID.split('_', 1)[0]
                series_name = series.seriesID.split('_', 1)[1]
                series_uid = series.seriesUID
            outputPath = PixelArrayDICOMTools.writeNewPixelArray(self.objWeasel, pixelArray, self.referencePath, self.suffix, series_id=series_id, series_name=series_name, series_uid=series_uid, output_dir=output_dir)
            self.path = outputPath[0]
            if series: series.add(self)
        
    def read(self):
        return self.PydicomObject

    def save(self, PydicomObject):
        changeXML = False
        newSubjectID = self.subjectID
        newStudyID = self.studyID
        newSeriesID = self.seriesID
        if PydicomObject.SeriesDescription != self.PydicomObject.SeriesDescription or PydicomObject.SeriesNumber != self.PydicomObject.SeriesNumber:
            changeXML = True
            newSeriesID = str(PydicomObject.SeriesNumber) + "_" + str(PydicomObject.SeriesDescription)
        if PydicomObject.StudyDate != self.PydicomObject.StudyDate or PydicomObject.StudyTime != self.PydicomObject.StudyTime or PydicomObject.StudyDescription != self.PydicomObject.StudyDescription:
            changeXML = True
            newStudyID = str(PydicomObject.StudyDate) + "_" + str(PydicomObject.StudyTime).split(".")[0] + "_" + str(PydicomObject.StudyDescription)
        if PydicomObject.PatientID != self.PydicomObject.PatientID:
            changeXML = True
            newSubjectID = str(PydicomObject.PatientID)
        SaveDICOM_Image.saveDicomToFile(PydicomObject, output_path=self.path)
        if changeXML == True:
            interfaceDICOMXMLFile.moveImageInXMLFile(self.objWeasel, self.subjectID, self.studyID, self.seriesID, newSubjectID, newStudyID, newSeriesID, self.path, '')
        # Only after updating the Element Tree (XML), we can change the instance values and save the DICOM file
        self.subjectID = newSubjectID
        self.studyID = newStudyID
        self.seriesID = newSeriesID

    @staticmethod
    def merge(listImages, series_id=None, series_name='NewSeries', series_uid=None, suffix='_Merged', overwrite=False):
        outputSeries = Image.newSeriesFrom(listImages, suffix=suffix, series_id=series_id, series_name=series_name, series_uid=series_uid)    
        outputPathList = GenericDICOMTools.mergeDicomIntoOneSeries(outputSeries.objWeasel, outputSeries.referencePathsList, series_uid=series_uid, series_id=series_id, series_name=series_name, suffix=suffix, overwrite=overwrite)
        #UserInterfaceTools(listImages[0].objWeasel).refreshWeasel(new_series_name=listImages[0].seriesID)
        outputSeries.images = outputPathList
        return outputSeries
    
    def display(self):
        UserInterfaceTools(self.objWeasel).displayImages(self.path, self.subjectID, self.studyID, self.seriesID)

    @staticmethod
    def displayListImages(listImages):
        pathsList = [image.path for image in listImages]
        UserInterfaceTools(listImages[0].objWeasel).displayImages(pathsList, listImages[0].subjectID, listImages[0].studyID, listImages[0].seriesID)

    @property
    def name(self):
        return treeView.returnImageName(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.path)

    @property
    def SeriesUID(self):
        if not self.path:
            self.seriesUID = None
        elif os.path.exists(self.path):
            self.seriesUID = ReadDICOM_Image.getImageTagValue(self.path, 'SeriesInstanceUID')
        else:
            self.seriesUID = None
        return self.seriesUID
    
    @property
    def StudyUID(self):
        if not self.path:
            self.studyUID = None
        elif os.path.exists(self.path):
            self.studyUID = ReadDICOM_Image.getImageTagValue(self.path, 'StudyInstanceUID')
        else:
            self.studyUID = None
        return self.studyUID
    
    def Metadata(self):
        UserInterfaceTools(self.objWeasel).displayMetadata(self.path)

    @property
    def PixelArray(self, ROI=None):
        pixelArray = PixelArrayDICOMTools.getPixelArrayFromDICOM(self.path)
        if isinstance(ROI, Image):
            mask = np.zeros(np.shape(pixelArray))
            coords = ROI.ROIindices
            mask[tuple(zip(*coords))] = list(np.ones(len(coords)).flatten())
            #pixelArray = pixelArray * mask
            pixelArray = np.extract(mask.astype(bool), pixelArray)
        elif ROI == None:
            pass
        else:
            warnings.warn("The input argument ROI should be an Image instance.") 
        return pixelArray
    
    @property
    def ROIindices(self):
        tempImage = self.PixelArray
        tempImage[tempImage != 0] = 1
        return np.transpose(np.where(tempImage == 1))

    @property
    def Affine(self):
        return ReadDICOM_Image.returnAffineArray(self.path)
    
    def get_value(self, tag):
        if isinstance(tag, list):
            outputValuesList = []
            for ind_tag in tag:
                outputValuesList.append(ReadDICOM_Image.getImageTagValue(self.path, ind_tag))
            return outputValuesList
        else:
            return ReadDICOM_Image.getImageTagValue(self.path, tag)

    def set_value(self, tag, newValue):
        comparisonDicom = self.PydicomObject
        changeXML = False
        # Not necessary new IDs, but they may be new. The changeXML flag coordinates that.
        oldSubjectID = self.subjectID
        oldStudyID = self.studyID
        oldSeriesID = self.seriesID
        # Set tag commands
        if isinstance(tag, list) and isinstance(newValue, list):
            for index, ind_tag in enumerate(tag):
                GenericDICOMTools.editDICOMTag(self.path, ind_tag, newValue[index])
        else:
            GenericDICOMTools.editDICOMTag(self.path, tag, newValue)
        # Consider the case where XML fields are changed
        if comparisonDicom.SeriesDescription != self.PydicomObject.SeriesDescription or comparisonDicom.SeriesNumber != self.PydicomObject.SeriesNumber:
            changeXML = True
            newSeriesID = str(self.PydicomObject.SeriesNumber) + "_" + str(self.PydicomObject.SeriesDescription)
            self.seriesID = newSeriesID
        else:
            newSeriesID = oldSeriesID
        if comparisonDicom.StudyDate != self.PydicomObject.StudyDate or comparisonDicom.StudyTime != self.PydicomObject.StudyTime or comparisonDicom.StudyDescription != self.PydicomObject.StudyDescription:
            changeXML = True
            newStudyID = str(self.PydicomObject.StudyDate) + "_" + str(self.PydicomObject.StudyTime).split(".")[0] + "_" + str(self.PydicomObject.StudyDescription)
            self.studyID = newStudyID
        else:
            newStudyID = oldStudyID
        if comparisonDicom.PatientID != self.PydicomObject.PatientID:
            changeXML = True
            newSubjectID = str(self.PydicomObject.PatientID)
            self.subjectID = newSubjectID
        else:
            newSubjectID = oldSubjectID
        if changeXML == True:
            interfaceDICOMXMLFile.moveImageInXMLFile(self.objWeasel, oldSubjectID, oldStudyID, oldSeriesID, newSubjectID, newStudyID, newSeriesID, self.path, '')
        
    def __getitem__(self, tag):
        return self.get_value(tag)

    def __setitem__(self, tag, value):
        self.set_value(tag, value)

    def Item(self, tagDescription, newValue=None):
        if self.path:
            if newValue:
                GenericDICOMTools.editDICOMTag(self.path, tagDescription, newValue)
            item = ReadDICOM_Image.getImageTagValue(self.path, tagDescription)
        else:
            item = []
        return item

    def Tag(self, tag, newValue=None):
        hexTag = '0x' + tag.split(',')[0] + tag.split(',')[1]
        if self.path:
            if newValue:
                GenericDICOMTools.editDICOMTag(self.path, literal_eval(hexTag), newValue)
            item = ReadDICOM_Image.getImageTagValue(self.path, literal_eval(hexTag))
        else:
            item = []
        return item

    @property
    def PydicomObject(self):
        if self.path:
            return PixelArrayDICOMTools.getDICOMobject(self.path)
        else:
            return []

    def export_as_nifti(self, directory=None, filename=None):
        if directory is None: directory=os.path.dirname(self.path)
        if filename is None: filename=self.seriesID
        dicomHeader = nib.nifti1.Nifti1DicomExtension(2, self.PydicomObject)
        niftiObj = nib.Nifti1Image(np.transpose(self.PixelArray), affine=self.Affine)
        niftiObj.header.extensions.append(dicomHeader)
        nib.save(niftiObj, directory + '/' + filename + '.nii.gz')

from Scripting.OriginalPipelines import ImagesList, SeriesList, StudyList, SubjectList