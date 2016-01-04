set SYSROOT=C:\sysroot-win-64
if exist build rmdir /s /q build
c:\Python34\Scripts\pyqtdeploycli --project pyqt-demo.pdy build
chdir build
%SYSROOT%\qt-5.5.1\bin\qmake
nmake
chdir release
pyqt-demo
chdir ..\..
