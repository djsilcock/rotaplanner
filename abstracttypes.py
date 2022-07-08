"""Abstract classes for type hints"""

from constants import Duties,Shifts,Staff

class Constraint():
    """base class for constraints"""
    def __init__(self, rota, *, startdate=None, enddate=None, weekdays=None, exclusions=None, **kwargs):
        pass
    def days(self):
        """return iterator of days"""

    def apply_constraint(self):
        """apply constraint to model"""
        
    def define_constraint(self, **kwargs):
        """actual constraint definition"""
        
    def event_stream(self, solver, event_stream):
        """called after solver has completed"""
        
    def remove(self):
        """remove constraint from model"""
        

class RotaSolver():
    """Main rotasolver class"""

    def make_json_solution(self, solver, all_duties):
        """Render solution as JSON
        params: solver:solver class
        all_duties:dict of variables
        """
 
    def get_duty(self, duty: Duties, day: int, shift: Shifts, staff: Staff):
        """retrieve the duty atom"""
 
    def create_duty(self, duty: Duties, day: int, shift: Shifts, staff: Staff):
        """create duty"""
 
    def get_or_create_duty(self, duty: Duties, day: int, shift: Shifts, staff: Staff):
        """Retrieve duty or create new if not found"""
 
    def __init__(self,
                 leavebook: dict,
                 slots_on_rota: int,
                 people_on_rota: int,
                 startdate: str,
                 enddate:str,
                 pipe):

        pass

    def set_enforcement_period(self, startdate, enddate, exclusions=None):
        """sets period for enforcement of rules"""
    
    def clear_enforcement_period(self):
        """clear previously set enforcement period"""
    
    def days(self, startdate=None, enddate=None, weekdays=None, exclusions=None):
        """returns iterator of days"""
    
    def apply_jobplans(self):
        """apply jobplans"""

    def apply_base_rules(self):
        """apply basic rules"""

    def apply_constraint(self, constraintspec):
        """Convenience method for constraintmanager.apply_constraint(model,**constraintspec)"""

    def solve(self):
        """solve model"""
