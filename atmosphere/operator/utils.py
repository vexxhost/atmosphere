from atmosphere.operator import constants


def generate_image_tags(image_repository: str):
    return {
        image_name: get_image_ref(image_repository, image_name)
        for image_name in constants.IMAGE_LIST
    }


def get_image_ref(image_repository: str, image_name: str):
    return f"{image_repository}/{constants.IMAGE_LIST[image_name].split('/')[-1]}"
