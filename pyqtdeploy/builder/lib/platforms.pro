linux-* {
    LIBS += -lutil -ldl
}

win32 {
    LIBS += -ladvapi32 -lshell32 -luser32
}

macx {
    LIBS += -framework SystemConfigration -framework CoreFoundation
}
