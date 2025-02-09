#!/bin/bash -x

echo mount_efs.sh

# Function to determine if we're running in a Docker container
in_docker() {
    [ -f /.dockerenv ] || grep -Eq '(lxc|docker)' /proc/1/cgroup
}

# Function to handle sudo based on environment
sudo_cmd() {
    if in_docker; then
        "$@"
    else
        sudo "$@"
    fi
}

LOGFILE="/var/log/bagg_analysis/bagg_analysis_deployment.log"
exec > >(tee -a $LOGFILE)
exec 2>&1

####### Mount EFS

# Install dependencies
sudo_cmd apt-get update
sudo_cmd apt-get -y install git binutils rustc cargo pkg-config libssl-dev gettext
sudo_cmd apt-get -y install cargo-doc llvm-17 lld-17 clang-17

# Upgrade stunnel
sudo_cmd apt-get -y install build-essential libwrap0-dev libssl-dev
sudo_cmd curl -o stunnel-5.74.tar.gz https://www.stunnel.org/downloads/stunnel-5.74.tar.gz
sudo_cmd tar xvfz stunnel-5.74.tar.gz
cd stunnel-5.74/
sudo_cmd ./configure
sudo_cmd make
sudo_cmd rm /bin/stunnel
sudo_cmd make install
sudo_cmd ln -s /usr/local/bin/stunnel /bin/stunnel

# Upgrade botocore
cd /home/ubuntu/bagg_analysis
poetry update botocore
cd /home/ubuntu

# install amazon-efs-utils
sudo_cmd rm -rf efs-utils
sudo_cmd git clone https://github.com/aws/efs-utils
cd efs-utils
sudo_cmd ./build-deb.sh
sudo_cmd apt-get -y install ./build/amazon-efs-utils*deb
cd ..
sudo_cmd rm -rf efs-utils

# Create EFS mount point
sudo_cmd mkdir /mnt/efs

# Add EFS to /etc/fstab for persistence across reboots
#echo "fs-0fc1b59ee31493ed4.efs.us-east-2.amazonaws.com:/ /mnt/efs nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport 0 0" | sudo_cmd tee -a /etc/fstab
echo "fs-0fc1b59ee31493ed4 /mnt/efs efs tls,_netdev 0 0" | sudo_cmd tee -a /etc/fstab

# Mount EFS
sudo_cmd mount -a || {
    # echo "Fallback to NFS mount"
    # sudo_cmd mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport fs-0fc1b59ee31493ed4.efs.us-east-2.amazonaws.com:/ /mnt/efs
    echo "Fallback to EFS helper mount"
    sudo_cmd mount -t efs -o tls fs-0fc1b59ee31493ed4 /mnt/efs/
}

# Set permissions
sudo_cmd chmod go+rw /mnt/efs

# Create test file to verify mount
echo "EFS successfully mounted on $(hostname)" | sudo_cmd tee /mnt/efs/instance-$(hostname)-test-file.txt

# Test EFS Service
df -h | grep efs
ls -l /mnt/efs