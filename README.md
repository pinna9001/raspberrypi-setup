# Raspberrypi Setup

## Inital Setup

After flashing the OS (in this case Raspbian OS Lite 64Bit) and enabling ssh the system should be updated:

```
sudo apt update
sudo apt upgrade
```

Then to use this repo in setting up the raspberrypi you should install git:

```
sudo apt install git
```

... and generate a ssh key to use with Github:

```
ssh-keygen -t ed25519 -C "email"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

For uploading follow these instructions: [Adding a new SSH key to your GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)

Then the key should be tested with and the fingerprints of the Github keys verified ([GitHub's SSH key fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)):

```
ssh -T git@github.com
```

Then some more packages have to be installed:

- neovim or another text editor
- samba - for setting up filesharing
- python - to combine the docker-compose.yml into a single file

```
sudo apt install neovim samba python
```


