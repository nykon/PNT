# -*- coding: utf-8 -*-
from django.db import models
from synergy.contrib.history.models import HistoricalRecords
import datetime

def _default_unicode(obj):
    return "%s #%d" % (obj._meta.verbose_name, obj.id)
    
class Patient(models.Model):
    first_name = models.CharField(max_length=255, verbose_name="Imię")
    last_name = models.CharField(max_length=255, verbose_name="Nazwisko")
    pesel = models.CharField(max_length=11, verbose_name="Pesel", unique=True)

    phone = models.CharField(max_length=255, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-mail")

    # grupa choiców dostepnych ustawiana jest na podstawie nazwy
    # pola, chyba, że podano limit_choices_to
    gender = models.ForeignKey('records.CategoricalValue', related_name="patients_by_gender", verbose_name="Płeć", limit_choices_to={'group__name': 'gender'})
    education = models.ForeignKey('records.CategoricalValue', related_name="patients_by_education", verbose_name="Wykształcenie", limit_choices_to={'group__name': 'education'})
    occupation = models.ForeignKey('records.CategoricalValue', related_name="patients_by_occupation", verbose_name="Status aktywności zawodowej", limit_choices_to={'group__name': 'occupation'})
    occupation_name = models.CharField(max_length=255, verbose_name="Nazwa zawodu", blank=True)
    history = HistoricalRecords()

    def __unicode__(self):
        return u"%s %s (%s)" % (self.first_name, self.last_name, self.pesel)

    def get_birth_date(self):
        return datetime.date(int('19%s' % self.pesel[:2]), int(self.pesel[2:4]), int(self.pesel[4:6]))
    
    def get_age(self):
        return datetime.date.today().year - self.get_birth_date().year

    class Meta:
        verbose_name = "Pacjent"
        verbose_name_plural = "Pacjenci"

class Address(models.Model):
    patient = models.OneToOneField('Patient')
    address = models.CharField(max_length=255, verbose_name="Adres")
    city = models.CharField(max_length=255, verbose_name="Miasto")
    zip_code = models.CharField(max_length=255, verbose_name="Kod pocztowy")
    
    def __unicode__(self):
        return "%s, %s, %s" % (self.city, self.address, self.zip_code)

    class Meta:
        verbose_name = "Adres"
        verbose_name_plural = "Adresy"

class Disease(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    disease = models.ForeignKey('records.CategoricalValue', verbose_name="Choroba", limit_choices_to={'group__name': 'disease'})

    class Meta:
        unique_together = (('casehistory', 'disease'),)
        verbose_name = "Rodzaj choroby w historii"
        verbose_name_plural = "Rodzaje chorób w historii"

class GeneralDisease(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    generaldisease = models.ForeignKey('records.CategoricalValue', verbose_name="Choroba", limit_choices_to={'group__name': 'generaldisease'})
    note = models.TextField(blank=True, verbose_name="Notatka uzupełniająca")

    class Meta:
        unique_together = (('casehistory', 'generaldisease'),)
        verbose_name = "Choroba złożona w historii"
        verbose_name_plural = "Choroby złożone  w historii"


class Consultant(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    consultant = models.ForeignKey('records.CategoricalValue')

    class Meta:
        unique_together = (('casehistory', 'consultant'),)
        verbose_name = "Leczenie u specjalisty"
        verbose_name_plural = "Rodzaje leczenia u specjalisty"

class CaseHistory(models.Model):
    patient = models.ForeignKey('Patient', verbose_name="Pacjent")
    diagnosis_year = models.IntegerField(verbose_name="Rok diagnozy")
    already_hospitalized = models.BooleanField(verbose_name="Hospitalizowany w tutejszej klinice?")

    diseases = models.ManyToManyField('records.CategoricalValue', through=Disease, verbose_name="Choroby współistniejące", related_name="casehistory_by_disease")
    general_disepases = models.ManyToManyField('records.CategoricalValue', through=GeneralDisease, verbose_name="Choroby złożone", related_name="casehistory_by_general_disease")

    treatements = models.ManyToManyField('records.CategoricalValue', through='Consultant', related_name="casehistory_by_treatements", verbose_name="Leczenie u specjalisty")

    def __unicode__(self):
        return "Rok diagnozy: %s" % self.diagnosis_year

    class Meta:
        verbose_name = "Historia choroby"
        verbose_name_plural = "Historie choroby"

class LatestBP(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    sbp = models.FloatField(verbose_name="Ciśnienie skurczowe")
    dbp = models.FloatField(verbose_name="Ciśnienie rozkurczowe")

    class Meta:
        verbose_name = "Ostatnie zapisy BP"
        verbose_name_plural = "Ostatnie zapisy BP"


class ChemicalInternationalType(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nazwa", unique=True)

    class Meta:
        verbose_name = "Międzynarodowa nazwa leku"
        verbose_name_plural = "Międzynarodowe nazwy leków"

class PharmaGroup(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nazwa", unique=True)

    class Meta:
        verbose_name = "Grupa farmakoterapeutyczna"
        verbose_name_plural = "Grupy farmakoterapeutyczne"


class HipotensionChemical(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nazwa", unique=True)
    international_name = models.ForeignKey('ChemicalInternationalType', verbose_name="Nazwa międzynarodowa")
    pharma_group = models.ForeignKey('PharmaGroup', verbose_name="Grupa farmakoterapeutyczna")
        
    def __unicode__(self):
        return u"%s (%s, %s)" % (self.name, self.international_name.name, self.pharma_group.name)

    class Meta:
        unique_together = (('name', 'pharma_group',),)
        verbose_name = "Lek hipotensyjny"
        verbose_name_plural = "Lek hipotensyjny"
        ordering = ('name', 'international_name__name')
    
class HipotensionChemicalTaken(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    hipotension_chemical = models.ForeignKey('HipotensionChemical', verbose_name="Rodzaj leku")
    morning_dose = models.CharField(max_length=4, verbose_name="Dawka poranna")
    midday_dose = models.CharField(max_length=4, verbose_name="Dawka południowa")
    evening_dose = models.CharField(max_length=4, verbose_name="Dawka wieczorna")
    taken_less_then_week = models.BooleanField(verbose_name="Przyjmuje krócej niż tydzień")

    class Meta:
        unique_together = (('casehistory', 'hipotension_chemical',),)
        verbose_name = "Przyjmowany lek hipotensyjny"
        verbose_name_plural = "Przyjmowany lek hipotensyjny"

class OtherChemical(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    other_chemical = models.ForeignKey('records.CategoricalValue', limit_choices_to={'group__name': 'other_chemical'}, verbose_name="Nazwa leku")
    morning_dose = models.CharField(max_length=4, verbose_name="Dawka poranna")
    midday_dose = models.CharField(max_length=4, verbose_name="Dawka popołudniowa")
    evening_dose = models.CharField(max_length=4, verbose_name="Dawka wieczorna")

    class Meta:
        unique_together = (('casehistory', 'other_chemical',),)
        verbose_name = "Inny lek"
        verbose_name_plural = "Inny lek"
    
class FamilyDisease(models.Model):
    MEMBERS = (('a','Ojciec'), ('b', 'Matka'), ('c', 'Brat'), ('d', 'Siostra'))
    casehistory = models.ForeignKey('CaseHistory')
    familydisease = models.ForeignKey('records.CategoricalValue', limit_choices_to={'group__name': 'familydisease'}, verbose_name="Rodzaj choroby")
    member = models.CharField(max_length=1, choices=MEMBERS, verbose_name="Członek rodziny")
    age = models.IntegerField(verbose_name="Wiek w którym zachorował", null=True, blank=True)
    
    class Meta:
        unique_together = (('casehistory', 'familydisease', 'member'),)
        verbose_name = "Choroba w rodzinie"
        verbose_name_plural = "Choroby w rodzinie"

class LifeStyle(models.Model):
    patient = models.ForeignKey('Patient', verbose_name="Pacjent")

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
    
    stimulants = models.ManyToManyField('records.CategoricalValue', through='Stimulant', verbose_name="Spożycie używek", related_name="lifestyle_by_stimulants")
    contraceptives = models.ManyToManyField('records.CategoricalValue', through='Contraceptive', verbose_name="Leki antykoncepcyjne", related_name="lifestyle_by_contraceptive")

    def __unicode__(self):
        return _default_unicode(self)


    class Meta:
        verbose_name = u"Styl życia"
        verbose_name_plural = u"Styl życia"


class WomenSexLife(models.Model):
    lifestyle = models.OneToOneField('LifeStyle')
    menopause = models.ForeignKey('records.CategoricalValue', related_name="womensexlifes_by_contraceptive", null=True, verbose_name="Menopauza", limit_choices_to={'group__name': 'menopause'})
    pregnancy_count = models.IntegerField(verbose_name="Liczba ciąż")
    births_count = models.IntegerField(verbose_name="Liczba urodzeń żywych", )
    miscarriage_count = models.IntegerField(verbose_name="Liczba poronień")
    still_birth_count = models.IntegerField(verbose_name="Liczba urodzeń martwych")

    class Meta:
        verbose_name = "Informacje dot. kobiety"
        verbose_name_plural = "Informacje dot. kobiet"
    
    
class Contraceptive(models.Model):
    lifestyle = models.ForeignKey('LifeStyle')
    contraceptive = models.ForeignKey('records.CategoricalValue', related_name="sexlifes_by_contraceptive", limit_choices_to={'group__name': 'contraceptive'})
    name = models.CharField(max_length=255, verbose_name="Nazwa leku")
    how_long = models.IntegerField(verbose_name="Jak długo był przyjmowany (miesiące)?")

    class Meta:
        unique_together = (('lifestyle', 'contraceptive'),)
        verbose_name = "Lek antykoncpecyjny"
        verbose_name_plural = "Leki antykoncpecyjne"


class Stimulant(models.Model):
    FREQ = (('a', 'codziennie'), ('b', 'co tydzień'), ('c', 'co miesiąc'), ('d', 'co rok'))
    lifestyle = models.ForeignKey('LifeStyle')
    stimulant = models.ForeignKey('records.CategoricalValue', related_name="stimulant_by_stimulant", limit_choices_to={'group__name': 'stimulant'})
    usage_frequency = models.CharField(max_length=1, choices=FREQ, verbose_name="Jak często spożywa?")
    avg_volume = models.FloatField(verbose_name="Ile ml przeciętnie wypija za każdym razem?")
    
    class Meta:
        unique_together = (('lifestyle', 'stimulant',))
        verbose_name = "Spożycie używek"
        verbose_name_plural = "Spożycie używek"


class MealType(models.Model):
    meal = models.ForeignKey('Meal')
    mealtype = models.ForeignKey('records.CategoricalValue', related_name="mealtype_by_meal", verbose_name="Rodzaj pożywienia", limit_choices_to={'group__name': 'mealtype'})
    times_per_week = models.IntegerField(verbose_name="Ile razy w tygodniu?")

class Meal(models.Model):
    patient = models.ForeignKey('Patient', verbose_name="Pacjent")
    
    ready_meal_count = models.IntegerField(verbose_name="Jak często kupuje Pani/Pan gotowe posiłki?")
    ready_meal_frequency = models.ForeignKey('records.CategoricalValue', related_name="meal_by_meal_usage_frequency", verbose_name="Tydzień/miesiąc/rok", limit_choices_to={'group__name': 'ready_meal_frequency'})

    outdoor_meal_count = models.IntegerField(verbose_name="Jak często je Pani/Pan w restauracjach typu fast-food?")
    outdoor_meal_frequency = models.ForeignKey('records.CategoricalValue', related_name="meal_by_outdoor_usage_frequency", verbose_name="Tydzień/miesiąc/rok", limit_choices_to={'group__name': 'outdoor_meal_frequency'})

    meal_types = models.ManyToManyField('records.CategoricalValue', through='MealType', verbose_name="Rodzaj pożywienia")
    dairy_type = models.CharField(max_length=255, verbose_name="Jaki typ nabiału najczęściej spożywa?")

    meat_type = models.ForeignKey('records.CategoricalValue', related_name="meal_by_meat_type", verbose_name="Jaki typ mięsa najczęściej spożywa?")

    oil_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_oil_type_most_frequent", verbose_name="Jakiego tłuszczu używa do przyrządzania potraw?", limit_choices_to={'group__name': 'oil_type_most_frequent'})
    meal_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_meal_type_most_frequent", verbose_name="Jaki typ potraw najczęściej spożywa", limit_choices_to={'group__name': 'meal_type_most_frequent'})
    bread_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_bread_type_most_frequent", verbose_name="Jaki typ pieczywa spożywa najczęściej?", limit_choices_to={'group__name': 'bread_type_most_frequent'})
    butter_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_butter_type_most_frequent", verbose_name="Czym zazwyczaj smaruje pieczywo?",  limit_choices_to={'group__name': 'butter_type_most_frequent'})
    

    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = u"Posiłki"
        verbose_name_plural = u"Posiłki"

class Drink(models.Model):
    patient = models.ForeignKey('Patient', verbose_name="Pacjent")
    
    water_volume = models.ForeignKey('records.CategoricalValue', related_name="drinks_by_water_volume", verbose_name="Ile szklanek wody dziennie wypija? ")
    sweet_dring_daily = models.IntegerField(verbose_name="Ile szklanek słodzonych napojów gazowanych wypija dziennie?")
    veg_fruit_dring_daily = models.IntegerField(verbose_name="Ile szklanek soków owocowo-warzywnych dziennie wypija?")
    coffe_daily = models.IntegerField(verbose_name="Ile szklanek kawy dziennie wypija?")
    tee_daily = models.IntegerField(verbose_name="Ile szklanek herbaty dziennie wypija?")
    tee_type = models.ForeignKey('records.CategoricalValue', related_name="drinks_by_tee_type", verbose_name="Jaki rodzaj herbaty najczęściej pije?")
    sugar_spoons = models.IntegerField(verbose_name="Iloma łyżeczkami cukru słodzi herbatę/kawę?")

    mainly_preservative_meal = models.BooleanField(verbose_name="Czy spożywa Pani/Pan głównie produkty konserwowe?")
    extra_salt = models.BooleanField(verbose_name="Czy dosala Pani/Pan potrawy?")

    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = "Napoje"
        verbose_name_plural = "Napoje"

class PhysicalActivity(models.Model):
    patient = models.ForeignKey('Patient', verbose_name="Pacjent")

    work_mode = models.ForeignKey('records.CategoricalValue', verbose_name="Jaki tryb pracy Pani/Pan wykonuje?")
    # multiple
    # movement_mode = models.ForeignKey('records.CategoricalValue')
    
    daily_in_car = models.IntegerField(verbose_name="Ile minut dziennie spędza w samochodzie?")
    daily_in_bike = models.IntegerField(verbose_name="Ile minut dziennie jeździ rowerem?")
    daily_on_foot = models.IntegerField(verbose_name="Ile minut dziennie chodzi pieszo?")

    last_year_sport_months = models.IntegerField(verbose_name="Ile miesięcy w ciągu ostatniego roku uprawiał regularnie sport?")
    last_year_sport_weeks = models.IntegerField(verbose_name="Ile razy w tygodniu uprawia sport?")
    minutes_on_sport = models.IntegerField(verbose_name="Ile minut za każdym razem poświęca na uprawianie sportu?")
    prefered_sport = models.CharField(max_length=255, verbose_name="Jaki sport uprawiał najbardziej regularnie w ciągu ostatniego roku?")
    sport_activities = models.CharField(max_length=255, verbose_name="Jaki aktualnie wykonuje wysiłek fizyczny poza godzinami pracy? ")
    
    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = u"Aktywność sportowa"
        verbose_name_plural = u"Aktywności sportowe"

class EpworthScale(models.Model):
    apnoea = models.OneToOneField('Apnoea', verbose_name="Ocena bezdechu")

    CHOICES = (('0', 'Nigdy nie zasnę'), ('1', 'Małe prawdopodobieństwo'),
               ('2', 'Prawdopodobnie tak'), ('3', 'Prawie na pewno'))

    sitting = models.CharField(max_length=1, choices=CHOICES, verbose_name="Siedząc lub/i czytając")
    tv_watch = models.CharField(max_length=1, choices=CHOICES, verbose_name="Oglądając telewizję")
    public = models.CharField(max_length=1, choices=CHOICES, verbose_name="Siedząc w miejscu publicznym, np.: w teatrze lub na zebraniu")
    in_car_passenger = models.CharField(max_length=1, choices=CHOICES, verbose_name="Podczas godzinnej, nieprzerwanej jazdy samochodem jako pasażer")
    afternoon_rest = models.CharField(max_length=1, choices=CHOICES, verbose_name="Po południu, leżąc celem odpoczynku")
    talk_sitting = models.CharField(max_length=1, choices=CHOICES, verbose_name="Podczas rozmowy, siedząc")
    after_dinner = models.CharField(max_length=1, choices=CHOICES, verbose_name="Po obiedzie (bez alkoholu), siedząc w spokojnym miejscu")
    car_driving = models.CharField(max_length=1, choices=CHOICES, verbose_name="Prowadząc samochód, podczas kilkuminutowego oczekiwania w korku")
    
    class Meta:
        verbose_name = u"Skala Epworth"
        verbose_name_plural = u"Skala Epworth"

class Apnoea(models.Model):
    patient = models.ForeignKey('Patient', verbose_name="Pacjent")

    FREQ = (('1', 'Nigdy'), ('2', 'Rzadko (mniej niż raz w tygodniu)'),
               ('3', 'Okazjonalnie (1 - 3 x/tydzień)'), ('4', 'Często (częściej niż 3 x w tygodniu)'))    

    OVERWEIGHT = (('1', 'Wcale'), ('2', 'niewielką (4,5 – 9 kg) = w oryginale to 10-20 funtów(?)'),
                  ('3', 'umiarkowaną (10-20 kg) = w oryginale to 20-40 funtów(?)'), 
                  ('4', 'znaczną (powyżej 20 kg) = w oryginale to > 40 funtów(?)'))    

    snooring = models.CharField(max_length=1, choices=FREQ, verbose_name=u"Jak często zauważa Pan/Pani sam-a lub mówią o tym współmieszkańcy, że Pana/Pani chrapanie jest na tyle głośne, że przeszkadza im spać?")
    sleap_apnoea = models.CharField(max_length=1, choices=FREQ, verbose_name=u"Jak często mówiono Panu/Pani, że ma Pan/Pani „przerwy w oddychaniu podczas snu?")
    overweight = models.CharField(max_length=1, choices=OVERWEIGHT, verbose_name=u"Ile ma Pan/Pani kilogramów (w oryginale funtów) nadwagi?")
    # D. Ile wynosi Pana/Pani wynik w skali Epworth?
    identifications = models.ManyToManyField('records.CategoricalValue', through='ApnoeaIdentification', verbose_name="Czynniki identyfikujące")

    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = u"Ocena Ryzyka Bezdechu Sennego"
        verbose_name_plural = u"Oceny Ryzyka Bezdechu Sennego"

class ApnoeaIdentification(models.Model):
    apnoea = models.ForeignKey('Apnoea')
    apnoeaidentification = models.ForeignKey('records.CategoricalValue', related_name="apnoea_by_identification", verbose_name="Rozpoznanie", limit_choices_to={'group__name': 'apnoeaidentification'})

    class Meta:
        unique_together = (('apnoea', 'apnoeaidentification'),)
        verbose_name = u"Czynnik identyfikujący bezdech"
        verbose_name_plural = u"Czynniki identyfikujące bezdech"

class LifeQuality(models.Model):
    patient = models.ForeignKey('Patient', verbose_name="Pacjent")
    alergen_chemical = models.TextField(verbose_name="Jeżeli występują alergie na leki, podać jakie i dla jakich leków", blank=True)
    factors = models.ManyToManyField('records.CategoricalValue', through='LifeQualityFactor', verbose_name="Czynniki jakościujące")

    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = u"Jakość życia"
        verbose_name_plural = u"Jakość życia"

class LifeQualityFactor(models.Model):
    lifequality = models.ForeignKey('LifeQuality')
    lifequalityfactor = models.ForeignKey('records.CategoricalValue', related_name="lifequiality_by_factor", verbose_name="Faktor", limit_choices_to={'group__name': 'lifequalityfactor'})    

    class Meta:
        unique_together = (('lifequality', 'lifequalityfactor'),)
        verbose_name = u"Czynnik jakości życia"
        verbose_name_plural = u"Czynniki jakości życia"

#class Antropometrics(models.Model):
#    pass

#class ABPM(models.Model):
#    pass



