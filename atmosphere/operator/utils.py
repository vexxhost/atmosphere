from docker_image import reference

from atmosphere.operator import constants


def get_image_ref(
    image_name: str, override_registry: str = None
) -> reference.Reference:
    ref = reference.Reference.parse(constants.IMAGE_LIST[image_name])
    if override_registry is None:
        return ref

    # NOTE(mnaser): We re-write the name of a few images to make sense of them
    #               in the context of the override registry.
    ref_name = ref.repository["path"].split("/")[-1]
    if image_name == "skopeo":
        ref_name = "skopeo-stable"

    # NOTE(mnaser): Since the attributes inside of reference.Reference are not
    #               determined during parse time, we need to re-parse the
    #               string to get the correct attributes.
    ref["name"] = "{}/{}".format(override_registry, ref_name)
    ref = reference.Reference.parse(ref.string())

    return ref
