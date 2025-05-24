# Description: houjie-WRT Theme for LuCI
# Author: houjie80
# License: GPL-3.0

include $(TOPDIR)/rules.mk

LUCI_TITLE:=HJ-WRT Theme
LUCI_DEPENDS:=+curl +jsonfilter
PKG_VERSION:=1.0.2
PKG_RELEASE:=24052025

CONFIG_LUCI_CSSTIDY:=

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature
