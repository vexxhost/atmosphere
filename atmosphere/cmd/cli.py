import click
import subprocess

from atmosphere.operator import constants, utils


@click.group()
def main():
    pass


@main.group()
def image():
    pass


@image.command()
@click.argument("destination")
def mirror(destination):
    seen = []

    for image in constants.IMAGE_LIST:
        if constants.IMAGE_LIST[image] in seen:
            continue

        click.echo(f"🪞  Starting to mirror {constants.IMAGE_LIST[image]}...")

        try:
            subprocess.run(
                f"skopeo copy --dest-tls-verify=false --multi-arch=all docker://{constants.IMAGE_LIST[image]} docker://{utils.get_image_ref(destination, image)}",
                capture_output=True,
                check=True,
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            click.secho(
                f"❌ Failed to mirror {image}: {e.stderr.decode('utf-8').strip()}",
                fg="red",
            )
            break

        seen.append(constants.IMAGE_LIST[image])
        click.secho(f"✅ Successfully mirrored {image}", fg="green")
