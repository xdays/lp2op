# lp2op

Script for lastpass to 1passwork mgiration

# how it works

First of all, this script use the following 5 attributes to identify one single item from both side

1. name
2. url
3. username
4. password
5. note

Every item will have its own digest caculated from 5 attributes internally.

It also map the folder from lastpass to vault in 1password, the map rule is defined in `config.yaml`

# setup

Prepare config file

```
cp config.yaml.example config.yaml
```

1. the lastpass credential section is optional, the script will prompt for it if not configured
2. this script support multiple 1password account, you can define mapping rule for every account.

This script assume you already setup your 1password command line, please refer
[here](https://support.1password.com/command-line-getting-started/#get-started-with-the-command-line-tool)
if you haven't

```
eval(op signin account)
```

# run

```
pipenv install
pipenv run lp2op.py
```
