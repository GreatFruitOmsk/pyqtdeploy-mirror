linux-* {
    LIBS += -lutil -ldl
}

win32 {
    LIBS += -ladvapi32 -lshell32 -luser32
}
