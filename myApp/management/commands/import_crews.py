import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from myApp.models import Crews

class Command(BaseCommand):
    help = 'Import a TSV file into the Crews table'

    def add_arguments(self, parser):
        parser.add_argument('tsv_file', type=str)

    def handle(self, *args, **options):
        with open(options['tsv_file'], 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                directors = row['directors'] if row['directors'] != '\\N' else None
                writers = row['writers'] if row['writers'] != '\\N' else None

                try:
                    crew, created = Crews.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'directors': directors,
                            'writers': writers,
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created crew entry {crew}'))
                    else:
                        self.stdout.write(f'Updated crew entry {crew}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating crew entry {tconst}: {e}'))
