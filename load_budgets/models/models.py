# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
import base64
import xlwt
from io import BytesIO
from xlrd import open_workbook
import xlrd
from odoo import exceptions, _

class BudgetaryPosition(models.Model):
    _inherit = 'account.budget.post'

    code = fields.Char(string="Code", required=True, )

class Budget(models.Model):
    _inherit = 'crossovered.budget'

    state = fields.Selection([
        ('draft', 'Inactive'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
        ('validate', 'Activated'),
        ('done', 'Done')
    ], 'Status', default='draft', index=True, required=True, readonly=True, copy=False, track_visibility='always')

    code = fields.Char(string="Code", required=True, )

    load_budget_id = fields.Many2one(comodel_name="load.budget", string="Load of Budget", required=False, )
    # ld_id = fields.Many2one(comodel_name="project.project", string="LD", required=False, )
    ld1 = fields.Char(string="Geographic Location", required=False, )
    ld2 = fields.Char(string="Sector", required=False, )
    ld3 = fields.Char(string="Donor", required=False, )
    ld4 = fields.Char(string="Agreement", required=False, )
    ld5 = fields.Char(string="Fund", required=False, )
    ld6 = fields.Char(string="Department", required=False, )
    ld7 = fields.Char(string="Employee Code", required=False, )
    ld9 = fields.Char(string="LD9", required=False, )
    ld10 = fields.Char(string="LD10 Code", required=False, )



class BudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    # code = fields.Char(string="Code", required=True, )
    name = fields.Char(string="Name", required=True, )

    # load_budget_id = fields.Many2one(comodel_name="load.budget", string="Load of Budget", required=False, )

    remaining_amount = fields.Float(compute='_compute_remaining_amount', string='Remaining Amount', digits=0)

    @api.one
    @api.depends('planned_amount', 'practical_amount')
    def _compute_remaining_amount(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for line in self:
            line.remaining_amount = line.planned_amount - abs(line.practical_amount)

class BudgetsPositions(models.Model):
    _name = 'load.positions'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Description", required=True, )
    date = fields.Date(string="Date", required=False, default=datetime.today())
    file_positions = fields.Binary(string="File of Positions",  )
    template_positions = fields.Binary(string="Template of Positions",  )
    name_file = fields.Char(string="Name of File", required=False, )
    company_id = fields.Many2one(comodel_name="res.company",
                                 string="Company",
                                 required=False,
                                 default=lambda self: self.env.user.company_id.id)
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('generated', 'Generated'), ],
                             required=False, default='draft')

    @api.multi
    def draft_this(self):

        self.state = 'draft'

    @api.multi
    def generate_template(self):
        filename = 'template_positions.xls'

        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Template of Positions')

        fields = ["Name Position", "Code Position", "Code of Account"]

        column = 0

        for h in fields:
            worksheet.write(0, column, h)

            column = column + 1


        stream = BytesIO()

        workbook.save(stream)

        self.template_positions = base64.encodestring(stream.getvalue())
        self.name_file = 'template_positions.xls'
        stream.close()

    def check_position(self, code):
        return self.env['account.budget.post'].search([('code', '=', code), ('company_id', '=', self.company_id.id)], limit=1)

    def generate_positions(self):

        file_data = base64.decodestring(self.file_positions)
        wb = open_workbook(file_contents=file_data)

        data = []

        row = 1
        column = 0

        sheet = wb.sheet_by_index(0)



        while True:
            try:

                name_position = sheet.cell_value(row, column)
                code_position = sheet.cell_value(row, column + 1)
                code_account = sheet.cell_value(row, column + 2)

                # raise exceptions.UserError(_(self.get_account(code_account)))

                position = self.check_position(code_position)

                if position:
                    if position.name != name_position:
                        position.name = name_position

                    # position.account_ids = [(5, )]
                    position.account_ids = [(6, 0, self.get_account(str(code_account).split('.')[0]))]
                    # self.get_account(str(code_account).split('.')[0])

                else:

                    data.append(
                    {
                        'name':str(name_position).split('.')[0],
                        'code': str(code_position).split('.')[0],
                        'account_ids': self.get_account(str(code_account).split('.')[0])
                    }
                )

                row = row + 1

            except IndexError:
                break

        self.write_lines(data)
        self.state = 'generated'

    def write_lines(self, data):


        for line in data:

            self.env['account.budget.post'].create(
                {
                    'name': line['name'],
                    'code': line['code'],
                    'account_ids': [(6, 0, line['account_ids'])]
                }
            )

    def get_account(self, code):

        return [self.env['account.account'].search(
           [('code', '=', code), ('company_id', '=', self.company_id.id)]
        )[0].id]




class load_budgets(models.Model):
    _name = 'load.budget'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Description", required=True, )
    date = fields.Date(string="Create On", required=False, default=datetime.today())
    date_from = fields.Date(string="Date Start", required=True, default=datetime.today())
    date_to = fields.Date(string="Date End", required=True, default=datetime.today() + timedelta(days=365))
    file_budgets = fields.Binary(string="File of Budgets",  )
    template_budgets = fields.Binary(string="Template of Budgets",  )
    name_file = fields.Char(string="Name of File", required=False, )
    company_id = fields.Many2one(comodel_name="res.company",
                                 string="Company",
                                 required=False,
                                 default=lambda self: self.env.user.company_id.id)
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('generated', 'Generated'), ],
                             required=False, default='draft')
    budget_ids = fields.One2many(comodel_name="crossovered.budget", inverse_name="load_budget_id", string="Budgets", required=False, )
    state_budget = fields.Selection([
        ('draft', 'Inactive'),
        ('validate', 'Active')
    ], 'Status', default='draft', required=True, )
    is_there_warning = fields.Boolean(string="There Warning", default=False)
    warn = fields.Text(string="Warnings", required=False, )

    def get_user(self, code):

        employee = self.env['hr.employee'].search([('code', '=', code), ('company_id', '=', self.company_id.id)])[0]

        return employee.user_id.id

    @api.multi
    def draft_this(self):

        self.state = 'draft'

    @api.multi
    def generate_template(self):
        filename = 'template_budgets.xls'

        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Template of Positions')

        worksheet.write(3, 0, "G/L Account No.")
        worksheet.write(3, 1, "Name")
        worksheet.write(3, 2, "Geographic Location Code")
        worksheet.write(3, 3, "Sector Code")
        worksheet.write(3, 4, "Donor Code")
        worksheet.write(3, 5, "Agreement Code")
        worksheet.write(3, 6, "Fund Code")
        worksheet.write(3, 7, "Department Code")
        worksheet.write(3, 8, "Employee Code")
        worksheet.write(3, 9, "LD9 Code")
        worksheet.write(3, 10, "LD10 Code")
        worksheet.write(3, 11, "Planned Amount")

        stream = BytesIO()

        workbook.save(stream)

        self.template_budgets = base64.encodestring(stream.getvalue())
        self.name_file = 'template_budgets.xls'
        stream.close()

        # filename = 'template_budgets.xls'
        #
        # workbook = xlwt.Workbook()
        #
        # worksheet = workbook.add_sheet('Template of Positions')
        #
        # worksheet.write(0, 0, "Dimension")
        # worksheet.write(0, 1, "Code")
        # worksheet.write(0, 2, "Name Budget")
        # worksheet.write(0, 3, "Code Reponsable")
        # worksheet.write(0, 4, "Date From")
        # worksheet.write(0, 5, "Date To")
        # worksheet.write(0, 6, "Name Line")
        # worksheet.write(0, 7, "Code Position")
        # worksheet.write(0, 8, "Planned Amount")
        #
        # stream = BytesIO()
        #
        # workbook.save(stream)
        #
        # self.template_budgets = base64.encodestring(stream.getvalue())
        # self.name_file = 'template_budgets.xls'
        # stream.close()

    def get_account(self, code):
        account = self.sudo().env['account.account'].search([('code', '=', code),
                                                             ('company_id', '=', self.company_id.id)])[0].id
        # raise exceptions.UserError(code)
        return account

    def get_position(self, account, name):
        account = str(account).split('.')[0]
        position = []

        if not name == '':
            position = self.sudo().env['account.budget.post'].search([('name', '=', account + ' - ' + name),
                                                               ('company_id', '=', self.company_id.id)])

        else:
            position = self.sudo().env['account.budget.post'].search([('name', 'like', account),
                                                               ('company_id', '=', self.company_id.id)])

        if position:
            return position[0]
        else:
            position = self.env['account.budget.post'].create({
                'name': account + ' - ' + name,
                'code': account,
                'account_ids': [(6, 0, [self.get_account(account)])]
            })

            # position.account_ids = [(4, [self.get_account(account)])]
            return position

    def activate_budget(self):

        for budget in self.budget_ids:
            budget.state = self.state_budget

        self.state = 'generated'

    def generate_name(self, sheet, row):

        ld1 = ''
        ld2 = ''
        ld3 = ''
        ld4 = ''
        ld5 = ''
        ld6 = ''
        ld7 = ''
        ld9 = ''
        ld10 = ''

        try:
            ld1 = str(sheet.cell_value(row, 2))
            # len1 = len(ld1.split(' '))
            #
            # if len1 >
        except IndexError:
            return False

        try:
            ld2 = sheet.cell_value(row, 3)
            if ld2 == '' or ld2 == ' ':
                ld2 = ''
            else:
                ld2 = '-' + ld2
        except IndexError:
            ld2 = ''

        try:
            ld3 = sheet.cell_value(row, 4)
            if ld3 == '' or ld3 == ' ':
                ld3 = ''
            else:
                ld3 = '-' + ld3
        except IndexError:
            ld3 = ''

        try:
            ld4 = sheet.cell_value(row, 5)

            if ld4 == '' or ld4 == ' ':
                ld4 = ''
            else:
                ld4 = '-' + ld4
        except IndexError:
            ld4 = ''

        try:
            ld5 = sheet.cell_value(row, 6)

            if ld5 == '' or ld5 == ' ':
                ld5 = ''
            else:
                ld5 = '-' + ld5

        except IndexError:
            ld5 = ''

        try:
            ld6 = sheet.cell_value(row, 7)

            if ld6 == '' or ld6 == ' ':
                ld6 = ''
            else:
                ld6 = '-' + ld6
        except IndexError:
            ld6 = ''

        try:
            ld7 = sheet.cell_value(row, 8)

            if ld7 == '' or ld7 == ' ':
                ld7 = ''
            else:
                ld7 = '-' + ld7
        except IndexError:
            ld7 = ''

        try:
            ld9 = sheet.cell_value(row, 9)

            if ld9 == '' or ld9 == ' ':
                ld9 = ''
            else:
                ld9 = '-' + ld9
        except IndexError:
            ld9 = ''

        try:
            ld10 = sheet.cell_value(row, 10)

            if ld10 == '' or ld10 == ' ':
                ld10 = ''
            else:
                ld10 = '-' + ld10

        except IndexError:
            ld10 = ''

        name = ld1 + ld2 + ld3 + ld4 + ld5 + ld6 + ld7 + ld9 + ld10
        l = {'ld1' : ld1,
            'ld2' : ld2,
            'ld3' : ld3,
            'ld4' : ld4,
            'ld5' : ld5,
            'ld6' : ld6,
            'ld7' : ld7,
            'ld9' : ld9,
            'ld10' : ld10 }

        return name, l

    def search_budget(self, name):

        search_budget = self.sudo().env['crossovered.budget'].search([('code', '=', name),
                                                                      ('state', '=', 'validate'),
                                                                      ('company_id', '=', self.company_id.id)])
        return search_budget

    def load_budget2(self):

        file_data = base64.decodestring(self.file_budgets)
        wb = open_workbook(file_contents=file_data)
        row = 4
        sheet = wb.sheet_by_index(0)

        budgets = []
        lds = []
        name = ""
        budget_warn = []
        blines = ''
        while True:
            try:

                name, l = self.generate_name(sheet, row)

                if name == False:
                    row = row + 1
                    continue
                else:
                    sname = name.split(' ')
                    if len(sname) > 1:
                        row = row + 1
                        continue

                line_name = ''

                try:
                    line_name = sheet.cell_value(row, 1)
                except IndexError:
                    break

                account = self.get_position(sheet.cell_value(row, 0), line_name)

                amount = sheet.cell_value(row, 11)

                row = row + 1

                search_budget = self.search_budget(name)

                if not search_budget:

                    # analitic = self.env['account.analytic.account'].create({'name': name,})

                    if not name in lds:

                        if int(amount or '0') == 0:
                            budgets.append(
                                (name, {
                                    'name': name,
                                    'date_from': self.date_from,
                                    'date_to': self.date_to,
                                    'code': name,
                                    'ld1': l['ld1'],
                                    'ld2': l['ld2'].replace('-', ''),
                                    'ld3': l['ld3'].replace('-', ''),
                                    'ld4': l['ld4'].replace('-', ''),
                                    'ld5': l['ld5'].replace('-', ''),
                                    'ld6': l['ld6'].replace('-', ''),
                                    'ld7': l['ld7'].replace('-', ''),
                                    'ld9': l['ld9'].replace('-', ''),
                                    'ld10': l['ld10'].replace('-', ''),
                                    'crossovered_budget_line': [{
                                        # 'code': line['code_line'],
                                        'name': account.name,
                                        'general_budget_id': account.id,
                                        'planned_amount': amount,
                                        'date_from': self.date_from,
                                        'date_to': self.date_to,
                                    }],
                                    # 'analitic': analitic
                                }
                                 )
                            )

                            lds.append(name)
                            continue
                        else:
                            budgets.append(
                                (name, {
                                    'name': name,
                                    'date_from': self.date_from,
                                    'date_to': self.date_to,
                                    'code': name,
                                    'ld1': l['ld1'],
                                    'ld2': l['ld2'].replace('-', ''),
                                    'ld3': l['ld3'].replace('-', ''),
                                    'ld4': l['ld4'].replace('-', ''),
                                    'ld5': l['ld5'].replace('-', ''),
                                    'ld6': l['ld6'].replace('-', ''),
                                    'ld7': l['ld7'].replace('-', ''),
                                    'ld9': l['ld9'].replace('-', ''),
                                    'ld10': l['ld10'].replace('-', ''),
                                    'crossovered_budget_line': [],
                                    # 'analitic': analitic
                                }
                                 )
                            )

                            lds.append(name)
                            blines = blines + '<li>' + 'Row: ' + str(row) + ' Account And Name: ' + account.name + '</li>'
                            # self.is_there_warning = True
                            continue
                    else:
                        if int(amount or '0') > 0:
                            budgets[lds.index(name)][1]['crossovered_budget_line'].append({
                                    'name': account.name,
                                    'general_budget_id': account.id,
                                    'planned_amount': amount,
                                    'date_from': self.date_from,
                                    'date_to': self.date_to,
                                })
                            lds.append(name)
                            continue
                        else:
                            lds.append(name)
                            # self.is_there_warning = True
                            blines = blines + '<li>' + 'Row: ' + str(row) + ' Account And Name: ' + account.name + '</li>'
                            continue
                else:

                    if not search_budget[0].name in budget_warn:

                        budget_warn.append(search_budget[0].name)

                    # row = row + 1
                    continue

                # raise exceptions.UserError("Budgets: " + budgets + "\nBudgets Warn: " + budget_warn)
                #     raise exceptions.UserError(("Budgets: " + str(budgets) + "\nBudgets Warn: " + str(budget_warn) + '\nRow: ' + str(row)))

            except IndexError:
                # raise exceptions.UserError("Aqui es que se hace el error")
                # raise exceptions.UserError(("Budgets: " + str(budgets) + "\nBudgets Warn: " + str(budget_warn) + '\nRow: ' + str(row)))
                break

        self.sudo().load_lines2(budgets)
        # self.state = 'generated'
        self.write_warns(budget_warn, blines)

    def write_warns(self, budget_warn, blines):

        html = """"""
        lis = ''
        lines_blines = """The Follow Lines of Budget Have Planned Amount In Cero: <br/><ul>"""

        if budget_warn:
            for bw in budget_warn:
                lis = lis + '<li>' + bw + '</li>'

            html = """The Follow Budgets Already Exists On Actived Status: <br/><ul>""" + lis + '</ul>'
            self.is_there_warning = True

        if blines:
            if blines:
                html = html + '<br/>' + lines_blines + blines + '</ul>'

            self.is_there_warning = True

        self.warn = html

    def warn_on_create(self, budgets):
        html = """The Follow Budget Were Not Create Because Has Not Budget Lines<br/><ul>"""

        lines = ""

        for budget in budgets:
            lines = lines + "<li>" + budget + '</li>'

        if self.warn:
            self.warn = self.warn + html + str(lines) + '</ul>'
        else:
            self.warn = html + str(lines) + '</ul>'

    def load_lines2(self, budgets):

        no_create = []

        for budget in budgets:
            lines = []
            # raise exceptions.UserError((str(budget)))

            for line in budget[1]['crossovered_budget_line']:
                analitic = self.sudo().env['account.analytic.account'].create({'name': line['name'] + ':' + budget[1]['name'], 'company_id': self.company_id.id})

                lines.append((0, 0,
                    {
                        # 'code': line['code_line'],
                        'name': line['name'],
                        'general_budget_id': line['general_budget_id'],
                        'planned_amount': line['planned_amount'],
                        'date_from': budget[1]['date_from'],
                        'date_to': budget[1]['date_to'],
                        # 'analytic_account_id': budget[1]['analitic'].id,
                        'analytic_account_id': analitic.id,

                    })
                )

            if budget[1]['crossovered_budget_line']:

                self.env['crossovered.budget'].create(
                    {
                        'code': budget[1]['code'],
                     'name': budget[1]['name'],
                     'date_from': budget[1]['date_from'],
                     'date_to': budget[1]['date_to'],
                     'crossovered_budget_line': lines,
                     'load_budget_id': self.id,
                     # 'state': self.state_budget,
                     'ld1': budget[1]['ld1'],
                     'ld2': budget[1]['ld2'],
                     'ld3': budget[1]['ld3'],
                     'ld4': budget[1]['ld4'],
                     'ld5': budget[1]['ld5'],
                     'ld6': budget[1]['ld6'],
                     'ld9': budget[1]['ld9'],
                        'company_id': self.company_id.id

                     }
                )
            else:
                no_create.append(budget[1]['code'])

        if no_create:
            self.warn_on_create(no_create)


    def check_budget(self, code):
        return self.env['crossovered.budget'].search([('code', '=', code), ('compnay_id', '=', self.company_id.id)], limit=1)

    def check_budget_line(self, code):
        return self.env['crossovered.budget.lines'].search([('code', '=', code), ('compnay_id', '=', self.company_id.id)], limit=1)

    def load_budget(self):

        file_data = base64.decodestring(self.file_budgets)
        wb = open_workbook(file_contents=file_data)

        data = []
        lines = []

        row = 1
        column = 0

        sheet = wb.sheet_by_index(0)

        budget_line_row = -1
        budgets = []
        budget_exits = False
        budget = []

        while True:
            try:

                dimension = str(sheet.cell_value(row, 0)).split('.')[0]

                if dimension == '1':

                    code_budget = sheet.cell_value(row, 1)
                    budget = self.check_budget(code_budget)
                    name_budget = sheet.cell_value(row, 2)
                    responsible_budget = sheet.cell_value(row, 3)
                    date_from_1 = sheet.cell_value(row, 4)
                    date_from = datetime(*xlrd.xldate_as_tuple(date_from_1, wb.datemode))
                    date_to_1 = sheet.cell_value(row, 5)
                    date_to = datetime(*xlrd.xldate_as_tuple(date_to_1, wb.datemode))

                    if budget:
                        if budget.name != name_budget:
                            budget.name = name_budget

                        if budget.creating_user_id != self.get_user(responsible_budget):
                            budget.creating_user_id = self.get_user(responsible_budget)

                        if budget.date_from != date_from:
                            budget.date_from = date_from

                        if budget.date_to != date_to:
                            budget.date_to = date_to

                        budget_exits = True

                    else:

                        budget = {
                            'code_budget': code_budget,
                            'name': name_budget,
                            'code_employee': responsible_budget,
                            'date_from': date_from,
                            'date_to': date_to,
                            'analytic': self.env['account.analytic.account'].create(
                                {
                                    'name': name_budget,
                                }
                            ).id,
                            'lines': []
                        }

                        budgets.append(budget)

                        budget_line_row = budget_line_row + 1

                    # name_position = sheet.cell_value(row, 5)
                    # code_position = str(sheet.cell_value(row, 6)).split('.')[0]
                    # planned_amount = sheet.cell_value(row, 7)
                    #
                    # budgets[budget_line]['lines'].append({
                    #     'name_position': name_position,
                    #     'code_position': code_position,
                    #     'planned_amount': planned_amount
                    # })

                    row = row + 1

                else:
                    try:
                        code_line = sheet.cell_value(row, 1)
                        budget_line = self.check_budget_line(code_budget)
                        name_position = sheet.cell_value(row, 6)
                        code_position = str(sheet.cell_value(row, 7)).split('.')[0]
                        planned_amount = sheet.cell_value(row, 8)
                        date_from_1 = sheet.cell_value(row, 4)
                        date_from = datetime(*xlrd.xldate_as_tuple(date_from_1, wb.datemode))
                        date_to_1 = sheet.cell_value(row, 5)
                        date_to = datetime(*xlrd.xldate_as_tuple(date_to_1, wb.datemode))

                        if budget_exits:

                            if budget_line:
                                if budget_line.name != name_position:
                                    budget_line.name = name_position

                                if budget_line.general_budget_id != self.get_position(str(code_position).split('.')[0]):
                                    budget_line.general_budget_id = self.get_position(str(code_position).split('.')[0])

                                if budget_line.planned_amount != planned_amount:
                                    budget_line.planned_amount = planned_amount
                            else:

                                budget.crossovered_budget_line.create({
                                    'code': code_line,
                                    'name': name_position,
                                    'general_budget_id': self.get_position(str(code_position).split('.')[0]),
                                    'planned_amount': planned_amount,
                                    'date_from': date_from,
                                    'date_to': date_to,
                                    'crossovered_budget_id': budget.id
                                })
                        else:

                            budgets[budget_line_row]['lines'].append({
                                'code_line': code_line,
                                'name_position': name_position,
                                'code_position': code_position,
                                'planned_amount': planned_amount
                            })

                        row = row + 1

                    except IndexError:

                        raise exceptions.UserError(_('You have some empty field on the line %s' % (row)))

            except IndexError:
                break

        self.load_lines(budgets)
        self.state = 'generated'


    def load_lines(self, budgets):

        for budget in budgets:

            lines = []

            for line in budget['lines']:

                if not line['code_position'] == '':

                    lines.append((0, 0,
                        {
                            'code': line['code_line'],
                            'name': line['name_position'],
                            'general_budget_id': self.get_position(str(line['code_position']).split('.')[0]),
                            'planned_amount': line['planned_amount'],
                            'date_from': budget['date_from'],
                            'date_to': budget['date_to'],
                            'analytic_account_id': budget['analytic'],
                        })
                    )


            self.env['crossovered.budget'].create(
                {   'code': budget['code_budget'],
                    'name': budget['name'],
                    'creating_user_id': self.get_user(budget['code_employee']),
                    'date_from': budget['date_from'],
                    'date_to': budget['date_to'],
                    'crossovered_budget_line': lines,
                    'load_budget_id': self.id
                }
            )


    # def generate_budget(self):
    #
    #     file_data = base64.decodestring(self.file_budgets)
    #     wb = open_workbook(file_contents=file_data)
    #
    #     data = []
    #
    #     row = 3
    #     column = 0
    #
    #     sheet = wb.sheet_by_index(0)
    #
    #     name = sheet.cell_value(1, 0)
    #     date_from_1 = sheet.cell_value(1, 1)
    #     date_from = datetime(*xlrd.xldate_as_tuple(date_from_1, wb.datemode))
    #     date_to_1 = sheet.cell_value(1, 2)
    #     date_to = datetime(*xlrd.xldate_as_tuple(date_to_1, wb.datemode))
    #
    #     budget = {
    #         'name': name,
    #         'date_from': date_from,
    #         'date_to': date_to,
    #         'analytic': self.env['account.analytic.account'].create(
    #             {
    #                 'name': name,
    #             }
    #         ).id
    #     }
    #
    #     while True:
    #         try:
    #
    #             name_position = sheet.cell_value(row, column)
    #             code_position = sheet.cell_value(row, column + 1)
    #             planned_amount = sheet.cell_value(row, column + 2)
    #
    #             # raise exceptions.UserError(_(self.get_account(code_account)))
    #
    #             data.append(
    #                 {
    #                     'name': str(name_position).split('.')[0],
    #                     'planned_amount': planned_amount,
    #                     'general_budget_id': self.get_position(str(code_position).split('.')[0])
    #                 }
    #             )
    #
    #             row = row + 1
    #
    #         except IndexError:
    #             break
    #
    #     self.write_lines(data, budget)
    #     self.state = 'generated'
    #
    # def write_lines(self, data, budget):
    #
    #     lines = []
    #
    #
    #     for line in data:
    #
    #         lines.append((0, 0,
    #             {
    #                 'name': line['name'],
    #                 'general_budget_id': line['general_budget_id'],
    #                 'planned_amount': line['planned_amount'],
    #                 'date_from': budget['date_from'],
    #                 'date_to': budget['date_to'],
    #                 'analytic_account_id': budget['analytic'],
    #             })
    #         )
    #
    #     self.env['crossovered.budget'].create(
    #         {
    #             'name': budget['name'],
    #             'date_from': budget['date_from'],
    #             'date_to': budget['date_to'],
    #             'crossovered_budget_line': lines
    #         }
    #     )
    #
    #
    # def get_position(self, code):
    #
    #     return self.env['account.budget.post'].search(
    #        [('code', '=', code), ('company_id', '=', self.company_id.id)]
    #     )[0].id