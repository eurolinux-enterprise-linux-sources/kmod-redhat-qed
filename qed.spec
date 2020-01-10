%define kmod_name		qed
%define kmod_vendor		redhat
%define kmod_driver_version	8.10.10.21_dup7.3
%define kmod_rpm_release	2
%define kmod_kernel_version	3.10.0-514.el7
%define kmod_kbuild_dir		drivers/net/ethernet/qlogic/qed
%define kmod_dependencies       kmod-redhat-qede = 8.10.10.21_dup7.3
%define kmod_build_dependencies	%{nil}
%define kmod_devel_package	1

%{!?dist: %define dist .el7_3}

Source0:	%{kmod_name}-%{kmod_vendor}-%{kmod_driver_version}.tar.bz2
# Source code patches
Patch0:	0000-enable-config-options.patch
Patch1:	0001-add-backport-compat-headers.patch
Patch2:	0002-add-config-defines.patch
Patch3:	0003-firmware-file-rename.patch
Patch4:	0004-version-bump.patch
Patch5:	0005-firmware-selection.patch
Patch6:	0006-rename-driver-API.patch

%define findpat %( echo "%""P" )
%define __find_requires /usr/lib/rpm/redhat/find-requires.ksyms
%define __find_provides /usr/lib/rpm/redhat/find-provides.ksyms %{kmod_name} %{?epoch:%{epoch}:}%{version}-%{release}
%define sbindir %( if [ -d "/sbin" -a \! -h "/sbin" ]; then echo "/sbin"; else echo %{_sbindir}; fi )

Name:		kmod-redhat-qed
Version:	%{kmod_driver_version}
Release:	%{kmod_rpm_release}%{?dist}
Summary:	qed module for Driver Update Program
Group:		System/Kernel
License:	GPLv2
URL:		http://www.kernel.org/
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildRequires:	kernel-devel = %kmod_kernel_version redhat-rpm-config kernel-abi-whitelists
ExclusiveArch:	x86_64
%global kernel_source() /usr/src/kernels/%{kmod_kernel_version}.$(arch)

%global _use_internal_dependency_generator 0
Provides:	kernel-modules = %kmod_kernel_version.%{_target_cpu}
Provides:	kmod-%{kmod_name} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires(post):	%{sbindir}/weak-modules
Requires(postun):	%{sbindir}/weak-modules
Requires:	kernel >= 3.10.0-514.el7
Requires:	kernel < 3.10.0-515.el7
%if 1
Requires: firmware(%{kmod_name}) = 8.15.3.0_dup7_3
%endif
%if "%{kmod_build_dependencies}" != ""
BuildRequires:  %{kmod_build_dependencies}
%endif
%if "%{kmod_dependencies}" != ""
Requires:       %{kmod_dependencies}
%endif
# if there are multiple kmods for the same driver from different vendors,
# they should conflict with each other.
Conflicts:	kmod-%{kmod_name}

%description
qed module for Driver Update Program

%if 1

%package -n kmod-redhat-qed-firmware
Version:	8.15.3.0_dup7_3
Summary:	qed firmware for Driver Update Program
Provides:	firmware(%{kmod_name}) = 8.15.3.0_dup7_3
Provides:	kernel-modules = %{kmod_kernel_version}.%{_target_cpu}
%description -n  kmod-redhat-qed-firmware
qed firmware for Driver Update Program


%files -n kmod-redhat-qed-firmware
%defattr(644,root,root,755)
/lib/firmware/qed/qed_init_values_zipped-8.15.3.0_dup7.3.bin


%endif

# Development package
%if 0%{kmod_devel_package}
%package -n kmod-redhat-qed-devel
Version:	%{kmod_driver_version}
Requires:	kernel >= 3.10.0-514.el7
Requires:	kernel < 3.10.0-515.el7
Summary:	qed development files for Driver Update Program

%description -n  kmod-redhat-qed-devel
qed development files for Driver Update Program


%files -n kmod-redhat-qed-devel
%defattr(644,root,root,755)
/usr/share/kmod-%{kmod_vendor}-%{kmod_name}/Module.symvers
%endif

%post
modules=( $(find /lib/modules/%{kmod_kernel_version}.%(arch)/extra/kmod-%{kmod_vendor}-%{kmod_name} | grep '\.ko$') )
printf '%s\n' "${modules[@]}" >> /var/lib/rpm-kmod-posttrans-weak-modules-add

%pretrans -p <lua>
posix.unlink("/var/lib/rpm-kmod-posttrans-weak-modules-add")

%posttrans
if [ -f "/var/lib/rpm-kmod-posttrans-weak-modules-add" ]; then
	modules=( $(cat /var/lib/rpm-kmod-posttrans-weak-modules-add) )
	rm -rf /var/lib/rpm-kmod-posttrans-weak-modules-add
	printf '%s\n' "${modules[@]}" | %{sbindir}/weak-modules --add-modules
fi

%preun
rpm -ql kmod-redhat-qed-%{kmod_driver_version}-%{kmod_rpm_release}%{?dist}.$(arch) | grep '\.ko$' > /var/run/rpm-kmod-%{kmod_name}-modules

%postun
modules=( $(cat /var/run/rpm-kmod-%{kmod_name}-modules) )
rm /var/run/rpm-kmod-%{kmod_name}-modules
printf '%s\n' "${modules[@]}" | %{sbindir}/weak-modules --remove-modules

%files
%defattr(644,root,root,755)
/lib/modules/%{kmod_kernel_version}.%(arch)
/etc/depmod.d/%{kmod_name}.conf
/usr/share/doc/kmod-%{kmod_name}/greylist.txt

%prep
%setup -n %{kmod_name}-%{kmod_vendor}-%{kmod_driver_version}

%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
set -- *
mkdir source
mv "$@" source/
mkdir obj

%build
rm -rf obj
cp -r source obj
make -C %{kernel_source} M=$PWD/obj/%{kmod_kbuild_dir} \
	NOSTDINC_FLAGS="-I $PWD/obj/include -I $PWD/obj/include/uapi"
# mark modules executable so that strip-to-file can strip them
find obj/%{kmod_kbuild_dir} -name "*.ko" -type f -exec chmod u+x '{}' +

whitelist="/lib/modules/kabi-current/kabi_whitelist_%{_target_cpu}"
for modules in $( find obj/%{kmod_kbuild_dir} -name "*.ko" -type f -printf "%{findpat}\n" | sed 's|\.ko$||' | sort -u ) ; do
	# update depmod.conf
	module_weak_path=$(echo $modules | sed 's/[\/]*[^\/]*$//')
	if [ -z "$module_weak_path" ]; then
		module_weak_path=%{name}
	else
		module_weak_path=%{name}/$module_weak_path
	fi
	echo "override $(echo $modules | sed 's/.*\///') $(echo %{kmod_kernel_version} | sed 's/\.[^\.]*$//').* weak-updates/$module_weak_path" >> source/depmod.conf

	# update greylist
	nm -u obj/%{kmod_kbuild_dir}/$modules.ko | sed 's/.*U //' |  sed 's/^\.//' | sort -u | while read -r symbol; do
		grep -q "^\s*$symbol\$" $whitelist || echo "$symbol" >> source/greylist
	done
done
sort -u source/greylist | uniq > source/greylist.txt

%install
export INSTALL_MOD_PATH=$RPM_BUILD_ROOT
export INSTALL_MOD_DIR=extra/%{name}
make -C %{kernel_source} modules_install \
	M=$PWD/obj/%{kmod_kbuild_dir}
# Cleanup unnecessary kernel-generated module dependency files.
find $INSTALL_MOD_PATH/lib/modules -iname 'modules.*' -exec rm {} \;

install -m 644 -D source/depmod.conf $RPM_BUILD_ROOT/etc/depmod.d/%{kmod_name}.conf
install -m 644 -D source/greylist.txt $RPM_BUILD_ROOT/usr/share/doc/kmod-%{kmod_name}/greylist.txt
%if 1
install -m 644 -D source/firmware/qed/qed_init_values_zipped-8.15.3.0_dup7.3.bin $RPM_BUILD_ROOT/lib/firmware/qed/qed_init_values_zipped-8.15.3.0_dup7.3.bin

%endif
%if 0%{kmod_devel_package}
install -m 644 -D $PWD/obj/%{kmod_kbuild_dir}/Module.symvers $RPM_BUILD_ROOT/usr/share/kmod-%{kmod_vendor}-%{kmod_name}/Module.symvers
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Jul 13 2017 Eugene Syromiatnikov <esyr@redhat.com> 8.10.10.21_dup7.3-2
- Exclude ppc64 and ppc64le from ExclusiveArch tag.

* Thu Jul 13 2017 Eugene Syromiatnikov <esyr@redhat.com> 8.10.10.21_dup7.3-1
- d44f90c087a53365ef671c1a6414d07fd8bf4af0
- Resolves: #bz1448409, #bz1448411
- qed module for Driver Update Program
