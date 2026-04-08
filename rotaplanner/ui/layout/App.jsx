import MenuIcon from "@suid/icons-material/Menu";
import PersonIcon from "@suid/icons-material/Person";
import MapIcon from "@suid/icons-material/Map";
import Build from "@suid/icons-material/Build";
import ArrowDownward from "@suid/icons-material/ArrowDropDown";
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
import {
  Route,
  HashRouter as Router,
  A,
  query,
  useParams,
} from "@solidjs/router";
import { createSignal, lazy, Match } from "solid-js";

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

import { NavigationMenu } from "@kobalte/core/navigation-menu";
import "./navmenu.css";
export function NavMenu() {
  const [orientation, setOrientation] = createSignal("horizontal");
  return (
    <NavigationMenu class="navigation-menu__root" orientation={orientation()}>
      <NavigationMenu.Menu>
        <NavigationMenu.Trigger class="navigation-menu__trigger">
          Rota{" "}
          <NavigationMenu.Icon class="navigation-menu__trigger-indicator">
            <ArrowDownward />
          </NavigationMenu.Icon>
        </NavigationMenu.Trigger>
        <NavigationMenu.Portal>
          <NavigationMenu.Content class="navigation-menu__content content-1">
            <NavigationMenu.Item
              class="navigation-menu__item"
              href="/rota-grid/staff"
            >
              <NavigationMenu.ItemLabel class="navigation-menu__item-label">
                By person
              </NavigationMenu.ItemLabel>
              <NavigationMenu.ItemDescription class="navigation-menu__item-description">
                View rota organized by staff members.
              </NavigationMenu.ItemDescription>
            </NavigationMenu.Item>
            <NavigationMenu.Item
              class="navigation-menu__item"
              href="/rota-grid/location"
            >
              <NavigationMenu.ItemLabel class="navigation-menu__item-label">
                By location
              </NavigationMenu.ItemLabel>
              <NavigationMenu.ItemDescription class="navigation-menu__item-description">
                View rota organized by locations.
              </NavigationMenu.ItemDescription>
            </NavigationMenu.Item>
          </NavigationMenu.Content>
        </NavigationMenu.Portal>
      </NavigationMenu.Menu>
      <NavigationMenu.Menu>
        <NavigationMenu.Trigger class="navigation-menu__trigger">
          Manage{" "}
          <NavigationMenu.Icon class="navigation-menu__trigger-indicator">
            <ArrowDownward />
          </NavigationMenu.Icon>
        </NavigationMenu.Trigger>
        <NavigationMenu.Portal>
          <NavigationMenu.Content class="navigation-menu__content content-2">
            <NavigationMenu.Item
              class="navigation-menu__item"
              href="/manage-activity-templates"
            >
              <NavigationMenu.ItemLabel class="navigation-menu__item-label">
                Activity templates
              </NavigationMenu.ItemLabel>
              <NavigationMenu.ItemDescription class="navigation-menu__item-description">
                Create and manage activity templates.
              </NavigationMenu.ItemDescription>
            </NavigationMenu.Item>
            <NavigationMenu.Item
              class="navigation-menu__item"
              href="/manage-supply-templates"
            >
              <NavigationMenu.ItemLabel class="navigation-menu__item-label">
                Supply templates
              </NavigationMenu.ItemLabel>
              <NavigationMenu.ItemDescription class="navigation-menu__item-description">
                Create and manage supply templates.
              </NavigationMenu.ItemDescription>
            </NavigationMenu.Item>
            <NavigationMenu.Item
              class="navigation-menu__item"
              href="/rota-solver"
            >
              <NavigationMenu.ItemLabel class="navigation-menu__item-label">
                Rota solver
              </NavigationMenu.ItemLabel>
              <NavigationMenu.ItemDescription class="navigation-menu__item-description">
                Solve the rota using the solver.
              </NavigationMenu.ItemDescription>
            </NavigationMenu.Item>
            <NavigationMenu.Item
              class="navigation-menu__item"
              href="/import-from-clw"
            >
              <NavigationMenu.ItemLabel class="navigation-menu__item-label">
                Import from CLW
              </NavigationMenu.ItemLabel>
              <NavigationMenu.ItemDescription class="navigation-menu__item-description">
                Import data from CLW.
              </NavigationMenu.ItemDescription>
            </NavigationMenu.Item>
            <NavigationMenu.Item
              class="navigation-menu__item"
              href="/setup-staff"
            >
              <NavigationMenu.ItemLabel class="navigation-menu__item-label">
                Setup staff
              </NavigationMenu.ItemLabel>
              <NavigationMenu.ItemDescription class="navigation-menu__item-description">
                Add and manage staff members.
              </NavigationMenu.ItemDescription>
            </NavigationMenu.Item>
          </NavigationMenu.Content>
        </NavigationMenu.Portal>
      </NavigationMenu.Menu>
      <NavigationMenu.Viewport class="navigation-menu__viewport">
        <NavigationMenu.Arrow class="navigation-menu__arrow" />
      </NavigationMenu.Viewport>
    </NavigationMenu>
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
      <NavMenu />

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

const Table = lazy(() => import("../table/components/table"));

export default function App() {
  return (
    <Router root={Layout}>
      <Route path="/" component={IndexPage} />
      <Route path="/rota-grid/:tableType" component={Table} />

      <Route path="/manage-activity-templates" component={NotFound} />

      <Route path="*404" component={NotFound} />
    </Router>
  );
}
