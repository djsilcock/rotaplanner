from collections import namedtuple

Frontend=namedtuple('Frontend',('name','url','description'))

class Constraint:
    apply_before:list[str]|None=None
    apply_requires:list[str]|None=None
    name:str=""
    def apply_constraint(self,ctx):
        pass
    async def apply_contraint_async(self,ctx):
        return self.apply_constraint(ctx)
    def build_output(self,ctx,output_dict,solver):
        pass
    async def build_output_async(self,ctx,output_dict,solver):
        return self.build_output(ctx,output_dict,solver)
    def get_frontend_src(self):
        return Frontend(self.name,None,None)
