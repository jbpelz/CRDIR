# import PySimpleGUI as sg  # Qt works on MacOS better
import PySimpleGUIQt as sg  # Qt works on MacOS better
import sys
import os

from PyQt5 import QtWidgets

import crdir_funcs_v2 as cf

STDEV = 75  # Assumed constant standard deviation of pixels in image
Z_LIMIT = 3 # Z-score flagged as bad pixel

verbose = True

# Read the display resolution using QtGui
app = QtWidgets.QApplication(sys.argv)
mainScreenPix = QtWidgets.QDesktopWidget().screenGeometry(0)  # Rect: (x,y, width,height)

if verbose:
    print("Screen Resolution : " + str(mainScreenPix.height()) + " x " + str(mainScreenPix.width()))
    print("mainScreenPix.width() = {}".format(mainScreenPix.width()))
    print("=============================================\n")

MAX_WINDOW_WIDTH = int(mainScreenPix.width() * (3/4) )
MAX_WINDOW_HEIGHT = int(MAX_WINDOW_WIDTH/(5/3))  # 16/9

# Determine whose computer we're on:
if os.path.exists('/Users/pelz'):  # You are on Jeff's computer
    USER = 'Jeff'
    userPath = '/Users/pelz'
    crdirDirPath = 'Documents/CRDIR/to process images'  # 'Documents/CRDIR'

elif os.path.exists('/Users/peterablacksberg'):  # You are on Peter's computer:
    USER = 'PeterABlacksberg'
    userPath = '/Users/peterablacksberg'
    crdirDirPath = 'Documents/CRDIR/to process images'

else:
    USER = "Unknown"
    userPath = '/Users'
    crdirDirPath = ''

# Set basePath based on which computer we're on
basePath = "{}/{}".format(userPath, crdirDirPath)

if verbose:
    print("user = {}   basePath = {}".format(USER, basePath))
    print("=============================================\n")

# Set up the SimpleGUI (sg)
sg.ChangeLookAndFeel('Reddit')
refDirectoryPath = basePath
imgExtensionType = '.nef' # '.jpg'

# Select a directory and read in the IMAGE files from that directory
img_files, img_fileNames = cf.get_img_files(refDirectoryPath, imgExtensionType)

if verbose:
    print("img_fileNames = {}".format(img_fileNames))

# ####  Image browser ####
# create the imageBrowser that returns keyboard events
imageBrowser = sg.FlexForm('Image Browser', return_keyboard_events=True, location=(0,0), use_default_focus=False )

# Check to be sure there are images to read
try:  # Try to read in the first image:
    displayImage = cf.postprocessed_from_raw(refDirectoryPath, img_fileNames[0], verbose=verbose)  # extract the RGB image
    imgData, imgResizeLabel = cf.prep_img_for_display(displayImage,
                                                      maxDisplayWidth=MAX_WINDOW_WIDTH,
                                                      maxDisplayHeight=MAX_WINDOW_HEIGHT,
                                                      verbose=verbose)  # Convert to GUI window format

except IndexError:  # If no images of the correct type could be found:
    print('\n > > > > > > > > No "{}" images found in directory "{}". Quitting.\n'.format(imgExtensionType, refDirectoryPath))
    exit(0)

# Initialize image_elem to the first file in the list
image_elem = sg.Image(data=imgData)  # Image display element; will be updated later with other images

filename_display_elem = sg.Text(img_files[0],   size=(80, 1), font=("Helvetica", 18))
resize_display_elem   = sg.Text(imgResizeLabel, size=(80, 1), font=("Helvetica", 18))
file_num_display_elem = sg.Text('File 1 of {}'.format(len(img_files)), size=(10,1), font=("Helvetica", 18))

ref_dir_elem = [[sg.Text('Choose a directory containing the REFERENCE images: ', font=("Helvetica", 18))],
                [sg.InputText(basePath, key='_REF_DIR_', size=(50, 0.75), font=("Helvetica", 12)),
                 sg.FolderBrowse(initial_folder=basePath, font=("Helvetica", 16))]
                ]

file_listbox_elem = sg.Listbox(values=img_fileNames, size=(40,20), font=("Helvetica", 16), key='listbox')

# define layout, show and read the imageBrowser
# Define the buttons:
rightColumn = [[filename_display_elem], [resize_display_elem],
               [sg.ReadFormButton('Prev', size=(6,1), font=("Helvetica", 20)),
                sg.ReadFormButton('Next', size=(6,1), font=("Helvetica", 20)), file_num_display_elem,
                sg.ReadFormButton('Color Image', size=(14,1), font=("Helvetica", 20)),
                sg.ReadFormButton('Bayer Images 4up', size=(18, 1), font=("Helvetica", 20)),
                sg.ReadFormButton('Zscore Images 4up', size=(19, 1), font=("Helvetica", 20)),
                sg.ReadFormButton('Zscore > Limit 4up', size=(19, 1), font=("Helvetica", 20)),
                sg.ReadFormButton('QUIT', size=(10, 1.25), font=("Helvetica", 24))],
                [image_elem]
               ]

topRow = [[sg.Text('Choose a directory containing the REFERENCE images: ', font=("Helvetica", 18))],
          [sg.InputText(basePath, key='_REF_DIR_', size=(50, 0.75), font=("Helvetica", 12)),
           sg.FolderBrowse(initial_folder=basePath, font=("Helvetica", 16))],
          [sg.ReadFormButton('Change Directory', font=("Helvetica", 18))]
          ]

leftColumn = [[file_listbox_elem],
              [sg.ReadFormButton('Read selected image', font=("Helvetica", 18))]
              ]

layout = [[sg.Column(topRow)], [sg.Column(leftColumn), sg.Column(rightColumn)]]

button, values = imageBrowser.Layout(layout).Read()          # Shows imageBrowser on screen

i=0
keepGoing = True
filename = img_fileNames[0]  # initialize to first file

while keepGoing:
    if verbose: print('top')

    # Check for GUI buttons
    if button is None:
        if verbose: print("None\n")
        break  # do nothing; keep going

    elif button in ('Change Directory'):
        print("new reference folder chosen: {}".format(values['_REF_DIR_']))
        refDirectoryPath = values['_REF_DIR_']
        img_files, img_fileNames = cf.get_img_files(refDirectoryPath, '.jpg')

    elif button in ('Next', 'MouseWheel:Down', 'Down:40', 'Next:34'):  # and i < len(img_files)-1:
        print('down')
        i += 1
        if i > len(img_files) - 1:  # roll over to start of list
            i = 0

        filename = img_fileNames[i]  # update filename

    elif button in ('Prev', 'MouseWheel:Up', 'Up:38', 'Prior:33'):  # and i > 0:
        print('up')
        i -= 1
        if i < 0:  # roll over to end of list
            i = len(img_files) - 1

        filename = img_fileNames[i]  # update filename

    elif button in ('Color Image'):  # display the color image
        if verbose:
            print("Color Image")

        displayImage = cf.postprocessed_from_raw(refDirectoryPath, filename, verbose=verbose)  # extract the RGB image
        imgData, imgResizeLabel = cf.prep_img_for_display(displayImage,
                                                          maxDisplayWidth=MAX_WINDOW_WIDTH,
                                                          maxDisplayHeight=MAX_WINDOW_HEIGHT,
                                                          verbose=verbose)  # Convert to GUI window format
        image_elem.Update(data=imgData)  # update window with new image

    elif button in ('Bayer Images 4up'):  # display the Bayer array images
        if verbose:
            print("Bayer Images 4up")

        displayImage = cf.bayer4up_from_raw(refDirectoryPath, filename, verbose=verbose)  # extract the Bayer array images
        imgData, imgResizeLabel = cf.prep_img_for_display(displayImage,
                                                          maxDisplayWidth=MAX_WINDOW_WIDTH,
                                                          maxDisplayHeight=MAX_WINDOW_HEIGHT,
                                                          verbose=verbose)  # Convert to GUI window format

        image_elem.Update(data=imgData)  # update window with new image

    elif button in ('Zscore Images 4up'):  # display the Z-score image array
        if verbose:
            print("Zscore Images 4up")

        displayImage = cf.zScore4up_from_raw(refDirectoryPath, filename, stDev=STDEV, verbose=verbose)  # extract the Z-score images
        imgData, imgResizeLabel = cf.prep_img_for_display(displayImage,
                                                          maxDisplayWidth=MAX_WINDOW_WIDTH,
                                                          maxDisplayHeight=MAX_WINDOW_HEIGHT,
                                                          verbose=verbose)  # Convert to GUI window format

        image_elem.Update(data=imgData)  # update window with new image

    elif button in ('Zscore > Limit 4up'):  # display the Z-score exceeds limit image array
        if verbose:
            print("Zscore > Limit 4up")

        displayImage = cf.ZscoreExceedsZlimit4up_from_raw(refDirectoryPath, filename,
                         stDev=STDEV, zLimit=Z_LIMIT, verbose=verbose)  # Extract where the z-score exceeds a limit
        imgData, imgResizeLabel = cf.prep_img_for_display(displayImage,
                                                          maxDisplayWidth=MAX_WINDOW_WIDTH,
                                                          maxDisplayHeight=MAX_WINDOW_HEIGHT,
                                                          verbose=verbose)  # Convert to GUI window format

        image_elem.Update(data=imgData)  # update window with new image

    elif button in ('QUIT'):  # display the color image
        if verbose: print("Quit\n")
        sys.exit()

    elif button == 'Read selected image':
        try:
            filename = refDirectoryPath + '/' + values['listbox'][0]
            i = img_fileNames.index(values['listbox'][0])  # Locate the selected filename in the list of fileNames
            if verbose: print("filename = {}".format(filename))

        except IndexError:  # Throws an error if nothing is selected
            print('caught exception: IndexError - no image was selected ...')
            filename = img_files[0]
            i = 0  # Set to first element in listbox

        if verbose:
            print("Read selected image ({})  i set to {}.".format(filename, i))

    filename_display_elem.Update(filename)  # update window with filename
    resize_display_elem.Update(imgResizeLabel)  # update window with resize information
    file_num_display_elem.Update('File {} of {}'.format(i+1, len(img_files)))  # update page display

    file_listbox_elem.Update(values=img_fileNames, set_to_index=i)

    # read the imageBrowser
    button, values = imageBrowser.Read()


# Exit elegantly. (Without this, the Python object keeps running)
sys.exit()
