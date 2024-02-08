import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from myApp.models import Movies  

class Command(BaseCommand):
    help = 'Import a TSV file into the Movies table'

    def add_arguments(self, parser):
        parser.add_argument('tsv_file', type=str)

    def handle(self, *args, **options):
        with open(options['tsv_file'], 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                titleType = row['titleType']
                primaryTitle = row['primaryTitle']
                originalTitle = row['originalTitle']
                isAdult = row['isAdult'] 
                startYear = row['startYear'] if row['startYear'] != '\\N' else None
                endYear = row['endYear'] if row['endYear'] != '\\N' else None
                runtimeMinutes = row['runtimeMinutes'] if row['runtimeMinutes'] != '\\N' else None
                genres = row['genres'] if row['genres'] != '\\N' else None
                img_url_asset = row['img_url_asset'] if 'img_url_asset' in row and row['img_url_asset'] != '\\N' else '\\N'
                
                try:
                    movie, created = Movies.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'titleType': titleType,
                            'primaryTitle': primaryTitle,
                            'originalTitle': originalTitle,
                            'isAdult': isAdult,
                            'startYear': int(startYear) if startYear else None,
                            'endYear': int(endYear) if endYear else None,
                            'runtimeMinutes': int(runtimeMinutes) if runtimeMinutes else None,
                            'genres': genres,
                            'img_url_asset': img_url_asset,
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created movie {movie}'))
                    else:
                        self.stdout.write(f'Updated movie {movie}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating movie {tconst}: {e}'))
