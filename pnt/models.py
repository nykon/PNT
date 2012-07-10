# -*- coding: utf-8 -*-
from django.db import models
from synergy.contrib.history.models import HistoricalRecords
import datetime
from django.core.exceptions import ObjectDoesNotExist

def _default_unicode(obj):
    return u"%s #%d" % (obj._meta.verbose_name, obj.id)
    
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
        try:
            return datetime.date(int('19%s' % self.pesel[:2]), int(self.pesel[2:4]), int(self.pesel[4:6]))
        except:
            return datetime.date(1000, 1, 1)
    
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

class Appointment(models.Model):
    patient = models.ForeignKey('Patient', related_name="appointments", verbose_name="Pacjent")
    date = models.DateField(verbose_name="Data")
    time = models.TimeField(verbose_name="Godzina", null=True, blank=True)

    def __unicode__(self):
        return u"Wizyta z dnia: %s, %s" % (self.date, self.patient)

    def get_data(self):
        models = ('casehistory', 'physicalactivity', 'lifequality', 'lifestyle', 'meal', 'drink', 'apnoea', 'etiology', 'sideissue')
        data = {}
        for model in models:
            try:
                data[model] = getattr(self, model)
            except ObjectDoesNotExist:
                data[model] = None
        return data

    class Meta:
        verbose_name = "Wizyta"
        verbose_name_plural = "Wizyty"

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
    note = models.TextField(verbose_name="Notatka", blank=True)
    class Meta:
        unique_together = (('casehistory', 'consultant'),)
        verbose_name = "Leczenie u specjalisty"
        verbose_name_plural = "Rodzaje leczenia u specjalisty"


class WomenSexLife(models.Model):
    casehistory = models.OneToOneField('CaseHistory')
    menopause = models.ForeignKey('records.CategoricalValue', related_name="womensexlifes_by_contraceptive", null=True, verbose_name="Menopauza", limit_choices_to={'group__name': 'menopause'})
    pregnancy_count = models.IntegerField(verbose_name="Liczba ciąż")
    births_count = models.IntegerField(verbose_name="Liczba urodzeń żywych", )
    miscarriage_count = models.IntegerField(verbose_name="Liczba poronień")
    still_birth_count = models.IntegerField(verbose_name="Liczba urodzeń martwych")

    class Meta:
        verbose_name = "Wywiad ginekologiczno-położniczy"
        verbose_name_plural = "Wywiad ginekologiczno-położniczy"
    
    
class Contraceptive(models.Model):
    casehistory = models.ForeignKey('CaseHistory')
    contraceptive = models.ForeignKey('records.CategoricalValue', related_name="sexlifes_by_contraceptive", limit_choices_to={'group__name': 'contraceptive'})
    name = models.CharField(max_length=255, verbose_name="Nazwa leku")
    how_long = models.IntegerField(verbose_name="Liczba miesięcy stosowania")

    class Meta:
        unique_together = (('casehistory', 'contraceptive'),)
        verbose_name = "Lek antykoncpecyjny"
        verbose_name_plural = "Leki antykoncpecyjne"

class CaseHistory(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")

    diagnosis_year = models.IntegerField(verbose_name="Rok diagnozy")
    already_hospitalized = models.BooleanField(verbose_name="Hospitalizowany w tutejszej klinice?")

    diseases = models.ManyToManyField('records.CategoricalValue', through=Disease, verbose_name="Choroby współistniejące", related_name="casehistory_by_disease")
    general_disepases = models.ManyToManyField('records.CategoricalValue', through=GeneralDisease, verbose_name="Choroby współistniejące z opisem", related_name="casehistory_by_general_disease")

    treatements = models.ManyToManyField('records.CategoricalValue', through='Consultant', related_name="casehistory_by_treatements", verbose_name="Leczenie u specjalisty")
    contraceptives = models.ManyToManyField('records.CategoricalValue', through='Contraceptive', verbose_name="Leki antykoncepcyjne", related_name="lifestyle_by_contraceptive")

    def __unicode__(self):
        return u"Rok diagnozy: %s (%s)" % (self.diagnosis_year, self.appointment.patient)

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
        verbose_name = "Rodzaj leku hipotensyjnego"
        verbose_name_plural = "Rodzaje leków hipotensyjnych"
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
        verbose_name = "Lek hipotensyjny"
        verbose_name_plural = "Leki hipotensyjne"

class OtherChemical(models.Model):
    casehistory = models.ForeignKey('CaseHistory', related_name="other_chemicals")
    other_chemical = models.CharField(max_length=255, verbose_name="Nazwa leku")
    morning_dose = models.CharField(max_length=4, verbose_name="Dawka poranna")
    midday_dose = models.CharField(max_length=4, verbose_name="Dawka popołudniowa")
    evening_dose = models.CharField(max_length=4, verbose_name="Dawka wieczorna")

    class Meta:
        unique_together = (('casehistory', 'other_chemical',),)
        verbose_name = "Lek pozostałyk"
        verbose_name_plural = "Leki pozostałe"
    
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
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")

    cigarets_start_age = models.IntegerField(verbose_name="Wiek rozpoczęcia palenia", null=True)
    cigarets_quit_age = models.IntegerField(verbose_name="Wiek rzucenia palenia", null=True)
    cigarets_number = models.IntegerField(verbose_name="Liczba pap. dziennie", null=True)
    work_passive_smoker = models.BooleanField(verbose_name="Bierny palacz w pracy?")
    home_passive_smoker = models.BooleanField(verbose_name="Bierny palacz w domu?")

    alc_start_age = models.IntegerField(verbose_name="Wiek rozp. spożycia alkoholu?")
    alc_quit_age = models.IntegerField(verbose_name="Wiek zakończenia spożycia alk.")

    drugs_start_age = models.IntegerField(verbose_name="Wieku rozp. przyjm. narkotyków?")
    drugs_quit_age = models.IntegerField(verbose_name="Wiek zakończnia przyjm. narkot.")
    drugs_taken = models.CharField(max_length=255, verbose_name="Przyjmowane narkotyki")
    
    stimulants = models.ManyToManyField('records.CategoricalValue', through='Stimulant', verbose_name="Spożycie używek", related_name="lifestyle_by_stimulants")

    def __unicode__(self):
        return _default_unicode(self)


    class Meta:
        verbose_name = u"Styl życia"
        verbose_name_plural = u"Styl życia"


class Stimulant(models.Model):
    FREQ = (('a', 'codziennie'), ('b', 'co tydzień'), ('c', 'co miesiąc'), ('d', 'co rok'))
    lifestyle = models.ForeignKey('LifeStyle')
    stimulant = models.ForeignKey('records.CategoricalValue', related_name="stimulant_by_stimulant", limit_choices_to={'group__name': 'stimulant'})
    usage_frequency = models.CharField(max_length=1, choices=FREQ, verbose_name="Częstotliwość spożycia")
    avg_volume = models.FloatField(verbose_name="Ilość ml przeciętnie wypijanych za każdym razem")
    
    class Meta:
        unique_together = (('lifestyle', 'stimulant',))
        verbose_name = "Spożycie używek"
        verbose_name_plural = "Spożycie używek"


class MealType(models.Model):
    meal = models.ForeignKey('Meal')
    mealtype = models.ForeignKey('records.CategoricalValue', related_name="mealtype_by_meal", verbose_name="Rodzaj pożywienia", limit_choices_to={'group__name': 'mealtype'})
    times_per_week = models.IntegerField(verbose_name="Ile razy w tygodniu?")

class Meal(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    
    ready_meal_count = models.IntegerField(verbose_name="Jak często kupuje gotowe posiłki?")
    ready_meal_frequency = models.ForeignKey('records.CategoricalValue', related_name="meal_by_meal_usage_frequency", verbose_name="Na dzień/tydzień/miesiąc", limit_choices_to={'group__name': 'ready_meal_frequency'})

    outdoor_meal_count = models.IntegerField(verbose_name="Jak często jada w restauracjach typu fast food?")
    outdoor_meal_frequency = models.ForeignKey('records.CategoricalValue', related_name="meal_by_outdoor_usage_frequency", verbose_name="Na dzień/tydzień/miesiąc", limit_choices_to={'group__name': 'outdoor_meal_frequency'})

    meal_types = models.ManyToManyField('records.CategoricalValue', through='MealType', verbose_name="Rodzaj pożywienia")
    dairy_type = models.CharField(max_length=255, verbose_name="Typ nabiału spożywany najczęściej")

    meat_type = models.ForeignKey('records.CategoricalValue', related_name="meal_by_meat_type", verbose_name="Typ mięsa spożywany najczęściej")

    oil_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_oil_type_most_frequent", verbose_name="Typ tłuszczu używany do przyrządzania potraw", limit_choices_to={'group__name': 'oil_type_most_frequent'})
    meal_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_meal_type_most_frequent", verbose_name="Typ potrawy najczęściej spożywanej", limit_choices_to={'group__name': 'meal_type_most_frequent'})
    bread_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_bread_type_most_frequent", verbose_name="Typ pieczywa najczęściej spożywanego", limit_choices_to={'group__name': 'bread_type_most_frequent'})
    butter_type_most_frequent = models.ForeignKey('records.CategoricalValue', related_name="meal_by_butter_type_most_frequent", verbose_name="Rodzaj tłuszczu używanego  zazwyczaj do smarowania pieczywa",  limit_choices_to={'group__name': 'butter_type_most_frequent'})

    mainly_preservative_meal = models.BooleanField(verbose_name="Spożywa głównie produkty konserwowe")
    extra_salt = models.BooleanField(verbose_name="Dosala potrawy")
    

    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = u"Posiłki"
        verbose_name_plural = u"Posiłki"

class Drink(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    
    water_volume = models.ForeignKey('records.CategoricalValue', related_name="drinks_by_water_volume", verbose_name="Liczba szklanek wypijanych dziennie")
    sweet_dring_daily = models.IntegerField(verbose_name="Liczba szklanek słodzonych napojów gazowanych wypijanych dziennie")
    veg_fruit_dring_daily = models.IntegerField(verbose_name="Liczba szklanek soków owocowo-warzywnych wypijanych dziennie")
    coffe_daily = models.IntegerField(verbose_name="Liczba szklanek kawy wypijanych dziennie")
    tee_daily = models.IntegerField(verbose_name="Liczba szklanek herbaty wypijanych dziennie")
    tee_type = models.ForeignKey('records.CategoricalValue', related_name="drinks_by_tee_type", verbose_name="Najczęściej wypijany rodzaj herbaty")
    sugar_spoons = models.IntegerField(verbose_name="Liczba łyżeczek cukru do  herbaty/kawy")

    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = "Napoje"
        verbose_name_plural = "Napoje"

class PhysicalActivity(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")

    work_mode = models.ForeignKey('records.CategoricalValue', verbose_name="Tryb pracy")
    # multiple
    # movement_mode = models.ForeignKey('records.CategoricalValue')
    
    daily_in_car = models.IntegerField(verbose_name="Liczba minut dziennie w  samochodzie?")
    daily_in_bike = models.IntegerField(verbose_name="Liczba minut dziennie rowerem")
    daily_on_foot = models.IntegerField(verbose_name="Liczba minut dziennie pieszo")

    last_year_sport_months = models.IntegerField(verbose_name="Liczba miesięcy w ciągu ostatniego roku regularnego sportu")
    last_year_sport_weeks = models.IntegerField(verbose_name="Liczba razy w tygodniu gdy uprawia sport?")
    minutes_on_sport = models.IntegerField(verbose_name="Liczba minut za każdym razem poświęcanych na uprawianie sportu?")
    prefered_sport = models.CharField(max_length=255, verbose_name="Sport uprawiany najbardziej regularnie w ciągu ostatniego roku")
    sport_activities = models.CharField(max_length=255, verbose_name="Aktualnie wykonywany wysiłek fizyczny poza godzinami pracy")
    
    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = u"Aktywność sportowa"
        verbose_name_plural = u"Aktywności sportowe"

class EpworthScale(models.Model):
    apnoea = models.OneToOneField('Apnoea', verbose_name="Ocena bezdechu")

    CHOICES = (('1', 'Nigdy nie zasnę'), ('2', 'Małe prawdopodobieństwo'),
               ('3', 'Prawdopodobnie tak'), ('4', 'Prawie na pewno'))

    sitting = models.CharField(max_length=1, choices=CHOICES, verbose_name="Siedząc lub/i czytając")
    tv_watch = models.CharField(max_length=1, choices=CHOICES, verbose_name="Oglądając telewizję")
    public = models.CharField(max_length=1, choices=CHOICES, verbose_name="Siedząc w miejscu publicznym, np.: w teatrze lub na zebraniu")
    in_car_passenger = models.CharField(max_length=1, choices=CHOICES, verbose_name="Podczas godzinnej, nieprzerwanej jazdy samochodem jako pasażer")
    afternoon_rest = models.CharField(max_length=1, choices=CHOICES, verbose_name="Po południu, leżąc celem odpoczynku")
    talk_sitting = models.CharField(max_length=1, choices=CHOICES, verbose_name="Podczas rozmowy, siedząc")
    after_dinner = models.CharField(max_length=1, choices=CHOICES, verbose_name="Po obiedzie (bez alkoholu), siedząc w spokojnym miejscu")
    car_driving = models.CharField(max_length=1, choices=CHOICES, verbose_name="Prowadząc samochód, podczas kilkuminutowego oczekiwania w korku")
    
    def get_points(self):
        return sum(map(int, (getattr(self, attr) for attr in ('sitting', 'tv_watch', 'public', 'in_car_passenger', 'afternoon_rest', 'talk_sitting', 'after_dinner', 'car_driving'))))

    def at_risk(self):
        return self.get_points() >= 10

    class Meta:
        verbose_name = u"Skala Epworth"
        verbose_name_plural = u"Skala Epworth"

class Apnoea(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")

    FREQ = (('1', 'Nigdy'), ('2', 'Rzadko (mniej niż raz w tygodniu)'),
               ('3', 'Okazjonalnie (1 - 3 x/tydzień)'), ('4', 'Często (częściej niż 3 x w tygodniu)'))    

    OVERWEIGHT = (('1', 'Wcale'), ('2', 'niewielką (4,5 – 9 kg) = w oryginale to 10-20 funtów(?)'),
                  ('3', 'umiarkowaną (10-20 kg) = w oryginale to 20-40 funtów(?)'), 
                  ('4', 'znaczną (powyżej 20 kg) = w oryginale to > 40 funtów(?)'))    

    snooring = models.CharField(max_length=1, choices=FREQ, verbose_name=u"Jak często zauważa lub mówią o tym współmieszkańcy, że chrapanie jest na tyle głośne, że przeszkadza im spać?")
    sleap_apnoea = models.CharField(max_length=1, choices=FREQ, verbose_name=u"Jak często mówiono że ma „przerwy w oddychaniu podczas snu?")
    overweight = models.CharField(max_length=1, choices=OVERWEIGHT, verbose_name=u"Ile ma kilogramów (w oryginale funtów) nadwagi?")
    # D. Ile wynosi Pana/Pani wynik w skali Epworth?
    relateddiseases = models.ManyToManyField('records.CategoricalValue', through='ApnoeaRelatedDisease', related_name="a", verbose_name="Schorzenia sugerujące bezdech senny")
    identifications = models.ManyToManyField('records.CategoricalValue', through='ApnoeaIdentification', related_name="b", verbose_name="Objawy sugerujące bezdech senny")


    def get_epworth_points(self):
        try:
            return self.epworthscale.get_points()
        except ObjectDoesNotExist:
            return None
        
    def at_epworth_risk(self):
        try:
            return self.epworthscale.at_risk()
        except ObjectDoesNotExist:
            return None
        

    def get_epworth_scale(self):
        epworth_points = self.get_epworth_points()
        if epworth_points:
            for i, limit in enumerate((8, 13, 18, 19)):
                if epworth_points <= limit:
                    return i +1
        return None
            

    def get_apnoea_points(self):
        epworth_scale = self.get_epworth_scale()
        if epworth_scale:
            return sum([int(getattr(self, state)) for state in ('snooring', 'sleap_apnoea', 'overweight')]) + epworth_scale
        return None

    def get_apnoea_risk_limit(self):
        limits = {True: 12, False: 16}
        return limits[self.has_apnoea_suggestions()]

    def at_apnoea_risk(self):
        return self.get_apnoea_points() >= self.get_apnoea_risk_limit()

    def has_apnoea_suggestions(self):
        return self.relateddiseases.exists() or self.identifications.exists()
        
    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = u"Bezdech Senny"
        verbose_name_plural = u"Bezdech Senny"

class ApnoeaRelatedDisease(models.Model):
    apnoea = models.ForeignKey('Apnoea')
    apnoearelateddisease = models.ForeignKey('records.CategoricalValue', related_name="apnoea_by_disease", verbose_name="Rozpoznanie", limit_choices_to={'group__name': 'apnoearelateddisease'})

    class Meta:
        unique_together = (('apnoea', 'apnoearelateddisease'),)
        verbose_name = u"Schorzenie sugerujące bezdech senny"
        verbose_name_plural = u"Schorzenia sugerujące bezdech senny"


class ApnoeaIdentification(models.Model):
    apnoea = models.ForeignKey('Apnoea')
    apnoeaidentification = models.ForeignKey('records.CategoricalValue', related_name="apnoea_by_identification", verbose_name="Rozpoznanie", limit_choices_to={'group__name': 'apnoeaidentification'})

    class Meta:
        unique_together = (('apnoea', 'apnoeaidentification'),)
        verbose_name = u"Objaw sugerujący bezdech senny"
        verbose_name_plural = u"Objawy sugerujące bezdech senny"

        
class SideIssue(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    has_allergy = models.BooleanField(verbose_name = "Czy występują alergie na leki ?")
    alergen_chemical = models.TextField(verbose_name="Jeżeli występują alergie na leki, podać jakie i dla jakich leków", blank=True)
    factors = models.ManyToManyField('records.CategoricalValue', through='SideIssueFactor', verbose_name="Działania niepożądane")

    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = u"Objaw uboczny"
        verbose_name_plural = u"Objawy uboczne"

class SideIssueFactor(models.Model):
    sideissue = models.ForeignKey('SideIssue')
    sideissuefactor = models.ForeignKey('records.CategoricalValue', related_name="sideissues_by_factor", verbose_name="Faktor", limit_choices_to={'group__name': 'sideissuefactor'})    

    class Meta:
        unique_together = (('sideissue', 'sideissuefactor'),)
        verbose_name = u"Czynnik efektów ubocznych"
        verbose_name_plural = u"Czynniki efektów ubocznych"
        

class LifeQuality(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")


    STATES = (('a', 'Doskonały'), ('b', 'Bardzo doby'), ('c', 'Dobry'), ('d', 'Zadowalający'), ('e', 'Niezadowalający'))
    health_state = models.CharField(max_length=1, choices=STATES, verbose_name="Stan drowia")

    CHANGES = (('a', 'Dużo lepiej niż rok temu'), ('b', 'Trochę lepiej niż rok temu'), ('c', 'Bardzo podobnie jak rok temu'), 
               ('d', 'Trochę gorzej niż rok temu'), ('e', 'Dużo gorzej niż rok temu'))
    health_change = models.CharField(max_length=1, choices=CHANGES, verbose_name="Stan zdrowia w porównaniu z analogicznym okresem w ubiegłym roku")


    IMPACTS = (('a', 'Nie, wcale'), ('b', 'Rzadko'), ('c', 'Czasami'), 
               ('d', 'Nawet bardzo'), ('e', 'Bardzo duży'))
    problem_impact = models.CharField(max_length=1, choices=IMPACTS, verbose_name="Jak często problemy zdrowotne/emocjonalne wpływały na aktywności i kontakty w ciągu ostatniego miesiąca")


    PAIN_FREQ = (('a', 'Nigdy'), ('b', 'Bardzo rzadko'), ('c', 'Rzadko'), ('d', 'Wyjątkowo'), ('e', 'Często'), ('f', 'Bardzo często'))
    pain_freq= models.CharField(max_length=1, choices=CHANGES, verbose_name="Liczba razy gdy oczywał ból w ciągu ostatniego misiąca")


    PAIN_IMPACT = (('a', 'Wcale'), ('b', 'Trochę'), ('c', 'Średnio'), ('d', 'Nawet bardzo'), ('e', 'Bardzo'))
    pain_impact = models.CharField(max_length=1, choices=PAIN_IMPACT, verbose_name="Jak często w ostatnim miesiącu ból zakłócał normalną pracę (zawodową/domową)?")


    CONDITION_IMPACT = (('a', 'Cały czas'), ('b', 'Większość czasu'), ('c', 'Część czasu'), ('d', 'Mało czasu'), ('e', 'Wcale'))
    condition_impact = models.CharField(max_length=1, choices=CONDITION_IMPACT, verbose_name="Jak często w ostatnim miesiącu zdrowie lub emocje wpływały na kontakty towarzystkie?")


    activitylimits = models.ManyToManyField('records.CategoricalValue', through='ActivityLimit', verbose_name="Ograniczenia aktywności dziennych", related_name="al")
    healthproblems = models.ManyToManyField('records.CategoricalValue', through='HealthProblem', verbose_name="Problem z pracą/aktywnością ze względu na stan zdrowia", related_name="hp")
    emotionalproblems = models.ManyToManyField('records.CategoricalValue', through='EmotionalProblem', verbose_name="Problem z pracą/aktywnością ze względu na emocje", related_name="ep")
    moodsymptoms = models.ManyToManyField('records.CategoricalValue', through='MoodSymptom', verbose_name="Częstość występowania objawów stanu samopoczucia", related_name="ms")
    healthselfopinions = models.ManyToManyField('records.CategoricalValue', through='HealthSelfOpinion', verbose_name="Samoocena stanu zdrowia", related_name="hso")

    def __unicode__(self):
        return _default_unicode(self)

    class Meta:
        verbose_name = u"Jakość życia"
        verbose_name_plural = u"Jakość życia"

    #assumption: 1 - a, 2 - b, .... 
    def _key_translator(self, number):
        return chr(number-1 +ord('a') )

        
    def get_q1_points(self):
        health_state = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4}
        health_state_pts = health_state[self.health_state]
        return {'sum':health_state_pts}
        
    
    def get_q2_points(self):
        health_change = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4}
        health_change_pts = health_change[self.health_change]
        return {'sum':health_change_pts}
    
    def get_q3_points(self):
        points={'a':0, 'b':0, 'c':0, 'd':0, 'e':0, 'f':0, 'g':0, 'h':0, 'i':0, 'j':0}
        activity_limits = {'a':5, 'b':3, 'c':0}
        for i in self.activitylimit_set.all():
            key = self._key_translator(i.activitylimit.weight)
            points[key] = activity_limits[i.limit]
            
        points['sum'] = sum(points.values())
        return points
        
    def get_q4_points(self):
        points = {'a':0, 'b':0, 'c':0, 'd':0}
        for i in self.healthproblem_set.all():
            key = self._key_translator(i.healthproblem.weight)
            points[key]=5
        points['sum'] = sum(points.values())
        return points
        
    def get_q5_points(self):
        points = {'a':0, 'b':0, 'c':0}
        for i in self.emotionalproblem_set.all():
            key = self._key_translator(i.emotionalproblem.weight)
            points[key]=5
        points['sum'] = sum(points.values())
        return points
    
    def get_q6_points(self):
        problem_impact = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4}
        problem_impact_pts = problem_impact[self.problem_impact ]
        return {'sum':problem_impact_pts}
        
    def get_q7_points(self):
        pain_freq = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5}
        pain_freq_pts = pain_freq[self.pain_freq]
        return {'sum':pain_freq_pts}
    
    def get_q8_points(self):
        pain_impact = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4}
        pain_impact_pts = pain_impact[self.pain_impact]
        return {'sum':pain_impact_pts}
    
    def get_q9_points(self):
        points={'a':0, 'b':0, 'c':0, 'd':0, 'e':0, 'f':0, 'g':0, 'h':0, 'i':0}
        mood_symptoms = { 1: {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5},
                          2: {'a': 5, 'b': 4, 'c': 3, 'd': 2, 'e': 1, 'f': 0},
                          3: {'a': 5, 'b': 4, 'c': 3, 'd': 2, 'e': 1, 'f': 0},
                          4: {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5},
                          5: {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5},
                          6: {'a': 5, 'b': 4, 'c': 3, 'd': 2, 'e': 1, 'f': 0},
                          7: {'a': 5, 'b': 4, 'c': 3, 'd': 2, 'e': 1, 'f': 0},
                          8: {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5},
                          9: {'a': 5, 'b': 4, 'c': 3, 'd': 2, 'e': 1, 'f': 0}}
           
        for  i in self.moodsymptom_set.all():
            weight = i.moodsymptom.weight
            key = self._key_translator(weight)
            val = i.freq
            points[key] = mood_symptoms[weight][val]
            
        points['sum'] = sum(points.values())
        return points
           
    
    def get_q10_points(self):
        condition_impact = {'a':4, 'b':3, 'c':2, 'd':1, 'e':0}
        condition_impact_pts = condition_impact [self.condition_impact]
        return {'sum':condition_impact_pts}
        
    def get_q11_points(self):
        points={'a':0, 'b':0, 'c':0, 'd':0}
        health_opinion = { 1: {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4},
                           2: {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4},
                           3: {'a': 4, 'b': 3, 'c': 2, 'd': 1, 'e': 0},
                           4: {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4}}
           
        for  i in self.healthselfopinion_set.all():
            weight = i.healthselfopinion.weight
            key = self._key_translator(weight)
            val = i.state_power
            points[key] = health_opinion[weight][val]
            
        points['sum'] = sum(points.values())
        return points
        
      
    def get_sf36_groups(self):
        points = {}
        
        points['PF'] = self.get_q3_points()['sum']
        points['RP'] = self.get_q4_points()['sum']
        points['BP'] = self.get_q7_points()['sum'] + self.get_q8_points()['sum']
        points['GH'] = self.get_q1_points()['sum'] + self.get_q11_points()['sum']
        q9 = self.get_q9_points()
        points['VT'] = q9['a'] + q9['e'] + q9['g'] + q9['i']
        points['SF'] = self.get_q6_points()['sum'] + self.get_q10_points()['sum']
        points['RE'] = self.get_q5_points()['sum']
        points['MH'] = q9['b'] + q9['c'] + q9['d'] + q9['f'] + q9['h']
        points['HT'] = self.get_q2_points()['sum']
        
        return points
        
        
    def get_sf36_points_sum(self):
        try:
            return sum(self.get_sf36_groups().values())
        except Exception, error:
            return error
        
        
class ActivityLimit(models.Model):
    lifequality = models.ForeignKey('LifeQuality')
    activitylimit = models.ForeignKey('records.CategoricalValue', related_name="lifequality_by_activity", verbose_name="Czynność", limit_choices_to={'group__name': 'activitylimit'})    

    LIMITS = (('a', 'Bardzo ogranicza'), ('b', 'Trochę ogranicza'), ('c', 'Nie ogranicza wcale'))
    limit = models.CharField(max_length=1, choices=LIMITS, verbose_name="Poziom ograniczenia")

    class Meta:
        unique_together = (('lifequality', 'activitylimit'),)
        verbose_name = u"Ograniczenia aktywności dziennych"
        verbose_name_plural = u"Ograniczenia aktywności dziennych"

class HealthProblem(models.Model):
    lifequality = models.ForeignKey('LifeQuality')
    healthproblem = models.ForeignKey('records.CategoricalValue', related_name="lifequality_by_healthproblem", verbose_name="Problem", limit_choices_to={'group__name': 'healthproblem'})    

    class Meta:
        unique_together = (('lifequality', 'healthproblem'),)
        verbose_name = u"Proble związany ze zdrowiem"
        verbose_name_plural = u"Problemy związane ze zdrowiem"


class EmotionalProblem(models.Model):
    lifequality = models.ForeignKey('LifeQuality')
    emotionalproblem = models.ForeignKey('records.CategoricalValue', related_name="lifequality_by_emotionalproblem", verbose_name="Problem", limit_choices_to={'group__name': 'emotionalproblem'})    

    class Meta:
        unique_together = (('lifequality', 'emotionalproblem'),)
        verbose_name = u"Problem z pracą/aktywnością"
        verbose_name_plural = u"Problemy z pracą/aktywnością"


class MoodSymptom(models.Model):
    lifequality = models.ForeignKey('LifeQuality')
    moodsymptom = models.ForeignKey('records.CategoricalValue', related_name="lifequality_by_symptom", verbose_name="Symptom", limit_choices_to={'group__name': 'moodsymptom'})    

    FREQ = (('a', 'Cały czas'), ('b', 'Większość czasu'), ('c', 'Dużo czasu'), ('d', 'Jakiś czas'), ('e', 'Mało czasu'), ('f', 'Wcale'))
    freq = models.CharField(max_length=1, choices=FREQ, verbose_name="Ile razy wystąpił objaw w ciągu miesiąca")

    class Meta:
        unique_together = (('lifequality', 'moodsymptom'),)
        verbose_name = u"Występ. objawów samopoczucia"
        verbose_name_plural = u"Występ. objawów samopoczucia"


class HealthSelfOpinion(models.Model):
    lifequality = models.ForeignKey('LifeQuality')
    healthselfopinion = models.ForeignKey('records.CategoricalValue', related_name="lifequality_by_healthselfopinion", verbose_name="Samoocena stanu zdrowia", limit_choices_to={'group__name': 'healthselfopinion'})    

    POWER = (('a', 'Szczególnie prawdziwe'), ('b', 'Czasami prawdziwe'), ('c', 'Nie wiem'), ('d', 'Czasami fałszywe'), ('e', 'Szczególnie fałszywe'))
    state_power = models.CharField(max_length=1, choices=POWER, verbose_name="Prawdziwość stwierdzenia")
    
    
    class Meta:
        unique_together = (('lifequality', 'healthselfopinion'),)
        verbose_name = u"Samoocena stanu zdrowia"
        verbose_name_plural = u"Samoocena stanu zdrowia"



class EtiologySymptom(models.Model):
    etiology = models.ForeignKey('Etiology')
    etiologysymptom = models.ForeignKey('records.CategoricalValue')
    
    class Meta:
        verbose_name = u"Objaw sugerujący etiologię wtórną NT"
        verbose_name_plural = u"Objawy sugerujące etiologię wtórną NT"

    class Meta:
        unique_together = (('etiology', 'etiologysymptom'),)


class ExaminationResult(models.Model):
    etiology = models.ForeignKey('Etiology')
    examinationresult = models.ForeignKey('records.CategoricalValue', limit_choices_to={'group__name': 'examination_result'})

    class Meta:
        verbose_name = "Wynik badania przedmiotowego"
        verbose_name_plural = "Wynika badań przedmiotowych"

    class Meta:
        unique_together = (('etiology', 'examinationresult'),)
        verbose_name = u"Wynik badania przedmiotowego"
        verbose_name_plural = u"Wyniki badań przedmiotowych"


    
class DerivativeEtiologyBackground(models.Model):
    etiology = models.ForeignKey('Etiology')
    derivativeetiologybackground = models.ForeignKey('records.CategoricalValue')
    
    STATE = (('a', 'Podejrzenie'), ('b', 'Diagnoza'))
    state = models.CharField(max_length=1, choices=STATE, verbose_name="Status rozpoznania")

    class Meta:
        unique_together = (('etiology', 'derivativeetiologybackground'),)
        verbose_name = u"Tło wtórnej etiologii"
        verbose_name_plural = u"Tła wtórnej etiologii"


class HypertensionChemicalRelation(models.Model):
    etiology = models.ForeignKey('Etiology')
    hypertensionchemicalrelation = models.ForeignKey('records.CategoricalValue')

    class Meta:
        unique_together = (('etiology', 'hypertensionchemicalrelation'),)

        verbose_name = u"Związek leku/chemii z NT"
        verbose_name_plural = u"Związki leków/chemii z NT"


class Etiology(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")

    ACTUAL = (('a', 'Pierwotna'), ('b', 'Wtórna'))
    actual_etiology_value = models.CharField(max_length=1, choices=ACTUAL, verbose_name="Aktualna etiologia nadciśnienia")

    nt_etiology_symptoms = models.ManyToManyField('records.CategoricalValue', through='EtiologySymptom', related_name="etiology_by_symptom", verbose_name = "Obecne objawy sugerujące etiologię wtórną NT")
    examination_results = models.ManyToManyField('records.CategoricalValue', through='ExaminationResult', related_name="etiology_by_examination", verbose_name = "W badaniu przedmiotowym obecne")
    derivative_etiology_backgrounds = models.ManyToManyField('records.CategoricalValue', through='DerivativeEtiologyBackground', related_name="etiology_by_derivatives", verbose_name = "Tło etiologi wtórnej")

    derivative_etiology_backgrounds = models.ManyToManyField('records.CategoricalValue', through='DerivativeEtiologyBackground', related_name="etiology_by_derivatives", verbose_name = "Tło etiologi wtórnej")
    
    hypertension_chemicals = models.ManyToManyField('records.CategoricalValue', through='HypertensionChemicalRelation', related_name="etiology_by_chemicals", verbose_name="NT związane z lekami/środkami chemicznymi")


    def __unicode__(self):
        return u"Etiologia NT z dnia %s, %s" % (self.appointment.date, self.appointment.patient)


    class Meta:
        verbose_name = u"Etiologia nadciśnienia tętnicznego"
        verbose_name_plural = u"Etiologia nadciśnienia tętnicznego"

        
class Antropometrics(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    loins_perimeter = models.FloatField(verbose_name="Obwód bioder [cm]")
    weist_perimeter = models.FloatField(verbose_name="Obwód talii [cm]")
    height = models.FloatField(verbose_name="Wzrost [w cm]")
    
    def __unicode__(self):
        return u"Data wizyty - %s, pacjent - %s" % (self.appointment.date, self.appointment.patient)

    class Meta:
        verbose_name = u"Pomiar antropometryczny"
        verbose_name_plural = u"Pomiary antropometryczne"

class BodyPressure(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    systolic_left = models.FloatField(verbose_name="Ciśnienie skurczowe strona lewa")
    systolic_right = models.FloatField(verbose_name="Ciśnienie skurczowe strona prawa")
    diastolic_left = models.FloatField(verbose_name="Ciśnienie rozkurczowe strona lewa")
    diastolic_right = models.FloatField(verbose_name="Ciśnienie rozkurczowe strona prawa")
    
    def __unicode__(self):
        return u"Data wizyty - %s, pacjent - %s" % (self.appointment.date, self.appointment.patient)

    class Meta:
        verbose_name = u"Pomiar BP"
        verbose_name_plural = u"Pomiary BP"

class HeartEcho(models.Model):
    
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    la_d = models.FloatField(verbose_name="LA D [cm]")
    lvidd = models.FloatField(verbose_name="LVIDd [cm]")
    rvdd = models.FloatField(verbose_name="RVDd [cm]")
    lvpwd = models.FloatField(verbose_name="LVPWd [cm]")
    ivsd = models.FloatField(verbose_name="IVSd [cm]")
    asc_ao = models.FloatField(verbose_name="Asc.Ao [cm]")
    ao_diam_stub = models.FloatField(verbose_name="Ao diam STub[cm]")
    aoroot = models.FloatField(verbose_name="AoRoot [cm]")
    lvd_massase = models.FloatField(verbose_name="LVd MassASE [g]")
    lvd_mi_ase = models.FloatField(verbose_name="LVd MI Ase [g/m^2]")
    lvd_masspenn = models.FloatField(verbose_name="LVd MassPENN [g]")
    lvd_mi_penn = models.FloatField(verbose_name="LVd MI Penn [g/m^2]")
    mitral_valve = models.TextField(verbose_name="Zastawka mitralna")
    aortal_valve = models.TextField(verbose_name="Zastawka aortalna")
    tricuspid_valve = models.TextField(verbose_name="Zastawka trójdzielna")
    ef = models.FloatField(verbose_name="EF [%]")
    contractility = models.TextField(verbose_name="Kurczliwość")
    im = models.ForeignKey('records.CategoricalValue', related_name="heart_echo_by_im", verbose_name="IM", limit_choices_to={'group__name': 'heart_echo_level'})
    ia = models.ForeignKey('records.CategoricalValue', related_name="heart_echo_by_ia", verbose_name="IA", limit_choices_to={'group__name': 'heart_echo_level'})
    it = models.ForeignKey('records.CategoricalValue', related_name="heart_echo_by_it", verbose_name="IT", limit_choices_to={'group__name': 'heart_echo_level'})

    def __unicode__(self):
        return u"Data wizyty - %s, pacjent - %s" % (self.appointment.date, self.appointment.patient)

    class Meta:
        verbose_name = u"Echo serca"
        verbose_name_plural = u"Echa serca"

    
class Biochemistry(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    wbc = models.FloatField(verbose_name="WBC [10e9/L]")
    rbc = models.FloatField(verbose_name="RBC [10e12/L]")
    hgb = models.FloatField(verbose_name="HGB [mmol/L]")
    hct = models.FloatField(verbose_name="HCT [L/L]")
    mvc = models.FloatField(verbose_name="MVC [fL]")
    plt = models.FloatField(verbose_name="PLT [10e9/L]")
    Na = models.FloatField(verbose_name="Na [mmol/L]")
    K = models.FloatField(verbose_name="K [mmol/L]")
    chol = models.FloatField(verbose_name="CHOL [mmol/L]")
    ldl = models.FloatField(verbose_name="LDL [mmol/L]")
    ahdl = models.FloatField(verbose_name="AHDL [mmol/L]")
    tgl = models.FloatField(verbose_name="TGL [mmol/L]")
    bun = models.FloatField(verbose_name= "BUN [mmol/L]")
    ast = models.FloatField(verbose_name="AST [U/L]")
    alt = models.FloatField(verbose_name="ALT [U/L]")
    gluc = models.FloatField(verbose_name="GLUC [mmol/L]")
    urca = models.FloatField(verbose_name="URCA [mg/L]")
    rcrp = models.FloatField(verbose_name="RCRP [mg/L]")
    crea = models.FloatField(verbose_name="CREA [umol/L]")
    
    
    def __unicode__(self):
        return u"Data wizyty - %s, pacjent - %s" % (self.appointment.date, self.appointment.patient)

    class Meta:
        verbose_name = u"Badanie laboratoryjne"
        verbose_name_plural = u"Badania laboratoryjne"
    

class ABI(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    left_side = models.FloatField(verbose_name="Strona lewa")
    right_side = models.FloatField(verbose_name="Strona prawa")
    
    def __unicode__(self):
        return u"Data wizyty - %s, pacjent - %s" % (self.appointment.date, self.appointment.patient)

    class Meta:
        verbose_name = u"ABI"
        verbose_name_plural = u"ABI"

class CartoidUSG(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    imt_left = models.FloatField(verbose_name="IMT strona lewa [mm]")
    imt_right = models.FloatField(verbose_name="IMT strona prawa [mm]")
    plaques = models.BooleanField(verbose_name="Blaszki miażdzycowe [mm]")
    notes = models.TextField(verbose_name="Notatki")
    
    def __unicode__(self):
        return u"Data wizyty - %s, pacjent - %s" % (self.appointment.date, self.appointment.patient)

    class Meta:
        verbose_name = u"USG tetnic szyjnych"
        verbose_name_plural = u"USG tetnic szyjnych"

class EKG(models.Model):
    appointment = models.OneToOneField('Appointment', verbose_name="Wizyta")
    hr = models.FloatField(verbose_name="HR [/min]")
    sl_factor = models.FloatField(verbose_name="Wskaźnik Sokołowa-Lyona [mm]")
    cornell_factor = models.FloatField(verbose_name="Wskaźnik Cornell [mm]")
    notes = models.TextField(verbose_name="Notatki")
    
    def __unicode__(self):
        return u"Data wizyty - %s, pacjent - %s" % (self.appointment.date, self.appointment.patient)

    class Meta:
        verbose_name = u"EKG"
        verbose_name_plural = u"EKG"

    

    
    
    
    
    
    
#class Antropometrics(models.Model):
#    pass

#class ABPM(models.Model):
#    pass



