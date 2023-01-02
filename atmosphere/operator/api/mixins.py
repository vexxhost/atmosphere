import json


class ServerSideApplyMixin:
    def apply(self):
        print(self.obj)
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

        self.api.raise_for_status(resp)
        self.set_obj(resp.json())
        return self
