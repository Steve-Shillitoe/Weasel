import os
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.sequence import Sequence
import datetime
import copy
import random
from scipy.stats import iqr
from matplotlib import cm
import CoreModules.readDICOM_Image as readDICOM_Image
import CoreModules.ParametricMapsDictionary as param


def returnFilePath(imagePath, suffix, new_path=None):
    """This method returns the new filepath of the object to be saved."""
    # Think of a way to choose a select a new FilePath
    try:
        if os.path.exists(imagePath):
            # Need to think about what new name to give to the file and how to save multiple files for the same sequence
            if new_path is not None:
                newFilePath = new_path + '.dcm'
            else:
                outputFolder = os.path.join(os.path.dirname(imagePath), "output" + suffix)
                fileName = os.path.splitext(os.path.basename(imagePath))[0]
                try: os.mkdir(outputFolder)
                except: pass
                newFilePath = os.path.join(outputFolder, fileName + suffix + '.dcm')
            return newFilePath

        else:
            return None
    except Exception as e:
        print('Error in function saveDICOM_Image.returnFilePath: ' + str(e))


def saveDicomOutputResult(newFilePath, imagePath, pixelArray, suffix, series_id=None, series_uid=None, image_number=None, parametric_map=None, colormap=None, list_refs_path=None):
    """This method saves the new pixelArray into DICOM in the given newFilePath"""
    try:
        if os.path.exists(imagePath):
            dataset = readDICOM_Image.getDicomDataset(imagePath)
            if list_refs_path is not None:
                refs = []
                for individualRef in list_refs_path:
                    refs.append(readDICOM_Image.getDicomDataset(individualRef))
            else:
                refs = None
            newDataset = createNewSingleDicom(dataset, pixelArray, series_id=series_id, series_uid=series_uid, comment=suffix, parametric_map=parametric_map, colormap=colormap, list_refs=refs)
            if (image_number is not None) and (len(np.shape(pixelArray)) < 3):
                newDataset.InstanceNumber = image_number
                newDataset.ImageNumber = image_number
            saveDicomToFile(newDataset, output_path=newFilePath)
            del dataset, newDataset, refs, image_number
            return
        else:
            return None

    except Exception as e:
        print('Error in function saveDICOM_Image.saveDicomOutputResult: ' + str(e))


def saveDicomNewSeries(derivedImagePathList, imagePathList, pixelArrayList, suffix, series_id=None, series_uid=None, parametric_map=None, colormap=None, list_refs_path=None):
    """This method saves the pixelArrayList into DICOM files with metadata pointing to the same series"""
    # What if it's a map with less files than original? Think about iterating the first elements and sort path list by SliceLocation - see T2* algorithm
    # Think of a way to choose a select a new FilePath or Folder
    try:
        if os.path.exists(imagePathList[0]):
            if series_id is None:
                series_id = int(str(readDICOM_Image.getDicomDataset(imagePathList[0]).SeriesNumber) + str(random.randint(0, 9999)))
            if series_uid is None:
                series_uid = pydicom.uid.generate_uid()

            refs = None
            for index, newFilePath in enumerate(derivedImagePathList):
                # Extra references, besides the main one, which is imagePathList
                if list_refs_path is not None:
                    if len(np.shape(list_refs_path)) == 1:
                        refs = list_refs_path[index]
                    else:
                        refs = []
                        for individualRef in list_refs_path:
                            refs.append(individualRef[index])

                saveDicomOutputResult(newFilePath, imagePathList[index], pixelArrayList[index], suffix, series_id=series_id, series_uid=series_uid, image_number=index,  parametric_map=parametric_map, colormap=colormap, list_refs_path=refs)
            del series_id, series_uid, refs
            return
        else:
            return None
    except Exception as e:
        print('Error in function saveDICOM_Image.saveDicomNewSeries: ' + str(e))     


def saveDicomToFile(dicomData, output_path=None):
    """This method takes a DICOM object and saves it as a DICOM file 
        with the set filename in the input arguments.
    """
    try:
        if output_path is None:
            try:
                output_path = os.getcwd() + copy.deepcopy(dicomData.InstanceNumber).zfill(6) + ".dcm"
            except:
                try:
                    output_path = os.getcwd() + copy.deepcopy(dicomData.ImageNumber).zfill(6) + ".dcm"
                except:
                    output_path = os.getcwd() + copy.deepcopy(dicomData.SOPInstanceUID) + ".dcm"

        pydicom.filewriter.dcmwrite(output_path, dicomData, write_like_original=True)
        del dicomData
        return
    except Exception as e:
        print('Error in function saveDicomToFile: ' + str(e))


def createNewSingleDicom(dicomData, imageArray, series_id=None, series_uid=None, comment=None, parametric_map=None, colormap=None, list_refs=None):
    """This function takes a DICOM Object, copies most of the DICOM tags from the DICOM given in input
        and writes the imageArray into the new DICOM Object in PixelData. 
    """
    try:
        newDicom = copy.deepcopy(dicomData)
        imageArray = copy.deepcopy(imageArray)

        # Generate Unique ID
        newDicom.SOPInstanceUID = pydicom.uid.generate_uid()

        # Series ID and UID
        if series_id is None:
            newDicom.SeriesNumber = int(str(dicomData.SeriesNumber) + str(random.randint(0, 999)))
        else:
            newDicom.SeriesNumber = series_id
        if series_uid is None:
            newDicom.SeriesInstanceUID = pydicom.uid.generate_uid()
        else:
            newDicom.SeriesInstanceUID = series_uid

        # Date and Time of Creation
        dt = datetime.datetime.now()
        timeStr = dt.strftime('%H%M%S')  # long format with micro seconds
        newDicom.ContentDate = dt.strftime('%Y%m%d')
        newDicom.ContentTime = timeStr
        newDicom.InstanceCreationDate = dt.strftime('%Y%m%d')
        newDicom.InstanceCreationTime = timeStr
        newDicom.SeriesDate = dt.strftime('%Y%m%d')
        newDicom.ImageDate = dt.strftime('%Y%m%d')
        newDicom.AcquisitionDate = dt.strftime('%Y%m%d')
        newDicom.SeriesTime = timeStr
        newDicom.ImageTime = timeStr
        newDicom.AcquisitionTime = timeStr
        newDicom.ImageType[0] = "DERIVED"

        # Series, Instance and Class for Reference
        refd_series_sequence = Sequence()
        newDicom.ReferencedSeriesSequence = refd_series_sequence
        refd_series1 = Dataset()
        refd_instance_sequence = Sequence()
        refd_series1.ReferencedInstanceSequence = refd_instance_sequence
        refd_instance1 = Dataset()
        refd_instance1.ReferencedSOPClassUID = dicomData.SOPClassUID
        refd_instance1.ReferencedSOPInstanceUID = dicomData.SOPInstanceUID
        refd_instance_sequence.append(refd_instance1)
        refd_series1.SeriesInstanceUID = dicomData.SeriesInstanceUID
        refd_series_sequence.append(refd_series1)

        # Extra references, besides the main one, which is dicomData
        if list_refs is not None:
            if np.shape(list_refs) == ():
                refd_series1 = Dataset()
                refd_instance_sequence = Sequence()
                refd_series1.ReferencedInstanceSequence = refd_instance_sequence
                refd_instance1 = Dataset()
                refd_instance1.ReferencedSOPInstanceUID = list_refs.SOPInstanceUID
                refd_instance1.ReferencedSOPClassUID = list_refs.SOPClassUID
                refd_instance_sequence.append(refd_instance1)
                refd_series1.SeriesInstanceUID = list_refs.SeriesInstanceUID
                refd_series_sequence.append(refd_series1)
            else:
                for individualRef in list_refs:
                    refd_series1 = Dataset()
                    refd_instance_sequence = Sequence()
                    refd_series1.ReferencedInstanceSequence = refd_instance_sequence
                    refd_instance1 = Dataset()
                    refd_instance1.ReferencedSOPInstanceUID = individualRef.SOPInstanceUID
                    refd_instance1.ReferencedSOPClassUID = individualRef.SOPClassUID
                    refd_instance_sequence.append(refd_instance1)
                    refd_series1.SeriesInstanceUID = individualRef.SeriesInstanceUID
                    refd_series_sequence.append(refd_series1)
            del list_refs

        # Comments
        if comment is not None:
            newDicom.ImageComments = comment
            if len(dicomData.dir("SeriesDescription"))>0:
                newDicom.SeriesDescription = dicomData.SeriesDescription + comment
            elif len(dicomData.dir("SequenceName"))>0 & len(dicomData.dir("PulseSequenceName"))==0:
                newDicom.SeriesDescription = dicomData.SequenceName + comment
            elif len(dicomData.dir("SeriesDescription"))>0:
                newDicom.SeriesDescription = dicomData.SeriesDescription + comment
            elif len(dicomData.dir("ProtocolName"))>0:
                newDicom.SeriesDescription = dicomData.ProtocolName + comment
            else:
                newDicom.SeriesDescription = "NewSeries" + newDicom.SeriesNumber 

        # Parametric Map
        if parametric_map is not None:
            param.editDicom(newDicom, imageArray, parametric_map)

        # INSERT IF ENHANCED MRI HERE - First attempt below
        # for each frame, slope and intercept are M and B. For registration, I will have to add Image Position and Orientation
        numberFrames = 1
        enhancedArrayInt = []
        if hasattr(dicomData, 'PerFrameFunctionalGroupsSequence'):
            if len(np.shape(imageArray)) == 2:
                newDicom.NumberOfFrames = 1
            else:
                newDicom.NumberOfFrames = np.shape(imageArray)[0]
            del newDicom.PerFrameFunctionalGroupsSequence[newDicom.NumberOfFrames:]
            numberFrames = newDicom.NumberOfFrames
        for index in range(numberFrames):
            if len(np.shape(imageArray)) == 2:
                tempArray = imageArray
            else:
                tempArray = np.squeeze(imageArray[index, ...])
            #colormap = "viridis"
            if (int(np.amin(imageArray)) < 0) and colormap is None:
                newDicom.PixelRepresentation = 1
                target = (np.power(2, dicomData.BitsAllocated) - 1)*(np.ones(np.shape(tempArray)))
                maximum = np.ones(np.shape(tempArray))*np.amax(tempArray)
                minimum = np.ones(np.shape(tempArray))*np.amin(tempArray)
                extra = target / (2*np.ones(np.shape(tempArray)))
                imageScaled = target * (tempArray - minimum) / (maximum - minimum) - extra
                slope =  target / (maximum - minimum)
                intercept = (- target * minimum - extra * (maximum - minimum))/ (maximum - minimum)
                rescaleSlope = np.ones(np.shape(tempArray)) / slope
                rescaleIntercept = - intercept / slope
                if newDicom.BitsAllocated == 8:
                    imageArrayInt = imageScaled.astype(np.int8)
                elif newDicom.BitsAllocated == 16:
                    imageArrayInt = imageScaled.astype(np.int16)
                elif newDicom.BitsAllocated == 32:
                    imageArrayInt = imageScaled.astype(np.int32)
                elif newDicom.BitsAllocated == 64:
                    imageArrayInt = imageScaled.astype(np.int64)
                else:
                    imageArrayInt = imageScaled.astype(dicomData.pixel_array.dtype)
                smallestValue = pydicom.dataelem.DataElement(0x00280106, 'SS', int(np.amin(imageArrayInt)))
                largestValue = pydicom.dataelem.DataElement(0x00280107, 'SS', int(np.amax(imageArrayInt)))
            else:
                newDicom.PixelRepresentation = 0
                target = (np.power(2, dicomData.BitsAllocated) - 1)*np.ones(np.shape(tempArray))
                maximum = np.ones(np.shape(tempArray))*np.amax(tempArray)
                minimum = np.ones(np.shape(tempArray))*np.amin(tempArray)
                imageScaled = target * (tempArray - minimum) / (maximum - minimum)
                slope =  target / (maximum - minimum)
                intercept = (- target * minimum - (maximum - minimum))/ (maximum - minimum)
                rescaleSlope = np.ones(np.shape(tempArray)) / slope
                rescaleIntercept = - intercept / slope
                if newDicom.BitsAllocated == 8:
                    imageArrayInt = imageScaled.astype(np.uint8)
                elif newDicom.BitsAllocated == 16:
                    imageArrayInt = imageScaled.astype(np.uint16)
                elif newDicom.BitsAllocated == 32:
                    imageArrayInt = imageScaled.astype(np.uint32)
                elif newDicom.BitsAllocated == 64:
                    imageArrayInt = imageScaled.astype(np.uint64)
                else:
                    imageArrayInt = imageScaled.astype(dicomData.pixel_array.dtype)
                smallestValue = pydicom.dataelem.DataElement(0x00280106, 'US', int(np.amin(imageArrayInt)))
                largestValue = pydicom.dataelem.DataElement(0x00280107, 'US', int(np.amax(imageArrayInt)))

            if hasattr(dicomData, 'PerFrameFunctionalGroupsSequence'):
                enhancedArrayInt.append(imageArrayInt)
                newDicom.PerFrameFunctionalGroupsSequence[index].PixelValueTransformationSequence[0].RescaleSlope = rescaleSlope.flatten()[0]
                newDicom.PerFrameFunctionalGroupsSequence[index].PixelValueTransformationSequence[0].RescaleIntercept = rescaleIntercept.flatten()[0]
            else:
                newDicom.RescaleSlope = rescaleSlope.flatten()[0]
                newDicom.RescaleIntercept = rescaleIntercept.flatten()[0]
        if enhancedArrayInt:
            imageArrayInt = np.array(enhancedArrayInt)

        # Add colormap here
        if colormap is not None:
            newDicom.PhotometricInterpretation = 'PALETTE COLOR'
            arrayForRGB = np.arange(int(np.percentile(imageArrayInt, 1)), int(np.percentile(imageArrayInt, 99)))
            colorsList = cm.ScalarMappable(cmap=colormap).to_rgba(np.array(arrayForRGB), bytes=True)
            stringType = ('SS' if int(np.amin(imageArrayInt)) < 0 else 'US')
            numberValues = len(arrayForRGB)
            minValue = int(np.amin(arrayForRGB))
            redDesc = pydicom.dataelem.DataElement(0x00281101, stringType, [numberValues, minValue, newDicom.BitsAllocated])
            greenDesc = pydicom.dataelem.DataElement(0x00281102, stringType, [numberValues, minValue, newDicom.BitsAllocated])
            blueDesc = pydicom.dataelem.DataElement(0x00281103, stringType, [numberValues, minValue, newDicom.BitsAllocated])
            newDicom.add(redDesc)
            newDicom.add(greenDesc)
            newDicom.add(blueDesc)
            newDicom.RedPaletteColorLookupTableData = bytes(np.array([value.astype('uint'+str(newDicom.BitsAllocated)) for value in colorsList[:,0].flatten()]))
            newDicom.GreenPaletteColorLookupTableData = bytes(np.array([value.astype('uint'+str(newDicom.BitsAllocated)) for value in colorsList[:,1].flatten()]))
            newDicom.BluePaletteColorLookupTableData = bytes( np.array([value.astype('uint'+str(newDicom.BitsAllocated)) for value in colorsList[:,2].flatten()]))

        # Take Phase Encoding into account
        newDicom.Rows = np.shape(imageArrayInt)[-2]
        newDicom.Columns = np.shape(imageArrayInt)[-1]
        newDicom.WindowCenter = int(np.mean(imageArrayInt))
        newDicom.WindowWidth = int(iqr(imageArrayInt, rng=(1, 99)))
        newDicom.add(smallestValue)
        newDicom.add(largestValue)
        newDicom.PixelData = imageArrayInt.tobytes()

        del dicomData, imageArray, imageScaled, imageArrayInt, enhancedArrayInt, tempArray
        return newDicom
    except Exception as e:
        print('Error in function createNewSingleDicom: ' + str(e))