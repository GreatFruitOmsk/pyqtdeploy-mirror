win32 {
    ASM = $$find(SOURCES, ^.*\.asm$)
    SOURCES -= $$ASM

    masm.input = ASM
    masm.output = ${QMAKE_FILE_BASE}.obj

    contains(QMAKE_TARGET.arch, x86_64) {
        CONFIG += win32_x64
        masm.name = MASM64 compiler
        masm.commands = ml64 /Fo ${QMAKE_FILE_OUT} /c ${QMAKE_FILE_IN}
    } else {
        CONFIG += win32_x86
        masm.name = MASM compiler
        masm.commands = ml /Fo ${QMAKE_FILE_OUT} /c ${QMAKE_FILE_IN}
    }

    QMAKE_EXTRA_COMPILERS += masm
}
