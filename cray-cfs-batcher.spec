# Copyright 2020-2021 Hewlett Packard Enterprise Development LP
Name: cray-cfs-batcher-crayctldeploy
License: MIT
Summary: Cray Configuration Framework Batcher
Group: System/Management
Version: %(cat .rpm_version)
Release: %(echo ${BUILD_METADATA})
Source: %{name}-%{version}.tar.bz2
Vendor: Cray Inc.
Requires: cray-crayctl
Requires: kubernetes-crayctldeploy

# Project level defines TODO: These should be defined in a central location; DST-892
%define afd /opt/cray/crayctl/ansible_framework
%define roles %{afd}/roles
%define playbooks %{afd}/main
%define modules %{afd}/library

%description
This package provides the CFS Batcher API.

%prep
%setup -q

%build

%install

%clean

%files
