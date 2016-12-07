# /bin/bash
if [ $# -lt 1 ];then
	echo "usage: $0 <build options: --install --unistall --all --load-module>"
	action="--all"
	#  exit
else
	action=$1
fi

bp_dir_vers="backports-4.2.6-1"

if [ $action == "--uninstall" ] || [ $action == "--all" ]; then
  rm -r ${bp_dir_vers}*
  rm -r athmodules

  echo "clean all... "
  if [ $action == "--uninstall" ]; then
	echo "done, exit."
        exit
  fi
fi

if [ $action == "--install" ] || [ $action == "--all" ]; then
        if [ ! -d "$bp_dir_vers" ]; then
		wget https://www.kernel.org/pub/linux/kernel/projects/backports/stable/v4.2.6/${bp_dir_vers}.tar.gz
		tar fvxz ${bp_dir_vers}.tar.gz
		cd ${bp_dir_vers}
		patch -p 2 < ../edca_tpc_patch.patch
		echo "CPTCFG_ATH9K_STATION_STATISTICS=y" >> defconfigs/ath9k-debug
		echo "CPTCFG_MAC80211_DEBUG_COUNTERS=y"  >> defconfigs/ath9k-debug
		make defconfig-ath9k-debug
		make -j8
        else
		cd ${bp_dir_vers}
		make -j8
	fi

	cd ../

        if [ ! -d "athmodules" ]; then
		mkdir athmodules ; 
	fi

	cp ${bp_dir_vers}/compat/compat.ko athmodules/
	cp ${bp_dir_vers}/net/mac80211/mac80211.ko athmodules/
	cp ${bp_dir_vers}/drivers/net/wireless/ath/ath.ko  athmodules/
	cp ${bp_dir_vers}/drivers/net/wireless/ath/ath9k/*.ko  athmodules/
	cp ${bp_dir_vers}/net/wireless/cfg80211.ko  athmodules/
	if [ ! $action == "--all" ]; then
		exit
	fi 
fi

if [ $action == "--load-module" ] || [ $action == "--all" ]; then
	sudo rmmod ath9k
	sudo rmmod ath9k_common
	sudo rmmod ath9k_hw
	sudo rmmod ath
	sudo rmmod mac80211
	sudo rmmod cfg80211
	sudo rmmod compat

	sudo insmod athmodules/compat.ko
	sudo insmod athmodules/cfg80211.ko
	sudo insmod athmodules/mac80211.ko
	sudo insmod athmodules/ath.ko
	sudo insmod athmodules/ath9k_hw.ko
	sudo insmod athmodules/ath9k_common.ko
	sudo insmod athmodules/ath9k.ko
        exit
fi
