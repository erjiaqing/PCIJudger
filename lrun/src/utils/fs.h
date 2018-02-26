////////////////////////////////////////////////////////////////////////////////
// Copyright (C) 2012-2015 Jun Wu <quark@zju.edu.cn>
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <fcntl.h>
#include <string>
#include <map>
#include <list>
#include <sys/stat.h>
#include <sys/mount.h>
#include <unistd.h>

// If kernel does not support shared mount, MS_{REC,PRIVATE,SHARED} are missing
#ifndef MS_REC
# define MS_REC 0
#endif

#ifndef MS_SHARED
# define MS_SHARED 0
#endif

#ifndef MS_PRIVATE
# define MS_PRIVATE 0
#endif

#ifndef MS_SLAVE
# define MS_SLAVE 0
#endif

#ifndef MS_RELATIME
# define MS_RELATIME 0
#endif

namespace fs {
    /**
     * Path separator, should be '/'
     */
    extern const char PATH_SEPARATOR;

    /**
     * Path to file containing mounts information
     * Typically, it is "/proc/mounts" ("/etc/mtab")
     */
    extern const char * const MOUNTS_PATH;
    extern const char * const PROC_PATH;

    /**
     * Cgroup filesystem type name: "cgroup"
     */
    extern const char * const TYPE_CGROUP;

    /**
     * tmpfs type name: "tmpfs"
     */
    extern const char * const TYPE_TMPFS;

    /**
     * Join path
     * @param  dirname      directory path
     * @param  basename     file name, can contain separator
     * @return joined path
     */
    std::string join(const std::string& dirname, const std::string& basename);

    std::string dirname(const std::string& path);
    std::string basename(const std::string& path);
    std::string extname(const std::string& path);

    bool is_absolute(const std::string& path);
    bool is_disconnected(const std::string& path);
    bool is_dir(const std::string& path);
    bool is_regular_file(const std::string& path);
    bool is_symlink(const std::string& path);
    bool is_fd_valid(int fd);

    /**
     * List directory, return basenames
     */
    std::list<std::string> list(const std::string& path);

    /**
     * see man 'glob'
     */
    std::list<std::string> glob(const std::string& pattern);

    /**
     * Expand a path. Do not follow symbol links.
     * @param  path         path to expand
     * @return path         expanded path
     */
    std::string expand(const std::string& path);

    /**
     * Follow symbolic links, recursively
     * @param  path         path to resolve
     * @return path         resolved path
     *         ""           error happened. ex. symlink to non-exist path
     */
    std::string resolve(const std::string& path);

    /**
     * Convert absolute path to relative path
     * ex. relative_path("/a/b/c", "/a/d/e") = "../b/c"
     * @param  path         absolute path to convert (must be absolute)
     * @param  reference    reference path (must be absolute)
     * @return path         resolved relative path
     */
    std::string relative_path(const std::string& path, const std::string& reference);

    /**
     * Test access to a specified file
     * @param  path         relative or absolute path
     * @param  mode         refer to `man faccessat`
     * @param  work_dir     work dir path, used to resolve related path
     * @return 1            accessible
     *         0            otherwise
     */
    bool is_accessible(const std::string& path, int mode = F_OK, const std::string& work_dir = "");

    /**
     * Write string content to file
     * @param  path         file path
     * @param  content      content to write
     * @return  0           success
     *         -1           file can not open
     *         -2           write error (or not complete)
     */
    int write(const std::string& path, const std::string& content);

    /**
     * Read from file
     * @param  path         file path
     * @param  max_length   max length to read (not include '\0')
     * @return string       content read, empty if failed
     */
    std::string read(const std::string& path, size_t max_length = 1024);

    /**
     * mkdir -p
     * @param  dir          dir
     * @param  mode         dir mode
     * @return >=0          the count of directories maked
     *          -1          error
     */
    int mkdir_p(const std::string& dir, const mode_t mode = 0755);

    /**
     * rm -rf
     * @param  path         path
     * @return  0           success
     *         -1           error
     */
    int rm_rf(const std::string& path);

    /**
     * chmod
     * @return  0           success
     *         -1           failed
     */
    int chmod(const std::string& path, const mode_t mode);

    /**
     * mount -o remount
     * @param   dest        target path
     * @param   flags       mount flags
     * @reutrn  0           success
     *         -1           failed
     */
    int remount(const std::string& dest, unsigned long flags);

    /**
     * mount --bind -o nosuid
     * @param   src         source location
     * @param   dest        target path
     * @reutrn  0           success
     *         -1           failed
     */
    int mount_bind(const std::string& src, const std::string& dest);

    /**
     * mount -t tmpfs
     * @param   dest        target path
     * @param   max_size    size in bytes, note that this can be rounded to block size
     * @reutrn  0           success
     *          other       failed
     */
    int mount_tmpfs(const std::string& dest, size_t max_size, mode_t mode = 0777);

    /**
     * mount --make-*
     * @param   dest        target path
     * @param   type        (MS_SLAVE | MS_PRIVATE | MS_SHARED) | [MS_REC]
     * @return  0           success
     *          other       failed
     */
    int mount_set_shared(const std::string& dest, int type = MS_SLAVE);

    /**
     * umount
     * @param   dest        target path
     * @parm    lazy        true: MNT_DETACH
     * @return  0           success
     *         -1           fail
     */
    int umount(const std::string& dest, bool lazy = true);

    struct MountEntry {
        std::string type;
        std::string opts;
        std::string fsname;
        std::string dir;
    };

    std::map<std::string, MountEntry> get_mounts();

    std::string get_mount_point(const std::string& path);

    class ScopedFileLock {
        public:
            ScopedFileLock(const char path[]);
            ~ScopedFileLock();
        private:
            int fd_;
    };
}

