"""
Creates a copy of the checked subjects showing progress with a status bar.
"""

def main(weasel):
    list_of_subjects = weasel.subjects()                # get the list of studies checked by the user
    for i, subject in enumerate(list_of_subjects):      # Loop over studies in the list and display a progress Bar
        weasel.progress_bar(max=len(list_of_subjects), index=i+1, msg="Copying subjects {}")
        subject.copy()                       # Copy and Display the new study  
    weasel.refresh()                       # Refresh Weasel
    