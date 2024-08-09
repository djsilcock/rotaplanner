from nicegui import ui
from nicegui.binding import BindableProperty,bind
import json

cells={}
selection_grid={'x0':None,'y0':None,'x1':None}

class Coords:
    x0=BindableProperty()
    y0=BindableProperty()
    cx=BindableProperty()
    cy=BindableProperty()
    def __init__(self):
        self.x0=None
        self.y0=None
        self.cx=None
        self.cy=None
        self.dragging=False


class colorful_div(ui.element):
    """A label with a bindable background color."""

    # This class variable defines what happens when the background property changes.
    x0 = BindableProperty(on_change=lambda sender,val:sender._handle_background_change())
    y0 = BindableProperty(on_change=lambda sender,val:sender._handle_background_change())
    cx = BindableProperty(on_change=lambda sender,val:sender._handle_background_change())
    cy = BindableProperty(on_change=lambda sender,val:sender._handle_background_change())

    def __init__(self, x,y) -> None:
        super().__init__('div')
        self.style(f'grid-row:{y+1};grid-column:{x+2};')
        self.my_x=x
        self.my_y=y
        self.background= None  # initialize the background property
        

    def _handle_background_change(self) -> None:
        """Update the classes of the label when the background property changes."""
        try:
            if all(x is not None for x in (self.x0,self.cx,self.my_x,self.y0,self.cy,self.my_y)) and sorted([self.x0,self.cx,self.my_x])[1]==self.my_x and sorted([self.y0,self.cy,self.my_y])[1]==self.my_y:
                bg_class='bg-yellow'
            else:
                bg_class='bg-white'
            self._classes = [c for c in self._classes if not c.startswith('bg-')]
            self._classes.append(bg_class)
            self.update()
        except TypeError:
            print (json.dumps({'cx':self.cx,'cy':self.cy,'x0':self.x0,'y0':self.y0,'my_x':self.my_x,'my_y':self.my_y}))



def make_handlers(x,y):
    def on_hover(e):
        if e.args['buttons']:
            if coords.x0 is None or not coords.dragging:
                coords.x0=x
                coords.y0=y
            coords.cx=x
            coords.cy=y
            coords.dragging=True
    def on_click(e):
        coords.dragging=False
        coords.x0=x
        coords.y0=y
        coords.cx=x
        coords.cy=y
    return on_hover,on_click

coords=Coords()
rows=4
def mouseup(e):
    coords.dragging=False
    print(e.args['button'])
with ui.element('div').style('position:relative;user-select:none'):
  with ui.grid(rows=f'repeat({rows},3rem)',columns=100).style(add="width:8000px") as grid:
    grid.on('mouseup',mouseup)
    for y in range(rows):
        with ui.element('div').style(f'position:sticky;z-index:100;left:0px;background-color:gray;grid-column:1;grid-row:{y+1};'):
                ui.label(f'Row {y}')

    for x in range(100):
      for y in range(rows):
        with colorful_div(x,y) as cell:
            ui.label('Hello!').bind_text(coords,'cx',backward=json.dumps,forward=json.loads)
            ui.label(str(x))
            bind(self_obj=cell, self_name='x0',other_obj=coords, other_name='x0')
            bind(self_obj=cell, self_name='y0',other_obj=coords, other_name='y0')
            bind(self_obj=cell, self_name='cx',other_obj=coords, other_name='cx')
            bind(self_obj=cell, self_name='cy',other_obj=coords, other_name='cy')
            on_hover,on_click=make_handlers(x,y)
            cell.on('mousemove',on_hover)
            cell.on('click',on_click)
            with ui.context_menu():
                ui.menu_item('bleh')
                

ui.run()