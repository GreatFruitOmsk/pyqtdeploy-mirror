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
    Config('DOUBLE_IS_LITTLE_ENDIAN_IEEE754', osx=1),

    # Define if --enable-ipv6 is specified
    Config('ENABLE_IPV6', osx=1),

    # Define if getpgrp() must be called as getpgrp(0).
    Config('GETPGRP_HAVE_ARG'),

    # Define if gettimeofday() does not have second (timezone) argument
    Config('GETTIMEOFDAY_NO_TZ'),

    # Define to 1 if you have the `accept4' function.
    Config('HAVE_ACCEPT4'),

    # Define to 1 if you have the `acosh' function.
    Config('HAVE_ACOSH', osx=1),

    # struct addrinfo (netdb.h)
    Config('HAVE_ADDRINFO', osx=1),

    # Define to 1 if you have the `alarm' function.
    Config('HAVE_ALARM', osx=1),

    # Define if aligned memory access is required
    Config('HAVE_ALIGNED_REQUIRED'),

    # Define to 1 if you have the <alloca.h> header file.
    Config('HAVE_ALLOCA_H', osx=1),

    # Define this if your time.h defines altzone.
    Config('HAVE_ALTZONE'),

    # Define to 1 if you have the `asinh' function.
    Config('HAVE_ASINH', osx=1),

    # Define to 1 if you have the <asm/types.h> header file.
    Config('HAVE_ASM_TYPES_H'),

    # Define to 1 if you have the `atanh' function.
    Config('HAVE_ATANH', osx=1),

    # Define if GCC supports __attribute__((format(PyArg_ParseTuple, 2, 3)))
    Config('HAVE_ATTRIBUTE_FORMAT_PARSETUPLE'),

    # Define to 1 if you have the `bind_textdomain_codeset' function.
    Config('HAVE_BIND_TEXTDOMAIN_CODESET'),

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
    Config('HAVE_BROKEN_SEM_GETVALUE', osx=1),

    # Define if `unsetenv` does not return an int.
    Config('HAVE_BROKEN_UNSETENV'),

    # Define this if you have the type _Bool.
    Config('HAVE_C99_BOOL', osx=1),

    # Define to 1 if you have the `chflags' function.
    Config('HAVE_CHFLAGS', osx=1),

    # Define to 1 if you have the `chown' function.
    Config('HAVE_CHOWN', osx=1),

    # Define if you have the 'chroot' function.
    Config('HAVE_CHROOT', osx=1),

    # Define to 1 if you have the `clock' function.
    Config('HAVE_CLOCK', osx=1),

    # Define to 1 if you have the `clock_getres' function.
    Config('HAVE_CLOCK_GETRES'),

    # Define to 1 if you have the `clock_gettime' function.
    Config('HAVE_CLOCK_GETTIME'),

    # Define if the C compiler supports computed gotos.
    Config('HAVE_COMPUTED_GOTOS', osx=1),

    # Define to 1 if you have the `confstr' function.
    Config('HAVE_CONFSTR', osx=1),

    # Define to 1 if you have the <conio.h> header file.
    Config('HAVE_CONIO_H'),

    # Define to 1 if you have the `copysign' function.
    Config('HAVE_COPYSIGN', osx=1),

    # Define to 1 if you have the `ctermid' function.
    Config('HAVE_CTERMID', osx=1),

    # Define if you have the 'ctermid_r' function.
    Config('HAVE_CTERMID_R', osx=1),

    # Define to 1 if you have the <curses.h> header file.
    Config('HAVE_CURSES_H', osx=1),

    # Define if you have the 'is_term_resized' function.
    Config('HAVE_CURSES_IS_TERM_RESIZED', osx=1),

    # Define if you have the 'resizeterm' function.
    Config('HAVE_CURSES_RESIZETERM', osx=1),

    # Define if you have the 'resize_term' function.
    Config('HAVE_CURSES_RESIZE_TERM', osx=1),

    # Define to 1 if you have the declaration of `isfinite'.
    Config('HAVE_DECL_ISFINITE', osx=1),

    # Define to 1 if you have the declaration of `isinf'.
    Config('HAVE_DECL_ISINF', osx=1),
    Config('HAVE_ISINF', osx=1),

    # Define to 1 if you have the declaration of `isnan'.
    Config('HAVE_DECL_ISNAN', osx=1),
    Config('HAVE_ISNAN', osx=1),

    # Define to 1 if you have the declaration of `tzname'.
    Config('HAVE_DECL_TZNAME'),

    # Define to 1 if you have the device macros.
    Config('HAVE_DEVICE_MACROS', osx=1),

    # Define to 1 if you have the /dev/ptc device file.
    Config('HAVE_DEV_PTC'),

    # Define to 1 if you have the /dev/ptmx device file.
    Config('HAVE_DEV_PTMX', osx=1),

    # Define to 1 if you have the <direct.h> header file.
    Config('HAVE_DIRECT_H'),

    # Define to 1 if you have the <dirent.h> header file, and it defines `DIR'.
    Config('HAVE_DIRENT_H', osx=1),

    # Define if you have the 'dirfd' function or macro.
    Config('HAVE_DIRFD', osx=1),

    # Define to 1 if you have the <dlfcn.h> header file.
    Config('HAVE_DLFCN_H', osx=1),

    # Define to 1 if you have the `dlopen' function.
    Config('HAVE_DLOPEN', osx=1),

    # Define to 1 if you have the `dup2' function.
    Config('HAVE_DUP2', osx=1),

    # Define to 1 if you have the `dup3' function.
    Config('HAVE_DUP3'),

    # Defined when any dynamic module loading is enabled.
    Config('HAVE_DYNAMIC_LOADING', osx=1),

    # Define to 1 if you have the <endian.h> header file.
    Config('HAVE_ENDIAN_H'),

    # Define if you have the 'epoll' functions.
    Config('HAVE_EPOLL'),

    # Define if you have the 'epoll_create1' function.
    Config('HAVE_EPOLL_CREATE1'),

    # Define to 1 if you have the `erf' function.
    Config('HAVE_ERF', osx=1),

    # Define to 1 if you have the `erfc' function.
    Config('HAVE_ERFC', osx=1),

    # Define to 1 if you have the <errno.h> header file.
    Config('HAVE_ERRNO_H', osx=1),

    # Define to 1 if you have the `execv' function.
    Config('HAVE_EXECV', osx=1),

    # Define to 1 if you have the `expm1' function.
    Config('HAVE_EXPM1', osx=1),

    # Define to 1 if you have the `faccessat' function.
    Config('HAVE_FACCESSAT'),

    # Define if you have the 'fchdir' function.
    Config('HAVE_FCHDIR', osx=1),

    # Define to 1 if you have the `fchmod' function.
    Config('HAVE_FCHMOD', osx=1),

    # Define to 1 if you have the `fchmodat' function.
    Config('HAVE_FCHMODAT'),

    # Define to 1 if you have the `fchown' function.
    Config('HAVE_FCHOWN', osx=1),

    # Define to 1 if you have the `fchownat' function.
    Config('HAVE_FCHOWNAT'),

    # Define to 1 if you have the <fcntl.h> header file.
    Config('HAVE_FCNTL_H', osx=1),

    # Define if you have the 'fdatasync' function.
    Config('HAVE_FDATASYNC'),

    # Define to 1 if you have the `fdopendir' function.
    Config('HAVE_FDOPENDIR'),

    # Define to 1 if you have the `fexecve' function.
    Config('HAVE_FEXECVE'),

    # Define to 1 if you have the `finite' function.
    Config('HAVE_FINITE', osx=1),

    # Define to 1 if you have the 'flock' function.
    Config('HAVE_FLOCK', osx=1),

    # Define to 1 if you have the `fork' function.
    Config('HAVE_FORK', osx=1),

    # Define to 1 if you have the `forkpty' function.
    Config('HAVE_FORKPTY', osx=1),

    # Define to 1 if you have the `fpathconf' function.
    Config('HAVE_FPATHCONF', osx=1),

    # Define to 1 if you have the `fseek64' function.
    Config('HAVE_FSEEK64'),

    # Define to 1 if you have the `fseeko' function.
    Config('HAVE_FSEEKO', osx=1),

    # Define to 1 if you have the `fstatat' function.
    Config('HAVE_FSTATAT'),

    # Define to 1 if you have the `fstatvfs' function.
    Config('HAVE_FSTATVFS', osx=1),

    # Define if you have the 'fsync' function.
    Config('HAVE_FSYNC', osx=1),

    # Define to 1 if you have the `ftell64' function.
    Config('HAVE_FTELL64'),

    # Define to 1 if you have the `ftello' function.
    Config('HAVE_FTELLO', osx=1),

    # Define to 1 if you have the `ftime' function.
    Config('HAVE_FTIME', osx=1),

    # Define to 1 if you have the `ftruncate' function.
    Config('HAVE_FTRUNCATE', osx=1),

    # Define to 1 if you have the `futimens' function.
    Config('HAVE_FUTIMENS'),

    # Define to 1 if you have the `futimes' function.
    Config('HAVE_FUTIMES', osx=1),

    # Define to 1 if you have the `futimesat' function.
    Config('HAVE_FUTIMESAT'),

    # Define to 1 if you have the `gai_strerror' function.
    Config('HAVE_GAI_STRERROR', osx=1),

    # Define to 1 if you have the `gamma' function.
    Config('HAVE_GAMMA', osx=1),

    # Define if we can use x64 gcc inline assembler
    Config('HAVE_GCC_ASM_FOR_X64', osx=1),

    # Define if we can use gcc inline assembler to get and set x87 control word
    Config('HAVE_GCC_ASM_FOR_X87', osx=1),

    # Define if your compiler provides __uint128_t
    Config('HAVE_GCC_UINT128_T', osx=1),

    # Define if you have the getaddrinfo function.
    Config('HAVE_GETADDRINFO', osx=1),

    # Define to 1 if you have the `getcwd' function.
    Config('HAVE_GETCWD', osx=1),

    # Define this if you have flockfile(), getc_unlocked(), and funlockfile()
    Config('HAVE_GETC_UNLOCKED', osx=1),

    # Define to 1 if you have the `getgrouplist' function.
    Config('HAVE_GETGROUPLIST', osx=1),

    # Define to 1 if you have the `getgroups' function.
    Config('HAVE_GETGROUPS', osx=1),

    # Define to 1 if you have the `gethostbyname' function.
    Config('HAVE_GETHOSTBYNAME', osx=1),

    # Define this if you have some version of gethostbyname_r()
    Config('HAVE_GETHOSTBYNAME_R'),

    # Define this if you have the 3-arg version of gethostbyname_r().
    Config('HAVE_GETHOSTBYNAME_R_3_ARG'),

    # Define this if you have the 5-arg version of gethostbyname_r().
    Config('HAVE_GETHOSTBYNAME_R_5_ARG'),

    # Define this if you have the 6-arg version of gethostbyname_r().
    Config('HAVE_GETHOSTBYNAME_R_6_ARG'),

    # Define to 1 if you have the `getitimer' function.
    Config('HAVE_GETITIMER', osx=1),

    # Define to 1 if you have the `getloadavg' function.
    Config('HAVE_GETLOADAVG', osx=1),

    # Define to 1 if you have the `getlogin' function.
    Config('HAVE_GETLOGIN', osx=1),

    # Define to 1 if you have the `getnameinfo' function.
    Config('HAVE_GETNAMEINFO', osx=1),

    # Define if you have the 'getpagesize' function.
    Config('HAVE_GETPAGESIZE', osx=1),

    # Define to 1 if you have the `getpeername' function.
    Config('HAVE_GETPEERNAME', osx=1),

    # Define to 1 if you have the `getpgid' function.
    Config('HAVE_GETPGID', osx=1),

    # Define to 1 if you have the `getpgrp' function.
    Config('HAVE_GETPGRP', osx=1),

    # Define to 1 if you have the `getpid' function.
    Config('HAVE_GETPID', osx=1),

    # Define to 1 if you have the `getpriority' function.
    Config('HAVE_GETPRIORITY', osx=1),

    # Define to 1 if you have the `getpwent' function.
    Config('HAVE_GETPWENT', osx=1),

    # Define to 1 if you have the `getresgid' function.
    Config('HAVE_GETRESGID'),

    # Define to 1 if you have the `getresuid' function.
    Config('HAVE_GETRESUID'),

    # Define to 1 if you have the `getsid' function.
    Config('HAVE_GETSID', osx=1),

    # Define to 1 if you have the `getspent' function.
    Config('HAVE_GETSPENT'),

    # Define to 1 if you have the `getspnam' function.
    Config('HAVE_GETSPNAM'),

    # Define to 1 if you have the `gettimeofday' function.
    Config('HAVE_GETTIMEOFDAY', osx=1),

    # Define to 1 if you have the `getwd' function.
    Config('HAVE_GETWD', osx=1),

    # Define if glibc has incorrect _FORTIFY_SOURCE wrappers for memmove and
    # bcopy.
    Config('HAVE_GLIBC_MEMMOVE_BUG'),

    # Define to 1 if you have the <grp.h> header file.
    Config('HAVE_GRP_H', osx=1),

    # Define if you have the 'hstrerror' function.
    Config('HAVE_HSTRERROR', osx=1),

    # Define this if you have le64toh()
    Config('HAVE_HTOLE64'),

    # Define to 1 if you have the `hypot' function.
    Config('HAVE_HYPOT', osx=1),

    # Define to 1 if you have the <ieeefp.h> header file.
    Config('HAVE_IEEEFP_H'),

    # Define to 1 if you have the `if_nameindex' function.
    Config('HAVE_IF_NAMEINDEX', osx=1),

    # Define if you have the 'inet_aton' function.
    Config('HAVE_INET_ATON', osx=1),

    # Define if you have the 'inet_pton' function.
    Config('HAVE_INET_PTON', osx=1),

    # Define to 1 if you have the `initgroups' function.
    Config('HAVE_INITGROUPS', osx=1),

    # Define if your compiler provides int32_t.
    Config('HAVE_INT32_T', osx=1),

    # Define if your compiler provides int64_t.
    Config('HAVE_INT64_T', osx=1),

    # Define to 1 if you have the <inttypes.h> header file.
    Config('HAVE_INTTYPES_H', osx=1),

    # Define to 1 if you have the <io.h> header file.
    Config('HAVE_IO_H'),

    # Define if gcc has the ipa-pure-const bug.
    Config('HAVE_IPA_PURE_CONST_BUG'),

    # Define to 1 if you have the `kill' function.
    Config('HAVE_KILL', osx=1),

    # Define to 1 if you have the `killpg' function.
    Config('HAVE_KILLPG', osx=1),

    # Define if you have the 'kqueue' functions.
    Config('HAVE_KQUEUE', osx=1),

    # Define to 1 if you have the <langinfo.h> header file.
    Config('HAVE_LANGINFO_H', osx=1),

    # Defined to enable large file support when an off_t is bigger than a long
    # and long long is available and at least as big as an off_t. You may need
    # to add some flags for configuration and compilation to enable this mode.
    # (For Solaris and Linux, the necessary defines are already defined.),
    Config('HAVE_LARGEFILE_SUPPORT'),

    # Define to 1 if you have the `lchflags' function.
    Config('HAVE_LCHFLAGS', osx=1),

    # Define to 1 if you have the `lchmod' function.
    Config('HAVE_LCHMOD', osx=1),

    # Define to 1 if you have the `lchown' function.
    Config('HAVE_LCHOWN', osx=1),

    # Define to 1 if you have the `lgamma' function.
    Config('HAVE_LGAMMA', osx=1),

    # Define to 1 if you have the `dl' library (-ldl).
    Config('HAVE_LIBDL', osx=1),

    # Define to 1 if you have the `dld' library (-ldld).
    Config('HAVE_LIBDLD'),

    # Define to 1 if you have the `ieee' library (-lieee).
    Config('HAVE_LIBIEEE'),

    # Define to 1 if you have the <libintl.h> header file.
    Config('HAVE_LIBINTL_H'),

    # Define if you have the `readline' library (-lreadline).
    Config('HAVE_LIBREADLINE', osx=1),

    # Define to 1 if you have the `resolv' library (-lresolv).
    Config('HAVE_LIBRESOLV'),

    # Define to 1 if you have the `sendfile' library (-lsendfile).
    Config('HAVE_LIBSENDFILE'),

    # Define to 1 if you have the <libutil.h> header file.
    Config('HAVE_LIBUTIL_H'),

    # Define if you have the 'link' function.
    Config('HAVE_LINK', osx=1),

    # Define to 1 if you have the `linkat' function.
    Config('HAVE_LINKAT'),

    # Define to 1 if you have the <linux/can/bcm.h> header file.
    Config('HAVE_LINUX_CAN_BCM_H'),

    # Define to 1 if you have the <linux/can.h> header file.
    Config('HAVE_LINUX_CAN_H'),

    # Define to 1 if you have the <linux/can/raw.h> header file.
    Config('HAVE_LINUX_CAN_RAW_H'),

    # Define to 1 if you have the <linux/netlink.h> header file.
    Config('HAVE_LINUX_NETLINK_H'),

    # Define to 1 if you have the <linux/tipc.h> header file.
    Config('HAVE_LINUX_TIPC_H'),

    # Define to 1 if you have the `lockf' function.
    Config('HAVE_LOCKF', osx=1),

    # Define to 1 if you have the `log1p' function.
    Config('HAVE_LOG1P', osx=1),

    # Define to 1 if you have the `log2' function.
    Config('HAVE_LOG2', osx=1),

    # Define this if you have the type long double.
    Config('HAVE_LONG_DOUBLE', osx=1),

    # Define this if you have the type long long.
    Config('HAVE_LONG_LONG', osx=1),

    # Define to 1 if you have the `lstat' function.
    Config('HAVE_LSTAT', osx=1),

    # Define to 1 if you have the `lutimes' function.
    Config('HAVE_LUTIMES', osx=1),

    # Define this if you have the makedev macro.
    Config('HAVE_MAKEDEV', osx=1),

    # Define to 1 if you have the `mbrtowc' function.
    Config('HAVE_MBRTOWC', osx=1),

    # Define to 1 if you have the `memmove' function.
    Config('HAVE_MEMMOVE', osx=1),

    # Define to 1 if you have the <memory.h> header file.
    Config('HAVE_MEMORY_H', osx=1),

    # Define to 1 if you have the `memrchr' function.
    Config('HAVE_MEMRCHR'),

    # Define to 1 if you have the `mkdirat' function.
    Config('HAVE_MKDIRAT'),

    # Define to 1 if you have the `mkfifo' function.
    Config('HAVE_MKFIFO', osx=1),

    # Define to 1 if you have the `mkfifoat' function.
    Config('HAVE_MKFIFOAT'),

    # Define to 1 if you have the `mknod' function.
    Config('HAVE_MKNOD', osx=1),

    # Define to 1 if you have the `mknodat' function.
    Config('HAVE_MKNODAT'),

    # Define to 1 if you have the `mktime' function.
    Config('HAVE_MKTIME', osx=1),

    # Define to 1 if you have the `mmap' function.
    Config('HAVE_MMAP', osx=1),

    # Define to 1 if you have the `mremap' function.
    Config('HAVE_MREMAP'),

    # Define to 1 if you have the <ncurses.h> header file.
    Config('HAVE_NCURSES_H', osx=1),

    # Define to 1 if you have the <ndir.h> header file, and it defines `DIR'.
    Config('HAVE_NDIR_H'),

    # Define to 1 if you have the <netpacket/packet.h> header file.
    Config('HAVE_NETPACKET_PACKET_H'),

    # Define to 1 if you have the <net/if.h> header file.
    Config('HAVE_NET_IF_H', osx=1),

    # Define to 1 if you have the `nice' function.
    Config('HAVE_NICE', osx=1),

    # Define to 1 if you have the `openat' function.
    Config('HAVE_OPENAT'),

    # Define to 1 if you have the `openpty' function.
    Config('HAVE_OPENPTY', osx=1),

    # Define if compiling using MacOS X 10.5 SDK or later.
    Config('HAVE_OSX105_SDK', osx=1),

    # Define to 1 if you have the `pathconf' function.
    Config('HAVE_PATHCONF', osx=1),

    # Define to 1 if you have the `pause' function.
    Config('HAVE_PAUSE', osx=1),

    # Define to 1 if you have the `pipe2' function.
    Config('HAVE_PIPE2'),

    # Define to 1 if you have the `plock' function.
    Config('HAVE_PLOCK'),

    # Define to 1 if you have the `poll' function.
    Config('HAVE_POLL', osx=1),

    # Define to 1 if you have the <poll.h> header file.
    Config('HAVE_POLL_H', osx=1),

    # Define to 1 if you have the `posix_fadvise' function.
    Config('HAVE_POSIX_FADVISE'),

    # Define to 1 if you have the `posix_fallocate' function.
    Config('HAVE_POSIX_FALLOCATE'),

    # Define to 1 if you have the `pread' function.
    Config('HAVE_PREAD', osx=1),

    # Define if you have the 'prlimit' functions.
    Config('HAVE_PRLIMIT'),

    # Define to 1 if you have the <process.h> header file.
    Config('HAVE_PROCESS_H'),

    # Define if your compiler supports function prototype
    Config('HAVE_PROTOTYPES', osx=1),

    # Define to 1 if you have the `pthread_atfork' function.
    Config('HAVE_PTHREAD_ATFORK', osx=1),

    # Defined for Solaris 2.6 bug in pthread header.
    Config('HAVE_PTHREAD_DESTRUCTOR'),

    # Define to 1 if you have the <pthread.h> header file.
    Config('HAVE_PTHREAD_H', osx=1),

    # Define to 1 if you have the `pthread_init' function.
    Config('HAVE_PTHREAD_INIT'),

    # Define to 1 if you have the `pthread_kill' function.
    Config('HAVE_PTHREAD_KILL', osx=1),

    # Define to 1 if you have the `pthread_sigmask' function.
    Config('HAVE_PTHREAD_SIGMASK', osx=1),

    # Define to 1 if you have the <pty.h> header file.
    Config('HAVE_PTY_H'),

    # Define to 1 if you have the `putenv' function.
    Config('HAVE_PUTENV', osx=1),

    # Define to 1 if you have the `pwrite' function.
    Config('HAVE_PWRITE', osx=1),

    # Define to 1 if you have the `readlink' function.
    Config('HAVE_READLINK', osx=1),

    # Define to 1 if you have the `readlinkat' function.
    Config('HAVE_READLINKAT'),

    # Define to 1 if you have the `readv' function.
    Config('HAVE_READV', osx=1),

    # Define to 1 if you have the `realpath' function.
    Config('HAVE_REALPATH', osx=1),

    # Define to 1 if you have the `renameat' function.
    Config('HAVE_RENAMEAT'),

    # Define if you have readline 2.1
    Config('HAVE_RL_CALLBACK', osx=1),

    # Define if you can turn off readline's signal handling.
    Config('HAVE_RL_CATCH_SIGNAL'),

    # Define if you have readline 2.2
    Config('HAVE_RL_COMPLETION_APPEND_CHARACTER', osx=1),

    # Define if you have readline 4.0
    Config('HAVE_RL_COMPLETION_DISPLAY_MATCHES_HOOK', osx=1),

    # Define if you have readline 4.2
    Config('HAVE_RL_COMPLETION_MATCHES', osx=1),

    # Define if you have rl_completion_suppress_append
    Config('HAVE_RL_COMPLETION_SUPPRESS_APPEND'),

    # Define if you have readline 4.0
    Config('HAVE_RL_PRE_INPUT_HOOK', osx=1),

    # Define to 1 if you have the `round' function.
    Config('HAVE_ROUND', osx=1),

    # Define to 1 if you have the `sched_get_priority_max' function.
    Config('HAVE_SCHED_GET_PRIORITY_MAX', osx=1),

    # Define to 1 if you have the <sched.h> header file.
    Config('HAVE_SCHED_H', osx=1),

    # Define to 1 if you have the `sched_rr_get_interval' function.
    Config('HAVE_SCHED_RR_GET_INTERVAL'),

    # Define to 1 if you have the `sched_setaffinity' function.
    Config('HAVE_SCHED_SETAFFINITY'),

    # Define to 1 if you have the `sched_setparam' function.
    Config('HAVE_SCHED_SETPARAM'),

    # Define to 1 if you have the `sched_setscheduler' function.
    Config('HAVE_SCHED_SETSCHEDULER'),

    # Define to 1 if you have the `select' function.
    Config('HAVE_SELECT', osx=1),

    # Define to 1 if you have the `sem_getvalue' function.
    Config('HAVE_SEM_GETVALUE', osx=1),

    # Define to 1 if you have the `sem_open' function.
    Config('HAVE_SEM_OPEN', osx=1),

    # Define to 1 if you have the `sem_timedwait' function.
    Config('HAVE_SEM_TIMEDWAIT'),

    # Define to 1 if you have the `sem_unlink' function.
    Config('HAVE_SEM_UNLINK', osx=1),

    # Define to 1 if you have the `sendfile' function.
    Config('HAVE_SENDFILE', osx=1),

    # Define to 1 if you have the `setegid' function.
    Config('HAVE_SETEGID', osx=1),

    # Define to 1 if you have the `seteuid' function.
    Config('HAVE_SETEUID', osx=1),

    # Define to 1 if you have the `setgid' function.
    Config('HAVE_SETGID', osx=1),

    # Define if you have the 'setgroups' function.
    Config('HAVE_SETGROUPS', osx=1),

    # Define to 1 if you have the `sethostname' function.
    Config('HAVE_SETHOSTNAME', osx=1),

    # Define to 1 if you have the `setitimer' function.
    Config('HAVE_SETITIMER', osx=1),

    # Define to 1 if you have the `setlocale' function.
    Config('HAVE_SETLOCALE', osx=1),

    # Define to 1 if you have the `setpgid' function.
    Config('HAVE_SETPGID', osx=1),

    # Define to 1 if you have the `setpgrp' function.
    Config('HAVE_SETPGRP', osx=1),

    # Define to 1 if you have the `setpriority' function.
    Config('HAVE_SETPRIORITY', osx=1),

    # Define to 1 if you have the `setregid' function.
    Config('HAVE_SETREGID', osx=1),

    # Define to 1 if you have the `setresgid' function.
    Config('HAVE_SETRESGID'),

    # Define to 1 if you have the `setresuid' function.
    Config('HAVE_SETRESUID'),

    # Define to 1 if you have the `setreuid' function.
    Config('HAVE_SETREUID', osx=1),

    # Define to 1 if you have the `setsid' function.
    Config('HAVE_SETSID', osx=1),

    # Define to 1 if you have the `setuid' function.
    Config('HAVE_SETUID', osx=1),

    # Define to 1 if you have the `setvbuf' function.
    Config('HAVE_SETVBUF', osx=1),

    # Define to 1 if you have the <shadow.h> header file.
    Config('HAVE_SHADOW_H'),

    # Define to 1 if you have the `sigaction' function.
    Config('HAVE_SIGACTION', osx=1),

    # Define to 1 if you have the `sigaltstack' function.
    Config('HAVE_SIGALTSTACK', osx=1),

    # Define to 1 if you have the `siginterrupt' function.
    Config('HAVE_SIGINTERRUPT', osx=1),

    # Define to 1 if you have the <signal.h> header file.
    Config('HAVE_SIGNAL_H', osx=1),

    # Define to 1 if you have the `sigpending' function.
    Config('HAVE_SIGPENDING', osx=1),

    # Define to 1 if you have the `sigrelse' function.
    Config('HAVE_SIGRELSE', osx=1),

    # Define to 1 if you have the `sigtimedwait' function.
    Config('HAVE_SIGTIMEDWAIT'),

    # Define to 1 if you have the `sigwait' function.
    Config('HAVE_SIGWAIT', osx=1),

    # Define to 1 if you have the `sigwaitinfo' function.
    Config('HAVE_SIGWAITINFO'),

    # Define to 1 if you have the `snprintf' function.
    Config('HAVE_SNPRINTF', osx=1),

    # Define if sockaddr has sa_len member
    Config('HAVE_SOCKADDR_SA_LEN', osx=1),

    # struct sockaddr_storage (sys/socket.h),
    Config('HAVE_SOCKADDR_STORAGE', osx=1),

    # Define if you have the 'socketpair' function.
    Config('HAVE_SOCKETPAIR', osx=1),

    # Define to 1 if you have the <spawn.h> header file.
    Config('HAVE_SPAWN_H', osx=1),

    # Define if your compiler provides ssize_t
    Config('HAVE_SSIZE_T', osx=1),

    # Define to 1 if you have the `statvfs' function.
    Config('HAVE_STATVFS', osx=1),

    # Define if you have struct stat.st_mtim.tv_nsec
    Config('HAVE_STAT_TV_NSEC'),

    # Define if you have struct stat.st_mtimensec
    Config('HAVE_STAT_TV_NSEC2', osx=1),

    # Define if your compiler supports variable length function prototypes
    # (e.g.  void fprintf(FILE *, char *, ...);) *and* <stdarg.h>
    Config('HAVE_STDARG_PROTOTYPES', osx=1),

    # Define to 1 if you have the <stdint.h> header file.
    Config('HAVE_STDINT_H', osx=1),

    # Define to 1 if you have the <stdlib.h> header file.
    Config('HAVE_STDLIB_H', osx=1),

    # Define to 1 if you have the `strdup' function.
    Config('HAVE_STRDUP', osx=1),

    # Define to 1 if you have the `strftime' function.
    Config('HAVE_STRFTIME', osx=1),

    # Define to 1 if you have the <strings.h> header file.
    Config('HAVE_STRINGS_H', osx=1),

    # Define to 1 if you have the <string.h> header file.
    Config('HAVE_STRING_H', osx=1),

    # Define to 1 if you have the `strlcpy' function.
    Config('HAVE_STRLCPY', osx=1),

    # Define to 1 if you have the <stropts.h> header file.
    Config('HAVE_STROPTS_H'),

    # Define to 1 if `st_birthtime' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_BIRTHTIME', osx=1),

    # Define to 1 if `st_blksize' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_BLKSIZE', osx=1),

    # Define to 1 if `st_blocks' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_BLOCKS', osx=1),

    # Define to 1 if `st_flags' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_FLAGS', osx=1),

    # Define to 1 if `st_gen' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_GEN', osx=1),

    # Define to 1 if `st_rdev' is a member of `struct stat'.
    Config('HAVE_STRUCT_STAT_ST_RDEV', osx=1),

    # Define to 1 if `tm_zone' is a member of `struct tm'.
    Config('HAVE_STRUCT_TM_TM_ZONE', osx=1),

    # Define if you have the 'symlink' function.
    Config('HAVE_SYMLINK', osx=1),

    # Define to 1 if you have the `symlinkat' function.
    Config('HAVE_SYMLINKAT'),

    # Define to 1 if you have the `sync' function.
    Config('HAVE_SYNC', osx=1),

    # Define to 1 if you have the `sysconf' function.
    Config('HAVE_SYSCONF', osx=1),

    # Define to 1 if you have the <sysexits.h> header file.
    Config('HAVE_SYSEXITS_H', osx=1),

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
    Config('HAVE_SYS_EPOLL_H'),

    # Define to 1 if you have the <sys/event.h> header file.
    Config('HAVE_SYS_EVENT_H', osx=1),

    # Define to 1 if you have the <sys/file.h> header file.
    Config('HAVE_SYS_FILE_H', osx=1),

    # Define to 1 if you have the <sys/ioctl.h> header file.
    Config('HAVE_SYS_IOCTL_H', osx=1),

    # Define to 1 if you have the <sys/kern_control.h> header file.
    Config('HAVE_SYS_KERN_CONTROL_H', osx=1),

    # Define to 1 if you have the <sys/loadavg.h> header file.
    Config('HAVE_SYS_LOADAVG_H'),

    # Define to 1 if you have the <sys/lock.h> header file.
    Config('HAVE_SYS_LOCK_H', osx=1),

    # Define to 1 if you have the <sys/mkdev.h> header file.
    Config('HAVE_SYS_MKDEV_H'),

    # Define to 1 if you have the <sys/modem.h> header file.
    Config('HAVE_SYS_MODEM_H'),

    # Define to 1 if you have the <sys/ndir.h> header file, and it defines
    # `DIR'.
    Config('HAVE_SYS_NDIR_H'),

    # Define to 1 if you have the <sys/param.h> header file.
    Config('HAVE_SYS_PARAM_H', osx=1),

    # Define to 1 if you have the <sys/poll.h> header file.
    Config('HAVE_SYS_POLL_H', osx=1),

    # Define to 1 if you have the <sys/resource.h> header file.
    Config('HAVE_SYS_RESOURCE_H', osx=1),

    # Define to 1 if you have the <sys/select.h> header file.
    Config('HAVE_SYS_SELECT_H', osx=1),

    # Define to 1 if you have the <sys/sendfile.h> header file.
    Config('HAVE_SYS_SENDFILE_H'),

    # Define to 1 if you have the <sys/socket.h> header file.
    Config('HAVE_SYS_SOCKET_H', osx=1),

    # Define to 1 if you have the <sys/statvfs.h> header file.
    Config('HAVE_SYS_STATVFS_H', osx=1),

    # Define to 1 if you have the <sys/stat.h> header file.
    Config('HAVE_SYS_STAT_H', osx=1),

    # Define to 1 if you have the <sys/syscall.h> header file.
    Config('HAVE_SYS_SYSCALL_H', osx=1),

    # Define to 1 if you have the <sys/sys_domain.h> header file.
    Config('HAVE_SYS_SYS_DOMAIN_H', osx=1),

    # Define to 1 if you have the <sys/termio.h> header file.
    Config('HAVE_SYS_TERMIO_H'),

    # Define to 1 if you have the <sys/times.h> header file.
    Config('HAVE_SYS_TIMES_H', osx=1),

    # Define to 1 if you have the <sys/time.h> header file.
    Config('HAVE_SYS_TIME_H', osx=1),

    # Define to 1 if you have the <sys/types.h> header file.
    Config('HAVE_SYS_TYPES_H', osx=1),

    # Define to 1 if you have the <sys/uio.h> header file.
    Config('HAVE_SYS_UIO_H', osx=1),

    # Define to 1 if you have the <sys/un.h> header file.
    Config('HAVE_SYS_UN_H', osx=1),

    # Define to 1 if you have the <sys/utsname.h> header file.
    Config('HAVE_SYS_UTSNAME_H', osx=1),

    # Define to 1 if you have the <sys/wait.h> header file.
    Config('HAVE_SYS_WAIT_H', osx=1),

    # Define to 1 if you have the <sys/xattr.h> header file.
    Config('HAVE_SYS_XATTR_H', osx=1),

    # Define to 1 if you have the `tcgetpgrp' function.
    Config('HAVE_TCGETPGRP', osx=1),

    # Define to 1 if you have the `tcsetpgrp' function.
    Config('HAVE_TCSETPGRP', osx=1),

    # Define to 1 if you have the `tempnam' function.
    Config('HAVE_TEMPNAM', osx=1),

    # Define to 1 if you have the <termios.h> header file.
    Config('HAVE_TERMIOS_H', osx=1),

    # Define to 1 if you have the <term.h> header file.
    Config('HAVE_TERM_H', osx=1),

    # Define to 1 if you have the `tgamma' function.
    Config('HAVE_TGAMMA', osx=1),

    # Define to 1 if you have the <thread.h> header file.
    Config('HAVE_THREAD_H'),

    # Define to 1 if you have the `timegm' function.
    Config('HAVE_TIMEGM', osx=1),

    # Define to 1 if you have the `times' function.
    Config('HAVE_TIMES', osx=1),

    # Define to 1 if you have the `tmpfile' function.
    Config('HAVE_TMPFILE', osx=1),

    # Define to 1 if you have the `tmpnam' function.
    Config('HAVE_TMPNAM', osx=1),

    # Define to 1 if you have the `tmpnam_r' function.
    Config('HAVE_TMPNAM_R'),

    # Define to 1 if you have the `truncate' function.
    Config('HAVE_TRUNCATE', osx=1),

    # Define to 1 if you don't have `tm_zone' but do have the external array
    # `tzname'.
    Config('HAVE_TZNAME'),

    # Define if your compiler provides uint32_t.
    Config('HAVE_UINT32_T', osx=1),

    # Define if your compiler provides uint64_t.
    Config('HAVE_UINT64_T', osx=1),

    # Define to 1 if the system has the type `uintptr_t'.
    Config('HAVE_UINTPTR_T', osx=1),

    # Define to 1 if you have the `uname' function.
    Config('HAVE_UNAME', osx=1),

    # Define to 1 if you have the <unistd.h> header file.
    Config('HAVE_UNISTD_H', osx=1),

    # Define to 1 if you have the `unlinkat' function.
    Config('HAVE_UNLINKAT'),

    # Define to 1 if you have the `unsetenv' function.
    Config('HAVE_UNSETENV', osx=1),

    # Define if you have a useable wchar_t type defined in wchar.h; useable
    # means wchar_t must be an unsigned type with at least 16 bits. (see
    # Include/unicodeobject.h).
    Config('HAVE_USABLE_WCHAR_T'),

    # Define to 1 if you have the <util.h> header file.
    Config('HAVE_UTIL_H', osx=1),

    # Define to 1 if you have the `utimensat' function.
    Config('HAVE_UTIMENSAT'),

    # Define to 1 if you have the `utimes' function.
    Config('HAVE_UTIMES', osx=1),

    # Define to 1 if you have the <utime.h> header file.
    Config('HAVE_UTIME_H', osx=1),

    # Define to 1 if you have the `wait3' function.
    Config('HAVE_WAIT3', osx=1),

    # Define to 1 if you have the `wait4' function.
    Config('HAVE_WAIT4', osx=1),

    # Define to 1 if you have the `waitid' function.
    Config('HAVE_WAITID', osx=1),

    # Define to 1 if you have the `waitpid' function.
    Config('HAVE_WAITPID', osx=1),

    # Define if the compiler provides a wchar.h header file.
    Config('HAVE_WCHAR_H', osx=1),

    # Define to 1 if you have the `wcscoll' function.
    Config('HAVE_WCSCOLL', osx=1),

    # Define to 1 if you have the `wcsftime' function.
    Config('HAVE_WCSFTIME', osx=1),

    # Define to 1 if you have the `wcsxfrm' function.
    Config('HAVE_WCSXFRM', osx=1),

    # Define to 1 if you have the `wmemcmp' function.
    Config('HAVE_WMEMCMP', osx=1),

    # Define if tzset() actually switches the local timezone in a meaningful
    # way.
    Config('HAVE_WORKING_TZSET', osx=1),

    # Define to 1 if you have the `writev' function.
    Config('HAVE_WRITEV', osx=1),

    # Define if the zlib library has inflateCopy
    Config('HAVE_ZLIB_COPY', osx=1),

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
    Config('MVWDELCH_IS_EXPRESSION', osx=1),

    # Define to the address where bug reports for this package should be sent.
    Config('PACKAGE_BUGREPORT'),

    # Define to the full name of this package.
    Config('PACKAGE_NAME'),

    # Define to the full name and version of this package.
    Config('PACKAGE_STRING'),

    # Define to the one symbol short name of this package.
    Config('PACKAGE_TARNAME'),

    # Define to the home page for this package.
    Config('PACKAGE_URL'),

    # Define to the version of this package.
    Config('PACKAGE_VERSION'),

    # Define if POSIX semaphores aren't enabled on your system
    Config('POSIX_SEMAPHORES_NOT_ENABLED'),

    # Defined if PTHREAD_SCOPE_SYSTEM supported.
    Config('PTHREAD_SYSTEM_SCHED_SUPPORTED', osx=1),

    # Define as the preferred size in bits of long digits
    Config('PYLONG_BITS_IN_DIGIT'),

    # Define to printf format modifier for long long type
    Config('PY_FORMAT_LONG_LONG', osx='"ll"'),

    # Define to printf format modifier for Py_ssize_t
    Config('PY_FORMAT_SIZE_T', osx='"z"'),

    # Define as the integral type used for Unicode representation.
    Config('PY_UNICODE_TYPE', osx='unsigned short'),

    # Define if you want to build an interpreter with many run-time checks.
    Config('Py_DEBUG'),

    # Define hash algorithm for str, bytes and memoryview. SipHash24: 1,
    # FNV: 2, externally defined: 0
    Config('Py_HASH_ALGORITHM'),

    # Define as the size of the unicode type.
    Config('Py_UNICODE_SIZE', osx=2),

    # Define if you want to have a Unicode type.
    Config('Py_USING_UNICODE', osx=1),

    # Define if setpgrp() must be called as setpgrp(0, 0).
    Config('SETPGRP_HAVE_ARG'),

    # Define if i>>j for signed int i does not extend the sign bit when i < 0
    Config('SIGNED_RIGHT_SHIFT_ZERO_FILLS'),

    # The size of `double', as computed by sizeof.
    Config('SIZEOF_DOUBLE', osx=8),

    # The size of `float', as computed by sizeof.
    Config('SIZEOF_FLOAT', osx=4),

    # The size of `fpos_t', as computed by sizeof.
    Config('SIZEOF_FPOS_T', osx=8),

    # The size of `int', as computed by sizeof.
    Config('SIZEOF_INT', osx=4),

    # The size of `long', as computed by sizeof.
    Config('SIZEOF_LONG', osx=8),

    # The size of `long double', as computed by sizeof.
    Config('SIZEOF_LONG_DOUBLE', osx=16),

    # The size of `long long', as computed by sizeof.
    Config('SIZEOF_LONG_LONG', osx=8),

    # The size of `off_t', as computed by sizeof.
    Config('SIZEOF_OFF_T', osx=8),

    # The size of `pid_t', as computed by sizeof.
    Config('SIZEOF_PID_T', osx=4),

    # The size of `pthread_t', as computed by sizeof.
    Config('SIZEOF_PTHREAD_T', osx=8),

    # The size of `short', as computed by sizeof.
    Config('SIZEOF_SHORT', osx=2),

    # The size of `size_t', as computed by sizeof.
    Config('SIZEOF_SIZE_T', osx=8),

    # The size of `time_t', as computed by sizeof.
    Config('SIZEOF_TIME_T', osx=8),

    # The size of `uintptr_t', as computed by sizeof.
    Config('SIZEOF_UINTPTR_T', osx=8),

    # The size of `void *', as computed by sizeof.
    Config('SIZEOF_VOID_P', osx=8),

    # The size of `wchar_t', as computed by sizeof.
    Config('SIZEOF_WCHAR_T', osx=4),

    # The size of `_Bool', as computed by sizeof.
    Config('SIZEOF__BOOL', osx=1),

    # Define to 1 if you have the ANSI C header files.
    Config('STDC_HEADERS', osx=1),

    # Define if you can safely include both <sys/select.h> and <sys/time.h>
    # (which you can't on SCO ODT 3.0).
    Config('SYS_SELECT_WITH_SYS_TIME', osx=1),

    # Define if tanh(-0.) is -0., or if platform doesn't have signed zeros
    Config('TANH_PRESERVES_ZERO_SIGN', osx=1),

    # Define to 1 if you can safely include both <sys/time.h> and <time.h>.
    Config('TIME_WITH_SYS_TIME', osx=1),

    # Define to 1 if your <sys/time.h> declares `struct tm'.
    Config('TM_IN_SYS_TIME'),

    # Define if you want to use computed gotos in ceval.c.
    Config('USE_COMPUTED_GOTOS'),

    # Define to use the C99 inline keyword.
    Config('USE_INLINE', osx=1),

    # Define if you want to use MacPython modules on MacOSX in unix-Python.
    Config('USE_TOOLBOX_OBJECT_GLUE', osx=1),

    # Define if a va_list is an array of some kind
    Config('VA_LIST_IS_ARRAY', osx=1),

    # Define if you want SIGFPE handled (see Include/pyfpe.h).
    Config('WANT_SIGFPE_HANDLER'),

    # Define if you want wctype.h functions to be used instead of the one
    # supplied by Python itself. (see Include/unicodectype.h).
    Config('WANT_WCTYPE_FUNCTIONS'),

    # Define if WINDOW in curses.h offers a field _flags.
    Config('WINDOW_HAS_FLAGS'),

    # Define if you want documentation strings in extension modules
    Config('WITH_DOC_STRINGS'),

    # Define to 1 if libintl is needed for locale functions.
    Config('WITH_LIBINTL'),

    # Define if you want to compile in Python-specific mallocs
    Config('WITH_PYMALLOC', osx=1),

    # Define if you want to compile in rudimentary thread support
    Config('WITH_THREAD', osx=1),

    # Define to profile with the Pentium timestamp counter
    Config('WITH_TSC'),

    # Define to 1 if your processor stores words with the most significant byte
    # first (like Motorola and SPARC, unlike Intel and VAX).
    Config('WORDS_BIGENDIAN'),

    # Define if arithmetic is subject to x87-style double rounding issue
    Config('X87_DOUBLE_ROUNDING'),

    # Define on OpenBSD to activate all library features
    Config('_BSD_SOURCE'),

    # Define on Darwin to activate all library features
    Config('_DARWIN_C_SOURCE', osx=1),

    # This must be set to 64 on some systems to enable large file support.
    Config('_FILE_OFFSET_BITS', osx=64),

    # Define on Linux to activate all library features
    Config('_GNU_SOURCE', osx=1),

    # Define to include mbstate_t for mbrtowc
    Config('_INCLUDE__STDC_A1_SOURCE'),

    # This must be defined on some systems to enable large file support.
    Config('_LARGEFILE_SOURCE', osx=1),

    # Define on NetBSD to activate all library features
    Config('_NETBSD_SOURCE', osx=1),

    # Define to 2 if the system does not provide POSIX.1 features except with
    # this defined.
    Config('_POSIX_1_SOURCE'),

    # Define to activate features from IEEE Stds 1003.1-2008
    Config('_POSIX_C_SOURCE'),

    # Define to 1 if you need to in order for `stat' and other things to work.
    Config('_POSIX_SOURCE'),

    # Define if you have POSIX threads, and your system does not define that.
    Config('_POSIX_THREADS'),

    # Define to force use of thread-safe errno, h_errno, and other functions
    Config('_REENTRANT', osx=1),

    # Define to the level of X/Open that your system supports
    Config('_XOPEN_SOURCE'),

    # Define to activate Unix95-and-earlier features
    Config('_XOPEN_SOURCE_EXTENDED'),

    # Define on FreeBSD to activate all library features
    Config('__BSD_VISIBLE', osx=1),

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


def generate_pyconfig_h(pyconfig_h_name, target):
    """ Create the pyconfig.h file for a specific target variant. """

    pyconfig_h = create_file(pyconfig_h_name)

    for config in pyconfig:
        value = config.value(target)

        if value is None:
            # We provide an commented out #define to make it easier to modify
            # the file by hand later.
            pyconfig_h.write('/* #define {0} */\n'.format(config.name))
        else:
            pyconfig_h.write('#define {0} {1}\n'.format(config.name, value))

    pyconfig_h.close()
