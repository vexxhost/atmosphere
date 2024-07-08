# Copyright (c) 2024 VEXXHOST, Inc.
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

import asyncio
import os
import pathlib
import textwrap
from datetime import datetime, timezone

import aiopath
import aioshutil
import platformdirs
from asynctempfile import NamedTemporaryFile
from gerrit import GerritClient
from pydantic import BaseModel, HttpUrl, PrivateAttr
from pydantic_yaml import parse_yaml_file_as, to_yaml_file


class ChartRepository(BaseModel):
    url: HttpUrl

    @property
    def name(self):
        return self.url.host.replace(".", "-") + self.url.path.replace("/", "-")


class ChartPatches(BaseModel):
    gerrit: dict[str, list[int]] = {}


class ChartDependency(BaseModel):
    name: str
    repository: HttpUrl
    version: str


class ChartRequirements(BaseModel):
    dependencies: list[ChartDependency] = []


class ChartLock(BaseModel):
    dependencies: list[ChartDependency] = []
    digest: str
    generated: datetime

    class Config:
        json_encoders = {
            "generated": lambda dt: dt.isoformat(),
        }


class Chart(BaseModel):
    name: str
    version: str
    repository: ChartRepository
    dependencies: list[ChartDependency] = []
    patches: ChartPatches = ChartPatches()


async def patch(input: bytes, path: aiopath.AsyncPath):
    async with NamedTemporaryFile() as temp_file:
        await temp_file.write(
            textwrap.dedent(
                f"""\
                {path.name}/*
                """
            )
            .strip()
            .encode()
        )
        await temp_file.flush()

        proc = await asyncio.create_subprocess_shell(
            f"filterdiff -p1 -I {temp_file.name}",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(input=input)
        if proc.returncode != 0:
            raise Exception(stderr)

    async with NamedTemporaryFile() as temp_file:
        await temp_file.write(
            textwrap.dedent(
                f"""\
                {path.name}/Chart.yaml
                {path.name}/values_overrides/*
                """
            )
            .strip()
            .encode()
        )
        await temp_file.flush()

        proc = await asyncio.create_subprocess_shell(
            f"filterdiff -p1 -X {temp_file.name}",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(input=stdout)
        if proc.returncode != 0:
            raise Exception(stderr)

    proc = await asyncio.create_subprocess_shell(
        f"patch -p2 -d {path} -E",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(input=stdout)
    if proc.returncode != 0:
        raise Exception(stdout)


class Config(BaseModel):
    charts: list[Chart]

    _workspace: pathlib.Path = PrivateAttr(
        default=pathlib.Path(
            platformdirs.user_cache_dir("atmosphere-sync-charts", "vexxhost")
        )
    )

    @property
    def repositories(self):
        repositories = []

        for chart in self.charts:
            if chart.repository in repositories:
                continue
            repositories.append(chart.repository)

        return repositories

    async def _helm(self, args: list[str]):
        proc = await asyncio.create_subprocess_shell(
            f"helm {' '.join(args)}",
            env={**dict(os.environ), **{"HOME": str(self._workspace)}},
        )
        await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"helm {' '.join(args)} failed")

    async def _fetch_chart(self, chart: Chart, path="charts"):
        charts_path: aiopath.AsyncPath = aiopath.AsyncPath(path)
        chart_path = charts_path / chart.name

        try:
            await aioshutil.rmtree(f"{path}/{chart.name}-{chart.version}")
        except FileNotFoundError:
            pass

        try:
            try:
                os.rename(
                    f"{path}/{chart.name}", f"{path}/{chart.name}-{chart.version}"
                )
            except FileNotFoundError:
                pass

            await self._helm(
                [
                    "fetch",
                    "--untar",
                    f"--destination={path}",
                    f"{chart.repository.name}/{chart.name}",
                    f"--version={chart.version}",
                ]
            )
        except Exception:
            os.rename(f"{path}/{chart.name}-{chart.version}", f"{path}/{chart.name}")
            raise

        try:
            await aioshutil.rmtree(f"{path}/{chart.name}-{chart.version}")
        except FileNotFoundError:
            pass

        if chart.dependencies:
            requirements = ChartRequirements(dependencies=chart.dependencies)
            to_yaml_file(f"{path}/{chart.name}/requirements.yaml", requirements)

            await asyncio.gather(
                *[
                    aioshutil.rmtree(f"{path}/{chart.name}/charts/{req.name}")
                    for req in chart.dependencies
                ]
            )

            await self._helm(
                ["dependency", "update", "--skip-refresh", f"{path}/{chart.name}"]
            )

            await asyncio.gather(
                *[
                    aioshutil.unpack_archive(
                        f"{path}/{chart.name}/charts/{req.name}-{req.version}.tgz",
                        f"{path}/{chart.name}/charts",
                    )
                    for req in chart.dependencies
                ]
            )

            await asyncio.gather(
                *[
                    (chart_path / "charts" / f"{req.name}-{req.version}.tgz").unlink()
                    for req in chart.dependencies
                ]
            )

            for req in chart.dependencies:
                lock = parse_yaml_file_as(
                    ChartLock,
                    f"{path}/{chart.name}/charts/{req.name}/requirements.lock",
                )
                lock.generated = datetime.min.replace(tzinfo=timezone.utc)
                to_yaml_file(
                    f"{path}/{chart.name}/charts/{req.name}/requirements.lock", lock
                )

            # Reset the generated time in the lock file to make things reproducible
            lock = parse_yaml_file_as(
                ChartLock, f"{path}/{chart.name}/requirements.lock"
            )
            lock.generated = datetime.min.replace(tzinfo=timezone.utc)
            to_yaml_file(f"{path}/{chart.name}/requirements.lock", lock)

        for gerrit, changes in chart.patches.gerrit.items():
            client = GerritClient(base_url=f"https://{gerrit}")

            for change_id in changes:
                change = client.changes.get(change_id)
                gerrit_patch = change.get_revision().get_patch(decode=True)
                await patch(input=gerrit_patch.encode(), path=chart_path)

        patches_path = charts_path / "patches" / chart.name
        if await patches_path.exists():
            patch_paths = sorted(
                [patch_path for patch_path in await patches_path.glob("*.patch")]
            )
            for patch_path in patch_paths:
                async with patch_path.open(mode="rb") as patch_file:
                    patch_data = await patch_file.read()
                    await patch(input=patch_data, path=chart_path)

    async def fetch_charts(self):
        await asyncio.gather(
            *[
                self._helm(["repo", "add", repo.name, str(repo.url)])
                for repo in self.repositories
            ]
        )
        await self._helm(["repo", "update"])

        await asyncio.gather(*[self._fetch_chart(chart) for chart in self.charts])


async def main():
    config = parse_yaml_file_as(Config, ".charts.yml")
    await config.fetch_charts()


if __name__ == "__main__":
    asyncio.run(main())
