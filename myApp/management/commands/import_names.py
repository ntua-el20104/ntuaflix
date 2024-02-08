import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from myApp.models import Names

class Command(BaseCommand):
    help = 'Import a TSV file into the Names table'

    def add_arguments(self, parser):
        parser.add_argument('tsv_file', type=str)

    def handle(self, *args, **options):
        with open(options['tsv_file'], 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                nconst = row['nconst']
                primaryName = row['primaryName']
                birthYear = None if row['birthYear'] == "\\N" else row['birthYear']
                deathYear = None if row['deathYear'] == "\\N" else row['deathYear']
                primaryProfession = None if row['primaryProfession'] == "\\N" else row['primaryProfession']
                knownForTitles = None if row['knownForTitles'] == "\\N" else row['knownForTitles']
                img_url_asset = None if row['img_url_asset'] == "\\N" else row['img_url_asset']

                try:
                    person, created = Names.objects.update_or_create(
                        nconst=nconst,
                        defaults={
                            'primaryName': primaryName,
                            'birthYear': birthYear,
                            'deathYear': deathYear,
                            'primaryProfession': primaryProfession,
                            'knownForTitles': knownForTitles,
                            'img_url_asset': img_url_asset,
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created person {person}'))
                    else:
                        self.stdout.write(f'Updated person {person}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating person {nconst}: {e}'))
