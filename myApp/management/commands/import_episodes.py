import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from myApp.models import Episode

class Command(BaseCommand):
    help = 'Import a TSV file into the Episode table'

    def add_arguments(self, parser):
        parser.add_argument('tsv_file', type=str)

    def handle(self, *args, **options):
        with open(options['tsv_file'], 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                parentTconst = row['parentTconst']
                seasonNumber = row['seasonNumber'] if row['seasonNumber'] != '\\N' else None
                episodeNumber = row['episodeNumber'] if row['episodeNumber'] != '\\N' else None

                try:
                    episode, created = Episode.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'parentTconst': parentTconst,
                            'seasonNumber': seasonNumber,
                            'episodeNumber': episodeNumber,
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created episode {episode}'))
                    else:
                        self.stdout.write(f'Updated episode {episode}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating episode {tconst}: {e}'))
