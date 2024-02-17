from django.contrib import admin
from django.contrib.auth.models import User
from .models import *

admin.site.register(Names)
admin.site.register(Movies)
admin.site.register(Crews)
admin.site.register(Episode)
admin.site.register(Ratings)
admin.site.register(Akas)
admin.site.register(Principals)
admin.site.register(Liked)
admin.site.register(Disliked)

#admin.site.register(User)
# Register your models here.
