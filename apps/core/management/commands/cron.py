import importlib
import time
from typing import Callable

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--duration",
            type=int,
            default=None,
            help=(
                "Optional max runtime in seconds. If set, the command will stop "
                "starting new jobs once the duration is exceeded."
            ),
        )

    def handle(self, *args, **kwargs):
        duration: int | None = kwargs.get("duration")
        start = time.monotonic()

        jobs = []
        for s in settings.CRONJOBS:
            module_name = ".".join(s.split(".")[:-1])
            module = importlib.import_module(module_name)
            function_name = s.split(".")[-1]
            job: Callable[[], None] = getattr(module, function_name)
            jobs.append(job)
        for job in jobs:
            if duration is not None and duration >= 0 and (time.monotonic() - start) > duration:
                self.stdout.write("duration limit reached, stopping")
                break
            self.stdout.write(f"running {job}")
            try:
                job()
            except AssertionError as e:
                raise e
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"{job} failed with \n{e}"))
