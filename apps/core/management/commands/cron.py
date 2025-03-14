import importlib
from typing import Callable

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        jobs = []
        for s in settings.CRONJOBS:
            module_name = ".".join(s.split(".")[:-1])
            module = importlib.import_module(module_name)
            function_name = s.split(".")[-1]
            job: Callable[[], None] = getattr(module, function_name)
            jobs.append(job)
        for job in jobs:
            self.stdout.write(f"running {job}")
            try:
                job()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"{job} failed with {e}"))
