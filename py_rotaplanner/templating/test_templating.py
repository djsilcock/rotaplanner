from py_rotaplanner.templating.database import *
from pytest import fixture
from py_rotaplanner.app import app


def test_templating():
    with app.app_context():
        db.create_all()
        rulegroup=RuleGroup(group_type="and")
        daily_rule=DailyRule(day_interval=2,anchor_date=datetime.datetime.today())
        rulegroup.members.append(daily_rule)
        template=DemandTemplate(name='x',start_time=datetime.datetime.today(),finish_time=datetime.datetime.today(),activity_tags="")
        template.ruleset=rulegroup
        db.session.add(template)
        db.session.add(DateTag(tag_id='PH',date=datetime.datetime(2024,12,25)))
        print('adding')
        db.session.commit()
