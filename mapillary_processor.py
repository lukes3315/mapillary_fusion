import sys
import os
from subprocess import call
from PIL.ExifTags import TAGS
from PIL import Image

# Generic fusion path on Mac OS X to execute.
fusion_path="/Applications/Fusion Studio 1.3.app/Contents/MacOS/./FusionStudio"

def showHelp():
    print("Usage:\n--help: show this menu.\n--stitch_directory: GoPro root directory that contains images to fuse.\n--output_directory: output directory, where your stitched will be stored.\n--dwarp: on/off turns on or off d.warp in stitching process (off by default).\n--upload_directory: directory containing images to upload to Mapillary's services.\n--debug: display debug information from Fusion software.\n--user: Your mapillary username, view README (only required for upload procedure).\n")
    exit(1)

if (len(sys.argv) == 1):
    showHelp()

# Global parameters and configuration acquired from CLI
stitch_directory=""
output_directory=""
upload_directory=""
mapillary_username=""
dwarp_enabled="off"
debug_enabled="off"

# Extract value of CLI argument
def extractCLIValue(value):
    idx=value.find("=")
    return value[idx+1:]

def parseCLI(arg):
    global stitch_directory
    global output_directory
    global upload_directory
    global dwarp_enabled
    global debug_enabled
    global mapillary_username
    
    # Parsing CLI.
    if (arg.find("help") >= 0):
        # Display help
        showHelp()
    elif (arg.find("stitch_directory") >= 0):
        #go pro dir
        stitch_directory=extractCLIValue(arg)
    elif (arg.find("output_directory") >= 0):
        #output directory
        output_directory=extractCLIValue(arg)
    elif (arg.find("upload_directory")>=0):
        #upload directory
        upload_directory=extractCLIValue(arg)
    elif (arg.find("dwarp")>=0):
        #enabling/disabling dwarp
        dwarp_enabled=extractCLIValue(arg)
    elif (arg.find("debug")>=0):
        #enabling/disabling FusionStudio debug logs
        debug_enabled=extractCLIValue(arg)
    elif (arg.find("user")>=0):
        #entering mapillary username for upload
        mapillary_username=extractCLIValue(arg)
i = 1
while (i < len(sys.argv)):
    idx=sys.argv[i].find("--")
    if (idx>=0):
        # Run through CLI arguments.
        parseCLI(sys.argv[i][idx+2:])
    i=i+1

if (len(upload_directory) > 0 and os.path.isdir(upload_directory)):
    # run Mapillary's uploader
    if (len(mapillary_username) == 0 ):
        print("You need to enter your user name, please view README.md")
        exit(0)
    # Run Mapillary's process and upload system.
    mapillary_call=[]
    mapillary_call.append("mapillary_tools")
    mapillary_call.append("process_and_upload")
    mapillary_call.append("--import_path")
    # Set upload directory for Mapillary's upload engine
    mapillary_call.append(upload_directory)
    mapillary_call.append("--user_name")
    # Set username for upload.
    mapillary_call.append(mapillary_username)
    call(mapillary_call)
    exit(0)
elif (len(stitch_directory) == 0 or len(output_directory) == 0):
    print("Error: you need to input both the directory to stitch AND the output directory.")
    exit(0)

gopro_filepaths=dict()


def getMetaInformation(file):
    img = Image.open(file)
    info = img._getexif()
    decoded = dict((TAGS.get(key, key), value) for key, value in info.items())
    # print(decoded)
    if decoded.get('GPSInfo'):
        exif = img.info['exif']
        return exif
    return None


def writeExif(meta, output_path):
    override_img=Image.open(output_path)
    override_img.save(output_path, exif=meta)


def saveExifToStitchedImage(front_meta, back_meta, output_path):
    if (front_meta != None):
        writeExif(front_meta,output_path)
    elif(back_meta != None):
        writeExif(back_meta, output_path)

def execute_fusion(front_image, back_image, output_path):
    global dwarp_enabled

    front_meta=getMetaInformation(front_image)
    back_meta=None
    if (front_meta == None):
        back_meta=getMetaInformation(back_image)

    system_call_array=[]
    system_call_array.append(fusion_path)
    # Set front image path
    system_call_array.append("--front")
    system_call_array.append(front_image)
    # Set back image path
    system_call_array.append("--back")
    system_call_array.append(back_image)
    # Set output path for stitched image
    system_call_array.append("--output")
    system_call_array.append(output_path)
    if (debug_enabled.find("on") >= 0 ):
        # Set log level for FusionStudio
        system_call_array.append("-l")
        system_call_array.append("6")
    if (dwarp_enabled.find("on") >= 0 ):
        # Enable parallax compensation
        system_call_array.append("--pc")
        system_call_array.append("1")
    
    call(system_call_array)
    saveExifToStitchedImage(front_meta, back_meta, output_path)


def runStitching(go_pro_number, dir_list):
        # Create output directory for stitched images of current GoPro dataset being processed.
        output_for_gopro_run="GP_"+go_pro_number
        generated_dir_for_output=os.path.join(output_directory, output_for_gopro_run)
        if (os.path.isdir(generated_dir_for_output) == False):
            os.mkdir(generated_dir_for_output)
        idx=0
        # Sort file list to ensure they are in the same numerical order for stitching.
        front_img=sorted(os.listdir(dir_list[0]))
        back_img=sorted(os.listdir(dir_list[1]))
        sz=len(front_img)
        bk_sz=len(back_img)
        if (sz != bk_sz):
            print("Error: matching directories %s and %s have different sizes. This means your GoPro datasets are invalid." % (dir_list[0], dir_list[1]))
            exit(0)
        while (idx < sz):
            # Loop through FRONT and BACK files from associated GoPro directories.
            front_path=os.path.join(dir_list[0], front_img[idx])
            back_path=os.path.join(dir_list[1], back_img[idx])
            # Generated stitched image output file.

            stitched_img=os.path.join(generated_dir_for_output, os.path.basename(front_path))
            print("Stitching " + stitched_img + "... with dwarp "  + dwarp_enabled)

            # Run stitching with parameters.
            # Could be done in parallel, tried it with Python's process pool, but FusionStudio doesn't seem to like it...
            execute_fusion(front_path, back_path, stitched_img)
            idx = idx+1
            
        


def listDirs():
    # If output directory for stitched images doesn't exist, create it.
    if (os.path.isdir(output_directory)==0):
        os.mkdir(output_directory)
    # Traverse directory structure by depth to find GoPro file directories and match up the FRONT and BACK directories automatically
    # in gopro_filepaths dict()
    for subdir, dirs, files in os.walk(stitch_directory):
        raw_name=os.path.basename(subdir)
        gopro_number=os.path.basename(raw_name)[:3]
        if (gopro_number.isdigit() and (subdir.find("GF") >= 0 or subdir.find("GB") >= 0)):
            if (gopro_number in gopro_filepaths.keys()):
                gopro_filepaths[gopro_number].append(subdir)
                # Found associated directory, run stitching.
                runStitching(gopro_number, gopro_filepaths[gopro_number])
            else:
                gopro_filepaths[gopro_number]=[]
                gopro_filepaths[gopro_number].append(subdir)

listDirs()