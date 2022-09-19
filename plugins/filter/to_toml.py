#!/usr/bin/python

import json

import toml


class FilterModule(object):
    def filters(self):
        return {"to_toml": self.to_toml}

    def to_toml(self, variable):
        s = json.dumps(dict(variable))
        d = json.loads(s)
        return toml.dumps(d)
