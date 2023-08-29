from django.core.management.base import BaseCommand

from apps.core.selenium import get_chrome_driver


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        driver = get_chrome_driver()
        driver.get("https://www.google.com/")
        title = driver.title
        self.stdout.write(self.style.SUCCESS(f"Title: {title}"))
        driver.quit()
