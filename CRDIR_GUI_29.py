# import PySimpleGUI as sg  # Qt works on MacOS better
import PySimpleGUIQt as sg  # Qt works on MacOS better
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import cv2
import rawpy
import fitz
from scipy import signal

import crdir_funcs as cf




import CRDIR_GUI_SUPPORT as crdir

STDEV = 50  # Assumed constant standard deviation of pixels in image
Z_LIMIT = 2 # Z-score flagged as bad pixel

verbose = True

# MAX_DISPLAY_SIZE = 1900 # 1280

MAX_WINDOW_WIDTH = 2200
MAX_WINDOW_HEIGHT = int(MAX_WINDOW_WIDTH*0.7)

# Determine whose computer we're on:
if os.path.exists('/Users/pelz'):  # You are on Jeff's computer
    USER = 'Jeff'
    userPath = '/Users/pelz'
    crdirDirPath = 'Documents/CRDIR/to process images'  # 'Documents/CRDIR'

elif os.path.exists('/Users/xx'):  # You are on XX's computer:
    USER = 'XX'
    userPath = '/Users/xx'
    crdirDirPath = 'Documents/CRDIR'

else:
    USER = "Unknown"
    userPath = '/Users'
    crdirDirPath = ''

# Set basePath based on which computer we're on
basePath = "{}/{}".format(userPath, crdirDirPath)

if verbose:
    print("user = {}   basePath = {}".format(USER, basePath))

# Set up the SimpleGUI (sg)
sg.ChangeLookAndFeel('Reddit')
refDirectoryPath = basePath
imgExtensionType = '.nef' # '.jpg'
msgExtensionType = '.png'

# Select a directory and read in the IMAGE files from that directory
img_files, img_fileNames = crdir.get_img_files(refDirectoryPath, imgExtensionType)

# Select a directory and read in the MESSAGE files from that directory
msg_files, msg_fileNames = crdir.get_img_files(refDirectoryPath, msgExtensionType)

print('msg_fileNames = {}'.format(msg_fileNames))

# ####  Image browser ####
# create the imageBrowser that returns keyboard events
imageBrowser = sg.FlexForm('Image Browser', return_keyboard_events=True, location=(0,0), use_default_focus=False )

# Check to be sure there are images to read
try:
    img = fitz.Pixmap(img_files[0])  # Read first image into PyMuPDF
    if verbose: print("Reading {}:".format(img_files[0]))

except IndexError:  # If no images of the correct type could be found:
    print('\n > > > > > > > > No "{}" images found in directory "{}". Quitting.\n'.format(imgExtensionType, refDirectoryPath))
    exit(0)

# create target pixmap
blank_pix = fitz.Pixmap(img.colorspace, (0, 0, MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT), img.alpha)
blank_pix.clearWith(225)  # Set to 'background' color

imgResizeRatio = max(img.height/MAX_WINDOW_HEIGHT, img.width/MAX_WINDOW_WIDTH)
if verbose:
    print('img.height={} MAX_WINDOW_HEIGHT= {}'.format(img.height, MAX_WINDOW_HEIGHT))
    print('img.width={}  MAX_WINDOW_WIDTH = {}'.format(img.width,  MAX_WINDOW_WIDTH))
    print('imgResizeRatio = {}'.format(imgResizeRatio))

imgResizeLabel = ''  # Initialize to blank

if imgResizeRatio < 1.0:  # If image is too large to display without resizing: Resize the image to fit in the display
    shrinkN = int(np.ceil(np.log2(imgResizeRatio)))  # 2^n power by which image will be resized by shrink()
    imgResizeLabel = 'Resized from {}x{} by factor of {}    (2^{})'.format(img.width, img.height, 2**shrinkN, shrinkN)
    img.shrink(shrinkN)

# Set the x,y location of img based on width (to keep it centered)
img.x, img.y = int((MAX_WINDOW_WIDTH - img.width) / 2), int((MAX_WINDOW_HEIGHT - img.height) / 2)

blank_pix.copyPixmap(img, img.irect)  # Copy the image onto the background
imgDdata = blank_pix.getImageData("png")   # Convert to data string in png format

# Make these 3 elements outside the layout because we want to "update" them later

# Initialize image_elem to the first file in the list
# Initialize wait_elem to "loading"

image_elem = sg.Image(data=imgDdata)  # Image display element; can be updated later

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
        img_files, img_fileNames = crdir.get_img_files(refDirectoryPath, '.jpg')

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

        displayImage = cf.postprocessed_from_raw(filename, verbose=verbose)  # extract the RGB image
        imgData = cf.prep_img_for_display(displayImage, maxDisplaySize=MAX_WINDOW_WIDTH)    # Convert to GUI window format
        image_elem.Update(data=imgData)  # update window with new image

    elif button in ('Bayer Images 4up'):  # display the Bayer array images
        if verbose:
            print("Bayer Images 4up")

        displayImage = cf.bayer4up_from_raw(filename, verbose=verbose)  # extract the Bayer array images
        imgData = cf.prep_img_for_display(displayImage, maxDisplaySize=MAX_WINDOW_WIDTH)  # Convert to GUI window format
        image_elem.Update(data=imgData)  # update window with new image

    elif button in ('Zscore Images 4up'):  # display the Z-score image array
        if verbose:
            print("Zscore Images 4up")

        displayImage = cf.zScore4up_from_raw(filename, stDev=STDEV, verbose=verbose)  # extract the Z-score images
        imgData = cf.prep_img_for_display(displayImage, maxDisplaySize=MAX_WINDOW_WIDTH)  # Convert to GUI window format
        image_elem.Update(data=imgData)  # update window with new image

    elif button in ('Zscore > Limit 4up'):  # display the Z-score exceeds limit image array
        if verbose:
            print("Zscore > Limit 4up")

        displayImage = cf.ZscoreExceedsZlimit4up_from_raw(filename,
                         stDev=STDEV, zLimit=Z_LIMIT, verbose=verbose)  # Extract where the z-score exceeds a limit
        imgData = cf.prep_img_for_display(displayImage, maxDisplaySize=MAX_WINDOW_WIDTH)  # Convert to GUI window format
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
