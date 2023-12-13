Oncolysis Controller
====================

Installation Instructions
-------------------------
Install/Run 32-bit Python 3.10+ (MUST BE 32-bit)::

    <path to 32 bit python>\python.exe install.py

This creates a virtual environment called env with the required dependencies. On Windows 10, Python may be installed to ``C:\Users\<uname>\AppData\Local\Programs\Python\Python310-32``

Install IVI Compliance Package 21.0
`https://www.ni.com/en-us/support/downloads/drivers/download/packaged.ivi-compliance-package.409836.html <https://www.ni.com/en-us/support/downloads/drivers/download/packaged.ivi-compliance-package.409836.html>`_

Install DG4000 IVI Driver
`https://www.rigolna.com/products/waveform-generators/dg4000/ <https://www.rigolna.com/products/waveform-generators/dg4000/>`_

Install UltraSigma Instrument Connectivity Driver
`https://beyondmeasure.rigoltech.com/acton/attachment/1579/u-0003/0/-/-/-/-/ <https://beyondmeasure.rigoltech.com/acton/attachment/1579/u-0003/0/-/-/-/-/>`_

Enable Windows to load drivers from unknown sources:
`https://www.isunshare.com/windows-11/how-to-disable-driver-signature-enforcement-on-windows-11.html <https://www.isunshare.com/windows-11/how-to-disable-driver-signature-enforcement-on-windows-11.html>`_

Download and install the Radiall USB Drivers from `https://www.radiall.com/products/rf-microwave-switches/usb-coaxial-switches.html <https://www.radiall.com/products/rf-microwave-switches/usb-coaxial-switches.html>`_. 

Copy the folder containing ``CP210xRuntime.dll``, ``Radial_USBInterface.dll`` and ``Radial_USBInterface.xml`` into a folder called ``dll`` in the root directory of the project.

License
-------
This project is licensed under the GNU Affero General Public License v3.0. See `LICENSE <LICENSE>`_ for details.

Contributing
------------
See `Contributor Guidelines <Contributor-Guidelines>`_ for details.

Disclaimer
----------
CAUTION - Investigational device. Limited by Federal (or United States) law to investigational use. The system described here has *not* been evaluated by the FDA and is not designed for the treatment or diagnosis of any disease. It is provided AS-IS, with no warranties. User assumes all liability and responsibility for identifying and mitigating risks associated with using this software.
