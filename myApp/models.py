from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError



class User(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=50)

    def __str__(self):
        return self.username

class Liked(models.Model):
   username = models.CharField(max_length=30)
   tconst = models.CharField(max_length=255)

   class Meta:
        # Define a composite primary key
        unique_together = (('username', 'tconst'))

class Disliked(models.Model):
   username = models.CharField(max_length=30)
   tconst = models.CharField(max_length=255)

   class Meta:
        # Define a composite primary key
        unique_together = (('username', 'tconst'))


class Names(models.Model):
  nconst = models.CharField(max_length=255, unique=True, primary_key=True)
  primaryName = models.CharField(max_length=255, null=False)
  birthYear = models.CharField(max_length=255, default="\\N", null=True,blank=True)
  deathYear = models.CharField(max_length=255, default="\\N", null=True, blank=True)
  primaryProfession = models.CharField(default="\\N", max_length=255,null=True, blank=True)
  knownForTitles = models.CharField(default="\\N", max_length=255,null=True, blank=True)  # Assuming this is a comma-separated list of movie IDs
  img_url_asset = models.URLField(default="\\N",max_length=1024, null=True, blank=True)


class Movies(models.Model):
  IS_ADULT_CHOICES = [
    (0, 'False'),
    (1, 'True')
  ]

  TITLE_TYPE_CHOICES = [
    ('short', 'short'),
    ('movie', 'movie'),
    ('tvEpisode', 'tvEpisode'),
    ]
  
  tconst = models.CharField(max_length=255, unique=True, primary_key=True)
  titleType = models.CharField(max_length=20, choices=TITLE_TYPE_CHOICES, null=False)
  primaryTitle = models.CharField(max_length=255, null=False)
  originalTitle = models.CharField(max_length=255, null=False)
  isAdult = models.BooleanField(choices=IS_ADULT_CHOICES, default=0)
  startYear = models.CharField(max_length=255, null=False, blank=False)
  endYear = models.CharField(max_length=255, default='\\N', null=True, blank=True)
  runtimeMinutes = models.PositiveIntegerField(default="\\N",null=True, blank=True)
  genres = models.CharField(max_length=255,default="\\N", null=True, blank=True)
  img_url_asset = models.URLField(max_length=2000, default="\\N", blank=True, null=True)

class Crews(models.Model):#directors and writers of each movie
  tconst = models.CharField(max_length=255, unique=True, primary_key=True)
  directors = models.CharField(max_length=255 , null=True, blank=True, default="\\N")
  writers = models.CharField(max_length=255 , null=True, blank=True, default="\\N") 

class Episode(models.Model):#a table that contains the seasons and number of episodes of each TV show in the Movies database
  tconst = models.CharField(max_length=255, unique=True, primary_key=True)
  parentTconst = models.CharField(max_length=255, default="\\N",null=False, blank=False)
  seasonNumber = models.CharField(max_length=255, default="\\N",null=True, blank=True)
  episodeNumber = models.CharField(max_length=255, default="\\N",null=True, blank=True)

class Ratings(models.Model):
  tconst = models.CharField(max_length=255, unique=True, primary_key=True)
  averageRating = models.CharField(max_length=255, null=False, blank=False)
  numVotes = models.PositiveIntegerField(null=False, blank=False)

class Akas(models.Model):
    IS_ORIGINAL_CHOICES = [
     (0, 'False'),
     (1, 'True')
  ]
    titleId = models.CharField(max_length=255,null=False, blank=False)
    ordering = models.SmallIntegerField(null=False, blank=False)
    title = models.CharField(max_length=255,null=False, blank=False)
    region = models.CharField(max_length=255,null=True, blank=True, default="\\N")
    language = models.CharField(max_length=255,null=True, blank=True, default="\\N")
    types = models.CharField(max_length=255, null=True, blank=True, default="\\N")
    attributes = models.CharField(max_length=255, null=True, blank=True, default="\\N")
    isOriginalTitle = models.BooleanField(choices=IS_ORIGINAL_CHOICES, default=0)

    class Meta:
        # Define a composite primary key
        unique_together = (('titleId', 'ordering'))

class Principals(models.Model):
   tconst = models.CharField(max_length=255,null=False, blank=False)
   ordering = models.SmallIntegerField(null=False, blank=False)
   nconst = models.CharField(max_length=255,null=False, blank=False)
   category = models.CharField(max_length=255,null=False, blank=False)
   job = models.CharField(max_length=255,null=True, blank=True, default="\\N")
   characters = models.CharField(max_length=255,null=True, blank=True, default="\\N")
   img_url_asset = models.URLField(max_length=2000, default="\\N", blank=True, null=True)
   
   class Meta:
        # Define a composite primary key
    unique_together = (('tconst', 'ordering'))
  