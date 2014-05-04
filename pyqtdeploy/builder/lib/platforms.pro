linux-* {
    LIBS += -lutil -ldl
}

win32-msvc* {
    LIBS += -ladvapi32 -lshell32 -luser32
}
