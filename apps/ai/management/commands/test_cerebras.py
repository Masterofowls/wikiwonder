"""Verify Cerebras API connectivity. Usage: uv run python manage.py test_cerebras"""
from django.core.management.base import BaseCommand

from apps.ai.services import get_ai_service


class Command(BaseCommand):
    help = "Send a test prompt to Cerebras and print the response"

    def add_arguments(self, parser):
        parser.add_argument(
            "--prompt",
            default="Why is fast inference important?",
            help="User message to send",
        )
        parser.add_argument("--stream", action="store_true", help="Use streaming mode")

    def handle(self, *args, **options):
        service = get_ai_service()
        if not service.is_configured:
            self.stderr.write(self.style.ERROR("CEREBRAS_API_KEY is not set"))
            return

        messages = [{"role": "user", "content": options["prompt"]}]
        self.stdout.write(f"Model: {service.model}")

        if options["stream"]:
            self.stdout.write("Streaming response:\n")
            for chunk in service.chat_stream(messages, max_completion_tokens=1024):
                self.stdout.write(chunk, ending="")
            self.stdout.write("")
        else:
            reply = service.chat(messages, max_completion_tokens=1024)
            self.stdout.write(self.style.SUCCESS(reply))
