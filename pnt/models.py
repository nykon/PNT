# -*- coding: utf-8 -*-
from django.db import models
from synergy.contrib.history.models import HistoricalRecords

class Patient(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    pesel = models.CharField(max_length=255)

    phone = models.CharField(max_length=255)
    email = models.EmailField(blank=True)

    already_hospitalized = models.BooleanField()
    # grupa choiców dostepnych ustawiana jest na podstawie nazwy
    # pola
    gender = models.ForeignKey('records.CategoricalValue', related_name="patients_by_gender")
    education = models.ForeignKey('records.CategoricalValue', related_name="patients_by_education")
    occupation = models.ForeignKey('records.CategoricalValue', related_name="patients_by_occupation")

    history = HistoricalRecords()

    def __unicode__(self):
        return u"%s %s (%s)" % (self.first_name, self.last_name, self.pesel)


    class Meta:
        verbose_name = "Pacjent"
        verbose_name_plural = "Pacjenci"

class Address(models.Model):
    patient = models.OneToOneField('Patient')
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=255)
    
    history = HistoricalRecords()

    def __unicode__(self):
        return "%s, %s, %s" % (self.city, self.address, self.zip_code)

    class Meta:
        verbose_name = "Adres"
        verbose_name_plural = "Adresy"


class Disease(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    disease = models.ForeignKey('records.CategoricalValue')
    note = models.TextField(blank=True)

class Consultant(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    consultant = models.ForeignKey('records.CategoricalValue')

class CaseHistory(models.Model):
    patient = models.ForeignKey('Patient')
    diagnosis_year = models.IntegerField()

    diseases = models.ManyToManyField('records.CategoricalValue', through=Disease)

    treatements = models.ManyToManyField('records.CategoricalValue', through='Consultant', related_name="rr")

    history = HistoricalRecords()

    def __unicode__(self):
        return "Rok diagnozy: %s" % self.diagnosis_year

    class Meta:
        verbose_name = "Historia choroby"
        verbose_name_plural = "Historie choroby"

class LatestBP(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    sbp = models.FloatField()
    dbp = models.FloatField()

    class Meta:
        verbose_name = "Ostatnie zapisy BP"
        verbose_name_plural = "Ostatnie zapisy BP"

class HipotensionChemicals(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    hipotension_chemical = models.ForeignKey('records.CategoricalValue')
    morning_dose = models.CharField(max_length=4)
    midday_dose = models.CharField(max_length=4)
    evening_dose = models.CharField(max_length=4)
    taken_less_then_week = models.BooleanField()

    class Meta:
        verbose_name = "Lek hipotensyjny"
        verbose_name_plural = "Lek hipotensyjny"


class OtherChemicals(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    other_chemical = models.ForeignKey('records.CategoricalValue')
    morning_dose = models.CharField(max_length=4)
    midday_dose = models.CharField(max_length=4)
    evening_dose = models.CharField(max_length=4)

    
class FamilyDisease(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    family_disease = models.ForeignKey('records.CategoricalValue')

class LifeStyle(models.Model):
    patient = models.ForeignKey('Patient')

    cigarets_start_age = models.IntegerField(verbose_name="W jakim wieku zaczął palić?", null=True)
    cigarets_quit_age = models.IntegerField(verbose_name="W jakim wieku rzucił", null=True)
    cigarets_number = models.IntegerField(verbose_name="Liczba papierosów dziennie", null=True)
    work_passive_smoker = models.BooleanField(verbose_name="Bierny palacz w pracy?")
    home_passive_smoker = models.BooleanField(verbose_name="Bierny palacz w domu?")


    alc_start_age = models.IntegerField(verbose_name="W jakim wieku zaczął pić alkohol?")
    alc_quit_age = models.IntegerField(verbose_name="W jakim wieku przestał pić?")

    drugs_start_age = models.IntegerField(verbose_name="W jakim wieku zaczął brać narkotyki?")
    drugs_quit_age = models.IntegerField(verbose_name="W jakim wieku przestał brać?")
    drugs_taken = models.CharField(max_length=255, verbose_name="Jakie narkotyki przyjmował?")
    
    history = HistoricalRecords()

    def __unicode__(self):
        return "Rok diagnozy: %s" % self.diagnosis_year

    class Meta:
        verbose_name = "Styl życia"
        verbose_name_plural = "Styl życia"


class SexLife(models.Model):
    lifestyle = models.OneToOneField('LifeStyle')
    menopause = models.ForeignKey('records.CategoricalValue', related_name="sexlifes_by_contraceptive", null=True)
    pregnancy_count = models.IntegerField(verbose_name="Liczba ciąż")
    births_count = models.IntegerField(verbose_name="Liczba urodzeń żywych")
    miscarriage_count = models.IntegerField(verbose_name="Liczba poronień")
    still_birth_count = models.IntegerField(verbose_name="Liczba urodzeń martwych")
    
    
class SexLife(models.Model):
    lifestyle = models.ForeignKey('LifeStyle')
    contraceptive = models.ForeignKey('records.CategoricalValue', related_name="sexlifes_by_contraceptive")
    name = models.CharField(max_length=255, verbose_name="Nazwa leku")
    how_long = models.IntegerField(verbose_name="Jak długo był przyjmowany?")


class StimulantUsage(models.Model):
    lifestyle = models.ForeignKey('LifeStyle')
    stimulant = models.ForeignKey('records.CategoricalValue', related_name="stimulantusages_by_stimulant")
    usage_frequency = models.ForeignKey('records.CategoricalValue', related_name="stimulantusages_by_usage_frequency")
    avg_volume = models.FloatField(verbose_name="Ile ml przecietnie?")
    
    class Meta:
        unique_together = (('lifestyle', 'stimulant',))
        verbose_name = "Spożycie używek"
        verbose_name_plural = "Spożycie używek"


class Diet(models.Model):
    lifestyle = models.OneToOneField('LifeStyle')

    class Meta:
        verbose_name = "Dieta"
        verbose_name_plural = "Dietu"

class Meal(models.Model):
    diet = models.OneToOneField('Diet')

    
    ready_meal_count = models.IntegerField()
    meal_usage_frequency = models.ForeignKey('records.CategoricalValue', related_name="meal_by_meal_usage_frequency")

    outdoor_meal_count = models.IntegerField()
    outdoor_usage_frequency = models.ForeignKey('records.CategoricalValue', related_name="meal_by_outdoor_usage_frequency")

    fishes_per_week = models.IntegerField()
    fruits_per_week = models.IntegerField()
    veg_per_week = models.IntegerField()
    eggs_per_week = models.IntegerField()
    dairy_per_week = models.IntegerField()
    dairy_type = models.CharField(max_length=255)

    meat_per_week = models.IntegerField()
    meat_type = models.ForeignKey('records.CategoricalValue', related_name="meal_by_meat_type")

    oil_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_oil_type_most_frequent")
    meal_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_meal_type_most_frequent")
    bread_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_bread_type_most_frequent")
    butter_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_butter_type_most_frequent")
    
    
    class Meta:
        verbose_name = "Dieta"
        verbose_name_plural = "Dietu"


class Drink(models.Model):
    diet = models.OneToOneField('Diet')
    
    water_volume = models.ForeignKey('records.CategoricalValue', related_name="drinks_by_water_volume")
    sweet_dring_daily = models.IntegerField()
    veg_fruit_dring_daily = models.IntegerField()
    coffe_daily = models.IntegerField()
    tee_daily = models.IntegerField()

    tee_type = models.ForeignKey('records.CategoricalValue', related_name="drinks_by_tee_type")
    sugar_spoons = models.IntegerField()

    mainly_preservative_meal = models.BooleanField()
    extra_salt = models.BooleanField()

    class Meta:
        verbose_name = "Napoje"
        verbose_name_plural = "Napoje"


class PhysicalActivity(models.Model):
    diet = models.OneToOneField('Diet')
    
    work_mode = models.ForeignKey('records.CategoricalValue')
    # multiple
    # movement_mode = models.ForeignKey('records.CategoricalValue')
    
    daily_in_car = models.IntegerField()
    daily_in_bike = models.IntegerField()
    daily_on_foot = models.IntegerField()

    last_year_sport_months = models.IntegerField()
    last_year_sport_weeks = models.IntegerField()
    minutes_on_sport = models.IntegerField()
    prefered_sport = models.CharField(max_length=255)
    sport_activities = models.CharField(max_length=255)
    
    class Meta:
        verbose_name = u"Aktywność sportowa"
        verbose_name_plural = u"Aktywności sportowe"
