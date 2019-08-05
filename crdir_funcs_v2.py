# crdir_funcs_v2.py
# V2 04 Aug 2019

# Support routines for Cosmic Ray Damage Image Repair (CRDIR) project
import os
import numpy as np
import inspect
import fitz  # Install "PyMuPDF", to get fitz functionality!
import rawpy
from scipy import signal

##############################################################################################################
def this_func():
    # return the name of the current function
    return inspect.stack()[1][3]

##############################################################################################################
def calling_func():
    # return the name of the calling function
    return inspect.stack()[2][3]

##############################################################################################################
def fitz_format(imgIn):
# Convert image to a fitz formated image for display:

    rawPixels = bytearray(imgIn.tostring())  # get plain pixel data from numpy array
    h, w = imgIn.shape[0:2]  # So it should work with monochrome and RGB images ...
    fitzImg = fitz.Pixmap(fitz.csRGB, w, h, rawPixels)

    return fitzImg

##############################################################################################################

def extract_from_raw(rawImage, verbose=False):

    RG1BG2Image = rawImage.raw_image   # image-size array (before demosaicing)
    BayerArray = rawImage.raw_colors  # image-size array with 0 = R, 1 = G1, 2 = B, 3 = G2

    Rimage  = RG1BG2Image[BayerArray == 0]  # extract the R  pixels from the RG1BG2 image (1/4 size)
    G1image = RG1BG2Image[BayerArray == 1]  # extract the G1 pixels from the RG1BG2 image (1/4 size)
    Bimage  = RG1BG2Image[BayerArray == 2]  # extract the B  pixels from the RG1BG2 image (1/4 size)
    G2image = RG1BG2Image[BayerArray == 3]  # extract the G2 pixels from the RG1BG2 image (1/4 size)

    h, w = RG1BG2Image.shape[0:2]  # get height and width of original image

    nColsReshape, nRowsReshape = int(w / 2), int(h / 2)
    Rimage  = np.reshape(Rimage,  (-1, nColsReshape))
    G1image = np.reshape(G1image, (-1, nColsReshape))
    G2image = np.reshape(G2image, (-1, nColsReshape))
    Bimage  = np.reshape(Bimage,  (-1, nColsReshape))

    if verbose:
        print('\n ************* In |{}|, called by |{}|: ************* '.format(this_func(), calling_func()))
        print('BayerArray.shape = {}'.format(BayerArray.shape))
        print('RGBGimage.shape = {}'.format(RG1BG2Image.shape))
        print('type(Rimage) = {}'.format(type(Rimage)))

        print('Rimage.shape  AFTER reshaping = {}'.format(Rimage.shape))
        print('G1image.shape AFTER reshaping = {}'.format(G1image.shape))
        print('G2image.shape AFTER reshaping = {}'.format(G2image.shape))
        print('Bimage.shape  AFTER reshaping = {}'.format(Bimage.shape))

        print("BayerArray[0:12,0:12] = \n{}".format(BayerArray[0:12,0:12]))
        print("RGBGimage[0:12,0:12] = \n{}".format(RG1BG2Image[0:12,0:12]))

        print("Rimage[0:6,0:6]  = \n{}".format(Rimage[0:6,0:6]))
        print("G1image[0:6,0:6] = \n{}".format(G1image[0:6,0:6]))
        print("G2image[0:6,0:6] = \n{}".format(G2image[0:6,0:6]))
        print("Bimage[0:9,0:9]  = \n{}".format(Bimage[0:9,0:9]))

    if verbose:
            print('\n ************* Returning to |{}| from |{}|. ************* \n'.format(calling_func(), this_func()))

    return RG1BG2Image, Rimage, G1image, G2image, Bimage

##############################################################################################################

def calculate_eight_neighbor_mean(grayscaleImg, verbose=False):

    # Return an image in which each pixel value is the mean of the 'surrounding' eight pixels. Treat the borders as '0'
    # and return an image the same size as the original (mode='same'). [Calculated via convolution with 'ring' kernel]

    imgDim = len(grayscaleImg.shape)  # Dimensionality of image; want 2D (grayscale), not 3D (color)

    if imgDim != 2:
        print('\n ************* In |{}|, called by |{}|: ************* '.format(this_func(), calling_func()))
        print("Error: {} requires a grayscale (2D) image, but received a {}D image".format(this_func(), imgDim))

        return None

    eightNeighborKernel = np.array([[1, 1, 1],
                                    [1, 0, 1],
                                    [1, 1, 1]]) / 8

    EightNeighborMeanImg = signal.convolve2d(grayscaleImg, eightNeighborKernel, mode='same')

    if verbose:
        print('\n ************* In |{}|, called by |{}|: ************* '.format(this_func(), calling_func()))
        print("EightNeighborMeanImg[0:9,0:9] = \n{}".format(EightNeighborMeanImg[0:9,0:9]))

    if verbose:
            print('\n ************* Returning to |{}| from |{}|. ************* \n'.format(calling_func(), this_func()))

    return EightNeighborMeanImg

##############################################################################################################

def calculate_median_image(grayscaleImg, medianFilterSize=3, verbose=False):

    # Return an image in which each pixel value is the median of the 'surrounding' pixels based on a filter size
    # of medianFilterSize (default = 3x3).

    imgDim = len(grayscaleImg.shape)  # Dimensionality of image; want 2D (grayscale), not 3D (color)

    if imgDim != 2:
        print('\n ************* In |{}|, called by |{}|: ************* '.format(this_func(), calling_func()))
        print("Error: {} requires a grayscale (2D) image, but received a {}D image".format(this_func(), imgDim))

        return None

    kernel_size = medianFilterSize

    medianFilteredImg = signal.medfilt2d(grayscaleImg, kernel_size = medianFilterSize)

    if verbose:
        print('\n ************* In |{}|, called by |{}|: ************* '.format(this_func(), calling_func()))
        print("medianFilterSize[0:9,0:9] = \n{}".format(medianFilterSize[0:9,0:9]))

    if verbose:
            print('\n ************* Returning to |{}| from |{}|. ************* \n'.format(calling_func(), this_func()))

    return medianFilteredImg


##############################################################################################################

def calculate_eight_neighbor_mean_images_from_raw(rawImage, verbose=False):
    # Extract RG1G2B, R, G1, G2, & B from raw image, and calculate 8-neighbor mean images for each

    RG1BG2image, Rimage, G1image, G2image, Bimage = extract_from_raw(rawImage, verbose=verbose)

    RG1BG2meanImage = calculate_eight_neighbor_mean(RG1BG2image, verbose=verbose)

    RmeanImage  = calculate_eight_neighbor_mean(Rimage,  verbose=verbose)
    G1meanImage = calculate_eight_neighbor_mean(G1image, verbose=verbose)
    G2meanImage = calculate_eight_neighbor_mean(G2image, verbose=verbose)
    BmeanImage  = calculate_eight_neighbor_mean(Bimage,  verbose=verbose)

    return RG1BG2meanImage, RmeanImage, G1meanImage, G2meanImage, BmeanImage

##############################################################################################################

def calculate_Zscore_images_from_raw(rawImage, globalSigma, verbose=False):
    # Extract RG1G2B, R, G1, G2, & B from raw image,
    # calculate 8-neighbor mean images for each,
    # and calculate Z-scores based on those values and the passed global sigma value

    RG1BG2image, Rimage, G1image, G2image, Bimage = extract_from_raw(rawImage, verbose=verbose)

    RG1BG2meanImage, RmeanImage, G1meanImage, G2meanImage, BmeanImage = \
        calculate_eight_neighbor_mean_images_from_raw(rawImage, verbose=False)

    RG1BG2_ZscoreImage = (RG1BG2image - RG1BG2meanImage) / globalSigma  # how many StDevs is pixel away from its 8 nearest neighbors?

    R_ZscoreImage  = (Rimage  - RmeanImage)  / globalSigma  # how many StDevs is pixel from its neighbors?
    G1_ZscoreImage = (G1image - G1meanImage) / globalSigma  # how many StDevs is pixel from its neighbors?
    G2_ZscoreImage = (G2image - G2meanImage) / globalSigma  # how many StDevs is pixel from its neighbors?
    B_ZscoreImage  = (Bimage  - BmeanImage)  / globalSigma  # how many StDevs is pixel from its neighbors?

    if verbose:
        print("RG1BG2_ZscoreImage[0:9,0:9]  = \n{}".format(RG1BG2_ZscoreImage[0:9, 0:9]))

        print("R_ZscoreImage[0:9,0:9]  = \n{}".format(R_ZscoreImage[0:9, 0:9]))
        print("G1_ZscoreImage[0:9,0:9] = \n{}".format(G1_ZscoreImage[0:9, 0:9]))
        print("G2_ZscoreImage[0:9,0:9] = \n{}".format(G2_ZscoreImage[0:9, 0:9]))
        print("B_ZscoreImage[0:9,0:9]  = \n{}".format(B_ZscoreImage[0:9, 0:9]))


    return RG1BG2_ZscoreImage, R_ZscoreImage, G1_ZscoreImage, G2_ZscoreImage, B_ZscoreImage

##############################################################################################################


def find_where_Zscore_exceeds_Z_limit(ZscoreImage, ZscoreLimit, label='', verbose=False):
    # Check each pixel in Zscore image to see where it exceeds the Zscore limit passed as parameter

    exceedsZlimitArray = np.argwhere(abs(ZscoreImage) > ZscoreLimit)

    if verbose:
        h,w = ZscoreImage.shape[0:2]

        print("np.abs({}_ZscoreImage) > {} StDev: [{:4d} / {:5.2f}M pixels ({:0.4f}%)]= \n{}"
              .format(label, ZscoreLimit, len(exceedsZlimitArray),
                      (w * h) / (1024 * 1024),
                      100 * len(exceedsZlimitArray) / (w * h), exceedsZlimitArray))

    return exceedsZlimitArray

##############################################################################################################

def postprocessed_from_raw(imgDir, rawImgFname, verbose=False):

    if rawImgFname.lower().endswith('.nef'):  # If this is a raw image

        if verbose:
            print("In {}, called from {}:  imgDir = {}, rawImgFname = {}"
                  .format(this_func(), calling_func(), imgDir, rawImgFname))

        # Extract rawImage
        rawImage = rawpy.imread(os.path.join(imgDir, rawImgFname))
        postprocessedImage = rawImage.postprocess()  # extract the RGB image

        if verbose:
            print("postprocessedImage.shape = {}".format(postprocessedImage.shape))
            print("type(postprocessedImage) = {}".format(type(postprocessedImage)))
            print("type(postprocessedImage[0]) = {}".format(type(postprocessedImage[0, 0, 0])))

        return postprocessedImage
    else:
        print("postprocessedImage requires a raw image - received {}".format(rawImgFname))
        return None  # If no valid raw image received

##############################################################################################################

def bayer4up_from_raw(imgDir, rawImgFname, verbose=False):

    if rawImgFname.lower().endswith('.nef'):  # If this is a raw image

        # Extract R, G1, B, & G2 channels from raw image
        rawImage = rawpy.imread(os.path.join(imgDir, rawImgFname))
        RG1BG2image, Rimage, G1image, G2image, Bimage = extract_from_raw(rawImage, verbose=verbose)

        # Create 4up Bayer images
        bayer4up = np.vstack([np.hstack([Rimage, G1image]), np.hstack([G2image, Bimage])])  # make 2x2 R G1 / G2 B
        bayer4upRGB = np.dstack([bayer4up, bayer4up, bayer4up]).astype(np.uint8)  # make a 3-color version

        if verbose:
            print("bayer4upRGB.shape = {}".format(bayer4upRGB.shape))
            print("type(bayer4upRGB) = {}".format(type(bayer4upRGB)))
            print("type(bayer4upRGB[0]) = {}".format(type(bayer4upRGB[0, 0, 0])))

        return bayer4upRGB
    else:
        print("bayer4up_from_raw requires a raw image - received {}".format(rawImgFname))
        return None  # If no valid raw image received

##############################################################################################################

def zScore4up_from_raw(imgDir, rawImgFname, stDev, verbose=False):

    if rawImgFname.lower().endswith('.nef'):  # If this is a raw image

        # Extract R, G1, B, & G2 channels from raw image
        rawImage = rawpy.imread(os.path.join(imgDir, rawImgFname))

        # Create z-score images
        RG1BG2_ZscoreImage, R_ZscoreImage, G1_ZscoreImage, G2_ZscoreImage, B_ZscoreImage = \
            calculate_Zscore_images_from_raw(rawImage, stDev, verbose=False)

        # Create z-Score 4-up images
        Zscore4up = np.vstack([np.hstack([R_ZscoreImage, G1_ZscoreImage]),
                               np.hstack([G2_ZscoreImage, B_ZscoreImage])])  # make 2x2 R G1 / G2 B
        Zscore4upRGB = np.dstack([Zscore4up, Zscore4up, Zscore4up]).astype(np.uint8)  # make a 3-color version

        if verbose:
            print("np.max(Zscore4upRGB) = {}".format(np.max(Zscore4upRGB)))

        return Zscore4upRGB
    else:
        print("zScore4up_from_raw requires a raw image - received {}".format(rawImgFname))
        return None  # If no valid raw image received

##############################################################################################################

def ZscoreExceedsZlimit4up_from_raw(imgDir, rawImgFname, stDev, zLimit, verbose=False):

    if rawImgFname.lower().endswith('.nef'):  # If this is a raw image

        # Extract R, G1, B, & G2 channels from raw image
        rawImage = rawpy.imread(os.path.join(imgDir, rawImgFname))

        # Create z-score images
        RG1BG2_ZscoreImage, R_ZscoreImage, G1_ZscoreImage, G2_ZscoreImage, B_ZscoreImage = \
            calculate_Zscore_images_from_raw(rawImage, stDev, verbose=False)

        # Create z-score over limit images
        RawImageExceedsZlimit = find_where_Zscore_exceeds_Z_limit(RG1BG2_ZscoreImage, zLimit, 'RAW',
                                                                     verbose=verbose)

        RimageExceedsZlimit  = find_where_Zscore_exceeds_Z_limit(R_ZscoreImage,  zLimit, 'R',  verbose=verbose)
        G1imageExceedsZlimit = find_where_Zscore_exceeds_Z_limit(G1_ZscoreImage, zLimit, 'G1', verbose=verbose)
        G2imageExceedsZlimit = find_where_Zscore_exceeds_Z_limit(G2_ZscoreImage, zLimit, 'G2', verbose=verbose)
        BimageExceedsZlimit  = find_where_Zscore_exceeds_Z_limit(B_ZscoreImage,  zLimit, 'B',  verbose=verbose)

        R_ZscoreExceedsZlimitMask  = np.zeros_like(R_ZscoreImage)  # make 'black' image the size of R_Zscore image
        G1_ZscoreExceedsZlimitMask = np.zeros_like(G1_ZscoreImage) # make 'black' image the size of G1_Zscore image
        B_ZscoreExceedsZlimitMask  = np.zeros_like(B_ZscoreImage)  # make 'black' image the size of B_Zscore image
        G2_ZscoreExceedsZlimitMask = np.zeros_like(G2_ZscoreImage) # make 'black' image the size of G2_Zscore image

        if verbose:
            print("Before: np.sum(R_ZscoreExceedsZlimitMask)  = {}".format(np.sum(R_ZscoreExceedsZlimitMask)))
            print("Before: np.sum(G1_ZscoreExceedsZlimitMask) = {}".format(np.sum(G1_ZscoreExceedsZlimitMask)))
            print("Before: np.sum(B_ZscoreExceedsZlimitMask)  = {}".format(np.sum(B_ZscoreExceedsZlimitMask)))
            print("Before: np.sum(G2_ZscoreExceedsZlimitMask) = {}".format(np.sum(G2_ZscoreExceedsZlimitMask)))

        R_ZscoreExceedsZlimitMask = np.where(R_ZscoreImage > zLimit,  # Everywhere the Z-score exceeds the limit;
                                             255,  # Set to 'white'
                                             R_ZscoreExceedsZlimitMask)  # Else, keep the 0s
        G1_ZscoreExceedsZlimitMask = np.where(G1_ZscoreImage > zLimit,  # Everywhere the Z-score exceeds the limit;
                                             255,  # Set to 'white'
                                             G2_ZscoreExceedsZlimitMask)  # Else, keep the 0s
        B_ZscoreExceedsZlimitMask = np.where(B_ZscoreImage > zLimit,  # Everywhere the Z-score exceeds the limit;
                                             255,  # Set to 'white'
                                             B_ZscoreExceedsZlimitMask)  # Else, keep the 0s
        G2_ZscoreExceedsZlimitMask = np.where(G2_ZscoreImage > zLimit,  # Everywhere the Z-score exceeds the limit;
                                             255,  # Set to 'white'
                                             G2_ZscoreExceedsZlimitMask)  # Else, keep the 0s

        if verbose:
            print("After: np.sum(R_ZscoreExceedsZlimitMask)  = {}".format(np.sum(R_ZscoreExceedsZlimitMask)))
            print("After: np.sum(G1_ZscoreExceedsZlimitMask) = {}".format(np.sum(G1_ZscoreExceedsZlimitMask)))
            print("After: np.sum(B_ZscoreExceedsZlimitMask)  = {}".format(np.sum(B_ZscoreExceedsZlimitMask)))
            print("After: np.sum(G2_ZscoreExceedsZlimitMask) = {}".format(np.sum(G2_ZscoreExceedsZlimitMask)))
            print("After: np.max(G2_ZscoreExceedsZlimitMask) = {}".format(np.max(G2_ZscoreExceedsZlimitMask)))

        ZscoreExceedsZlimit4up = np.vstack([np.hstack([R_ZscoreExceedsZlimitMask, G1_ZscoreExceedsZlimitMask]),
                                            np.hstack([G2_ZscoreExceedsZlimitMask, B_ZscoreExceedsZlimitMask])])  # make 2x2 R G1 / G2 B

        ZscoreExceedsZlimit4upRGB = np.dstack(
            [ZscoreExceedsZlimit4up, ZscoreExceedsZlimit4up, ZscoreExceedsZlimit4up]).astype(np.uint8)  # 3-color

        if verbose:
            print("type(ZscoreExceedsZlimit4upRGB) = {}".format(type(ZscoreExceedsZlimit4upRGB)))
            print("ZscoreExceedsZlimit4upRGB[0:9, 0:9, 0] = {}".format(ZscoreExceedsZlimit4upRGB[0:9, 0:9, 0]))
            print("np.max(ZscoreExceedsZlimit4upRGB) = {}".format(np.max(ZscoreExceedsZlimit4upRGB)))

        return ZscoreExceedsZlimit4upRGB
    else:  # Not a raw image
        print("ZscoreExceedsZlimit4up_from_raw requires a raw image - received {}".format(rawImgFname))
        return None  # If no valid raw image received

###################################################################################################################
def prep_img_for_display(imgIn, maxDisplayWidth=1024, maxDisplayHeight=768, verbose=False):

    # Take as input an RGB image, return a png formatted string for use in GUI

    if verbose: print("type(imgIn) = {}".format(type(imgIn)))

    imgOut = fitz_format(imgIn)

    pixMap = fitz.Pixmap(imgOut.colorspace, (0, 0, maxDisplayWidth, maxDisplayHeight), imgOut.alpha)  # background
    pixMap.clearWith(225)  # Set to color

    imgResizeRatio = max(imgOut.height / maxDisplayHeight, imgOut.width / maxDisplayWidth)
    shrinkN = 0  # Initialize
    imgResizeLabel = ''  # Initialize to blank

    if imgResizeRatio > 1.0:  # If image is too large to display without resizing: Resize the image to fit in the display
        shrinkN = int(np.ceil(np.log2(imgResizeRatio)))  # 2^n power by which image will be resized by shrink()
        imgResizeLabel = 'Resized from {}x{} by factor of {}   (2^{})'.format(imgOut.width, imgOut.height,
                                                                              2 ** shrinkN, shrinkN)
        imgOut.shrink(shrinkN)

    if verbose:
        print('In |{}|,  called by |{}|'.format(this_func(), calling_func()))
        print('img.height={} MAX_WINDOW_HEIGHT= {}'.format(imgOut.height, maxDisplayHeight))
        print('img.width={}  MAX_WINDOW_WIDTH = {}'.format(imgOut.width, maxDisplayWidth))
        print('imgResizeRatio = {}'.format(imgResizeRatio))
        print('shrinkN = {}'.format(shrinkN))
        print('imgResizeLabel = {}'.format(imgResizeLabel))

    # Set the x,y location of img based on width (to keep it centered)
    imgOut.x, imgOut.y = int((maxDisplayWidth - imgOut.width) / 2), int((maxDisplayHeight - imgOut.height) / 2)
    pixMap.copyPixmap(imgOut, imgOut.irect)  # Copy the image onto the background

    imgData = pixMap.getImageData("png")  # Convert to data string in png format

    return imgData, imgResizeLabel

###################################################################################################################
def get_img_files(refDirectoryPath, fileExtension='.jpg', verbose=False):
    img_files = []
    img_fileNames = []

    for entry in os.scandir(refDirectoryPath):
        if entry.name.startswith('.'):  # it is a hidden file ...
            if verbose:
                print('"{}" is a hidden file and will be ignored.'.format(entry.name))
        else:
            if entry.is_file():  # Only take images in this directory, NOT subdirectories.
                if verbose:
                    print('"{}"'.format(entry.name), end='')
                if fileExtension in entry.name:
                    if verbose:
                        print(" is a {} file.".format(fileExtension))
                    img_files.append("{}/{}".format(refDirectoryPath, entry.name))
                    img_fileNames.append(entry.name)
                else:
                    if verbose:
                        print("{} is not the requested image type.")
            else:
                print('Any images in directory "{}" WILL NOT BE PROCESSED!'.format(entry.name))

    img_files.sort()
    img_fileNames.sort()

    return(img_files, img_fileNames)

###################################################################################################################
def cv_max_dim(img):
    return np.max(img.shape[1::-1])