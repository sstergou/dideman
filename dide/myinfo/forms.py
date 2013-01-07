# -*- coding: utf-8 -*-
from django import forms
from dideman.dide.models import Permanent
from django.utils.translation import ugettext as _
from django.contrib.admin.widgets import AdminDateWidget


class MyInfoForm(forms.Form):
    email = forms.EmailField(label=u'Email',
                             required=False)
    telephone_number1 = forms.CharField(label=u'Σταθερό Τηλέφωνο',
                                        required=False)
    telephone_number2 = forms.CharField(label=u'Κινητό Τηλέφωνο',
                                        required=False)
    mothername = forms.CharField(label=u'Όνομα Μητέρας', required=False)
    social_security_registration_number = forms.CharField(label=u'Α.Μ.Κ.Α.',
                                                          required=False)
    address = forms.CharField(label=u'Διεύθυνση Κατοικίας',
                              widget=forms.Textarea, required=False)
    tax_office = forms.CharField(label=u'Δ.Ο.Υ.', required=False)
    birth_date = forms.DateField(label=u'Ημερομηνία Γέννησης', required=False)
