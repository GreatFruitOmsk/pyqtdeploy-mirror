.. _ref-win-dynload:

Windows and Dynamic Loading of Extension Modules
================================================

If an application makes use of C/C++ extension modules that would normally be
loaded dynamically by the Python interpreter library then you can often choose
to build a static version of the extension module and link it directly with the
deployed application.  This reduces the number of files being deployed and
avoids any possibility of conflicts with other versions of the same extension
module installed on the target system.

However some extension modules are not able to be built statically and so a
Python interpreter library that supports dynamic loading must be used.  On
Windows this is further complicated by the fact that the Python interpreter
library can only support dynamic loading if it itself is built as a DLL.  (On
non-Windows platforms there is no problem in statically linking the Python
interpreter library with the deployed application.)

Building the Python interpreter DLL on Windows is not particularly
straightforward, especially if you want to customise it for your specific
needs.  Therefore it is recommended that *if* you wish to dynamically load
C/C++ extension modules then you use a copy of the Python interpreter DLL that
is installed by the binary installer from python.org.
