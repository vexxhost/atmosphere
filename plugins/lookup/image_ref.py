from ansible.plugins.lookup import LookupBase

from atmosphere.operator import utils

DOCUMENTATION = """
  name: image_ref
  author: Mohammed Naser (@mnaser) <mnaser@vexxhost.com>
  version_added: "0.13"
  short_description: Lookup image reference
  description:
    - This lookup returns the image reference for a given image tag
  options:
    _terms:
      description: tag(s) of images to generate
      required: True
    output:
      type: string
      required: True
      choices:
        - domain
        - name
        - path
        - tag
        - ref
        - digest
"""


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        if variables is not None:
            self._templar.available_variables = variables
        vars = getattr(self._templar, "_available_variables", {})

        self.set_options(var_options=variables, direct=kwargs)

        ret = []
        registry = vars.get("atmosphere_image_repository", None)
        output = self.get_option("output")

        for term in terms:
            ref = utils.get_image_ref(term, override_registry=registry)
            if output == "domain":
                ret.append(ref.repository["domain"])
            if output == "name":
                ret.append(ref["name"])
            if output == "path":
                ret.append(ref.repository["path"])
            if output == "ref":
                ret.append(ref.string())
            if output == "tag":
                ret.append(ref["tag"])
            if output == "digest":
                ret.append(ref["digest"])

        return ret
