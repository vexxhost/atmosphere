#!/usr/bin/python

import json

import tomli_w


class FilterModule(object):
    def filters(self):
        return {"to_toml": self.to_toml}

    def to_toml(self, variable):
        s = json.dumps(dict(variable))
        d = json.loads(s)
        return tomli_w.dumps(d)
