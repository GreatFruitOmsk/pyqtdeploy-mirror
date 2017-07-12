set SYSROOT=C:\sysroot-win-64
if exist build rmdir /s /q build
pyqtdeploycli --project pyqt-demo.pdy build
chdir build
%SYSROOT%\bin\qmake
nmake
chdir release
pyqt-demo
chdir ..\..
