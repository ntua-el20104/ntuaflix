import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from myApp.models import Ratings

class Command(BaseCommand):
    help = 'Import a TSV file into the Ratings table'

    def add_arguments(self, parser):
        parser.add_argument('tsv_file', type=str)

    def handle(self, *args, **options):
        with open(options['tsv_file'], 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                averageRating = row['averageRating']
                numVotes = row['numVotes']

                try:
                    rating, created = Ratings.objects.update_or_create(
                    tconst=tconst,
                    defaults={
                        'averageRating': averageRating,
                        'numVotes': numVotes,
                    }
                )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created rating {rating}'))
                    else:
                        self.stdout.write(f'Updated rating {rating}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating movie {tconst}: {e}'))
                
