================================
 HADK FAQ
================================

:abstract: FAQ for Sailfish OS porting guide (HADK)

.. contents:: Table of Contents
.. section-numbering::

Useful hints
============

Skip tutorial
-------------

Congratulations if you have got gui working. During the debugging process you will be building and flashing quite a few times, in which tutorial during the setup screen can be annoying. You can skip that by tapping on the each corner of the screen clockwise, while starting from left-top corner.

Monitoring udev events
----------------------

- udevadm monitor is your friend.
- To get it for cyanogenmod, add this repository https://github.com/chombourger/android-udev/ to your manifest as external/usb and make udevadm
- To monitor boot-time events, compile the kernel with CONFIG_DEBUG_KOBJECT=y and increase the log buffer size by setting the kernel command line option: log_buf_len=21 (or higher)

Persistent journalctl
---------------------

- Modify /etc/systemd/journald.conf

  - Storage=volatile --> Storage=automatic
  - mkdir /var/log/journal
  - Reboot

- Systemd suppresses journal, and some valuable info might get hidden. To prevent this, set

  - RateLimitInterval=0

Build issues
============

Updating local build target
---------------------------

- Change release version in the command if needed
- In Platform SDK::

    sb2 -t $VENDOR-$DEVICE-$PORT_ARCH -m sdk-install -R ssu release 2.1.4.14
    sb2 -t $VENDOR-$DEVICE-$PORT_ARCH -m sdk-install -R zypper ref
    sb2 -t $VENDOR-$DEVICE-$PORT_ARCH -m sdk-install -R zypper dup

Updating submodules
-------------------

- Submodule locations::

    rpm/dhd
    hybris/droid-configs/droid-configs-device
    hybris/droid-hal-version-$DEVICE/droid-hal-version

- In the each folder check remote name using::

    git remote -v

- Run (replace remote_name with the name you found out in previous step)::

    git fetch remote_name
    git pull remote_name master

rpm/dhd/helpers/build_packages.sh fails building libhybris, ...
---------------------------------------------------------------

- HOST$::

    cd $HOME
    sudo mkdir -p $MER_ROOT/devel
    sudo chown -R $USER mer/devel

- Run the script again

Repo init fails because of gpg
-------------------------------

- In sdk chroot gpg command is gpg2::

    $MERSDK
    git config --global gpg.program gpg2

Nothing provides /system/bin/sh
-------------------------------
- Add this to your .spec::

    %define __provides_exclude_from ^/system/.*$
    %define __requires_exclude ^/system/bin/.*$
    %define __find_provides %{nil}
    %define __find_requires %{nil}

Existence_error (yes, you read that right) when locally building policy-settings-common
---------------------------------------------------------------------------------------

- You get:
    ERROR: error(existence_error(procedure, qsave_program/2), context(precompile/0, _G669))

- Solution::
    sb2 -t $VENDOR-$DEVICE-armv7hl -R -msdk-install
    cd /usr/lib/swipl-5.6.50/library
    rm INDEX.pl
    zypper in fakeroot
    fakeroot swipl -g true -t 'make_library_index(.)'
- then rebuild the package again with mb2

make[3]: [security/commoncap.o] Error 1
-------------------------------------------

- Those errors appears because ANDROID_CONFIG_PARANOID_NETWORK is disabled in your kernel and with it enabled, you can't access internet with Sailfish OS. ( Since hybris-12.1, rild does not work without ANDROID_CONFIG_PARANOID_NETWORK. Add nemo to group inet if it is enabled.)
- Check http://forum.xda-developers.com/showpost.php?p=42880275&postcount=104
- To resolve this replace in <path of your kernel>/security/commoncap.c::

    if (cap == CAP_NET_RAW && in_egroup_p(AID_NET_RAW))
        return 0;
    if (cap == CAP_NET_ADMIN && in_egroup_p(AID_NET_ADMIN))
        return 0;

- With this::

    #ifdef CONFIG_ANDROID_PARANOID_NETWORK
           if (cap == CAP_NET_RAW && in_egroup_p(AID_NET_RAW))
               return 0;
           if (cap == CAP_NET_ADMIN && in_egroup_p(AID_NET_ADMIN))
               return 0;
    #endif

- Save the file and recompile the kernel

Building droid-config fails with: Segmentation fault      (core dumped) /usr/lib/qt5/bin/kmap2qmap
--------------------------------------------------------------------------------------------------

- Try updating the packages in the target with::

    sb2 -t $VENDOR-$DEVICE-armv7hl -R -m sdk-install zypper ref
    sb2 -t $VENDOR-$DEVICE-armv7hl -R -m sdk-install zypper dup

libdsyscalls is cause of segfault after lipstick or minimer
-----------------------------------------------------------

- Usually means that in your device repo, its enabling clang somewhere, do a grep and disable clang and rebuild :)

Issues with ngfd or ngfd-plugin-droid or pulseaudio
---------------------------------------------------

- Update submodules as described above
- Replace %define have_vibrator 1 in droid-hal-version-@DEVICE@.spec with %define have_vibrator_native 1
- Change package names in droid-configs patterns as described in templates https://github.com/mer-hybris/droid-hal-configs/commit/aac652aae840a15629c0f4e070275ea128fe088f
- in PLATFORM_SDK::

   sb2 -t $VENDOR-$DEVICE-$PORT_ARCH -m sdk-install -R zypper rm ngfd-plugin-droid-vibrator
   rpm/dhd/helpers/build_packages.sh

No installroot directory after droid-configs build when preparing .ks file
--------------------------------------------------------------------------

- rpm2cpio droid-local-repo/$DEVICE/droid-configs/droid-config-$DEVICE-ssu-kickcdstarts-1-1.armv7hl.rpm | cpio -idmv
- In the sed command use $ANDROID_ROOT/usr/share/kickstarts/$KS instead of $ANDROID_ROOT/hybris/droid-configs/installroot/usr/share/kickstarts/$KS


No rule to make target kernel needed by boot.img or similar error
-----------------------------------------------------------------

- Open device/$VENDOR/$DEVICE/BoardConfig.mk
- Comment out the lines::

    TARGET_KERNEL_SOURCE
    TARGET_KERNEL_PREBUILT

- Common error in hybris10.1 due to the old CM10.1 kernels and how they were built back then.

Migrate patterns to meta-packages
---------------------------------

Sailfish OS 3.4.0 is the last version where patterns are still supported.

If you're still using patterns (i.e. you still have ``$ANDROID_ROOT/hybris/droid-configs/patterns/jolla-hw-adaptation-$DEVICE.yaml``), the next Sailfish OS release will cause error when trying to build a flashable image for your port:

``Error <creator>[01/28 07:26:14] : Unable to find package: patterns-sailfish-device-configuration-$DEVICE``

To fix, migrate patterns to meta-packages with this helper script from the droid-configs submodule:

.. code-block:: bash

  PLATFORM_SDK $

  cd $ANDROID_ROOT
  cd hybris/droid-configs/droid-configs-device
  git fetch origin master
  git checkout master
  cd ..
  droid-configs-device/helpers/migrate_patterns.sh

Check the changes with ``git status; git diff``, commit when happy. The end result will be similar to https://github.com/mer-hybris/droid-config-sony-ganges-pie/pull/62.

If the script fails, comment out the offending patterns until it succeeds. Convert the failed patterns manually as shown in the sub-section below.

Lastly, update your ``droid-hal-version`` submodule to have this change https://github.com/mer-hybris/droid-hal-version/pull/18, which ensures your existing users also switch to meta-packages when they upgrade from 3.4.0 to newer releases.

If all of the above looks daunting, there should be someone to guide you through at the #sailfishos-porters IRC channel.

Alternatively, if you haven't gone too far into your port yet and/or haven't released it, you could restart porting from scratch (the ``add_new_device.sh`` script and the templates will initialise device repos to use meta-packages already).

Converting manually
~~~~~~~~~~~~~~~~~~~

The conversion is pretty straightforward. Let's assume the contents of the ``patterns/my-extra-tools.yaml`` file:

.. code-block:: yaml

  Description: My extra tools for porting
  Name: my-extra-tools
  Requires:
  - pattern:my-other-helpers
  - valgrind
  - my-custom-debugger
  - my-test-suite

  Summary: My extra tools

becomes a section in your ``.spec`` (or ``patterns/my-extra-tools.inc`` which then gets included into ``.spec``):

.. code-block:: spec

  %package -n patterns-sailfish-device-my-extra-tools
  Summary: My extra tools
  Requires: patterns-sailfish-device-my-other-helpers
  Requires: valgrind
  Requires: my-custom-debugger
  Requires: my-test-suite

  %description -n patterns-sailfish-device-my-extra-tools
  My extra tools for porting

  %files -n patterns-sailfish-device-my-extra-tools

Android base specific fixes
===========================

hybris-14.1
-----------

- If NINJA builds are not working, export USE_NINJA=false
- Run this script in $ANDROID_ROOT http://paste.opensuse.org/40869869

Details of what the script does::

  Symlinks for services: ::sh-3.2# ls -lh /usr/libexec/droid-hybris/system/etc/init/
  total 4.0K
  lrwxrwxrwx 1 root root   26 Oct  6 20:52 atrace.rc -> /system/etc/init/atrace.rc
  lrwxrwxrwx 1 root root   28 Oct  6 20:52 bootstat.rc -> /system/etc/init/bootstat.rc
  lrwxrwxrwx 1 root root   29 Oct  6 20:52 debuggerd.rc -> /system/etc/init/debuggerd.rc
  lrwxrwxrwx 1 root root   29 Oct  6 20:52 drmserver.rc -> /system/etc/init/drmserver.rc
  lrwxrwxrwx 1 root root   29 Oct  6 20:52 dumpstate.rc -> /system/etc/init/dumpstate.rc
  lrwxrwxrwx 1 root root   31 Oct  6 20:52 gatekeeperd.rc -> /system/etc/init/gatekeeperd.rc
  lrwxrwxrwx 1 root root   30 Oct  6 20:52 init-debug.rc -> /system/etc/init/init-debug.rc
  lrwxrwxrwx 1 root root   28 Oct  6 20:52 installd.rc -> /system/etc/init/installd.rc
  lrwxrwxrwx 1 root root   27 Oct  6 20:52 logcatd.rc -> /system/etc/init/logcatd.rc
  lrwxrwxrwx 1 root root   24 Oct  6 20:52 logd.rc -> /system/etc/init/logd.rc
  lrwxrwxrwx 1 root root   30 Oct  6 20:52 mediacodec.rc -> /system/etc/init/mediacodec.rc
  lrwxrwxrwx 1 root root   34 Oct  6 20:52 mediadrmserver.rc -> /system/etc/init/mediadrmserver.rc
  lrwxrwxrwx 1 root root   34 Oct  6 20:52 mediaextractor.rc -> /system/etc/init/mediaextractor.rc
  lrwxrwxrwx 1 root root   24 Oct  6 20:52 mtpd.rc -> /system/etc/init/mtpd.rc
  lrwxrwxrwx 1 root root   29 Oct  6 20:52 perfprofd.rc -> /system/etc/init/perfprofd.rc
  lrwxrwxrwx 1 root root   26 Oct  6 20:52 racoon.rc -> /system/etc/init/racoon.rc
  lrwxrwxrwx 1 root root   24 Oct  6 20:52 rild.rc -> /system/etc/init/rild.rc
  lrwxrwxrwx 1 root root   29 Oct  6 20:52 superuser.rc -> /system/etc/init/superuser.rc
  lrwxrwxrwx 1 root root   27 Oct  6 20:52 uncrypt.rc -> /system/etc/init/uncrypt.rc
  lrwxrwxrwx 1 root root   23 Oct  6 20:52 vdc.rc -> /system/etc/init/vdc.rc
  lrwxrwxrwx 1 root root   23 Oct  6 20:52 vold.rc -> /system/etc/init/vold.rc

NOTE, no audioserver and mediaserver links!
NOTE, bootanim was removed in the updated script, also vold was added


hybris-15.1
-----------

- Before building hybris-hal run the following commands::

    cd $ANDROID_ROOT/external
    git clone --recurse-submodules https://github.com/mer-hybris/libhybris.git
    cd $ANDROID_ROOT

- Copy files from https://github.com/mer-hybris/droid-config-sony-nile/tree/91c15efb576c29a9d41cc4cd1d40c62ddcce9824/sparse/usr/libexec/droid-hybris/system/etc/init to your config repo (to `hybris/droid-configs/sparse/usr/libexec/droid-hybris/system/etc/init`) and rebuild config packages using :code:`rpm/dhd/helpers/build_packages.sh -c`

hybris-16.0
-----------

- Before building hybris-hal run the following commands::

    cd $ANDROID_ROOT/external
    git clone --recurse-submodules https://github.com/mer-hybris/libhybris.git
    cd $ANDROID_ROOT
    hybris-patches/apply-patches.sh --mb

- Copy files from https://github.com/sailfishos-oneplus5/droid-config-cheeseburger/tree/hybris-16.0/sparse/usr/libexec/droid-hybris/system/etc/init to your config repo (to `hybris/droid-configs/sparse/usr/libexec/droid-hybris/system/etc/init`) and rebuild config packages using :code:`rpm/dhd/helpers/build_packages.sh -c`

- When you get :code:`telnet` in the SFOS rootfs (port 2323) and can run :code:`/usr/libexec/droid-hybris/system/bin/logcat`, see if you get lines similar to below filtering the output using :code:`grep` for example::

    E linker  : library "/usr/libexec/droid-hybris/system/lib64/libselinux_stubs.so" ("/usr/libexec/droid-hybris/system/lib64/libselinux_stubs.so") needed or dlopened by "/system/bin/hwservicemanager" is not accessible for the namespace: [name="(default)", ld_library_paths="", default_library_paths="/system/lib64", permitted_paths="/system/lib64/drm:/system/lib64/extractors:/system/lib64/hw:/system/product/lib64:/system/framework:/system/app:/system/priv-app:/vendor/framework:/vendor/app:/vendor/priv-app:/odm/framework:/odm/app:/odm/priv-app:/oem/app:/system/product/framework:/system/product/app:/system/product/priv-app:/data:/mnt/expand"]
    F linker  : CANNOT LINK EXECUTABLE "/system/bin/hwservicemanager": library "/usr/libexec/droid-hybris/system/lib64/libselinux_stubs.so" needed or dlopened by "/system/bin/hwservicemanager" is not accessible for the namespace "(default)"
    E linker  : library "/usr/libexec/droid-hybris/system/lib64/libselinux_stubs.so" ("/usr/libexec/droid-hybris/system/lib64/libselinux_stubs.so") needed or dlopened by "/system/bin/servicemanager" is not accessible for the namespace: [name="(default)", ld_library_paths="", default_library_paths="/system/lib64", permitted_paths="/system/lib64/drm:/system/lib64/extractors:/system/lib64/hw:/system/product/lib64:/system/framework:/system/app:/system/priv-app:/vendor/framework:/vendor/app:/vendor/priv-app:/odm/framework:/odm/app:/odm/priv-app:/oem/app:/system/product/framework:/system/product/app:/system/product/priv-app:/data:/mnt/expand"]
    F linker  : CANNOT LINK EXECUTABLE "/system/bin/servicemanager": library "/usr/libexec/droid-hybris/system/lib64/libselinux_stubs.so" needed or dlopened by "/system/bin/servicemanager" is not accessible for the namespace "(default)"
    E linker  : library "/usr/libexec/droid-hybris/system/lib64/libselinux_stubs.so" ("/usr/libexec/droid-hybris/system/lib64/libselinux_stubs.so") needed or dlopened by "/vendor/bin/vndservicemanager" is not accessible for the namespace: [name="(default)", ld_library_paths="", default_library_paths="/vendor/lib64", permitted_paths="/odm:/vendor"]
    F linker  : CANNOT LINK EXECUTABLE "/vendor/bin/vndservicemanager": library "/usr/libexec/droid-hybris/system/lib64/libselinux_stubs.so" needed or dlopened by "/vendor/bin/vndservicemanager" is not accessible for the namespace "(default)"

  - If you don't and :code:`systemctl status droid-hal-init` returns :code:`active (running)` you can skip the below steps.
  - Copy https://github.com/sailfishos-oneplus5/droid-config-cheeseburger/blob/hybris-16.0/sparse/usr/libexec/droid-hybris/system/etc/ld.config.28.txt and https://github.com/sailfishos-oneplus5/droid-config-cheeseburger/blob/hybris-16.0/sparse/lib/systemd/system/system-etc-ld.config.28.txt.mount to your droid-config sparse files.
  - Create the following symlink in your droid-config sparse files: https://github.com/sailfishos-oneplus5/droid-config-cheeseburger/blob/hybris-16.0/sparse/lib/systemd/system/local-fs.target.wants/system-etc-ld.config.28.txt.mount
  - Rebuild config packages using :code:`rpm/dhd/helpers/build_packages.sh -c` and install the first new droid-config RPM package from :code:`$ANDROID_ROOT/droid-local-repo/$DEVICE/droid-configs/` on your device using :code:`zypper`, or :code:`rpm/dhd/helpers/build_packages.sh -i` and flash the new zip.

hybris-17.1
-----------

- Apply patches as on hybris-16 but from the ``hybris-17.1`` branch
- You need to export ``TEMPORARY_DISABLE_PATH_RESTRICTIONS=true`` before building android part otherwise hybris-boot.img will not include hybris initramfs
- Do not disable selinux, set it to 1 from kernel cmdline and make it permissive
- Add to sparse: https://github.com/mer-hybris/droid-config-sony-seine/tree/eaa09db67b94352ef801417363008dc4005d9213/sparse/etc/selinux. You may need to replace symlinks with the actual files from your device.
- Add ``'%define android_version_major 10'`` to droid-config-$DEVICE.spec




Graphics
========

Lipstick segfaults/no display
-----------------------------

- As you follow steps below, strace any of the binaries that would fail for non-obvious reasons. You'll need to install strace to do so: zypper in strace
- test simple hwc as root:t

  - EGL_PLATFORM=hwcomposer test_hwcomposer
  - ^^ strace if segfaults
- if strace dies after open("/sys/kernel/debug/tracing/trace_marker..., perform

  - systemctl mask sys-kernel-debug.mount
- test_hwcomposer should not be used as reliable hwc test!! if fails, then try minimer:

  - curl -O https://qtl.me/minimer3.tar.gz # seems to currently give  404, the archive is mirrored at https://1drv.ms/u/s!AuDqiTFly4jxgxYNUdt16YluZn90
  - zypper in qt5-qtdeclarative-qmlscene
  - tar -xf minimer3.tar.gz; cd minimer
  - EGL_PLATFORM=hwcomposer /usr/lib/qt5/bin/qmlscene -platform hwcomposer main.qml
  - if fails as user, try as root
  - /system/bin/surfaceflinger", R_OK) = -1 ENOENT (No such file or directory)
- for more info: zypper in gdb

  - if you get test_hwcomposer, minimer or lipstick segfault, or test_hwcomposer or minimer running but doing nothing (as on m7)
  - Check if your device uses qcom_display-caf or display-legacy
  - Look in any of the BoardConfig.mk or BoardConfigCommon.mk in any of the device repos for the device for the variable TARGET_QCOM_DISPLAY_VARIANT. It should be set to either caf or legacy.
  - The repos included can be determined by looking at the -include device/$VENDOR/*/BoardConfig.mk or device/$VENDOR/*/BoardConfigCommon.mk lines at beginning the .mk files starting from the primary BoardConfig.mk
  - If you're on display-legacy or display-caf(repo sync before 2015.06.04) patch hwcomposer withhttp://pastebin.com/AfRXPKVA
  - From HABUILD_SDK recompile android hwcomposer*.so for your device

    * Find the name of the hwcomposer*.so module: run make modules | grep hwcomposer
    * If this command complains about missing column command run sudo apt-get install bsdmainutils)
    * Run `make hwcomposer.module_name` from results above
  - Once rebuilt, hwcomposer.*.so will be picked up and used by droid hal rebuild, and reside under /usr/libexec/droid-hybris/system/lib/hw
  - If your apps are crashing (like on flo): Repeat the same for gralloc and copybit
  - Scream on the IRC if this worked for you
- If strace indicates something like:

- "Waiting for service display.qservice..."

  - This error is known only on cm-10.1 base, and will be upstreamed to mer-hybris soon, but we need more tests: applyhttps://github.com/mer-hybris/android_frameworks_native/commit/6ed4a6e834f6c71b2b6bd8ae1134f50b060e70be to this line https://github.com/CyanogenMod/android_frameworks_base/blob/cm-10.1/cmds/servicemanager/service_manager.c#L88 and also apply https://github.com/mer-hybris/android_system_core/commit/34ea48fd3ad7bf47ec0d0524d76bd20e62717773
  - open("/sys/kernel/debug/tracing/trace_marker", O_WRONLY|O_LARGEFILE) =
  - disable debugfs by: https://github.com/mer-hybris/droid-hal-device/commit/8d437fc6f215081d4e1d2baaa6ac23bb94f73154
  - if it still crashes on gralloc or other gpu related bits, refer to WIP: https://wiki.merproject.org/wiki/Adaptations/libhybris/gpu


BOARD_USES_QCOM_HARDWARE is not in vendor device repo
-----------------------------------------------------

- On some Qualcomm devices QCOM hardware detection script fails to find needed define from device repos
- Add the following lines to rpm/droid-hal-$DEVICE.spec before the line "%include rpm/dhd/droid-hal-device.inc" (do not change that line or add anything after it)::

    %define android_config \
    #define QCOM_BSP 1\
    #define QTI_BSP 1\
    %{nil}

- Rebuild packages with build_packages.sh

Devices with Mali GPU
---------------------

- Add this to $ANDROID_ROOT/rpm/droid-hal-$DEVICE.spec before the last line (do not change the last line, ever)::

    %define android_config \
    #define MALI_QUIRKS 1\
    %{nil}

- Rebuild droid-hal and libhybris packages::

    sudo mount -i -o remount,suid $HOME)

Graphics performance improvements
---------------------------------

- Test framerate display (can be enabled in Settings->Developer mode) when using some apps like gallery
- If the top view is mostly red try to set QPA_HWC_IDLE_TIME=5 in /var/lib/environment/compositor/droid-hal-device.conf
- Run systemctl restart user@100000 using devel-su
- Test framerate display again and if you see more green than before you should use the value
- Different values can be tested but value 5 has been found to be helping on some devices
- On some devices also setting QPA_HWC_BUFFER_COUNT=3 in /var/lib/environment/compositor/droid-hal-device.conf helps with graphics performance

Black gallery pictures and no browser content/browser crash:
------------------------------------------------------------

Add this to droid-hal .spec file (before the last line, never change the last line in the spec file) and rebuild droid-hal and libhybris packages (remove the sources from hybris/mw/libhybris to make sure a clean rebuild is done)::

  %define android_config \
  #define WANT_ADRENO_QUIRKS 1\
  %{nil}

To change pixel ratio on a running device, as user
--------------------------------------------------

devel-su dconf update

# PIXEL_RATIO should be close to the value of horizontal_display_resolution/540
# e.g. Nexus 7 (800 x 1280) displays the pixel ratio is 800/540~=1.48
# always round the value up with two decimal precision

PIXEL_RATIO=1.48

# UPDATE! Please test the new formula for pixel ratio calculation:
# diagonal_display_size_inches/4.5 * horizontal_display_resolution/540
# and feedback the outcome to sledges via IRC (better/worse/closer via own trial&error picks?)
# Yet another formula: YourDevicePPI/sbjPPI (245), e.g. OnePlusX PPI 441/245 = 1.8
# Available ICON_RES values are 1.0, 1.25, 1.5, 1.75, and 2.0. Choose the closest one to

PIXEL_RATIO:
ICON_RES=1.5
devel-su zypper in sailfish-content-graphics-default-z$ICON_RES
dconf write /desktop/sailfish/silica/theme_pixel_ratio $PIXEL_RATIO
dconf write /desktop/sailfish/silica/theme_icon_subdir \"z$ICON_RES\"

# check that everything worked:

dconf read /desktop/sailfish/silica/theme_pixel_ratio
devel-su reboot

# PIXEL_RATIO and ICON_RES are subjects to fine tuning: https://bugs.nemomobile.org/show_bug.cgi?id=814#c1

Script to scale your icons https://pastebin.com/mxKRkt7Z

Touchscreen
===========

Determine which is the touch event
----------------------------------

- Install mce-tools on device and monitor output of `evdev_trace -t`
- Use command "getevent" as super user in adb shell. The event which spams most outputs on the screen when the screen is touched is the touch event.

Touchscreen problems / erratic behaviour
----------------------------------------

- Try the evdev plugin instead of the evdevtouch plugin in droid-hal-device.conf

WLAN
====

Build Wlan Driver as Module
---------------------------

- Most devices require the wlan driver to be built and loaded as a module during startup
- Ensure you have CONFIG_MODULES=y in your kernel config

- Find your wifi driver in your kernel config, it should already be set to `y` and have something like WLAN in the name.
- Set it to m, e.g.::

    CONFIG_BCMDHD=m
    CONFIG_PRIMA_WLAN=m
    CONFIG_PRONTO_WLAN=m

- Add the wlan-module-load.service to your droid-configs sparse directory

  - https://github.com/mer-hybris/droid-config-onyx/blob/master/sparse/lib/systemd/system/wlan-module-load.service

- And add a symlink to enable to service on startup

  - https://github.com/mer-hybris/droid-config-onyx/blob/master/sparse/lib/systemd/system/multi-user.target.wants/wlan-module-load.service

BCMDHD WLAN Driver sleep/suspend issues
---------------------------------------

- This is based on experience using the bcmdhd driver on the Xiaomi MiPad 2 (latte) device.
- The original driver would connect to networks ok, but then fail after the device tried to sleep.  This was resolved by doing the following:

  - Updating to a newer driver from Import new bcmdhd driver from https://github.com/sonyxperiadev/kernel.git branch aosp/LE.UM.2.3.2.r1.4
  - Adding features specific to the latte device (ACPI) to the newer driver

- This resulted in a working driver, but which failed to sleep/suspend.  The new driver has many config options in the makefile, 2 specific ones seemed responsible for the behaviour: DHD_PCIE_RUNTIMEPM and CONFIG_HAS_WAKELOCK

  - The driver has a config option for supporting runtime power management, the runtime PM rarely (never?) goes into a sleep state becuase of a wakelock
  - The wakelock also prevents mem sleep
  - There is a also a config option for wakelocks, so, turning off wakelocks and runtime PM allows sleeping which all seems a little counter intuitive!

- See https://github.com/piggz/android_kernel_xiaomi_latte/commits/hybris-13.0-latte-bcmdhd

Audio
=====

Audio not routed to headphones
------------------------------

Run evdev_trace from mce-tools package and find /dev/input/eventX that detects headphones connection. It will be the one with SW_HEADPHONE_INSERT*  and SW_MICROPHONE_INSERT* like here::

  ----====( /dev/input/event0 )====----
  Name: "sensorprocessor"
  ID: bus 0x0, vendor, 0x0, product 0x0, version 0x0
  Type 0x00 (EV_SYN)
  Type 0x01 (EV_KEY)
           KEY_VOLUMEDOWN KEY_VOLUMEUP KEY_POWER KEY_CAMERA KEY_MEDIA KEY_VOICECOMMAND
  Type 0x05 (EV_SW)
           SW_LID SW_HEADPHONE_INSERT* SW_MICROPHONE_INSERT*

Add this https://github.com/mlehtima/droid-config-fp2-sibon/blob/master/sparse/etc/ohm/plugins.d/accessories.ini file and replace jack-match and jack-device with values from evdev_trace:

- `jack-match` matches Name: field
- `jack-device` matches /dev/input/eventX, where X is your device input number

Optional way for devices without headphone connector event device:

- If your device doesn't have event device for the headphone jack then it might have a switch in /sys/class/switch/h2w/ or similar path
- If the state file in the  /sys/class/switch/h2w/ or similar path reacts to headphone connection by changing the value it can be used for headphone detection
- Add file /etc/ohm/plugins.d/accessories.ini with the following content (replace switch name with the name found in the path on your device)::

    model = uevent
    switch = h2w

- If the headphone detection works then add the file to your config repo sparse for future builds

Sensors
=======

Enabling the various hw settings for device (fixing sensors in latest builds and autobrightness toggle):

- If your device has broken sensors after updating to latest SailfishOS version or if your autobrightness toggle doesn't appear in settings, it is due to hw-settings.ini missing for device (light sensor is not declared in the configs and that's why Autobrightness option is not enabled in jolla-settings)
- Use this as a reference https://github.com/mer-hybris/droid-config-f5121/blob/master/sparse/usr/share/csd/settings.d/hw-settings.ini and make changes accordingly.
- When satisfied, make a copy of the file to `$ANDROID_ROOT/hybris/droid_configs/sparse/usr/share/csd/settings.d/`  and git commit !

Telephony (ofono/RIL)
=====================

RILD is running but ofono does not work
---------------------------------------

If ofono is not working properly and shows :code:`"ERROR! Can't connect to RILD: No such file or directory"` in logs, edit `/etc/ofono/ril_subscription.conf` to contain::

  [ril_0]
  name=RIL1
  socket=/dev/socket/rild

Dual SIM devices
-------------------------

Add the jolla-settings-networking-multisim to patterns like done here https://github.com/mlehtima/droid-config-fp2-sibon/blob/master/patterns/jolla-configuration-fp2-sibon.yaml#L15

If your device is dual SIM, add also these lines (don't add them otherwise!)::

  [ril_1]
  name=RIL2
  socket=/dev/socket/rild2

Or for hybris-15.1 or higher devices (e.g. OnePlus 5/5T/6)::

  [ril_1]
  transport=binder:name=slot2
  name=slot2

- If it works add your `ril_subscription.conf` to the `droid-config-$DEVICE` like done here https://github.com/Nokius/droid-config-find5/commit/3e3e636e7e3973f9102ebca9dea79794c00c9174
- Fix remembering manual access point configurations across reboots run the following command before building the image::

    sed -i "/begin 60_ssu/a chown -R radio:radio /var/lib/ofono" Jolla-@RELEASE@-$DEVICE-@ARCH@.ks

Devices without modem
---------------------

- File `/etc/ofono/ril_subscription.conf` should contain::

    [Settings]
    EmptyConfig=true

SIM card not detected
---------------------

- This often causes a bootloop
- Cellular Modem bringup is now in HADK v1.1.1 section 13.3
- Additional checks:
- Replicate /dev/block structure from Android as closely as possible (for rild to be able to access the modem partition)

  - Run ls -lR /dev/block in CM
  - Run ls -lR /dev/block in Sailfish OS
  - diff the two outputs (this is WIP - android's toolbox ls might need more parameters to produce a comparable output)
- If you see differences you need to add custom udev rules to create the correct /dev/block structure
- (added automatically since 2016-12-10) For devices with /dev/block/platform/msm_sdcc.1/by-name/ paths (msm_sdcc.1 can be different) add to $ANDROID_ROOT/rpm/ these paths and files with contents, and it most probably will help (but still paste your diff to the IRC channel):

  - https://github.com/mer-hybris-kis3/droid-config-kis3/blob/master/sparse/lib/udev/platform-device
  - https://github.com/mer-hybris-kis3/droid-config-kis3/blob/master/sparse/lib/udev/rules.d/998-droid-system.rules
- (added automatically since 2017-06-03) Some devices (at least all hybris-13.0 based ports) have /dev/block/bootdevice/by-name/ as /dev/block structure in CM in which case you need to add the following line to the end of the 998-droid-system.rules file in the last link::

    ENV{ID_PART_ENTRY_SCHEME}=="gpt", ENV{ID_PART_ENTRY_NAME}=="?*", IMPORT{program}="/bin/sh /lib/udev/platform-device $env{DEVPATH}", SYMLINK+="block/bootdevice/by-name/$env{ID_PART_ENTRY_NAME}"
- If you have logcat and journal error messages suggesting that RIL/ofono can't power the modem on and you have a qcom chipset, have a look in your init.qcom.rc for lines that power it on when the boot animation (bootanim) stops. If you have those, try this (paths may need correcting): https://github.com/stephgosling/android_device_htc_m7-common/commit/9f4abdca65356090e6dd6f0356c5cf4a1870aa5f (note the typo there in the chown line!)
- If you have pil-q6v5-mss fc880000.qcom,mss: modem: Failed to locate modem.mdt in your dmesg then try this steps:

  - Mask firmware.mount
  - add this service to /lib/systemd/system/ https://pastebin.com/9tbUtVnC
  - create symlink to that service in /lib/systemd/system/local-fs.target.wants/
  - add /usr/bin/droid/extract_firmware.sh with this content https://pastebin.com/bgphKn4z

Bluetooth
=========

Fix remembering Bluetooth state on reboot
-----------------------------------------

- Add this https://github.com/mlehtima/droid-config-fp2-sibon/commit/265310c24e254ba102211b6ea398f9ef2b68d523

Devices with binderized Bluetooth (Android 8.1/LineageOS 15.1 or newer)
-----------------------------------------------------------------------

- Not available on all Android 8.1+ devices especially if device was originally using older Android base
- Enable CONFIG_BT_HCIVHCI=y in kernel defconfig, rebuild kernel and repackage droid-hal
- Add bluebinder to patterns and rebuild config packages


Qualcomm devices (Android 7 (Lineage 14.1) or older)
----------------------------------------------------

- Enable CONFIG_BT_HCISMD in the kernel defconfig. If it is not present in your kernel, then make these changes (https://github.com/adeen-s/android_kernel_cyanogen_msm8916/commit/4627f4f6f5d886433ff1f9639dc18fe8a006fd00 )
- Add these files to sparse (or directly to device) and modify them as needed for your device -->
- https://github.com/adeen-s/droid-config-wt88047/blob/master/sparse/usr/bin/droid/droid-hcismd-up.sh
- https://github.com/adeen-s/droid-config-wt88047/blob/master/sparse/lib/systemd/system/droid-hcismd-up.service
- https://github.com/adeen-s/droid-config-wt88047/blob/master/sparse/lib/systemd/system/bluetooth.service.wants/droid-hcismd-up.service
- Bluetooth Should now work. If it doesn't then make sure the permissions are set correctly and all paths mentioned in above files point to valid locations.
- If you are still having trouble, check to see if there is a service that configures bluetooth and disable/comment it.  Eg, config_bluetooth in init.qcom.rc

Using backported Bluetooth drivers in 3.4 kernel for devices with Qualcomm bluetooth chip using hci_smd driver
---------------------------------------------------------------------------------------------------------------

- Generic guide: https://bluez-android.github.io/#building-own-kernel
- Sailfish specific guide:
- Build your kernel with patches from https://github.com/bluez-android/misc/tree/master/patches-kernel and with following flags defined in defconfig::

    CONFIG_BT=m
    CONFIG_CRYPTO_CMAC=y
    CONFIG_CRYPTO_USER_API=y
    CONFIG_CRYPTO_USER_API_HASH=y
    CONFIG_CRYPTO_USER_API_SKCIPHER=y

- NOTE: Patches may not be required for >= 3.18
- In your local_manifest, add::

    <project name="mlehtima/backports-bluetooth" path="external/backports-bluetooth" revision="master" />
- run repo sync in HABUILD_SDK
- Build backported drivers by running :code:`make backports` in HABUILD_SDK while in $ANDROID_ROOT folder
- if you get "external/backports-bluetooth/drivers/bluetooth/hci_smd.c:35:26: fatal error: mach/msm_smd.h: No such file or directory" error change
- #include <mach/msm_smd.h> to #include <soc/qcom/smd.h> in that file
- IMPORTANT: if you rerun :code:`make hybris-hal` at any time you will always have to rerun :code:`make backports` after that
- Package droid-hal as usual
- Change your config repo to use bluez5 https://github.com/mlehtima/droid-config-fp2-sibon/commit/1cba868fdcfebaffc14a084c5d82fbf2e4339173
- Rebuild config rpms and image
- Ensure that you use correct grep options, see  https://github.com/mlehtima/droid-config-fp2-sibon/commit/22023480f095d152412c74d3310388a94b049151

Broadcomm devices (Android 7 (Lineage 14.1) or older)
-----------------------------------------------------

- Enable CONFIG_BT_HCIUART_H4 in the kernel defconfig. These devices typically are attached on high speed uart to something like /dev/ttyHS0
- Symlink your firmware file to /etc/firmware.
- eg. https://github.com/r0kk3rz/droid-config-scorpion_windy/blob/master/sparse/etc/firmware/BCM4350C0.hcd
- You need to make sure the firmware symlink filename matches your bluetooth device name, which can be found by stracing hciattach
- Build rfkill middleware and add to patterns
- rpm/dhd/helpers/build_packages.sh --mw=https://github.com/mer-hybris/bluetooth-rfkill-event --spec=rpm/bluetooth-rfkill-event-hciattach.spec
- add configs: https://github.com/mer-hybris/droid-config-f5121/commit/afa01bdf4bdb8a0d16bbd34996ec7cac34bbbc55

FM radio
========

Qualcomm
--------

- Needs a device with suitable FM radio hardware and a kernel defconfig containing CONFIG_RADIO_IRIS=y (CONFIG_RADIO_IRIS=m if fail to build IRIS_TRANSPORT as module) and CONFIG_RADIO_IRIS_TRANSPORT=m (or =y)
- If your CONFIG_RADIO_IRIS_TRANSPORT is built-in then this is not needed, however if you have problems try building CONFIG_RADIO_IRIS_TRANSPORT as a module: add (adapt to fit your device if needed) https://github.com/mlehtima/droid-config-fp2-sibon/blob/master/sparse/lib/systemd/system/droid-fm-up.service and https://github.com/mlehtima/droid-config-fp2-sibon/blob/master/sparse/lib/systemd/system/bluetooth.service.wants/droid-fm-up.service
- Sometimes device permissions are wrong (root owner), in this case add https://github.com/mlehtima/droid-config-fp2-sibon/blob/master/sparse/lib/udev/rules.d/999-droid-fm.rules to your droid-configs repo (or directly to device for testing)
- Add qt5-qtmultimedia-plugin-mediaservice-irisradio to patterns (or install directly to device for testing)
- Add https://github.com/mlehtima/droid-config-fp2-sibon/blob/master/sparse/etc/pulse/xpolicy.conf.d/fmradio.conf to your droid-configs repo (or directly to device for testing)
- Starting from Sailfish OS 2.0.2 FM radio Media app plugin jolla-mediaplayer-radio can be added to patterns.

Vibrator
========

ff-memless haptics
------------------

To use memless haptics driver instead of droid-vibrator, you need a kernel haptics driver that supports a memless interface (evdev). This is briefly explained in HADK pdf chapter 13.1.

- Reference kernel driver implementation for qpnp vibrator is here;

  - https://github.com/kimmoli/android_kernel_oneplus_msm8974/pull/1
- It needs also vibrator configuration files if defaults are not ok; (this is also in HADK)
- https://github.com/kimmoli/droid-config-onyx/commit/dac479716a6b4300be3c5875982265f6914bb498
- And depends which evdev index the new ffmemless gets, one might need to change lipstick config;
- https://github.com/kimmoli/droid-config-onyx/pull/4/commits/73bb85fcdc5e2627a8cb0cea0fb5fc2ca9d8e814
- in droid-hal-version-$DEVICE.spec comment %define have_vibrator 0 out and add %define have_ffmemless 1
- Add build of qt5-feedback-haptics-ffmemless in build_packages.sh, and comment out other vibrator packages;
- buildmw "https://git.merproject.org/mer-core/qt-mobility-haptics-ffmemless.git" rpm/qt5-feedback-haptics-ffmemless.spec || die

Miscellaneous
=============

Bootctl fixes (Operation not permitted)
---------------------------------------

- For treble enabled devices, udev might create relative symlinks to your block devices in dev/block/bootdevice/by-name. This breaks bootctl because *someone* wrote some bad code in the boot control HAL (http://www.merproject.org/logs/%23sailfishos-porters/%23sailfishos-porters.2019-07-14.log.html#t2019-07-14T22:05:25).

- To fix "operation not permitted errors" apply the following patch to /lib/udev/rules.d/998-droid-system.rules: https://github.com/sailfish-oneplus6/droid-config-enchilada/commit/e96f5f9b380ddbee87626b3323ca72c43ba7a350#diff-02d3ee8eb10bab42c69060dd35f29c99

Flashlight shortcut
-------------------

- Starting from Sailfish 2.0.2 it's possible to have flashlight shortcut in eventsview. If your device supports flash torch mode add jolla-settings-system-flashlight package to patterns in your droid-configs repo. The shortcut can be enabled in the eventsview settings.


Actdead charging animation
------------------------------

- See changes here https://github.com/kimmoli/sfos-onyx-issues/issues/29 but also add 'trigger late-start' to 'on charging' in init.rc

Failed at step OOM_ADJUST spawning /usr/libexec/mapplauncherd/booster-qt5: Permission denied
--------------------------------------------------------------------------------------------

- Causes for example the failure of startup wizard on first boot
- try to revert kernel change in fs/proc/base.c
- https://github.com/mer-hybris/android_kernel_oneplus_msm8974/commit/0ed87d7f3cf7d3388f09bd264a856ad9efc564a3
- ping on the IRC if this worked for you :)

perf :)
-------

- MER_SDK $::

    cd $ANDROID_ROOT
    mkdir -p perf/rpm
    cd perf
    ln -s $ANDROID_ROOT/kernel/$VENDOR/$DEVICE linux
    curl -o rpm/perf.spec http://pastebin.com/raw/QiW7FD02
- Replace string <YOUR_KERNEL_VERSION> in rpm/perf.spec with kernel version for which you're building perf (for example: 3.4.0)::

    mb2 -s rpm/perf.spec -t $VENDOR-$DEVICE-armv7hl build
    mv RPMS/*.rpm $ANDROID_ROOT/droid-local-repo/$DEVICE/
    createrepo $ANDROID_ROOT/droid-local-repo/$DEVICE

- "less" package is needed for perf to format its output. You can find it here: http://repo.merproject.org/obs/nemo:/testing:/hw:/common/sailfish_latest_armv7hl/

Access Android's virtual SD card (needs more massaging)
-------------------------------------------------------

- Has received mixed feedback of working/not-working. Replicate onto your device accordingly::

  https://github.com/mer-hybris/droid-hal-hammerhead/commit/ca102d255f1b6f274e2768e8cbd4ad9c631890e9
  https://github.com/mer-hybris/droid-config-hammerhead/blob/master/sparse/usr/bin/droid/android-links.sh
  https://github.com/mer-hybris/droid-config-hammerhead/commit/e15591b98380c95e5be96bf9f386278b9825b5f3

If the pm-service complains about no permissions its because PARANOID_NETWORK is required for your kernel config
----------------------------------------------------------------------------------------------------------------

Kernel changes needed for updated systemd in Sailfish 2.1.1.X
-------------------------------------------------------------

- Apply this to all devices with 3.4 kernel https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=0640113be25d283e0ff77a9f041e1242182387f0

Devices that have qseecomd usually have issues getting to UI so its best to disable it in the init.$DEVICE.rc
--------------------------------------------------------------------------------------------------------------

Problems with tfa9890
---------------------

- Copy /system/etc/firmware to /etc/firmware. Symlink or mount doesn't work! (But why?)

Fixing the screen timeout issue
-------------------------------

- If display gets automatically blanked from lockscreen, but not when in app/home -> logical diffrences between those include:

  1. user activity (=input events) does not reset blanking timers in lockscreeen,
  2. similarly some blanking inhibitors are ignored while lockscreen is active
- In past there have been constantly reporting   , such as gyros that have been mistaken for something that user is doing -> check with evdev_trace if there is something that sends events regularly
- Could be some blanking inhibit mode (keep display on while charging, demo-mode & co), or some application doing blank prevent ping-pong with mce -> check with "dbus-monitor --system sender=com.nokia.mce" what kind of signals get emitted when swiping away from lockscreen / shortly after
- https://github.com/sailfishos-wt88047/droid-config-wt88047/commit/4512092dbba56ac9a6bf69cb034ceca8512f5a38

Kernel 3.0.x
------------

Since sailfish 3.0.3.x glibc is built with minimum kernel set to 3.2.0. On devices with kernel < 3.2.0 everything which use glibc or busybox-static will fail with error: "FATAL: kernel too old". /init-debug will fail with: "Kernel panic - not syncing: Attempted to kill init!"

- Add repository with patched glibc to droid-configs/sparse like here: https://github.com/elros34/droid-config-moto_msm8960_jbbl/blob/master/sparse/usr/share/ssu/features.d/glibc2.ini

OBS build and Over-the-Air updates (OTA)
========================================

OBS build
---------

- Benefits: automated builds, Jolla Store (see below), OTA (see below); local PC is then only needed for Android, dhd, audioflingerglue and droidmedia building (which barely happen when port becomes stable), and mic image creation
- It makes sense to go OBS as soon as you have polished your code, minimised hacks, and pushed it to github (usually when display+touch+WLAN and maybe cellular are working)
- On IRC ask r0kk3rz, mal, or sledges to create project and get maintainership for your nemo:devel:hw:$VENDOR:$DEVICE (you can try things out in your home repo first)
- Click on Repositories tab in your nemo:devel:hw:$VENDOR:$DEVICE

  - Then "Add repositories"
  - Check "SailfishOS latest"
  - Click "Add selected repositories" at the bottom of the page
- Add a hw:devel:common repo to build against (which contains all important backports for all ports:), you'll need to add it as an additional repo:

  - Click on Repositories tab in your nemo:devel:hw:$VENDOR:$DEVICE
  - Click "Edit repository"
  - Click Add additional path to this repository
  - Project:    nemo:devel:hw:common
  - Repository: sailfish_latest_armv7hl
- Check how other devices are built here e.g.
- Create droid-hal-$DEVICE package manually and upload RPMs for droid-hal-device and droidmedia (and audioflingerglue if device needs it)
- For all other packages create webhooks and trigger builds

  - How to create webhooks:
  - Which webhooks will you need for your device: https://webhook.merproject.org/webhook (search for nemo:devel:hw:lge:mako and replicate that structure)
- Add cibot as maintainer, then ask lbt via IRC to "patternise" your nemo:devel:hw:$VENDOR:$DEVICE
- Build an image successfully on your PC by following HADK but, using .ks file from droid-config-$DEVICE-ssu-kickstarts-\*.rpm built on OBS (don't forget to sed the repos and add nemo:hw:devel:common as adaptation1, this will help you more: http://images.devaamo.fi/sfe/mako/gamma6/Jolla-2.0.1.11-mako-armv7hl.ks )


Over-the-Air updates (OTA)
--------------------------

Prerequisities

- Your port has stabilised and is ready to face the big public (gets our retweets, you create Sailfish OS port thread on e.g. XDA, evangelise it :)

  - Good measure is to have bare necessities of a daily-driver for most people: LED, audio, texts, calls, data, WLAN, GPS, camera, light, proximity, accelerometer, vol keys, vibra, power management
- You should be building on OBS (guide above)
- Then add these two files (change contents apropriately)

  - https://github.com/mer-hybris/droid-config-hammerhead/blob/master/sparse/var/lib/flash-partition/device-info

    * Change PART_REAL_1 to match "boot" partition of your device
    * Change CPUCHECK_STRING to match the Hardware field in /proc/cpuinfo
  - https://github.com/mer-hybris/droid-config-hammerhead/blob/master/sparse/var/lib/platform-updates/flash-bootimg.sh

    * Don't forget to make it executable
- Port over to your device this line:

  - https://github.com/mer-hybris/droid-hal-hammerhead/blob/ca102d255f1b6f274e2768e8cbd4ad9c631890e9/droid-hal-hammerhead.spec#L12
- And this commit (only if MultiROM exists or in-the-works for your device):

  - https://github.com/mer-hybris/droid-config-hammerhead/commit/cb39670de095b914aea23d6ce0e633d295493016
- Don't forget to commit and tag so configs rebuild on OBS :)
- Simulate OTA on :devel: https://wiki.merproject.org/wiki/Template:SFOS_OTA , see if all is fine (e.g. you can build devel 1.1.9.28 image and OTA it to 2.0)
- Then you can test how an updated kernel package flashes itself automatically with an extra reboot, by making some change in kernel, reuploading RPMs and simulating OTA again
- For your users to actually use OTA, you should move it to :testing (on IRC ask mal or sledges to create nemo:testing:hw:$VENDOR:$DEVICE), to still be able to play (i.e. break things) in your :devel
- Get maintainership on that :testing repo
- Add cibot as maintainer, then via IRC ask lbt to "patternise" that repo too
- Click on Repositories tab in your nemo:testing:hw:$VENDOR:$DEVICE

  - Then "Add repositories"
  - Then "pick one via advanced interface"
  - Start typing "sailfishos", then pick the version you want OTA to be available for in format "sailfishos:X.Y.Z.W"
  - Choose "latest_$PORT_ARCH" for your architecture
  - Make the "Name" to match exactly "sailfishos_X.Y.Z.W"
- Add nemo:testing:hw:common to that as additional repo just like you did with :devel: above
- Ensure NO webhooks point to :testing ! Cross-check with https://webhook.merproject.org/webhook
- Promote by using osc copypac to all your device packages from devel to testing (useful script: https://pastebin.com/FwuVB52x )(How To https://gist.github.com/taaem/53ed3a99893d323d7ab3bd8d07540f50 )

  - use this (or simpler "Submit Package" WebUI option) also in future whenever a HW adaptation package needs updating in between sfos releases
  - (PR is being prepared to add device hw version to zip filename, HW Adaptation version is also shown in About Product, and is incremented by 1 each time OBS automatically rebuilds droid-hal-version-$DEVICE whenever any hw package changes ;))
- Make an image with adaptation-community repo pointing to testing, adaptation-community-common pointing to common in your .ks file, and start distributing that to the rest of the world
- Don't forget to document everything, create a nice installation wiki article for your device (if not yet already), and add such section: https://wiki.merproject.org/wiki/index.php?title=Adaptations/libhybris/Install_SailfishOS_for_mako&action=edit&section=4
- Point your existing users to the OTA section of your device's wiki
- Once the next Sailfish OS release comes out and your port adopts it, you can create a new repository in OBS with that version and your users will OTA to it.

OBS-less OTA updates
--------------------

Follow the "OTA (Over-the-Air) Updates" chapter in HADK.

For ports that **already have and established OTA via the current Sailfish OBS**, this is how to switch your current users to the self-hosted repository:

- Add the following two lines to your config spec:

.. code-block:: diff

    diff --git a/droid-config-$DEVICE.spec b/droid-config-$DEVICE.spec
     %define community_adaptation 1
    +# OTA via self-hosted repo needs to have all adaptation-community repos removed
    +Conflicts: community-adaptation-testing
    +Obsoletes: community-adaptation-testing

- Once you have tested the switch-over successfully, publish the changes made to your droid-configs repo to the existing OBS, so that all the users of your port can update and thus switch to your provided repository hosting.

- The above switch-over will remove both adaptation-community and adaptation-community-common repos. The latter is for the backports, which means it will be porter's responsibility to maintain backports after having switched to a self-hosted server.

Jolla Store access
==================

- Your device adaptation should be on Sailfish OS OBS (read "Building things on OBS" above)
- Do `ssu s` on your device, Device UID should show a unique ID that is:
- IMEI for devices with modem, note - your GSM modem should provide a valid IMEI even without an inserted SIM! Always a good cross-check that IMEI matches the one on your phone's box or under battery, and in CM/Lineage/Android
- For devices without modem -- WLAN or BT MAC address.
- Find another port/phone and prove that unique ID there is different than yours, and that all of them persist across reboots.
- If unique ID is OK then ping Keto on `#sailfishos-porters` (on OFTC IRC network) with "Device model" line from `ssu s` to enable store for you.
