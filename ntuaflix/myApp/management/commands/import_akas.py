import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from myApp.models import Akas

class Command(BaseCommand):
    help = 'Import a TSV file into the Akas table'

    def add_arguments(self, parser):
        parser.add_argument('tsv_file', type=str)

    def handle(self, *args, **options):
        with open(options['tsv_file'], 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                titleId = row['titleId']
                ordering = row['ordering']
                title = row['title']
                region = row['region'] if row['region'] != '\\N' else None
                language = row['language'] if row['language'] != '\\N' else None
                types = row['types'] if row['types'] != '\\N' else None
                attributes = row['attributes'] if row['attributes'] != '\\N' else None
                isOriginalTitle = row['isOriginalTitle'] if 'isOriginalTitle' in row and row['isOriginalTitle'] != '\\N' else 0

                try:
                    akas, created = Akas.objects.update_or_create(
                        titleId=titleId,
                        ordering=ordering,
                        defaults={
                            'title': title,
                            'region': region,
                            'language': language,
                            'types': types,
                            'attributes': attributes,
                            'isOriginalTitle': bool(int(isOriginalTitle)),
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created akas entry {akas}'))
                    else:
                        self.stdout.write(f'Updated akas entry {akas}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating akas entry {titleId}: {e}'))
