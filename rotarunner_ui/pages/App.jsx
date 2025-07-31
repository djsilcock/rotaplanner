import MenuIcon from "@suid/icons-material/Menu";
import PersonIcon from "@suid/icons-material/Person";
import MapIcon from "@suid/icons-material/Map";
import Build from "@suid/icons-material/Build";
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
import { Route, HashRouter as Router, A, query } from "@solidjs/router";
import { createSignal, lazy } from "solid-js";
import { QueryClient, QueryClientProvider } from "@tanstack/solid-query";
import { client } from "../generatedTypes/client.gen";

client.setConfig({
  baseUrl: "http://localhost:8000",
});
/**
 * @typedef {Object} MenuItemProps
 * @property {string} href
 * @property {any} icon
 * @property {string} text
 */

/**
 * @param {MenuItemProps} props
 */
function MenuItem(props) {
  return (
    <A href={props.href}>
      <ListItem disablePadding>
        <ListItemButton>
          <ListItemIcon>{props.icon}</ListItemIcon>
          <ListItemText primary={props.text} />
        </ListItemButton>
      </ListItem>
    </A>
  );
}
function Layout(props) {
  const [isOpen, setOpen] = createSignal(false);

  const toggleDrawer = (open) => (event) => {
    if (event.type === "keydown") {
      const keyboardEvent = event;
      if (keyboardEvent.key === "Tab" || keyboardEvent.key === "Shift") return;
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
        <MenuItem
          href="/rota-grid/staff"
          icon={<PersonIcon />}
          text="Rota by person"
        />
        <MenuItem
          href="/rota-grid/location"
          icon={<MapIcon />}
          text="Rota by location"
        />
      </List>
      <Divider />
      <List>
        <MenuItem
          href="/manage-activity-templates"
          icon={<Build />}
          text="Manage activity templates"
        />
        <MenuItem
          href="/manage-supply-templates"
          icon={<Build />}
          text="Manage supply templates"
        />
        <MenuItem href="/rota-solver" icon={<Build />} text="Rota solver" />
        <MenuItem
          href="/import-from-clw"
          icon={<Build />}
          text="Import from CLW"
        />
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
        anchor="left"
        open={isOpen()}
        sx={{ zIndex: 9999 }}
        onClose={toggleDrawer(false)}
      >
        {list()}
      </Drawer>
      <div style={{ padding: "1em" }}>{props.children}</div>
    </div>
  );
}

function IndexPage() {
  return <div>Hello!</div>;
}
function NotFound() {
  return <div>Not here!</div>;
}

const Table = lazy(() => import("./table"));
function TableByStaff() {
  return <Table y_axis_type="staff" />;
}
function TableByLocation() {
  return <Table y_axis_type="location" />;
}

const queryClient = new QueryClient();
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router root={Layout} base="/site">
        <Route path="/" component={IndexPage} />
        <Route path="/rota-grid/staff" component={TableByStaff} />
        <Route path="/rota-grid/location" component={TableByLocation} />
        <Route
          path="/manage-activity-templates"
          component={lazy(() => import("./activity_templates"))}
        />
        <Route path="/test-form" component={lazy(() => import("./testform"))} />
        <Route path="*404" component={NotFound} />
      </Router>
    </QueryClientProvider>
  );
}
