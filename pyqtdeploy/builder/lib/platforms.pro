linux-* {
    LIBS += -lutil
}

win32-msvc* {
    LIBS += -lshell32 -ladvapi32
}
