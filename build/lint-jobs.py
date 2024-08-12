import sys
import glob
import yaml


def main():
    passed = True

    for file in glob.glob("zuul.d/container-images/*.yaml"):
        with open(file, "r") as file:
            configs = yaml.safe_load(file)

        for config in configs:
            if "job" in config:
                job = config["job"]

                # Check if build or upload jobs are missing 'atmosphere-buildset-registry' dependency
                if (
                    "build-container-image-" in job["name"]
                    or "upload-container-image-" in job["name"]
                ):
                    deps = job.get("dependencies", [])
                    if not any(
                        dep.get("name") == "atmosphere-buildset-registry"
                        for dep in deps
                    ):
                        print(
                            f"Job '{job['name']}' is missing 'atmosphere-buildset-registry' dependency."
                        )
                        passed = False

    if passed:
        print(
            "All build and upload jobs have 'atmosphere-buildset-registry' dependency."
        )
    else:
        print("Jobs missing 'atmosphere-buildset-registry' dependency.")
        sys.exit(1)


if __name__ == "__main__":
    main()
