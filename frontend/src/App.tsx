
import MenuIcon from "@suid/icons-material/Menu";
import PersonIcon from "@suid/icons-material/Person";
import MapIcon from "@suid/icons-material/Map";
import {
  AppBar,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from "@suid/material";
import { DrawerProps } from "@suid/material/Drawer";
import { createMutable } from "solid-js/store";
import { createSignal } from "solid-js";
import { Route,HashRouter as Router,A } from "@solidjs/router";
import { Build } from "@suid/icons-material";

function B(props) {
  return props.children
}
function MenuItem(props: { href: string, icon: any, text: string }) { 
  return <A href={props.href}><ListItem disablePadding>
            <ListItemButton>
              <ListItemIcon>
                {props.icon}
              </ListItemIcon>
              <ListItemText primary={props.text} />
            </ListItemButton>
          </ListItem></A>
}
function Layout(props:any) {
  const [isOpen,setOpen] = createSignal(false)

  const toggleDrawer =
    (open: boolean) => (event: MouseEvent | KeyboardEvent) => {
      if (event.type === "keydown") {
        const keyboardEvent = event as KeyboardEvent;
        if (keyboardEvent.key === "Tab" || keyboardEvent.key === "Shift")
          return;
      }
      setOpen(open);
    };

  const list = () => (
    <Box
      sx={{ width: 250 }}
      role="presentation"
      onClick={toggleDrawer(false)}
      onKeyDown={toggleDrawer(false)}
    >
      <List>
        
          
        <MenuItem href="/rota-by-person" icon={<PersonIcon />} text="Rota by person" />
        <MenuItem href="/rota-by-location" icon={<MapIcon />} text="Rota by location" />
      </List>
      <Divider />
      <List>
        <MenuItem href="/manage-activity-templates" icon={<Build />} text="Manage activity templates" />
        <MenuItem href="/manage-supply-templates" icon={<Build />} text="Manage supply templates" />
        <MenuItem href="/rota-solver" icon={<Build />} text="Rota solver" />
        <MenuItem href="/import-from-clw" icon={<Build />} text="Import from CLW" />
        <MenuItem href="/setup-staff" icon={<Build />} text="Setup staff" />
      </List>
    </Box>
  );

  return (
    <div>
        <AppBar position="static">
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2 }}
            onClick={toggleDrawer(true)}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            News
          </Typography>
          <Button color="inherit">Login</Button>
        </Toolbar>
      </AppBar>
          
          <Drawer
            anchor='left'
            open={isOpen()}
            sx={{ zIndex: 9999 }}
            onClose={toggleDrawer(false)}
          >
            {list()}
          </Drawer>
        {props.children}
    
    </div>
  );
}

function IndexPage() {
  return <div>Hello!</div>
}
function NotFound() {
  return <div>Not here!</div>
}
export default function App() {
  return <Router root={Layout} base="/site">
    <Route path='/' component={IndexPage} />
    <Route path="*404" component={NotFound}/>
  </Router>
}