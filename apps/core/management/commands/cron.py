import importlib
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        jobs = []
        for s in settings.CRONJOBS:
            module_name = ".".join(s.split(".")[:-1])
            module = importlib.import_module(module_name)
            function_name = s.split(".")[-1]
            job: Callable[[], None] = getattr(module, function_name)  # type: ignore
            jobs.append(job)
        for job in jobs:
            try:
                job()
            except Exception as e:
                self.stdout.write(self.style.ERROR(e))
                continue
