from datetime import date, datetime
from django.db import models
from django.db.models.deletion import CASCADE, DO_NOTHING, SET_NULL
from django.db.models.fields import DateTimeField
from django.db.models.fields.related import ForeignKey
from django.db.models.signals import ModelSignal
from django.contrib.auth.models import User
from django.utils import tree


class MiniatureType(models.Model):
    name = models.CharField(max_length=256, verbose_name="Typ modelu", unique=True)

    def __str__(self) -> str:
        return self.name


class CompetitionType(models.Model):
    name = models.CharField(max_length=256, verbose_name="Typ soutěže", blank=False, null=False, unique=True)
    # admin systému bude mít možnost modifikovat typy soutěží

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        verbose_name = "Typ soutěže"
        verbose_name_plural = "Typy soutěží"


class Person(models.Model):
    first_name = models.CharField(max_length=128, null=False, verbose_name="Křestní jméno")
    last_name = models.CharField(max_length=64, null=False, verbose_name="Příjmení")
    town = models.CharField(max_length=128, null=True, verbose_name="Obec")
    address = models.CharField(max_length=128, null=True, verbose_name="Adresa")
    country = models.CharField(max_length=64, null=True, verbose_name="Země") #toto udělat jako choices místo charfield...
    email = models.EmailField(null=True, verbose_name="Email")
    phone = models.CharField(max_length=256, null=True, verbose_name="Telefonní číslo")
    owner = models.ForeignKey(User, on_delete=CASCADE, null=True)


class Competition(models.Model):
    name = models.CharField(max_length=256, verbose_name="Název")

    # datum konání
    date_organisation = models.DateTimeField(verbose_name="Datum a čas konání", null=True, blank=True)
    date_registration = models.DateTimeField(blank=True, null=True, verbose_name="Datum a čas uzavření registrace")

    type = models.ForeignKey(CompetitionType, on_delete=models.SET_NULL, verbose_name="Typ soutěže", null=True, blank=True)
    # typ soutěže
    organizer = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Jméno organizátora")
    visibly = models.BooleanField(default=True, verbose_name="Zveřejnit soutěž") #TODO: možná je to matoucí toto a udělat všechno viditelné
    description = models.TextField(verbose_name="Popis", blank=True, null=True)
    competition_logo = models.ImageField(blank=True, null=True, upload_to='competition_logos/', verbose_name="Logo soutěže")

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        verbose_name = "Soutěž"
        verbose_name_plural = "Soutěže"


class Miniature(models.Model):
    miniature_type = models.ForeignKey(MiniatureType, on_delete=DO_NOTHING, verbose_name='Druh modelu')
    #typ modelu se vybere z aktualizovatelné tabulky modelů
    name = models.CharField(null=False, max_length=128, verbose_name='Jméno')
    manufacturer = models.CharField(null=False, max_length=128, verbose_name='Výrobce')
    scale = models.CharField(null=False, max_length=128, verbose_name='Měřítko')
    owner = models.ForeignKey(Person, on_delete=CASCADE, related_name='miniature')

    # scale = měřítko - ale tady bude potřeba specializovaná validace:
    # některé modely používají notaci 1/xx (např 1/35), jiné výšku figurky
    # v mm (např 35 mm).


class CompetitionMiniatureCategory(models.Model):
    name = models.CharField(max_length=128, verbose_name='Název soutěžní kategorie')
    competition = ForeignKey(Competition, on_delete=DO_NOTHING)

    def __str__(self) -> str:
        return self.name


class MiniatureRegistration(models.Model):
    time_of_registration = models.DateTimeField(auto_now_add=True)
    additional_information = models.TextField(null=True, verbose_name='Dodatečné informace k registraci modelu')
    category = models.ForeignKey(CompetitionMiniatureCategory, on_delete=SET_NULL, null=True, verbose_name='Kategorie modelu')
    # kategorie na každé soutěži jsou spravované jejím organizátorem
    miniature = ForeignKey(Miniature, on_delete=CASCADE, related_name='registration')
    competition = ForeignKey(Competition, on_delete=CASCADE, related_name='registration')
# many to many přes modely, s tím že registrace se dá vždy odstranit
# + další informace
