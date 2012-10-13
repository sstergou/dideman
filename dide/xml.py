# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from models import Permanent, PaymentReport
from django.db import connection, transaction
from lxml import etree
from time import time


def read(file, namespace):

    def gretde(node, sql):  # function to create the gr / et / de section

        def rmv_nsp(node):  # function to remove the namespace from node
            return node.tag.rsplit('}', 1)[-1]

        sql = sql + "insert into dide_payment (id, category_id, type"
        for attr_name, attr_value in node.items():
            if attr_name == 'code':
                sql = sql + ", code_id"
            if attr_name == 'amount':
                sql = sql + ", amount"
            if attr_name == 'loanNumber':
                sql = sql + ", info"

        sql = sql + ") values (NULL, "
        sql = sql + "@lastcat, '" + rmv_nsp(node) + "',"

        for attr_name, attr_value in node.items():
            if attr_name == 'code':
                sql = sql + attr_value
            if attr_name == 'amount':
                sql = sql + ",'" + attr_value + "'"
            if attr_name == 'loanNumber':
                sql = sql + ",'" + attr_value + "'"

        sql = sql + ");\n"
        return sql

    print 'Ανάγνωση αρχείου...'
    start = time()
    ns = namespace  # 'http://www.gsis.gr/psp/2.3'
    element = etree.parse(file)
    sql = ''

    cntr1 = 0
    cntr2 = 0
    month = 0
    year = 0
    paytype = 0
    e = element.xpath('//xs:psp/xs:header/xs:transaction',
                      namespaces={'xs': ns})
    for i in e:
        el = i.xpath('./xs:period', namespaces={'xs': ns})
        month = el[0].get('month')
        year = el[0].get('year')
        el = i.xpath('./xs:periodType', namespaces={'xs': ns})
        paytype = el[0].get('value')

    e = element.xpath('//xs:psp/xs:body/xs:organizations/xs:organization/xs:employees/xs:employee',
                      namespaces={'xs': ns})

    reports = PaymentReport.objects.filter(pay_type=paytype,
                                           type=month, year=year).count()
    print u'Βρέθηκαν %s εγγραφες από προηγούμενο αρχείο.' % reports
    if reports > 0:
        cursor = connection.cursor()
        cursor.execute('delete from dide_paymentreport where pay_type = %s and type_id = %s and year = %s;' % (paytype,
                                                                                                            month,
                                                                                                            year))
        transaction.commit_unless_managed()
        cursor.close()
        reports = ''

    for i in e:
        iban = ''
        netAmount1 = ''
        netAmount2 = ''
        rank = 0
        cntr1 = cntr1 + 1
        el = i.xpath('./xs:identification/xs:amm', namespaces={'xs': ns})
        try:
            payemp = Permanent.objects.get(registration_number=el[0].text)
            cntr2 = cntr2 + 1
            el = i.xpath('./xs:identification/xs:bankAccount',
                         namespaces={'xs': ns})
            iban = el[0].get('iban')
            el = i.xpath('./xs:identification/xs:scale/xs:rank',
                         namespaces={'xs': ns})
            rank = el[0].text
            el = i.xpath('./xs:payment/xs:netAmount1', namespaces={'xs': ns})
            netAmount1 = el[0].get('value')
            el = i.xpath('./xs:payment/xs:netAmount2', namespaces={'xs': ns})
            netAmount2 = el[0].get('value')
            sql = sql + "insert into dide_paymentreport values (NULL, "
            sql = sql + "%s,%s,%s,%s,%s,'%s','%s','%s');" % (payemp.parent.id,
                                                             month,
                                                             year,
                                                             paytype,
                                                             rank,
                                                             iban,
                                                             netAmount1,
                                                             netAmount2)
            sql = sql + '\n'
            sql = sql + 'set @lastrep = last_insert_id();' + '\n'
            el = i.xpath('./xs:payment/xs:income', namespaces={'xs': ns})
            for p in el:
                sql = sql + "insert into dide_paymentcategory(id,paymentreport_id,title_id"
                for attr_name, attr_value in p.items():

                    if attr_name == 'startDate':
                        sql = sql + ",start_date"
                    if attr_name == 'endDate':
                        sql = sql + ",end_date"
                    if attr_name == 'month':
                        sql = sql + ",month"
                    if attr_name == 'year':
                        sql = sql + ",year"

                sql = sql + ") values (NULL, "
                sql = sql + "@lastrep"
                for attr_name, attr_value in p.items():
                    if attr_name == 'type':
                        sql = sql + "," + attr_value
                    if attr_name == 'startDate':
                        sql = sql + ",'" + attr_value + "'"
                    if attr_name == 'endDate':
                        sql = sql + ",'" + attr_value + "'"
                    if attr_name == 'month':
                        sql = sql + "," + attr_value + ""
                    if attr_name == 'year':
                        sql = sql + "," + attr_value + ""
                sql = sql + ");"
                sql = sql + '\n'

                sql = sql + 'set @lastcat = last_insert_id();' + '\n'

                for it in p.xpath('./xs:gr', namespaces={'xs': ns}):

                    sql = gretde(it, sql)

                for it in p.xpath('./xs:et', namespaces={'xs': ns}):

                    sql = gretde(it, sql)

                for it in p.xpath('./xs:de', namespaces={'xs': ns}):

                    sql = gretde(it, sql)

            sql_strings = sql.split('\n')
            for s_s in sql_strings:

                if s_s != '':
                    cursor = connection.cursor()
                    cursor.execute(s_s)
                    transaction.commit_unless_managed()
                    cursor.close()
#            print sql
            sql = ''

        except ObjectDoesNotExist:
            print el[0].text + " δεν βρέθηκε στη βάση."

    print u"Στο αρχείο XML βρέθηκαν %s. Στη βάση βρέθηκαν %s. (Διαφορά %d) " % (cntr1,
                                                                                cntr2,
                                                                                (cntr1 - cntr2))
    elapsed = (time() - start)
    print u"Διάρκεια ανάγνωσης %.2f δευτερόλεπτα" % (elapsed)
