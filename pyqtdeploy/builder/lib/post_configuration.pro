linux-* {
    LIBS += -lutil -ldl
}

win32 {
    LIBS += -ladvapi32 -lshell32 -luser32

    # This is added from the qmake spec files but clashes with _pickle.c.
    DEFINES -= UNICODE
}

macx {
    LIBS += -framework SystemConfiguration -framework CoreFoundation
}
