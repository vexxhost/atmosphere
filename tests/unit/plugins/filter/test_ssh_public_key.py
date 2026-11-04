# Copyright (c) 2026 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.vexxhost.atmosphere.plugins.filter.ssh_public_key import (
    ssh_public_key,
)

# NOTE: Throwaway keys generated with `ssh-keygen` for these tests only. The
#       expected public keys are the matching `.pub` files without a comment.

ED25519_PRIVATE_KEY = """\
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBwzsQgMX1vQUACsDaST8BCrg2dgQW6XGGZBkVVR9xC0AAAAJDNlegEzZXo
BAAAAAtzc2gtZWQyNTUxOQAAACBwzsQgMX1vQUACsDaST8BCrg2dgQW6XGGZBkVVR9xC0A
AAAED2m9ZIo7rvBJ/4Vpz2EpfnDHLIg/8ltTBUVdfy7QZuW3DOxCAxfW9BQAKwNpJPwEKu
DZ2BBbpcYZkGRVVH3ELQAAAAB2ZpeHR1cmUBAgMEBQY=
-----END OPENSSH PRIVATE KEY-----
"""
ED25519_PUBLIC_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHDOxCAxfW9BQAKwNpJPwEKuDZ2BBbpcYZkGRVVH3ELQ"
)

ECDSA_PRIVATE_KEY = """\
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAaAAAABNlY2RzYS
1zaGEyLW5pc3RwMjU2AAAACG5pc3RwMjU2AAAAQQTSQvEyHSJcF2nNSe09Gu41nYiFgapB
dPsgSEE1o3wKub/bXw31+X0i62w1Uv3tJ7ixehGUW1H0rpSrpFYmOQEDAAAAoH7yG1p+8h
taAAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBNJC8TIdIlwXac1J
7T0a7jWdiIWBqkF0+yBIQTWjfAq5v9tfDfX5fSLrbDVS/e0nuLF6EZRbUfSulKukViY5AQ
MAAAAgRdslMza2AFg+6apmIudQkoC7WIwAT5XEOoceCLFTU1cAAAAHZml4dHVyZQE=
-----END OPENSSH PRIVATE KEY-----
"""
ECDSA_PUBLIC_KEY = (
    "ecdsa-sha2-nistp256 "
    "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBNJC8TIdIlwXac1J"
    "7T0a7jWdiIWBqkF0+yBIQTWjfAq5v9tfDfX5fSLrbDVS/e0nuLF6EZRbUfSulKukViY5AQM="
)

RSA_PEM_PRIVATE_KEY = """\
-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDQkmQLifFE058xPDKfCyPHl4whLglwZ5EO5HRabnsJFl90Z1OS
8fvpdz3SNlNDJ5U4VEfKmm42XYMFA570T0KbVfMMz2ungDYAm1+vHGKkUMeZGIpv
HD7mFvBbeDZhtw/yjpZ1xtKe8IcbhFk9j+JN7iSED5nDl3TJBYzR1LREdwIDAQAB
AoGBAI1q9NKuERztr/6eJmSYFQZ7xtOod1XzovNKC2pVhq6+sLIobQ4xbPD7nLsv
gn0CFbc/zf2dgCT0eqWnsttL8ohOzoeJ9ei4Ojfn9vfSStHZOQ61cvOWUP0ENvsJ
TCoJY7ljLD4tibM7h9XFnPccb/gc8ZAhVizY9WDWwfqQDByBAkEA716OmYDRLHB3
647lq+0qkLcU+JPiuslYorNnxgsgggFTLRWATLOkQAn4fssNCKyFyjPAHwhSJ1b1
VTeTDiaycQJBAN8QEQYF1GzfgRHOh54GhB62zgOESdI8LQeJq8XafO3ostYw6wEv
UDMzr9Zp9aosd/yd+9oKXhAIG9cIBBHkiWcCQQDlvOc4RP59nGQ8XSXp4PKdelpS
Sf2uMFk1ruLGnR9SJ1thReWhuDjIjclGSDP2Qz8VVp3qKt5Oi5NjerdVOabBAkEA
vR13AV8x8TgwynMKYbzuiMe9tBeVKsvf9XMQEgeiQWY3MQd6Rp/hY/efTa66HBPl
imQ64WpGw1rMl6txH+ZdYwJANg4uwgo7q0G1w02K+nkjvBbJbJSFLFkFJzqE92gB
vBOmX376YUF8YxEEx3LCKs1n5rEq9+6UsGwXf70JXsgMhA==
-----END RSA PRIVATE KEY-----
"""
RSA_PEM_PUBLIC_KEY = (
    "ssh-rsa "
    "AAAAB3NzaC1yc2EAAAADAQABAAAAgQDQkmQLifFE058xPDKfCyPHl4whLglwZ5EO5HRabnsJ"
    "Fl90Z1OS8fvpdz3SNlNDJ5U4VEfKmm42XYMFA570T0KbVfMMz2ungDYAm1+vHGKkUMeZGIpv"
    "HD7mFvBbeDZhtw/yjpZ1xtKe8IcbhFk9j+JN7iSED5nDl3TJBYzR1LREdw=="
)

ENCRYPTED_PRIVATE_KEY = """\
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABCFl38BoX
OEE6ldv8FAKWegAAAAGAAAAAEAAAAzAAAAC3NzaC1lZDI1NTE5AAAAIE2GXf1P/yrhNvjI
n9atuU1IHTXJA2hkgxq/nMPx/67HAAAAkLr+5SzEbjN9np49oyQAH2MAhDOw6/EvYYmE+/
cUKJt5PYtRIOztJsXNkBFk6aDyMdAB+rjS7m/8d8fcESToNkn2pyvzbRdIofDwMC5WVNPG
sXOB6HcoGf8EqaKbrExb7m0P8VwRBdOOB030w3qBo+yWjgi5IIKfeKHC0t8RaD2uQH6hxQ
4bnYWf1RnZn25gcQ==
-----END OPENSSH PRIVATE KEY-----
"""


@pytest.mark.parametrize(
    "private_key,expected",
    [
        (ED25519_PRIVATE_KEY, ED25519_PUBLIC_KEY),
        (ECDSA_PRIVATE_KEY, ECDSA_PUBLIC_KEY),
        (RSA_PEM_PRIVATE_KEY, RSA_PEM_PUBLIC_KEY),
        # Keys passed in through inventory often lose their trailing newline.
        (ED25519_PRIVATE_KEY.rstrip("\n"), ED25519_PUBLIC_KEY),
        (RSA_PEM_PRIVATE_KEY.rstrip("\n"), RSA_PEM_PUBLIC_KEY),
    ],
)
def test_ssh_public_key(private_key, expected):
    assert ssh_public_key(private_key) == expected


@pytest.mark.parametrize(
    "value",
    [
        ENCRYPTED_PRIVATE_KEY,
        ED25519_PUBLIC_KEY,
        "not a key",
        None,
    ],
)
def test_ssh_public_key_invalid(value):
    with pytest.raises(AnsibleFilterError):
        ssh_public_key(value)
