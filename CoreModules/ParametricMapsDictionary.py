import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
import numpy as np
import datetime
import struct

def edit_dicom(new_dicom, image, parametric_map):

    call_case = ParametricClass()
    call_case.select_parametric_map(new_dicom, image, parametric_map)

    dt = datetime.datetime.now()
    timeStr = dt.strftime('%H%M%S')  # long format with micro seconds
    new_dicom.PerformedProcedureStepStartDate = dt.strftime('%Y%m%d')
    new_dicom.PerformedProcedureStepStartTime = timeStr
    new_dicom.PerformedProcedureStepDescription = "Post-processing application"

    return
  
class ParametricClass(object):
    def select_parametric_map(self, dicom, image, argument):
        method_name = argument
        method = getattr(self, method_name, lambda: "No valid Parametric Map chosen")
        return method(dicom, image)

    def ADC(self, dicom, image):
        # The commented parts are to apply when we decide to include Parametric Map IOD. No readers can deal with this yet
        #dicom.SOPClassUID='1.2.840.10008.5.1.4.1.1.30'
        dicom.SeriesDescription = "Apparent Diffusion Coefficient (um2/s)"
        dicom.Modality = "RWV"
        dicom.FrameLaterality = "U"
        dicom.DerivedPixelContrast = "ADC"
        #dicom.BitsAllocated = 32
        #dicom.BitsStored = 32
        #dicom.HighBit = 31
        #dicom.FloatPixelData = list(image.astype(np.float32).flatten())
        dicom.PixelData = image.astype(dicom.pixel_array.dtype)
        
        dicom.RealWorldValueMappingSequence = [Dataset(), Dataset(), Dataset(), Dataset()]
        dicom.RealWorldValueMappingSequence[0].QuantityDefinitionSequence = [Dataset(), Dataset()]
        dicom.RealWorldValueMappingSequence[0].QuantityDefinitionSequence[0].ValueType = "CODE"
        dicom.RealWorldValueMappingSequence[0].QuantityDefinitionSequence[1].ConceptCodeSequence = [Dataset(), Dataset(), Dataset()]
        dicom.RealWorldValueMappingSequence[0].QuantityDefinitionSequence[1].ConceptCodeSequence[0].CodeValue = "113041"
        dicom.RealWorldValueMappingSequence[0].QuantityDefinitionSequence[1].ConceptCodeSequence[1].CodingSchemeDesignator = "DCM"
        dicom.RealWorldValueMappingSequence[0].QuantityDefinitionSequence[1].ConceptCodeSequence[2].CodeMeaning = "Apparent Diffusion Coefficient"
        dicom.RealWorldValueMappingSequence[1].MeasurementUnitsCodeSequence = [Dataset(), Dataset(), Dataset()]
        dicom.RealWorldValueMappingSequence[1].MeasurementUnitsCodeSequence[0].CodeValue = "um2/s"
        dicom.RealWorldValueMappingSequence[1].MeasurementUnitsCodeSequence[1].CodingSchemeDesignator = "UCUM"
        dicom.RealWorldValueMappingSequence[1].MeasurementUnitsCodeSequence[2].CodeMeaning = "um2/s"
        dicom.RealWorldValueMappingSequence[2].RealWorldValueSlope = 1
        
        anatomy_string = dicom.BodyPartExamined
        save_anatomical_info(anatomy_string, dicom.RealWorldValueMappingSequence[3])

        return

    def T2Star(self, dicom, image):
        dicom.BitsAllocated = 16
        dicom.BitsStored = 16
        dicom.HighBit = 15
        dicom.Rows = np.shape(image)[0]
        dicom.Columns = np.shape(image)[1]
        dicom.PixelSpacing = [3, 3]

        return

    def SEG(self, dicom, image):
        #dicom.SOPClassUID = '1.2.840.10008.5.1.4.1.1.66.4' # WILL NOT BE USED HERE - This is for PACS. There will be another one for DICOM Standard
        # The commented parts are to apply when we decide to include SEG IOD. No readers can deal with this yet
        dicom.BitsAllocated = 8 # According to Federov DICOM Standard this should be 1-bit
        dicom.BitsStored = 8
        dicom.HighBit = 7
        dicom.SmallestImagePixelValue = 0
        dicom.LargestImagePixelValue = 255
        dicom.PixelRepresentation = 0
        dicom.SamplesPerPixel = 1
        dicom.WindowCenter = 128
        dicom.WindowWidth = 128
        dicom.LossyImageCompression = '00'
        image_array = image.astype(np.uint8)
        dicom.PixelData = image_array.tobytes()

        #dicom.Modality = 'SEG'
        dicom.SegmentationType = 'FRACTIONAL'
        dicom.MaximumFractionalValue = 255
        dicom.SegmentationFractionalType = 'OCCUPANCY'
        dicom.ContentLabel = 'SEGMENTATION'
        dicom.ContentDescription = 'Image segmentation'

        # Segment Labels
        # Insert a Label Dictionary that comes from PyQtGraph - roi_labels
        segment_numbers = np.unique(image_array)
        segment_dictionary = dict(list(enumerate(segment_numbers)))
        if segment_dictionary[0] == 0:
            segment_dictionary[0] = 'Background'
        for key in segment_dictionary:
            dicom.SegmentSequence = [Dataset(), Dataset(), Dataset(), Dataset(), Dataset(), Dataset()]
            dicom.SegmentSequence[0].SegmentAlgorithmType = 'MANUAL'
            dicom.SegmentSequence[1].SegmentNumber = key
            dicom.SegmentSequence[2].SegmentDescription = str(segment_dictionary[key])
            dicom.SegmentSequence[3].SegmentLabel = "Label " + str(dicom.SegmentSequence[1].SegmentNumber) + " = " + str(dicom.SegmentSequence[2].SegmentDescription)
            dicom.SegmentSequence[4].SegmentAlgorithmName = "Weasel"
            anatomy_string = dicom.BodyPartExamined
            save_anatomical_info(anatomy_string, dicom.SegmentSequence[5])

        return

    def Registration(self, dicom, image):
        dicom.Modality = "REG"
        return

# Could insert a method regarding ROI colours, like in ITK-SNAP???
def save_anatomical_info(anatomy_string, dicom):
    try:
        # FOR NOW, THE PRIORITY WILL BE ON KIDNEY
        if "KIDNEY" or "ABDOMEN" in anatomy_string.upper():
            dicom.AnatomicRegionSequence = [Dataset(), Dataset(), Dataset()]
            dicom.AnatomicRegionSequence[0].CodeValue = "T-71000"
            dicom.AnatomicRegionSequence[1].CodingSchemeDesignator = "SRT"
            dicom.AnatomicRegionSequence[2].CodeMeaning = "Kidney"
        elif "LIVER" in anatomy_string.upper():
            dicom.AnatomicRegionSequence = [Dataset(), Dataset(), Dataset()]
            dicom.AnatomicRegionSequence[0].CodeValue = "T-62000"
            dicom.AnatomicRegionSequence[1].CodingSchemeDesignator = "SRT"
            dicom.AnatomicRegionSequence[2].CodeMeaning = "Liver"
        elif "PROSTATE" in anatomy_string.upper():
            dicom.AnatomicRegionSequence = [Dataset(), Dataset(), Dataset()]
            dicom.AnatomicRegionSequence[0].CodeValue = "T-9200B"
            dicom.AnatomicRegionSequence[1].CodingSchemeDesignator = "SRT"
            dicom.AnatomicRegionSequence[2].CodeMeaning = "Prostate"      
        elif "BODY" in anatomy_string.upper():
            dicom.AnatomicRegionSequence = [Dataset(), Dataset(), Dataset()]
            dicom.AnatomicRegionSequence[0].CodeValue = "P5-0905E"
            dicom.AnatomicRegionSequence[1].CodingSchemeDesignator = "LN"
            dicom.AnatomicRegionSequence[2].CodeMeaning = "MRI whole body"
    except:
        pass
    return

    # Series, Instance and Class for Reference
    #new_dicom.ReferencedSeriesSequence = [Dataset(), Dataset()]
    #new_dicom.ReferencedSeriesSequence[0].SeriesInstanceUID = dicom_data.SeriesInstanceUID
    #new_dicom.ReferencedSeriesSequence[1].ReferencedInstanceSequence = [Dataset(), Dataset()]
    #new_dicom.ReferencedSeriesSequence[1].ReferencedInstanceSequence[0].ReferencedSOPClassUID = dicom_data.SOPClassUID
    #new_dicom.ReferencedSeriesSequence[1].ReferencedInstanceSequence[1].ReferencedSOPInstanceUID = dicom_data.SOPInstanceUID

# rwv_sequence = Sequence()
        # dicom.RealWorldValueMappingSequence = rwv_sequence
        # rwv_slope = Dataset()
        # rwv_slope.RealWorldValueSlope = 1
        # rwv_sequence.append(rwv_slope)

        # quantity_def = Dataset()
        # quantity_def_sequence = Sequence()
        # quantity_def.QuantityDefinitionSequence = quantity_def_sequence
        # value_type = Dataset()
        # value_type.ValueType = "CODE"
        # quantity_def_sequence.append(value_type)
        # concept_code = Dataset()
        # concept_code_sequence = Sequence()
        # concept_code.ConceptCodeSequence = concept_code_sequence
        # code_code = Dataset()
        # code_code.CodeValue = "113041"
        # code_code.CodingSchemeDesignator = "DCM"
        # code_code.CodeMeaning = "Apparent Diffusion Coefficient"
        # concept_code_sequence.append(code_code)
        # rwv_sequence.append(quantity_def)

        # measure_units = Dataset()
        # measure_units_sequence = Sequence()
        # measure_units.MeasurementUnitsCodeSequence = measure_units_sequence
        # measure_code = Dataset()
        # measure_code.CodeValue = "um2/s"
        # measure_code.CodingSchemeDesignator = "UCUM"
        # measure_code.CodeMeaning = "um2/s"
        # measure_units_sequence.append(measure_code)
        # rwv_sequence.append(measure_units)