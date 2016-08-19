set SYSROOT=C:\sysroot-win-64
if exist build rmdir /s /q build
c:\Python35\Scripts\pyqtdeploycli --project pyqt-demo.pdy build
chdir build
%SYSROOT%\bin\qmake
nmake
chdir release
pyqt-demo
chdir ..\..
