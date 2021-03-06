import enum
import json
import random
import decimal
#import pdf_rendering as pdf

from dataclasses import dataclass, asdict, field
from datetime import datetime, date, timedelta
from typing import List

from .micro_models import *

def previous_month():
    today = date.today()
    last_month = today.replace(day=1) - timedelta(days=1)
    last_month = last_month.replace(day=1)    
    return last_month


def create_empty_db(form_data):
    invoice_series = form_data.pop('invoice_series')
    start_no = form_data.pop('start_no')

    seller = FiscalEntity(**form_data)
    registry = InvoiceRegister(seller=seller, invoice_series=invoice_series, next_number=start_no)
    db = LocalStorage(registry)

    return db


def create_contract(form_data):
    hourly_rate = form_data.pop('hourly_rate')
    buyer = FiscalEntity(**form_data)
    contract = ServiceContract(buyer=buyer, hourly_rate=hourly_rate)

    return contract


def create_time_invoice(db, form_data):
    contract_id = form_data.pop('contract_id')
    duration = form_data.pop('duration')
    flavor = form_data.pop('flavor')
    project_id = form_data.pop('project_id')
    xchg_rate = form_data.pop('xchg_rate')

    contract = db.contracts[int(contract_id)]
    invoice_fields = {
        'status': InvoiceStatus.DRAFT,
        'seller': db.register.seller,
        'series': db.register.invoice_series,
        'number': db.register.next_number,
        'buyer': contract.buyer,
        'hourly_rate': contract.hourly_rate,
        'activity': create_random_activity(contract_id, duration, flavor, project_id),
        'conversion_rate': xchg_rate,
    }
    return TimeInvoice(**invoice_fields)

def draft_time_invoice(db, form_data):
    invoice = create_time_invoice(db, form_data)
    db.register.next_number += 1
    db.register.invoices.append(invoice)

    # file_save_activity_report_name = "demo_pdf_activity_report.pdf"
    # file_save_invoice_name = "demo_pdf_invoice.pdf"
    # pdf.render_activity_report(invoice, file_save_activity_report_name)
    # pdf.render_invoice(invoice, file_save_invoice_name)

    return db

def pick_task_names(flavor, count):
    taskname_pool = [
        "sprint planning",
        "sprint review",
        "development tasks estimation",
        "defects investigation",
        "code reviews",
        "refactoring old-code",
        "SDK architecture updates",
        "release notes",
        "{flavor} generic mock setup",
        "{flavor} state manager",
        "{flavor} components architecture",
        "{flavor} android communication layer",
        "{flavor} android native implementation",
        "{flavor} iOs communication layer",
        "{flavor} iOs native implementation",
        "{flavor} core implementation",
        "{flavor} public interfaces update",
        "{flavor} sample application",
        "{flavor} component design",
        "{flavor} data modeling",
        "{flavor} defects verification",
        "{flavor} code coverage testing",
        "Low level {flavor} event handling",
    ]
    tasks = [name.format(flavor=flavor) for name in random.sample(taskname_pool, k=count)]
    return tasks

def split_duration(duration, count):
    left = duration
    splits = []
    step = 1

    for step in range(count-1):
        max_split = round(left*(0.618*(step+2)/count))
        min_split = min(4, max_split-1)
        current_split = random.randrange(min_split, stop=max_split)
        splits.append(current_split)
        left -=current_split

    splits.append(left)

    return splits

def compute_start_dates(start_date, durations):
    dates = []
    trace_date = start_date
    for duration in durations:
        trace_date += timedelta(days=round(duration/8))
        if trace_date.weekday() > 4:
            trace_date += timedelta(days=7 - trace_date.weekday())
        dates.append(trace_date)

    return dates

def create_random_tasks(activity, how_many, hours):
    
    names = pick_task_names(flavor=activity.flavor, count=how_many)
    durations = split_duration(duration=hours, count=how_many)
    dates = compute_start_dates(activity.start_date, durations)
    projects = [activity.project_id] * how_many

    tasks = [Task(*t) for t in zip(names, dates, durations, projects)]

    return tasks

def create_random_activity(contract_id, hours, flavor, project_id):
    start_date = previous_month()
    activity = ActivityReport(contract_id, start_date, flavor, project_id)
    how_many = random.randrange(8, stop=13)
    activity.tasks = create_random_tasks(activity, how_many, hours=hours)

    return activity


def loads(content):
    def from_dict(pairs):
        factory_map = {
            'seller': FiscalEntity,
            'buyer': FiscalEntity,
            'register': InvoiceRegister,
            'activity': ActivityReport,
            'contracts': ServiceContract,
            'tasks': Task,
            'invoices': TimeInvoice,
        }
        obj = {}

        for key,value in pairs:
            if key in factory_map:
                if isinstance(value, list):
                    obj[key] = [factory_map[key](**item) for item in value ]
                else:
                    obj[key] = factory_map[key](**value)
            else:
                obj[key] = value

        return obj

    try:
        data = json.loads(content, object_pairs_hook=from_dict)
    except json.JSONDecodeError:
        return None

    return LocalStorage(register=data['register'], contracts=data['contracts'])


def dumps(db):
    def custom_serializer(obj):
        if isinstance(obj, date):
            return obj.isoformat()

        if isinstance(obj, decimal.Decimal):
            return float(obj)

        raise TypeError(f'Type {type(obj)} is not JSON serializable')

    content = json.dumps(asdict(db), indent=4, default=custom_serializer)
    return content


if __name__ == '__main__':
    print('This is a pure module, it cannot be executed.')
