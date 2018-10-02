import sys
import os
from subprocess import call

fusion_path="/Applications/Fusion Studio 1.3.app/Contents/MacOS/./FusionStudio"


def showHelp():
    print("Usage:\n--help: show this menu\n--stitch_directory: GoPro root directory that contains images to fuse.\n--output_directory: output directory\n--dwarp: on/off turns on or off d.warp in stitching process.\n--upload_directory: directory containing images to upload to Mapillary's services.\n--debug: display debug information from Fusion software.")
    exit(1)

if (len(sys.argv) == 1):
    showHelp()

i = 1


stitch_directory=""
output_directory=""
upload_directory=""
dwarp_enabled="off"
debug_enabled="off"

def extractCLIValue(value):
    idx=value.find("=")
    return value[idx+1:]

def parseCLI(arg):
    # print(arg)
    global stitch_directory
    global output_directory
    global upload_directory
    global dwarp_enabled
    global debugp_enabled

    if (arg.find("help") >= 0):
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
        dwarp_enabled=extractCLIValue(arg)
    elif (arg.find("debug")>=0):
        debug_enabled=extractCLIValue(arg)

while (i < len(sys.argv)):
    idx=sys.argv[i].find("--")
    if (idx>=0):
        parseCLI(sys.argv[i][idx+2:])
    i=i+1



if (len(upload_directory) > 0 and os.path.isdir(upload_directory)):
    # run Mapillary's uploader
    print("Upload")
    exit(0)
elif (len(stitch_directory) == 0 or len(output_directory) == 0):
    print("Error: you need to input ")
    exit(0)
# print(stitch_directory + " " + output_directory)

gopro_filepaths=dict()

def execute_fusion(front_image, back_image, output_path):
    global dwarp_enabled
    system_call_array=[]
    system_call_array.append(fusion_path)
    system_call_array.append("--front")
    system_call_array.append(front_image)
    system_call_array.append("--back")
    system_call_array.append(back_image)
    system_call_array.append("--output")
    system_call_array.append(output_path)
    if (debug_enabled.find("on") >= 0 ):
        system_call_array.append("-l")
        system_call_array.append("6")
    if (dwarp_enabled.find("on") >= 0 ):
        system_call_array.append("--pc")
        system_call_array.append("1")
    
    call(system_call_array)

def runStitching():
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
            else:
                gopro_filepaths[gopro_number]=[]
                gopro_filepaths[gopro_number].append(subdir)
    
    # Loop over dict containing matched gopro directories.
    for key in gopro_filepaths:
        output_for_gopro_run="GP_"+key
        generated_dir_for_output=os.path.join(output_directory, output_for_gopro_run)
        if (os.path.isdir(generated_dir_for_output) == False):
            os.mkdir(generated_dir_for_output)

        # Sort files in directories to ensure order is similar when running through file indexes.
        idx=0
        front_img=sorted(os.listdir(gopro_filepaths[key][0]))
        back_img=sorted(os.listdir(gopro_filepaths[key][1]))
        sz=len(front_img)
        while (idx < sz):
            front_path=os.path.join(gopro_filepaths[key][0], front_img[idx])
            back_path=os.path.join(gopro_filepaths[key][1], back_img[idx])
            stitched_img=os.path.join(generated_dir_for_output, os.path.basename(front_path))
            print("Stitching " + stitched_img + "... with dwarp "  + dwarp_enabled)

            # Run stitching with parameters.
            execute_fusion(front_path, back_path,stitched_img)
            idx = idx+1


runStitching()
