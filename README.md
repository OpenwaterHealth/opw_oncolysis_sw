# Oncolysis Controller

## Installation Instructions 
Install/Run 32-bit Python 3.10+ (MUST BE 32-bit):
`<path to 32 bit python>\python.exe install.py`

This creates a virtual environment called env with the required dependencies. On Windows 10, Python may be installed to `C:\Users\<uname>\AppData\Local\Programs\Python\Python310-32`

Install IVI Compliance Package 21.0
https://www.ni.com/en-us/support/downloads/drivers/download/packaged.ivi-compliance-package.409836.html

Install DG4000 IVI Driver
https://www.rigolna.com/products/waveform-generators/dg4000/

Install UltraSigma Instrument Connectivity Driver
https://beyondmeasure.rigoltech.com/acton/attachment/1579/u-0003/0/-/-/-/-/

Enable Windows to load drivers from unknown sources:
https://www.isunshare.com/windows-11/how-to-disable-driver-signature-enforcement-on-windows-11.html

Download and install the Radiall USB Drivers from https://www.radiall.com/products/rf-microwave-switches/usb-coaxial-switches.html. 
Copy the folder containing `CP210xRuntime.dll`, `Radial_USBInterface.dll` and `Radial_USBInterface.xml` into a folder called `dll` in the root directory of the project.
