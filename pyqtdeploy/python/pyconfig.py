# Copyright (c) 2014, Riverbank Computing Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from ..file_utilities import create_file


class Config:
    """ Encapsulate a configuration value defined in pyconfig.h. """

    def __init__(self, name, default=None, **targets):
        """ Define the value allowing target-specific overrides. """

        self.name = name
        self._default = default
        self._targets = targets

    def value(self, target):
        """ Get the value for a target. """

        # Convert the target to a valid Python name.
        target = target.replace('-', '_')

        # Try the specific target variant.
        try:
            return self._targets[target]
        except KeyError:
            pass

        # Try the main target if there was a variant.
        target_parts = target.split('_', maxsplit=1)

        if len(target_parts) != 1:
            try:
                return self._targets[target_parts[0]]
            except KeyError:
                pass

        # Return the default.
        return self._default


# The configuration values for all supported versions of Python.
pyconfig = (
    # Define if C doubles are 64-bit IEEE 754 binary format, stored in ARM
    # mixed-endian order (byte order 45670123)
    Config('DOUBLE_IS_ARM_MIXED_ENDIAN_IEEE754'),

    # Define if C doubles are 64-bit IEEE 754 binary format, stored with the
    # most significant byte first
    Config('DOUBLE_IS_BIG_ENDIAN_IEEE754'),

    # Define if C doubles are 64-bit IEEE 754 binary format, stored with the
    # least significant byte first
    Config('DOUBLE_IS_LITTLE_ENDIAN_IEEE754', ios=1, linux=1, osx=1),

    # Define if --enable-ipv6 is specified
    Config('ENABLE_IPV6', ios=1, linux=1, osx=1),

    # Define if getpgrp() must be called as getpgrp(0).
    Config('GETPGRP_HAVE_ARG'),

    # Define if gettimeofday() does not have second (timezone) argument
    Config('GETTIMEOFDAY_NO_TZ'),

    # Define to 1 if you have the `accept4' function.
    Config('HAVE_ACCEPT4', linux=1),

    # Define to 1 if you have the `acosh' function.
    Config('HAVE_ACOSH', ios=1, linux=1, osx=1),

    # struct addrinfo (netdb.h)
    Config('HAVE_ADDRINFO', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `alarm' function.
    Config('HAVE_ALARM', ios=1, linux=1, osx=1),

    # Define if aligned memory access is required
    Config('HAVE_ALIGNED_REQUIRED'),

    # Define to 1 if you have the <alloca.h> header file.
    Config('HAVE_ALLOCA_H', ios=1, linux=1, osx=1),

    # Define this if your time.h defines altzone.
    Config('HAVE_ALTZONE'),

    # Define to 1 if you have the `asinh' function.
    Config('HAVE_ASINH', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <asm/types.h> header file.
    Config('HAVE_ASM_TYPES_H', linux=1),

    # Define to 1 if you have the `atanh' function.
    Config('HAVE_ATANH', ios=1, linux=1, osx=1),

    # Define if GCC supports __attribute__((format(PyArg_ParseTuple, 2, 3)))
    Config('HAVE_ATTRIBUTE_FORMAT_PARSETUPLE'),

    # Define to 1 if you have the `bind_textdomain_codeset' function.
    Config('HAVE_BIND_TEXTDOMAIN_CODESET', linux=1),

    # Define to 1 if you have the <bluetooth/bluetooth.h> header file.
    Config('HAVE_BLUETOOTH_BLUETOOTH_H'),

    # Define to 1 if you have the <bluetooth.h> header file.
    Config('HAVE_BLUETOOTH_H'),

    # Define if mbstowcs(NULL, "text", 0) does not return the number of wide
    # chars that would be converted.
    Config('HAVE_BROKEN_MBSTOWCS'),

    # Define if nice() returns success/failure instead of the new priority.
    Config('HAVE_BROKEN_NICE'),

    # Define if the system reports an invalid PIPE_BUF value.
    Config('HAVE_BROKEN_PIPE_BUF'),

    # Define if poll() sets errno on invalid file descriptors.
    Config('HAVE_BROKEN_POLL'),

    # Define if the Posix semaphores do not work on your system
    Config('HAVE_BROKEN_POSIX_SEMAPHORES'),

    # Define if pthread_sigmask() does not work on your system.
    Config('HAVE_BROKEN_PTHREAD_SIGMASK'),

    # Define to 1 if your sem_getvalue is broken.
    Config('HAVE_BROKEN_SEM_GETVALUE', ios=1, osx=1),

    # Define if `unsetenv` does not return an int.
    Config('HAVE_BROKEN_UNSETENV'),

    # Define this if you have the type _Bool.
    Config('HAVE_C99_BOOL', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `chflags' function.
    Config('HAVE_CHFLAGS', ios=1, osx=1),

    # Define to 1 if you have the `chown' function.
    Config('HAVE_CHOWN', ios=1, linux=1, osx=1),

    # Define if you have the 'chroot' function.
    Config('HAVE_CHROOT', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `clock' function.
    Config('HAVE_CLOCK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `clock_getres' function.
    Config('HAVE_CLOCK_GETRES', linux=1),

    # Define to 1 if you have the `clock_gettime' function.
    Config('HAVE_CLOCK_GETTIME', linux=1),

    # Define if the C compiler supports computed gotos.
    Config('HAVE_COMPUTED_GOTOS', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `confstr' function.
    Config('HAVE_CONFSTR', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <conio.h> header file.
    Config('HAVE_CONIO_H'),

    # Define to 1 if you have the `copysign' function.
    Config('HAVE_COPYSIGN', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `ctermid' function.
    Config('HAVE_CTERMID', ios=1, linux=1, osx=1),

    # Define if you have the 'ctermid_r' function.
    Config('HAVE_CTERMID_R', ios=1, osx=1),

    # Define to 1 if you have the <curses.h> header file.
    Config('HAVE_CURSES_H', ios=1, linux=1, osx=1),

    # Define if you have the 'is_term_resized' function.
    Config('HAVE_CURSES_IS_TERM_RESIZED', ios=1, linux=1, osx=1),

    # Define if you have the 'resizeterm' function.
    Config('HAVE_CURSES_RESIZETERM', ios=1, linux=1, osx=1),

    # Define if you have the 'resize_term' function.
    Config('HAVE_CURSES_RESIZE_TERM', ios=1, linux=1, osx=1),

    # Define to 1 if you have the declaration of `isfinite'.
    Config('HAVE_DECL_ISFINITE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the declaration of `isinf'.
    Config('HAVE_DECL_ISINF', ios=1, linux=1, osx=1),
    Config('HAVE_ISINF', ios=1, linux=1, osx=1),

    # Define to 1 if you have the declaration of `isnan'.
    Config('HAVE_DECL_ISNAN', ios=1, linux=1, osx=1),
    Config('HAVE_ISNAN', ios=1, linux=1, osx=1),

    # Define to 1 if you have the declaration of `tzname'.
    Config('HAVE_DECL_TZNAME'),

    # Define to 1 if you have the device macros.
    Config('HAVE_DEVICE_MACROS', ios=1, linux=1, osx=1),

    # Define to 1 if you have the /dev/ptc device file.
    Config('HAVE_DEV_PTC'),

    # Define to 1 if you have the /dev/ptmx device file.
    Config('HAVE_DEV_PTMX', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <direct.h> header file.
    Config('HAVE_DIRECT_H'),

    # Define to 1 if you have the <dirent.h> header file, and it defines `DIR'.
    Config('HAVE_DIRENT_H', ios=1, linux=1, osx=1),

    # Define if you have the 'dirfd' function or macro.
    Config('HAVE_DIRFD', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <dlfcn.h> header file.
    Config('HAVE_DLFCN_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `dlopen' function.
    Config('HAVE_DLOPEN', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `dup2' function.
    Config('HAVE_DUP2', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `dup3' function.
    Config('HAVE_DUP3', linux=1),

    # Define to 1 if you have the <endian.h> header file.
    Config('HAVE_ENDIAN_H', linux=1),

    # Define if you have the 'epoll' functions.
    Config('HAVE_EPOLL', linux=1),

    # Define if you have the 'epoll_create1' function.
    Config('HAVE_EPOLL_CREATE1', linux=1),

    # Define to 1 if you have the `erf' function.
    Config('HAVE_ERF', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `erfc' function.
    Config('HAVE_ERFC', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <errno.h> header file.
    Config('HAVE_ERRNO_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `execv' function.
    Config('HAVE_EXECV', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `expm1' function.
    Config('HAVE_EXPM1', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `faccessat' function.
    Config('HAVE_FACCESSAT', linux=1),

    # Define if you have the 'fchdir' function.
    Config('HAVE_FCHDIR', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `fchmod' function.
    Config('HAVE_FCHMOD', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `fchmodat' function.
    Config('HAVE_FCHMODAT', linux=1),

    # Define to 1 if you have the `fchown' function.
    Config('HAVE_FCHOWN', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `fchownat' function.
    Config('HAVE_FCHOWNAT', linux=1),

    # Define to 1 if you have the <fcntl.h> header file.
    Config('HAVE_FCNTL_H', ios=1, linux=1, osx=1),

    # Define if you have the 'fdatasync' function.
    Config('HAVE_FDATASYNC', linux=1),

    # Define to 1 if you have the `fdopendir' function.
    Config('HAVE_FDOPENDIR', linux=1),

    # Define to 1 if you have the `fexecve' function.
    Config('HAVE_FEXECVE', linux=1),

    # Define to 1 if you have the `finite' function.
    Config('HAVE_FINITE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the 'flock' function.
    Config('HAVE_FLOCK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `fork' function.
    Config('HAVE_FORK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `forkpty' function.
    Config('HAVE_FORKPTY', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `fpathconf' function.
    Config('HAVE_FPATHCONF', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `fseek64' function.
    Config('HAVE_FSEEK64'),

    # Define to 1 if you have the `fseeko' function.
    Config('HAVE_FSEEKO', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `fstatat' function.
    Config('HAVE_FSTATAT', linux=1),

    # Define to 1 if you have the `fstatvfs' function.
    Config('HAVE_FSTATVFS', ios=1, linux=1, osx=1),

    # Define if you have the 'fsync' function.
    Config('HAVE_FSYNC', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `ftell64' function.
    Config('HAVE_FTELL64'),

    # Define to 1 if you have the `ftello' function.
    Config('HAVE_FTELLO', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `ftime' function.
    Config('HAVE_FTIME', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `ftruncate' function.
    Config('HAVE_FTRUNCATE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `futimens' function.
    Config('HAVE_FUTIMENS', linux=1),

    # Define to 1 if you have the `futimes' function.
    Config('HAVE_FUTIMES', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `futimesat' function.
    Config('HAVE_FUTIMESAT', linux=1),

    # Define to 1 if you have the `gai_strerror' function.
    Config('HAVE_GAI_STRERROR', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `gamma' function.
    Config('HAVE_GAMMA', ios=1, linux=1, osx=1),

    # Define if we can use x64 gcc inline assembler
    Config('HAVE_GCC_ASM_FOR_X64', ios_64=1, linux_64=1, osx_64=1),

    # Define if we can use gcc inline assembler to get and set x87 control word
    Config('HAVE_GCC_ASM_FOR_X87', ios=1, linux=1, osx=1),

    # Define if your compiler provides __uint128_t
    Config('HAVE_GCC_UINT128_T', ios_64=1, linux_64, osx_64=1),

    # Define if you have the getaddrinfo function.
    Config('HAVE_GETADDRINFO', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getcwd' function.
    Config('HAVE_GETCWD', ios=1, linux=1, osx=1),

    # Define this if you have flockfile(), getc_unlocked(), and funlockfile()
    Config('HAVE_GETC_UNLOCKED', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getgrouplist' function.
    Config('HAVE_GETGROUPLIST', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getgroups' function.
    Config('HAVE_GETGROUPS', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `gethostbyname' function.
    Config('HAVE_GETHOSTBYNAME', ios=1, osx=1),

    # Define this if you have some version of gethostbyname_r()
    Config('HAVE_GETHOSTBYNAME_R', linux=1),

    # Define this if you have the 3-arg version of gethostbyname_r().
    Config('HAVE_GETHOSTBYNAME_R_3_ARG'),

    # Define this if you have the 5-arg version of gethostbyname_r().
    Config('HAVE_GETHOSTBYNAME_R_5_ARG'),

    # Define this if you have the 6-arg version of gethostbyname_r().
    Config('HAVE_GETHOSTBYNAME_R_6_ARG', linux=1),

    # Define to 1 if you have the `getitimer' function.
    Config('HAVE_GETITIMER', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getloadavg' function.
    Config('HAVE_GETLOADAVG', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getlogin' function.
    Config('HAVE_GETLOGIN', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getnameinfo' function.
    Config('HAVE_GETNAMEINFO', ios=1, linux=1, osx=1),

    # Define if you have the 'getpagesize' function.
    Config('HAVE_GETPAGESIZE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getpeername' function.
    Config('HAVE_GETPEERNAME', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getpgid' function.
    Config('HAVE_GETPGID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getpgrp' function.
    Config('HAVE_GETPGRP', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getpid' function.
    Config('HAVE_GETPID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getpriority' function.
    Config('HAVE_GETPRIORITY', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getpwent' function.
    Config('HAVE_GETPWENT', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getresgid' function.
    Config('HAVE_GETRESGID', linux=1),

    # Define to 1 if you have the `getresuid' function.
    Config('HAVE_GETRESUID', linux=1),

    # Define to 1 if you have the `getsid' function.
    Config('HAVE_GETSID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getspent' function.
    Config('HAVE_GETSPENT', linux=1),

    # Define to 1 if you have the `getspnam' function.
    Config('HAVE_GETSPNAM', linux=1),

    # Define to 1 if you have the `gettimeofday' function.
    Config('HAVE_GETTIMEOFDAY', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `getwd' function.
    Config('HAVE_GETWD', ios=1, linux=1, osx=1),

    # Define if glibc has incorrect _FORTIFY_SOURCE wrappers for memmove and
    # bcopy.
    Config('HAVE_GLIBC_MEMMOVE_BUG'),

    # Define to 1 if you have the <grp.h> header file.
    Config('HAVE_GRP_H', ios=1, linux=1, osx=1),

    # Define if you have the 'hstrerror' function.
    Config('HAVE_HSTRERROR', ios=1, linux=1, osx=1),

    # Define this if you have le64toh()
    Config('HAVE_HTOLE64', linux=1),

    # Define to 1 if you have the `hypot' function.
    Config('HAVE_HYPOT', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <ieeefp.h> header file.
    Config('HAVE_IEEEFP_H'),

    # Define to 1 if you have the `if_nameindex' function.
    Config('HAVE_IF_NAMEINDEX', ios=1, linux=1, osx=1),

    # Define if you have the 'inet_aton' function.
    Config('HAVE_INET_ATON', ios=1, linux=1, osx=1),

    # Define if you have the 'inet_pton' function.
    Config('HAVE_INET_PTON', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `initgroups' function.
    Config('HAVE_INITGROUPS', ios=1, linux=1, osx=1),

    # Define if your compiler provides int32_t.
    Config('HAVE_INT32_T', ios=1, linux=1, osx=1),

    # Define if your compiler provides int64_t.
    Config('HAVE_INT64_T', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <inttypes.h> header file.
    Config('HAVE_INTTYPES_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <io.h> header file.
    Config('HAVE_IO_H'),

    # Define if gcc has the ipa-pure-const bug.
    Config('HAVE_IPA_PURE_CONST_BUG'),

    # Define to 1 if you have the `kill' function.
    Config('HAVE_KILL', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `killpg' function.
    Config('HAVE_KILLPG', ios=1, linux=1, osx=1),

    # Define if you have the 'kqueue' functions.
    Config('HAVE_KQUEUE', ios=1, osx=1),

    # Define to 1 if you have the <langinfo.h> header file.
    Config('HAVE_LANGINFO_H', ios=1, linux=1, osx=1),

    # Defined to enable large file support when an off_t is bigger than a long
    # and long long is available and at least as big as an off_t. You may need
    # to add some flags for configuration and compilation to enable this mode.
    # (For Solaris and Linux, the necessary defines are already defined.),
    Config('HAVE_LARGEFILE_SUPPORT', linux_32=1),

    # Define to 1 if you have the `lchflags' function.
    Config('HAVE_LCHFLAGS', ios=1, osx=1),

    # Define to 1 if you have the `lchmod' function.
    Config('HAVE_LCHMOD', ios=1, osx=1),

    # Define to 1 if you have the `lchown' function.
    Config('HAVE_LCHOWN', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `lgamma' function.
    Config('HAVE_LGAMMA', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `dl' library (-ldl).
    Config('HAVE_LIBDL', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `dld' library (-ldld).
    Config('HAVE_LIBDLD'),

    # Define to 1 if you have the `ieee' library (-lieee).
    Config('HAVE_LIBIEEE'),

    # Define to 1 if you have the <libintl.h> header file.
    Config('HAVE_LIBINTL_H', linux=1),

    # Define if you have the `readline' library (-lreadline).
    Config('HAVE_LIBREADLINE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `resolv' library (-lresolv).
    Config('HAVE_LIBRESOLV'),

    # Define to 1 if you have the `sendfile' library (-lsendfile).
    Config('HAVE_LIBSENDFILE'),

    # Define to 1 if you have the <libutil.h> header file.
    Config('HAVE_LIBUTIL_H'),

    # Define if you have the 'link' function.
    Config('HAVE_LINK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `linkat' function.
    Config('HAVE_LINKAT', linux=1),

    # Define to 1 if you have the <linux/can/bcm.h> header file.
    Config('HAVE_LINUX_CAN_BCM_H', linux=1),

    # Define to 1 if you have the <linux/can.h> header file.
    Config('HAVE_LINUX_CAN_H', linux=1),

    # Define to 1 if you have the <linux/can/raw.h> header file.
    Config('HAVE_LINUX_CAN_RAW_H', linux=1),

    # Define to 1 if you have the <linux/netlink.h> header file.
    Config('HAVE_LINUX_NETLINK_H', linux=1),

    # Define to 1 if you have the <linux/tipc.h> header file.
    Config('HAVE_LINUX_TIPC_H', linux=1),

    # Define to 1 if you have the `lockf' function.
    Config('HAVE_LOCKF', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `log1p' function.
    Config('HAVE_LOG1P', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `log2' function.
    Config('HAVE_LOG2', ios=1, linux=1, osx=1),

    # Define this if you have the type long double.
    Config('HAVE_LONG_DOUBLE', ios=1, linux=1, osx=1),

    # Define this if you have the type long long.
    Config('HAVE_LONG_LONG', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `lstat' function.
    Config('HAVE_LSTAT', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `lutimes' function.
    Config('HAVE_LUTIMES', ios=1, linux=1, osx=1),

    # Define this if you have the makedev macro.
    Config('HAVE_MAKEDEV', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `mbrtowc' function.
    Config('HAVE_MBRTOWC', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `memmove' function.
    Config('HAVE_MEMMOVE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <memory.h> header file.
    Config('HAVE_MEMORY_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `memrchr' function.
    Config('HAVE_MEMRCHR', linux=1),

    # Define to 1 if you have the `mkdirat' function.
    Config('HAVE_MKDIRAT', linux=1),

    # Define to 1 if you have the `mkfifo' function.
    Config('HAVE_MKFIFO', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `mkfifoat' function.
    Config('HAVE_MKFIFOAT', linux=1),

    # Define to 1 if you have the `mknod' function.
    Config('HAVE_MKNOD', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `mknodat' function.
    Config('HAVE_MKNODAT', linux=1),

    # Define to 1 if you have the `mktime' function.
    Config('HAVE_MKTIME', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `mmap' function.
    Config('HAVE_MMAP', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `mremap' function.
    Config('HAVE_MREMAP', linux=1),

    # Define to 1 if you have the <ncurses.h> header file.
    Config('HAVE_NCURSES_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <ndir.h> header file, and it defines `DIR'.
    Config('HAVE_NDIR_H'),

    # Define to 1 if you have the <netpacket/packet.h> header file.
    Config('HAVE_NETPACKET_PACKET_H', linux=1),

    # Define to 1 if you have the <net/if.h> header file.
    Config('HAVE_NET_IF_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `nice' function.
    Config('HAVE_NICE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `openat' function.
    Config('HAVE_OPENAT', linux=1),

    # Define to 1 if you have the `openpty' function.
    Config('HAVE_OPENPTY', ios=1, linux=1, osx=1),

    # Define if compiling using MacOS X 10.5 SDK or later.
    Config('HAVE_OSX105_SDK', ios=1, osx=1),

    # Define to 1 if you have the `pathconf' function.
    Config('HAVE_PATHCONF', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `pause' function.
    Config('HAVE_PAUSE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `pipe2' function.
    Config('HAVE_PIPE2', linux=1),

    # Define to 1 if you have the `plock' function.
    Config('HAVE_PLOCK'),

    # Define to 1 if you have the `poll' function.
    Config('HAVE_POLL', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <poll.h> header file.
    Config('HAVE_POLL_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `posix_fadvise' function.
    Config('HAVE_POSIX_FADVISE', linux=1),

    # Define to 1 if you have the `posix_fallocate' function.
    Config('HAVE_POSIX_FALLOCATE', linux=1),

    # Define to 1 if you have the `pread' function.
    Config('HAVE_PREAD', ios=1, linux=1, osx=1),

    # Define if you have the 'prlimit' functions.
    Config('HAVE_PRLIMIT', linux=1),

    # Define to 1 if you have the <process.h> header file.
    Config('HAVE_PROCESS_H'),

    # Define if your compiler supports function prototype
    Config('HAVE_PROTOTYPES', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `pthread_atfork' function.
    Config('HAVE_PTHREAD_ATFORK', ios=1, linux=1, osx=1),

    # Defined for Solaris 2.6 bug in pthread header.
    Config('HAVE_PTHREAD_DESTRUCTOR'),

    # Define to 1 if you have the <pthread.h> header file.
    Config('HAVE_PTHREAD_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `pthread_init' function.
    Config('HAVE_PTHREAD_INIT'),

    # Define to 1 if you have the `pthread_kill' function.
    Config('HAVE_PTHREAD_KILL', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `pthread_sigmask' function.
    Config('HAVE_PTHREAD_SIGMASK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <pty.h> header file.
    Config('HAVE_PTY_H', linux=1),

    # Define to 1 if you have the `putenv' function.
    Config('HAVE_PUTENV', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `pwrite' function.
    Config('HAVE_PWRITE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `readlink' function.
    Config('HAVE_READLINK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `readlinkat' function.
    Config('HAVE_READLINKAT', linux=1),

    # Define to 1 if you have the `readv' function.
    Config('HAVE_READV', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `realpath' function.
    Config('HAVE_REALPATH', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `renameat' function.
    Config('HAVE_RENAMEAT', linux=1),

    # Define if you have readline 2.1
    Config('HAVE_RL_CALLBACK', ios=1, linux=1, osx=1),

    # Define if you can turn off readline's signal handling.
    Config('HAVE_RL_CATCH_SIGNAL', linux=1),

    # Define if you have readline 2.2
    Config('HAVE_RL_COMPLETION_APPEND_CHARACTER', ios=1, linux=1, osx=1),

    # Define if you have readline 4.0
    Config('HAVE_RL_COMPLETION_DISPLAY_MATCHES_HOOK', ios=1, linux=1, osx=1),

    # Define if you have readline 4.2
    Config('HAVE_RL_COMPLETION_MATCHES', ios=1, linux=1, osx=1),

    # Define if you have rl_completion_suppress_append
    Config('HAVE_RL_COMPLETION_SUPPRESS_APPEND', linux=1),

    # Define if you have readline 4.0
    Config('HAVE_RL_PRE_INPUT_HOOK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `round' function.
    Config('HAVE_ROUND', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sched_get_priority_max' function.
    Config('HAVE_SCHED_GET_PRIORITY_MAX', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sched.h> header file.
    Config('HAVE_SCHED_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sched_rr_get_interval' function.
    Config('HAVE_SCHED_RR_GET_INTERVAL', linux=1),

    # Define to 1 if you have the `sched_setaffinity' function.
    Config('HAVE_SCHED_SETAFFINITY', linux=1),

    # Define to 1 if you have the `sched_setparam' function.
    Config('HAVE_SCHED_SETPARAM', linux=1),

    # Define to 1 if you have the `sched_setscheduler' function.
    Config('HAVE_SCHED_SETSCHEDULER', linux=1),

    # Define to 1 if you have the `select' function.
    Config('HAVE_SELECT', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sem_getvalue' function.
    Config('HAVE_SEM_GETVALUE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sem_open' function.
    Config('HAVE_SEM_OPEN', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sem_timedwait' function.
    Config('HAVE_SEM_TIMEDWAIT', linux=1),

    # Define to 1 if you have the `sem_unlink' function.
    Config('HAVE_SEM_UNLINK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sendfile' function.
    Config('HAVE_SENDFILE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setegid' function.
    Config('HAVE_SETEGID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `seteuid' function.
    Config('HAVE_SETEUID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setgid' function.
    Config('HAVE_SETGID', ios=1, linux=1, osx=1),

    # Define if you have the 'setgroups' function.
    Config('HAVE_SETGROUPS', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sethostname' function.
    Config('HAVE_SETHOSTNAME', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setitimer' function.
    Config('HAVE_SETITIMER', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setlocale' function.
    Config('HAVE_SETLOCALE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setpgid' function.
    Config('HAVE_SETPGID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setpgrp' function.
    Config('HAVE_SETPGRP', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setpriority' function.
    Config('HAVE_SETPRIORITY', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setregid' function.
    Config('HAVE_SETREGID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setresgid' function.
    Config('HAVE_SETRESGID', linux=1),

    # Define to 1 if you have the `setresuid' function.
    Config('HAVE_SETRESUID', linux=1),

    # Define to 1 if you have the `setreuid' function.
    Config('HAVE_SETREUID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setsid' function.
    Config('HAVE_SETSID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setuid' function.
    Config('HAVE_SETUID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `setvbuf' function.
    Config('HAVE_SETVBUF', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <shadow.h> header file.
    Config('HAVE_SHADOW_H', linux=1),

    # Define to 1 if you have the `sigaction' function.
    Config('HAVE_SIGACTION', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sigaltstack' function.
    Config('HAVE_SIGALTSTACK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `siginterrupt' function.
    Config('HAVE_SIGINTERRUPT', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <signal.h> header file.
    Config('HAVE_SIGNAL_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sigpending' function.
    Config('HAVE_SIGPENDING', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sigrelse' function.
    Config('HAVE_SIGRELSE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sigtimedwait' function.
    Config('HAVE_SIGTIMEDWAIT', linux=1),

    # Define to 1 if you have the `sigwait' function.
    Config('HAVE_SIGWAIT', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sigwaitinfo' function.
    Config('HAVE_SIGWAITINFO', linux=1),

    # Define to 1 if you have the `snprintf' function.
    Config('HAVE_SNPRINTF', ios=1, linux=1, osx=1),

    # Define if sockaddr has sa_len member
    Config('HAVE_SOCKADDR_SA_LEN', ios=1, osx=1),

    # struct sockaddr_storage (sys/socket.h),
    Config('HAVE_SOCKADDR_STORAGE', ios=1, linux=1, osx=1),

    # Define if you have the 'socketpair' function.
    Config('HAVE_SOCKETPAIR', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <spawn.h> header file.
    Config('HAVE_SPAWN_H', ios=1, linux=1, osx=1),

    # Define if your compiler provides ssize_t
    Config('HAVE_SSIZE_T', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `statvfs' function.
    Config('HAVE_STATVFS', ios=1, linux=1, osx=1),

    # Define if you have struct stat.st_mtim.tv_nsec
    Config('HAVE_STAT_TV_NSEC', linux=1),

    # Define if you have struct stat.st_mtimensec
    Config('HAVE_STAT_TV_NSEC2', ios=1, osx=1),

    # Define if your compiler supports variable length function prototypes
    # (e.g.  void fprintf(FILE *, char *, ...);) *and* <stdarg.h>
    Config('HAVE_STDARG_PROTOTYPES', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <stdint.h> header file.
    Config('HAVE_STDINT_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <stdlib.h> header file.
    Config('HAVE_STDLIB_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `strdup' function.
    Config('HAVE_STRDUP', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `strftime' function.
    Config('HAVE_STRFTIME', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <strings.h> header file.
    Config('HAVE_STRINGS_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <string.h> header file.
    Config('HAVE_STRING_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `strlcpy' function.
    Config('HAVE_STRLCPY', ios=1, osx=1),

    # Define to 1 if you have the <stropts.h> header file.
    Config('HAVE_STROPTS_H', linux=1),

    # Define to 1 if `st_birthtime' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_BIRTHTIME', ios=1, osx=1),

    # Define to 1 if `st_blksize' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_BLKSIZE', ios=1, linux=1, osx=1),

    # Define to 1 if `st_blocks' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_BLOCKS', ios=1, linux=1, osx=1),

    # Define to 1 if `st_flags' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_FLAGS', ios=1, osx=1),

    # Define to 1 if `st_gen' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_GEN', ios=1, osx=1),

    # Define to 1 if `st_rdev' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_RDEV', ios=1, linux=1, osx=1),

    # Define to 1 if `tm_zone' is a member of `struct tm'.
    Config('HAVE_STRUCT_TM_TM_ZONE', ios=1, linux=1, osx=1),

    # Define if you have the 'symlink' function.
    Config('HAVE_SYMLINK', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `symlinkat' function.
    Config('HAVE_SYMLINKAT', linux=1),

    # Define to 1 if you have the `sync' function.
    Config('HAVE_SYNC', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `sysconf' function.
    Config('HAVE_SYSCONF', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sysexits.h> header file.
    Config('HAVE_SYSEXITS_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/audioio.h> header file.
    Config('HAVE_SYS_AUDIOIO_H'),

    # Define to 1 if you have the <sys/bsdtty.h> header file.
    Config('HAVE_SYS_BSDTTY_H'),

    # Define to 1 if you have the <sys/devpoll.h> header file.
    Config('HAVE_SYS_DEVPOLL_H'),

    # Define to 1 if you have the <sys/dir.h> header file, and it defines
    # `DIR'.
    Config('HAVE_SYS_DIR_H'),

    # Define to 1 if you have the <sys/endian.h> header file.
    Config('HAVE_SYS_ENDIAN_H'),

    # Define to 1 if you have the <sys/epoll.h> header file.
    Config('HAVE_SYS_EPOLL_H', linux=1),

    # Define to 1 if you have the <sys/event.h> header file.
    Config('HAVE_SYS_EVENT_H', ios=1, osx=1),

    # Define to 1 if you have the <sys/file.h> header file.
    Config('HAVE_SYS_FILE_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/ioctl.h> header file.
    Config('HAVE_SYS_IOCTL_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/kern_control.h> header file.
    Config('HAVE_SYS_KERN_CONTROL_H', ios=1, osx=1),

    # Define to 1 if you have the <sys/loadavg.h> header file.
    Config('HAVE_SYS_LOADAVG_H'),

    # Define to 1 if you have the <sys/lock.h> header file.
    Config('HAVE_SYS_LOCK_H', ios=1, osx=1),

    # Define to 1 if you have the <sys/mkdev.h> header file.
    Config('HAVE_SYS_MKDEV_H'),

    # Define to 1 if you have the <sys/modem.h> header file.
    Config('HAVE_SYS_MODEM_H'),

    # Define to 1 if you have the <sys/ndir.h> header file, and it defines
    # `DIR'.
    Config('HAVE_SYS_NDIR_H'),

    # Define to 1 if you have the <sys/param.h> header file.
    Config('HAVE_SYS_PARAM_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/poll.h> header file.
    Config('HAVE_SYS_POLL_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/resource.h> header file.
    Config('HAVE_SYS_RESOURCE_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/select.h> header file.
    Config('HAVE_SYS_SELECT_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/sendfile.h> header file.
    Config('HAVE_SYS_SENDFILE_H', linux=1),

    # Define to 1 if you have the <sys/socket.h> header file.
    Config('HAVE_SYS_SOCKET_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/statvfs.h> header file.
    Config('HAVE_SYS_STATVFS_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/stat.h> header file.
    Config('HAVE_SYS_STAT_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/syscall.h> header file.
    Config('HAVE_SYS_SYSCALL_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/sys_domain.h> header file.
    Config('HAVE_SYS_SYS_DOMAIN_H', ios=1, osx=1),

    # Define to 1 if you have the <sys/termio.h> header file.
    Config('HAVE_SYS_TERMIO_H'),

    # Define to 1 if you have the <sys/times.h> header file.
    Config('HAVE_SYS_TIMES_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/time.h> header file.
    Config('HAVE_SYS_TIME_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/types.h> header file.
    Config('HAVE_SYS_TYPES_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/uio.h> header file.
    Config('HAVE_SYS_UIO_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/un.h> header file.
    Config('HAVE_SYS_UN_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/utsname.h> header file.
    Config('HAVE_SYS_UTSNAME_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/wait.h> header file.
    Config('HAVE_SYS_WAIT_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <sys/xattr.h> header file.
    Config('HAVE_SYS_XATTR_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `tcgetpgrp' function.
    Config('HAVE_TCGETPGRP', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `tcsetpgrp' function.
    Config('HAVE_TCSETPGRP', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `tempnam' function.
    Config('HAVE_TEMPNAM', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <termios.h> header file.
    Config('HAVE_TERMIOS_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <term.h> header file.
    Config('HAVE_TERM_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `tgamma' function.
    Config('HAVE_TGAMMA', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <thread.h> header file.
    Config('HAVE_THREAD_H'),

    # Define to 1 if you have the `timegm' function.
    Config('HAVE_TIMEGM', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `times' function.
    Config('HAVE_TIMES', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `tmpfile' function.
    Config('HAVE_TMPFILE', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `tmpnam' function.
    Config('HAVE_TMPNAM', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `tmpnam_r' function.
    Config('HAVE_TMPNAM_R', linux=1),

    # Define to 1 if you have the `truncate' function.
    Config('HAVE_TRUNCATE', ios=1, linux=1, osx=1),

    # Define to 1 if you don't have `tm_zone' but do have the external array
    # `tzname'.
    Config('HAVE_TZNAME'),

    # Define if your compiler provides uint32_t.
    Config('HAVE_UINT32_T', ios=1, linux=1, osx=1),

    # Define if your compiler provides uint64_t.
    Config('HAVE_UINT64_T', ios=1, linux=1, osx=1),

    # Define to 1 if the system has the type `uintptr_t'.
    Config('HAVE_UINTPTR_T', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `uname' function.
    Config('HAVE_UNAME', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <unistd.h> header file.
    Config('HAVE_UNISTD_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `unlinkat' function.
    Config('HAVE_UNLINKAT', linux=1),

    # Define to 1 if you have the `unsetenv' function.
    Config('HAVE_UNSETENV', ios=1, linux=1, osx=1),

    # Define if you have a useable wchar_t type defined in wchar.h; useable
    # means wchar_t must be an unsigned type with at least 16 bits. (see
    # Include/unicodeobject.h).
    Config('HAVE_USABLE_WCHAR_T'),

    # Define to 1 if you have the <util.h> header file.
    Config('HAVE_UTIL_H', ios=1, osx=1),

    # Define to 1 if you have the `utimensat' function.
    Config('HAVE_UTIMENSAT', linux=1),

    # Define to 1 if you have the `utimes' function.
    Config('HAVE_UTIMES', ios=1, linux=1, osx=1),

    # Define to 1 if you have the <utime.h> header file.
    Config('HAVE_UTIME_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `wait3' function.
    Config('HAVE_WAIT3', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `wait4' function.
    Config('HAVE_WAIT4', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `waitid' function.
    Config('HAVE_WAITID', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `waitpid' function.
    Config('HAVE_WAITPID', ios=1, linux=1, osx=1),

    # Define if the compiler provides a wchar.h header file.
    Config('HAVE_WCHAR_H', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `wcscoll' function.
    Config('HAVE_WCSCOLL', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `wcsftime' function.
    Config('HAVE_WCSFTIME', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `wcsxfrm' function.
    Config('HAVE_WCSXFRM', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `wmemcmp' function.
    Config('HAVE_WMEMCMP', ios=1, linux=1, osx=1),

    # Define if tzset() actually switches the local timezone in a meaningful
    # way.
    Config('HAVE_WORKING_TZSET', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `writev' function.
    Config('HAVE_WRITEV', ios=1, linux=1, osx=1),

    # Define if the zlib library has inflateCopy
    Config('HAVE_ZLIB_COPY', ios=1, linux=1, osx=1),

    # Define to 1 if you have the `_getpty' function.
    Config('HAVE__GETPTY'),

    # Define if log1p(-0.) is 0. rather than -0.
    Config('LOG1P_DROPS_ZERO_SIGN'),

    # Define to 1 if `major', `minor', and `makedev' are declared in <mkdev.h>.
    Config('MAJOR_IN_MKDEV'),

    # Define to 1 if `major', `minor', and `makedev' are declared in
    # <sysmacros.h>.
    Config('MAJOR_IN_SYSMACROS'),

    # Define if mvwdelch in curses.h is an expression.
    Config('MVWDELCH_IS_EXPRESSION', ios=1, linux=1, osx=1),

    # Define if POSIX semaphores aren't enabled on your system
    Config('POSIX_SEMAPHORES_NOT_ENABLED'),

    # Defined if PTHREAD_SCOPE_SYSTEM supported.
    Config('PTHREAD_SYSTEM_SCHED_SUPPORTED', ios=1, linux=1, osx=1),

    # Define as the preferred size in bits of long digits
    Config('PYLONG_BITS_IN_DIGIT'),

    # Define to printf format modifier for long long type
    Config('PY_FORMAT_LONG_LONG', ios='"ll"', linux='"ll"', osx='"ll"'),

    # Define to printf format modifier for Py_ssize_t
    Config('PY_FORMAT_SIZE_T', ios='"z"', linux='"z"', osx='"z"'),

    # Define as the integral type used for Unicode representation.
    Config('PY_UNICODE_TYPE', ios='unsigned short', linux='unsigned short', osx='unsigned short'),

    # Define if you want to build an interpreter with many run-time checks.
    Config('Py_DEBUG'),

    # Define hash algorithm for str, bytes and memoryview. SipHash24: 1,
    # FNV: 2, externally defined: 0
    Config('Py_HASH_ALGORITHM'),

    # Define as the size of the unicode type.
    Config('Py_UNICODE_SIZE', ios=2, linux=2, osx=2),

    # Define if you want to have a Unicode type.
    Config('Py_USING_UNICODE', default=1),

    # Define if setpgrp() must be called as setpgrp(0, 0).
    Config('SETPGRP_HAVE_ARG'),

    # Define if i>>j for signed int i does not extend the sign bit when i < 0
    Config('SIGNED_RIGHT_SHIFT_ZERO_FILLS'),

    # The size of `double', as computed by sizeof.
    Config('SIZEOF_DOUBLE', ios=8, linux=8, osx=8),

    # The size of `float', as computed by sizeof.
    Config('SIZEOF_FLOAT', ios=4, linux=4, osx=4),

    # The size of `fpos_t', as computed by sizeof.
    Config('SIZEOF_FPOS_T', ios=8, linux=16, osx=8),

    # The size of `int', as computed by sizeof.
    Config('SIZEOF_INT', ios=4, linux=4, osx=4),

    # The size of `long', as computed by sizeof.
    Config('SIZEOF_LONG', ios_64=8, linux_32=4, linux_64=8, osx_64=8),

    # The size of `long double', as computed by sizeof.
    Config('SIZEOF_LONG_DOUBLE', ios=16, linux_32=12, linux_64=16, osx=16),

    # The size of `long long', as computed by sizeof.
    Config('SIZEOF_LONG_LONG', ios=8, linux=8, osx=8),

    # The size of `off_t', as computed by sizeof.
    Config('SIZEOF_OFF_T', ios=8, linux=8, osx=8),

    # The size of `pid_t', as computed by sizeof.
    Config('SIZEOF_PID_T', ios=4, linux=4, osx=4),

    # The size of `pthread_t', as computed by sizeof.
    Config('SIZEOF_PTHREAD_T', ios_64=8, linux_32=4, linux_64=8, osx_64=8),

    # The size of `short', as computed by sizeof.
    Config('SIZEOF_SHORT', ios=2, linux=2, osx=2),

    # The size of `size_t', as computed by sizeof.
    Config('SIZEOF_SIZE_T', ios_64=8, linux_32=4, linux_64=8, osx_64=8),

    # The size of `time_t', as computed by sizeof.
    Config('SIZEOF_TIME_T', ios_64=8, linux_32=4, linux_64=8, osx_64=8),

    # The size of `uintptr_t', as computed by sizeof.
    Config('SIZEOF_UINTPTR_T', ios_64=8, linux_32=4, linux_64=8, osx_64=8),

    # The size of `void *', as computed by sizeof.
    Config('SIZEOF_VOID_P', ios_64=8, linux_32=4, linux_64=8, osx_64=8),

    # The size of `wchar_t', as computed by sizeof.
    Config('SIZEOF_WCHAR_T', ios=4, linux=4, osx=4),

    # The size of `_Bool', as computed by sizeof.
    Config('SIZEOF__BOOL', ios=1, linux=1, osx=1),

    # Define to 1 if you have the ANSI C header files.
    Config('STDC_HEADERS', ios=1, linux=1, osx=1),

    # Define if you can safely include both <sys/select.h> and <sys/time.h>
    # (which you can't on SCO ODT 3.0).
    Config('SYS_SELECT_WITH_SYS_TIME', ios=1, linux=1, osx=1),

    # Define if tanh(-0.) is -0., or if platform doesn't have signed zeros
    Config('TANH_PRESERVES_ZERO_SIGN', ios=1, linux=1, osx=1),

    # Define to 1 if you can safely include both <sys/time.h> and <time.h>.
    Config('TIME_WITH_SYS_TIME', ios=1, linux=1, osx=1),

    # Define to 1 if your <sys/time.h> declares `struct tm'.
    Config('TM_IN_SYS_TIME'),

    # Define if you want to use computed gotos in ceval.c.
    Config('USE_COMPUTED_GOTOS'),

    # Define to use the C99 inline keyword.
    Config('USE_INLINE', ios=1, linux=1, osx=1),

    # Define if you want to use MacPython modules on MacOSX in unix-Python.
    Config('USE_TOOLBOX_OBJECT_GLUE', ios=1, osx=1),

    # Define if a va_list is an array of some kind
    Config('VA_LIST_IS_ARRAY', ios_64=1, linux_64=1, osx_64=1),

    # Define if you want SIGFPE handled (see Include/pyfpe.h).
    Config('WANT_SIGFPE_HANDLER'),

    # Define if you want wctype.h functions to be used instead of the one
    # supplied by Python itself. (see Include/unicodectype.h).
    Config('WANT_WCTYPE_FUNCTIONS'),

    # Define if WINDOW in curses.h offers a field _flags.
    Config('WINDOW_HAS_FLAGS', linux=1),

    # Define if you want documentation strings in extension modules
    Config('WITH_DOC_STRINGS'),

    # Define to 1 if libintl is needed for locale functions.
    Config('WITH_LIBINTL'),

    # Define if you want to compile in Python-specific mallocs
    Config('WITH_PYMALLOC', ios=1, linux=1, osx=1),

    # Define if you want to compile in rudimentary thread support
    Config('WITH_THREAD', ios=1, linux=1, osx=1),

    # Define to profile with the Pentium timestamp counter
    Config('WITH_TSC'),

    # Define to 1 if your processor stores words with the most significant byte
    # first (like Motorola and SPARC, unlike Intel and VAX).
    Config('WORDS_BIGENDIAN'),

    # Define if arithmetic is subject to x87-style double rounding issue
    Config('X87_DOUBLE_ROUNDING', linux=1),

    # Define on OpenBSD to activate all library features
    Config('_BSD_SOURCE'),

    # Define on Darwin to activate all library features
    Config('_DARWIN_C_SOURCE', ios=1, osx=1),

    # This must be set to 64 on some systems to enable large file support.
    Config('_FILE_OFFSET_BITS', ios=64, linux=64, osx=64),

    # Define on Linux to activate all library features
    Config('_GNU_SOURCE', ios=1, linux=1, osx=1),

    # Define to include mbstate_t for mbrtowc
    Config('_INCLUDE__STDC_A1_SOURCE'),

    # This must be defined on some systems to enable large file support.
    Config('_LARGEFILE_SOURCE', ios=1, linux=1, osx=1),

    # Define on NetBSD to activate all library features
    Config('_NETBSD_SOURCE', ios=1, linux=1, osx=1),

    # Define to 2 if the system does not provide POSIX.1 features except with
    # this defined.
    Config('_POSIX_1_SOURCE'),

    # Define to activate features from IEEE Stds 1003.1-2008
    Config('_POSIX_C_SOURCE', linux='200809L'),

    # Define to 1 if you need to in order for `stat' and other things to work.
    Config('_POSIX_SOURCE'),

    # Define if you have POSIX threads, and your system does not define that.
    Config('_POSIX_THREADS'),

    # Define to force use of thread-safe errno, h_errno, and other functions
    Config('_REENTRANT', ios=1, osx=1),

    # Define to the level of X/Open that your system supports
    Config('_XOPEN_SOURCE', linux=700),

    # Define to activate Unix95-and-earlier features
    Config('_XOPEN_SOURCE_EXTENDED', linux=1),

    # Define on FreeBSD to activate all library features
    Config('__BSD_VISIBLE', ios=1, linux=1, osx=1),

    # Define to 1 if type `char' is unsigned and you are not using gcc. 
    Config('__CHAR_UNSIGNED__'),

    # Define to 'long' if <time.h> doesn't define.
    Config('clock_t'),

    # Define to empty if `const' does not conform to ANSI C.
    Config('const'),

    # Define to `int' if <sys/types.h> doesn't define.
    Config('gid_t'),

    # Define to the type of a signed integer type of width exactly 32 bits if
    # such a type exists and the standard includes do not define it.
    Config('int32_t'),

    # Define to the type of a signed integer type of width exactly 64 bits if
    # such a type exists and the standard includes do not define it.
    Config('int64_t'),

    # Define to `int' if <sys/types.h> does not define.
    Config('mode_t'),

    # Define to `long int' if <sys/types.h> does not define.
    Config('off_t'),

    # Define to `int' if <sys/types.h> does not define.
    Config('pid_t'),

    # Define to empty if the keyword does not work.
    Config('signed'),

    # Define to `unsigned int' if <sys/types.h> does not define.
    Config('size_t'),

    # Define to `int' if <sys/socket.h> does not define.
    Config('socklen_t'),

    # Define to `int' if <sys/types.h> doesn't define.
    Config('uid_t'),

    # Define to the type of an unsigned integer type of width exactly 32 bits
    # if such a type exists and the standard includes do not define it.
    Config('uint32_t'),

    # Define to the type of an unsigned integer type of width exactly 64 bits
    # if such a type exists and the standard includes do not define it.
    Config('uint64_t'),

    # Define to empty if the keyword does not work.
    Config('volatile'),
)


def generate_pyconfig_h(pyconfig_h_name, target, dynamic_loading):
    """ Create the pyconfig.h file for a specific target variant. """

    pyconfig_h = create_file(pyconfig_h_name)

    if dynamic_loading:
        pyconfig_h.write('#define HAVE_DYNAMIC_LOADING 1\n')

    for config in pyconfig:
        value = config.value(target)

        if value is None:
            # We provide an commented out #define to make it easier to modify
            # the file by hand later.
            pyconfig_h.write('/* #define {0} */\n'.format(config.name))
        else:
            pyconfig_h.write('#define {0} {1}\n'.format(config.name, value))

    pyconfig_h.close()
