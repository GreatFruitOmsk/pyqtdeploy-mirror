#!/bin/sh

# Build for all
export SYSROOT=$HOME/usr/sysroot
rm -rf build
pyqtdeploycli --project pyqt-demo.pdy build
cd build
$SYSROOT/qt-5.5.1/bin/qmake
make

# Run for OSX.
./pyqt-demo.app/Contents/MacOS/pyqt-demo

# Run for Linux.
#./pyqt-demo

# Deploy for Android.
#make install INSTALL_ROOT=deploy
#$SYSROOT/qt-5.5.1/bin/androiddeployqt --input android-libpyqt-demo.so-deployment-settings.json --output deploy
#adb install deploy/bin/QtApp-debug.apk
