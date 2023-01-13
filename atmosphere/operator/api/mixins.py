import json

import kopf
import requests


class ServerSideApplyMixin:
    def apply(self):
        resp = self.api.patch(
            **self.api_kwargs(
                headers={
                    "Content-Type": "application/apply-patch+yaml",
                },
                params={
                    "fieldManager": "atmosphere-operator",
                    "force": True,
                },
                data=json.dumps(self.obj),
            )
        )

        try:
            self.api.raise_for_status(resp)
        except requests.exceptions.HTTPError:
            if resp.status_code == 404:
                raise kopf.TemporaryError("CRD is not yet installed", delay=1)
            raise

        self.set_obj(resp.json())
        return self
