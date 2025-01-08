#!/bin/bash -x

echo mount_efs.sh

LOGFILE="/var/log/bagg_analysis/bagg_analysis_deployment.log"
exec > >(tee -a $LOGFILE)
exec 2>&1

####### Mount EFS

# Install dependencies
sudo apt-get update
sudo apt-get -y install git binutils rustc cargo pkg-config libssl-dev gettext
sudo apt-get -y install cargo-doc llvm-17 lld-17 clang-17

# Upgrade stunnel
sudo apt-get -y install build-essential libwrap0-dev libssl-dev
sudo curl -o stunnel-5.74.tar.gz https://www.stunnel.org/downloads/stunnel-5.74.tar.gz
sudo tar xvfz stunnel-5.74.tar.gz
cd stunnel-5.74/
sudo ./configure
sudo make
sudo rm /bin/stunnel
sudo make install
sudo ln -s /usr/local/bin/stunnel /bin/stunnel

# Upgrade botocore
cd /home/ubuntu/bagg_analysis
poetry update botocore
cd /home/ubuntu

# install amazon-efs-utils
sudo rm -rf efs-utils
sudo git clone https://github.com/aws/efs-utils
cd efs-utils
sudo ./build-deb.sh
sudo apt-get -y install ./build/amazon-efs-utils*deb
cd ..
sudo rm -rf efs-utils

# Create EFS mount point
sudo mkdir /mnt/efs

# Add EFS to /etc/fstab for persistence across reboots
#echo "fs-0fc1b59ee31493ed4.efs.us-east-2.amazonaws.com:/ /mnt/efs nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport 0 0" | sudo tee -a /etc/fstab
echo "fs-0fc1b59ee31493ed4 /mnt/efs efs tls,_netdev 0 0" | sudo tee -a /etc/fstab

# Mount EFS
sudo mount -a || {
    # echo "Fallback to NFS mount"
    # sudo mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport fs-0fc1b59ee31493ed4.efs.us-east-2.amazonaws.com:/ /mnt/efs
    echo "Fallback to EFS helper mount"
    sudo mount -t efs -o tls fs-0fc1b59ee31493ed4 /mnt/efs/
}

# Set permissions
sudo chmod go+rw /mnt/efs

# Create test file to verify mount
echo "EFS successfully mounted on $(hostname)" | sudo tee /mnt/efs/instance-$(hostname)-test-file.txt

# Test EFS Service
df -h | grep efs
ls -l /mnt/efs