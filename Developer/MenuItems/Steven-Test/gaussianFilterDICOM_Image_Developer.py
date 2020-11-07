from Developer.DeveloperTools import UserInterfaceTools as ui
from Developer.DeveloperTools import PixelArrayDICOMTools as pixel
#**************************************************************************
#Uncomment and edit the following line of code to import the function 
#containing your image processing algorithm. 
from Developer.External.imagingTools import gaussianFilter
FILE_SUFFIX = '_Gaussian'
#***************************************************************************

def isSeriesOnly(self):
    #This functionality only applies to a series of DICOM images
    return True


def main(objWeasel):
    # In this case, the user introduces the sigma value intended for the gaussian filter
    inputDict = {"Standard Deviation":"float"}
    paramList = ui.inputWindow(inputDict, title="Input Parameters for the Gaussian Filter")
    if paramList is None: return # Exit function if the user hits the "Cancel" button
    standard_deviation_filter = paramList[0]
    # Get selected images
    imagePathList = ui.getListOfAllCheckedImages(objWeasel)
    # Get PixelArray from the selected images
    pixelArray = pixel.getPixelArrayFromDICOM(imagePathList)
    # Apply Gaussian Filter
    pixelArray = gaussianFilter(pixelArray, standard_deviation_filter)
    # Save resulting image to DICOM (and update XML)
    outputPath = pixel.writeNewPixelArray(objWeasel, pixelArray, imagePathList, FILE_SUFFIX) #, series_name="GAUSSIAN-WEASEL")
    # Refresh the UI screen
    ui.refreshWeasel(objWeasel)
    # Display resulting image
    ui.displayImage(objWeasel, outputPath)
