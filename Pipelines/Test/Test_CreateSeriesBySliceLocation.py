#****************************************************************
# Create new series holding images of the same slice location
# If images are selected from multiple studies  
# then a new series is created inside each study
#****************************************************************

def main(weasel):
    images = weasel.images()
    studies = images.parent.parent
    for study in studies:
        imgs = study.allImages
        new_study_description = 'Sorted by slice location_' + study.studyID
        new_study = study.new(studyID='Sorted by slice location')
        #slices = np.unique([imag["SliceLocation"] for imag in imgs])
        for loc in weasel.unique_elements(imgs.get_value("SliceLocation")):
            imgs_loc = imgs.where("SliceLocation", "==", loc)
            # This option?
            #series = newSeriesFrom(imgs_loc)
            #series["SeriesDescription"] = 'Slice location [' + str(loc) + ']'
            # Or this option?
            series = imgs_loc.merge(series_name='Slice location [' + str(loc) + ']') # overwrite=False
            # New series is created from merge, so changing the Study Description should be enough
            series["StudyDescription"] = new_study_description
    weasel.refresh()


def suggestion(weasel):
    # Get all images checked by the user
    images = weasel.images()
    # Loop over the studies that the images are part of
    for study in images.studies():
        # Get the part of the images that are in the study
        imgs = images.of(study)
        # Create a new study
        new_study = study.new_sibling(StudyDescription = 'Sorted by slice location')
        # Loop over the unique slice locations
        for loc in imgs.SliceLocation.unique():
            # get the images at slice location loc
            imgs_loc = imgs.where("SliceLocation" == loc)
            # store those images in a new series of the new study
            series = new_study.new_child(imgs_loc)
            # rename the series with the slice location
            series.SeriesDescription = 'Slice location [' + str(loc) + ']'
            
