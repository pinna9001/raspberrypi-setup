# Raspberrypi Setup

## Table of Contents

- [Inital Setup](#inital-setup)
- [Samba Share](#samba-share)
- [Docker Services](#docker-services)
- [Git Mirrors](#git-mirrors)
- [VPN Server](#vpn-server)

## Inital Setup

[Back to Table of Contents](#table-of-contents)

After flashing the OS (in this case Raspbian OS Lite 64Bit) and enabling ssh the system should be updated:

```bash
sudo apt update
sudo apt upgrade
```

Then to use this repo in setting up the raspberrypi you should install git:

```bash
sudo apt install git
```

... and generate a ssh key to use with Github:

```bash
ssh-keygen -t ed25519 -C "email"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

For uploading follow these instructions: [Adding a new SSH key to your GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)

Then the key should be tested with and the fingerprints of the Github keys verified ([GitHub's SSH key fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)):

```bash
ssh -T git@github.com
```

Then some more packages have to be installed:

- neovim or another text editor
- samba - for setting up filesharing (see [Samba Share](#samba-share)
- python - to combine the docker-compose.ymls into a single large docker-compose file

```
sudo apt install neovim samba python
```

## Samba Share

[Back to Table of Contents](#table-of-contents)

First install the required package:

```bash
apt install samba
```

Then an user has to be activated for usage with samba:

```bash
smbpasswd -a username
```

After that a share can be defined in the config file `/etc/sambe/smb.conf`:

For example: 

```
[sharename]
path = /path/to/share
browsable = yes
writeable = yes
only guest = no
create mask = 0666
directory mask = 755
public = no
```

After adding a share restart the service with:

```bash
systemctl restart smbd.service
```

Refer to [ubuntuusers/Samba Server](https://wiki.ubuntuusers.de/Samba_Server/) or [archlinux/Samba](https://wiki.archlinux.org/title/Samba) for more information.

## Docker Services

[Back to Table of Contents](#table-of-contents)

To use docker first install it with:

```bash
apt install docker docker-compose
```

Then follow [these steps](https://docs.docker.com/engine/install/linux-postinstall/) to finish and test the installation.

If you want to use the script `create-docker-compose.py` to merge the docker-compose.ymls provided in the directory docker-services you first have to install python and create an virtual environment:

```bash
apt install python
python3 -m venv .venv
# activate the environment
source ./venv/bin/activate
# install dependencies
pip3 install -r requirements.txt
```

Then you can use the script create-docker-compose.py like so:

```bash
create-docker-compose.py -i ./docker-services -o ./out/
```

The script will merge the selected services into one docker-compose.yml and detect already used ports, volumes, container- and service names and change them automatically. The output directory will then contain a single docker-compose.yml.

## Git Mirrors

[Back to Table of Contents](#table-of-contents)

To setup a git server to be able to also clone the mirrors you first have to create the git user:

```bash
sudo adduser git
su git
cd
mkdir .ssh && chmod 700 .ssh
touch .ssh/authorized_keys && chmod 600 .ssh/authorized_keys
```

To automatically mirror repositories you can use the script `update-mirrors.sh`. You only have to add a single line to `/etc/crontab`.

```
# EDITOR=nvim sudoedit /etc/crontab
0 2 * * * git /home/git/update-mirrors.sh >> /home/git/cron.log 2> /dev/null
```

The script will mirror the repositories specified in the file `/home/git/mirrors.txt` (one line per repository url) into the directory `/home/git/mirrors`. To clone one of the repositories you can use:

```bash
git clone git@server:mirrors/reponame
```

You might have to add your ssh key to the authorized_keys file first.

Refer to [4.4 Git on the Server - Setting Up the Server](https://git-scm.com/book/en/v2/Git-on-the-Server-Setting-Up-the-Server) for more information.

## VPN Server

[Back to Table of Contents](#table-of-contents)

To setup the VPN server you need to setup the three components:

- terraform for deployment with hetzner
- discord bot for receiving commands and sending status messages
- vpn manager for managing terraform and the vpn connection from the device to the hetzner server

First you should install terraform. For the raspberrypi you have to download a prebuild binary for arm64 (see [here](https://developer.hashicorp.com/terraform/install#linux)). You can just move the file `terraform` to /usr/bin to be able to use it from anywhere.

Then you can stetup the vpn_manager and the discord bot by following the instructions in the repository.
